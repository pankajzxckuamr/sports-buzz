"""
run.py — Unified launcher for Sports Buzz + AthleteX frontend

Usage:
  python run.py setup              # First time: seed DB with players & sources
  python run.py crawl              # Run one crawl cycle (all sports)
  python run.py crawl --sport Cricket
  python run.py crawl --no-parallel
  python run.py schedule           # Crawl every 6 hours (production mode)
  python run.py api                # Start the REST API server on :8081
  python run.py dev                # API + instructions for frontend dev server
  python run.py all                # API + scheduled crawler together
  python run.py status             # Print current DB stats
  python run.py buzz               # Print today's top buzz scores
"""

import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# ── Command implementations ────────────────────────────────────────────────────

def cmd_setup():
    """Seed the DB with all players and sources."""
    from players_seed import seed
    seed()
    print("\n✓ Setup complete.")
    print("  Next steps:")
    print("    python run.py crawl        — fetch real article data")
    print("    python run.py api          — start the API server for the frontend")
    print("    python run.py dev          — full dev environment instructions")


def cmd_crawl(args):
    """Run one crawl cycle."""
    from crawler import run_crawl
    sport    = None
    parallel = True
    for i, arg in enumerate(args):
        if arg == "--sport" and i + 1 < len(args):
            sport = args[i + 1]
        if arg == "--no-parallel":
            parallel = False
    run_crawl(sport_filter=sport, parallel=parallel)


def cmd_schedule(args):
    """Run crawler on a repeating schedule."""
    from crawler import start_scheduler
    hours = 6
    sport = None
    for i, arg in enumerate(args):
        if arg == "--hours" and i + 1 < len(args):
            hours = int(args[i + 1])
        if arg == "--sport" and i + 1 < len(args):
            sport = args[i + 1]
    start_scheduler(interval_hours=hours, sport_filter=sport)


def cmd_api(args):
    """Start the REST API server."""
    from api import start_api
    port = 8081
    for i, arg in enumerate(args):
        if arg == "--port" and i + 1 < len(args):
            port = int(args[i + 1])
    start_api(port=port)


def cmd_dev(args):
    """
    Start the API server and print instructions for the React dev server.
    The React frontend (AthleteX) auto-detects the crawler and shows live data.
    """
    import os
    from api import start_api

    frontend_path = Path(__file__).parent.parent / "athletepulse2"

    print("\n" + "═" * 60)
    print("  Sports Buzz + AthleteX — Development Mode")
    print("═" * 60)
    print()
    print("  Step 1 (this terminal): API server starting on :8081")
    print()
    print("  Step 2 (new terminal): Start the React frontend")
    print(f"    cd {frontend_path}")
    print( "    npm install   (first time only)")
    print( "    npm run dev")
    print()
    print("  Step 3 (optional, new terminal): Run a crawl")
    print( "    python run.py crawl")
    print()
    print("  The AthleteX UI will:")
    print("    ✓  Show 'Crawler Online' badge when API is reachable")
    print("    ✓  Load real articles + buzz scores from the crawler")
    print("    ✓  Fall back to mock data when the API is offline")
    print()
    print("─" * 60)
    print()

    # Start API in this process
    start_api(port=8081)


def cmd_all(args):
    """Start both API server and scheduled crawler in parallel."""
    from api import start_api
    from crawler import start_scheduler

    print("[All] Starting API server and scheduler together …")
    print("[All] AthleteX frontend: cd athletepulse2 && npm run dev")
    print()

    api_thread = threading.Thread(
        target=start_api,
        kwargs={"port": 8081},
        daemon=True
    )
    api_thread.start()

    # Crawler runs in the main thread (blocking)
    start_scheduler(interval_hours=6)


def cmd_status():
    """Print DB stats."""
    from database import init_db, get_conn
    init_db()
    conn = get_conn()

    print("\n── Sports Buzz DB Status ─────────────────────────────────")
    for label, sql in [
        ("Players tracked",    "SELECT COUNT(*) FROM players"),
        ("Sources configured", "SELECT COUNT(*) FROM sources"),
        ("Articles stored",    "SELECT COUNT(*) FROM articles"),
        ("Mentions recorded",  "SELECT COUNT(*) FROM mentions"),
        ("Pages crawled today","SELECT COUNT(*) FROM crawl_log WHERE DATE(crawled_at)=DATE('now')"),
        ("Articles today",     "SELECT COUNT(*) FROM articles WHERE DATE(crawled_at)=DATE('now')"),
    ]:
        val = conn.execute(sql).fetchone()[0]
        print(f"  {label:<26} {val}")

    print("\n── Sports breakdown ──────────────────────────────────────")
    rows = conn.execute(
        "SELECT sport, COUNT(*) as cnt FROM players GROUP BY sport ORDER BY cnt DESC"
    ).fetchall()
    for r in rows:
        print(f"  {r[0]:<20} {r[1]} players")

    conn.close()
    print()


def cmd_social(args):
    """Fetch X / YouTube / Instagram JSON per config/social_accounts.yaml → sports-data-backend."""
    from social.run import run_social_ingest

    run_social_ingest()


def cmd_buzz(args):
    """Print today's top buzz scores."""
    from database import get_top_buzz, init_db
    init_db()

    sport = None
    limit = 15
    for i, arg in enumerate(args):
        if arg == "--sport" and i + 1 < len(args):
            sport = args[i + 1]
        if arg == "--limit" and i + 1 < len(args):
            limit = int(args[i + 1])

    top = get_top_buzz(sport=sport, limit=limit)

    title = f"Top Buzz Today{' — ' + sport if sport else ''}"
    print(f"\n── {title} {'─' * max(0, 45 - len(title))}")
    if not top:
        print("  No buzz scores yet. Run:  python run.py crawl")
    else:
        for i, p in enumerate(top, 1):
            bar = "█" * int(p["buzz_score"] / 5)
            print(f"  {i:>2}. {p['name']:<25} {p['sport']:<12} "
                  f"{p['buzz_score']:>6.1f}  {bar}")
    print()


# ── Command registry ───────────────────────────────────────────────────────────

COMMANDS = {
    "setup":    (cmd_setup,    "Seed DB with players & sources (first time)"),
    "crawl":    (cmd_crawl,    "Run one crawl cycle  [--sport X] [--no-parallel]"),
    "social":   (cmd_social,   "Ingest social JSON (X/YouTube/IG) → sports-data-backend"),
    "schedule": (cmd_schedule, "Crawl on a schedule  [--hours N] [--sport X]"),
    "api":      (cmd_api,      "Start REST API server on :8081 [--port N]"),
    "dev":      (cmd_dev,      "API + frontend dev setup instructions"),
    "all":      (cmd_all,      "Start API + scheduled crawler together"),
    "status":   (cmd_status,   "Show DB stats"),
    "buzz":     (cmd_buzz,     "Show today's top buzz [--sport X] [--limit N]"),
}


def usage():
    print("\nUsage:  python run.py <command> [options]\n")
    print("Commands:")
    for cmd, (_, desc) in COMMANDS.items():
        print(f"  {cmd:<12} {desc}")
    print()
    print("Quick start:")
    print("  python run.py setup         — seed the database")
    print("  python run.py api           — start API server")
    print("  python run.py crawl         — fetch sports data")
    print("  python run.py dev           — full dev mode with frontend instructions")
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        usage()
        sys.exit(1)

    command = sys.argv[1]
    rest    = sys.argv[2:]
    fn, _   = COMMANDS[command]

    if command in ("setup", "status", "social"):
        fn()
    else:
        fn(rest)
