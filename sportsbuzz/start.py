#!/usr/bin/env python3
"""
start.py — Single-command launcher for Sports Buzz (full stack).

Usage:
  python start.py           # Start API server only (frontend connects to it)
  python start.py --setup   # First-time: seed DB with players & sources
  python start.py --crawl   # Seed + crawl once + start API
  python start.py --all     # Seed + crawl + API + schedule every 6h

The React frontend is served separately:
  cd frontend && npm install && npm run dev   (runs on http://localhost:5173)
"""

import sys
import os
import subprocess
import threading
from pathlib import Path

# Make sure backend is on the Python path
BACKEND_DIR = Path(__file__).parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# Change to backend dir so relative paths (sports_buzz.db, etc.) work correctly
os.chdir(BACKEND_DIR)


def banner(text):
    line = "─" * 58
    print(f"\n{line}")
    print(f"  {text}")
    print(f"{line}\n")


def run_setup():
    banner("Setting up Sports Buzz database…")
    from players_seed import seed
    seed()
    print("\n✓ Setup complete — 38 players + 19 sources seeded.\n")


def run_crawl(sport=None):
    banner(f"Running crawl{'  (sport: ' + sport + ')' if sport else ''}…")
    from crawler import run_crawl as crawl
    crawl(sport_filter=sport)


def run_api(port=8081):
    banner(f"Starting Sports Buzz API on http://localhost:{port}")
    from api import start_api
    start_api(port=port)


def run_scheduler(hours=6):
    from crawler import start_scheduler
    start_scheduler(interval_hours=hours)


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Sports Buzz launcher")
    ap.add_argument("--setup",  action="store_true", help="Seed the database first")
    ap.add_argument("--crawl",  action="store_true", help="Run one crawl cycle after setup")
    ap.add_argument("--all",    action="store_true", help="Setup + crawl + API + scheduler")
    ap.add_argument("--sport",  default=None,        help="Filter crawl by sport")
    ap.add_argument("--port",   type=int, default=8081)
    args = ap.parse_args()

    if args.all or args.setup:
        run_setup()

    if args.all or args.crawl:
        run_crawl(args.sport)

    if args.all:
        # Run scheduler in a background thread, API in foreground
        banner("Starting scheduler (every 6h) + API server…")
        t = threading.Thread(target=run_scheduler, daemon=True)
        t.start()
        run_api(args.port)
    else:
        # Just start the API (default behaviour)
        run_api(args.port)


if __name__ == "__main__":
    main()
