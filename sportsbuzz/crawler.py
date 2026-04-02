"""
crawler.py — Core web crawler for Sports Buzz

Architecture:
  - BFS crawl starting from each source's base URL
  - Respects a polite crawl delay between requests
  - Reuses your existing browser.py fetch() function
  - Detects player mentions via parser.py
  - Stores everything in SQLite via database.py
  - Can be run manually or scheduled (cron / APScheduler)
"""

import sys
import time
import random
import threading
from collections import deque
from datetime import datetime
from pathlib import Path

# Allow running from any working directory
sys.path.insert(0, str(Path(__file__).parent))

from browser import fetch
from parser import parse_html, extract_links, find_mentions
from database import (
    init_db,
    get_all_players,
    save_article,
    save_mention,
    log_crawl,
    already_crawled_today,
    compute_buzz_scores,
)
from config_loader import get_sources_for_crawl
from backend_client import ingest_html, is_backend_configured


# ── Configuration ──────────────────────────────────────────────────────────────

class CrawlerConfig:
    MAX_PAGES_PER_SOURCE   = 30       # pages to crawl per source per run
    CRAWL_DELAY_MIN        = 1.5      # seconds — be polite
    CRAWL_DELAY_MAX        = 3.5
    MAX_DEPTH              = 2        # BFS depth from base URL
    MIN_TEXT_LENGTH        = 200      # skip pages with too little text
    REQUEST_TIMEOUT        = 10       # seconds
    MAX_THREADS            = 4        # parallel sources (not parallel per source)
    SKIP_EXTENSIONS = {
        ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg",
        ".mp4", ".mp3", ".zip", ".css", ".js", ".xml",
        ".ico", ".woff", ".woff2", ".ttf"
    }


# ── URL filter ─────────────────────────────────────────────────────────────────

def _should_crawl(url: str) -> bool:
    """Return False for URLs we definitely don't want."""
    if not url or len(url) > 500:
        return False
    lower = url.lower()
    for ext in CrawlerConfig.SKIP_EXTENSIONS:
        if lower.endswith(ext) or f"{ext}?" in lower:
            return False
    skip_patterns = [
        "/login", "/signup", "/register", "/logout", "/account",
        "/cart", "/checkout", "/privacy", "/terms", "/cookie",
        "/advertise", "/subscribe", "/newsletter", "javascript:",
        "mailto:", "#", "?page=", "&page=",
    ]
    return not any(p in lower for p in skip_patterns)


# ── Single-source crawler ─────────────────────────────────────────────────────

def crawl_source(source: dict, players: list, config: CrawlerConfig = None):
    """
    BFS-crawl one source and save any player mentions found.

    source = { 'id': int, 'name': str, 'base_url': str, 'sport': str, 'source_type': str }
    players = list of player dicts from database.get_all_players()
    """
    if config is None:
        config = CrawlerConfig()

    base_url   = source["base_url"].rstrip("/")
    source_id  = source["id"]
    source_name = source["name"]

    queue   = deque([(base_url, 0)])   # (url, depth)
    visited = set()
    pages_crawled = 0
    articles_saved = 0
    mentions_found = 0

    print(f"\n{'='*60}")
    print(f"[Crawl] Starting: {source_name} ({base_url})")
    print(f"{'='*60}")

    while queue and pages_crawled < config.MAX_PAGES_PER_SOURCE:
        url, depth = queue.popleft()

        if url in visited:
            continue
        visited.add(url)

        if not _should_crawl(url):
            continue

        if already_crawled_today(url):
            print(f"  [Skip] Already crawled today: {url[:70]}")
            continue

        # Polite delay
        time.sleep(random.uniform(config.CRAWL_DELAY_MIN, config.CRAWL_DELAY_MAX))

        # Fetch
        try:
            html = fetch(url)
        except Exception as e:
            print(f"  [Error] {url[:70]} — {e}")
            log_crawl(url, "error", str(e))
            continue

        if not html or not isinstance(html, str):
            log_crawl(url, "skip", "empty or binary response")
            continue

        pages_crawled += 1
        log_crawl(url, "ok")

        # Parse
        parsed = parse_html(html)
        text   = parsed["text"]

        if len(text) < config.MIN_TEXT_LENGTH:
            print(f"  [Thin] Skipping (too little text): {url[:70]}")
            continue

        print(f"  [OK] {url[:70]}")
        print(f"       Title: {parsed['title'][:60]}")

        if is_backend_configured():
            try:
                ingest_html(
                    source=source_name,
                    url=url,
                    html=html,
                    idempotency_key=f"crawler|{url}",
                )
                print(f"       → sent to sports-data-backend")
            except Exception as be:
                print(f"       [Backend] ingest failed: {be}")

        # Save article (local SQLite for buzz / AthleteX)
        article_id = save_article(
            url          = url,
            title        = parsed["title"],
            summary      = parsed["summary"],
            full_text    = text[:50_000],   # cap at 50k chars
            source_id    = source_id,
            published_at = parsed["published_at"],
        )

        if article_id:
            articles_saved += 1
            # Detect player mentions
            hits = find_mentions(text, players)
            for hit in hits:
                save_mention(
                    player_id    = hit["player_id"],
                    article_id   = article_id,
                    mention_count = hit["mention_count"],
                    sentiment    = hit["sentiment"],
                    context      = hit["context"],
                )
                mentions_found += 1
                print(f"       ✓ Mention: {hit['player_name']} "
                      f"(×{hit['mention_count']}, sentiment={hit['sentiment']:+.2f})")

        # BFS: enqueue links found on this page (up to MAX_DEPTH)
        if depth < config.MAX_DEPTH:
            links = extract_links(html, base_url)
            for link in links:
                if link not in visited:
                    queue.append((link, depth + 1))

    print(f"\n[Crawl] {source_name} done — "
          f"{pages_crawled} pages, {articles_saved} articles, "
          f"{mentions_found} mentions")
    return pages_crawled, articles_saved, mentions_found


# ── Full crawl run ─────────────────────────────────────────────────────────────

def run_crawl(sport_filter: str = None, source_ids: list = None, parallel: bool = True):
    """
    Run a full crawl of all (or filtered) sources.

    sport_filter — only crawl sources for this sport (e.g. "Cricket")
    source_ids   — whitelist of source ids (overrides sport_filter)
    parallel     — run sources in parallel threads
    """
    print(f"\n{'#'*60}")
    print(f"# Sports Buzz Crawler — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}\n")

    if is_backend_configured():
        print("[Init] SPORTS_BACKEND_URL set — HTML pages will POST to sports-data-backend\n")
    else:
        print("[Init] SPORTS_BACKEND_URL not set — only local SQLite (set .env to enable backend)\n")

    init_db()
    players = get_all_players()
    print(f"[Init] Loaded {len(players)} players to track\n")

    sources = get_sources_for_crawl(sport_filter)
    if source_ids:
        sources = [s for s in sources if s["id"] in source_ids]
    print(f"[Init] Crawling {len(sources)} sources (YAML + DB via config_loader)\n")

    if not sources:
        print("[Error] No sources found. Did you run players_seed.py first?")
        return

    config = CrawlerConfig()
    total_pages = total_articles = total_mentions = 0

    if parallel and len(sources) > 1:
        results = {}
        lock = threading.Lock()

        def _worker(source):
            p, a, m = crawl_source(source, players, config)
            with lock:
                results[source["id"]] = (p, a, m)

        threads = []
        sem = threading.Semaphore(config.MAX_THREADS)

        for source in sources:
            sem.acquire()
            def run(s=source):
                try:
                    _worker(s)
                finally:
                    sem.release()
            t = threading.Thread(target=run, daemon=True)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        for p, a, m in results.values():
            total_pages    += p
            total_articles += a
            total_mentions += m

    else:
        for source in sources:
            p, a, m = crawl_source(source, players, config)
            total_pages    += p
            total_articles += a
            total_mentions += m

    # Recompute buzz scores after crawl
    compute_buzz_scores()

    print(f"\n{'#'*60}")
    print(f"# Crawl complete!")
    print(f"#   Pages crawled:  {total_pages}")
    print(f"#   Articles saved: {total_articles}")
    print(f"#   Mentions found: {total_mentions}")
    print(f"{'#'*60}\n")


# ── Scheduler (optional — keeps crawl running every N hours) ──────────────────

def start_scheduler(interval_hours: int = 6, **kwargs):
    """
    Run crawl every `interval_hours`. Blocking — run in a background thread
    or as a standalone process.
    """
    print(f"[Scheduler] Will crawl every {interval_hours} hours. Press Ctrl+C to stop.")
    while True:
        try:
            run_crawl(**kwargs)
        except Exception as e:
            print(f"[Scheduler] Crawl failed: {e}")
        next_run = datetime.now().strftime("%H:%M:%S")
        print(f"[Scheduler] Next run in {interval_hours}h (started at {next_run})")
        time.sleep(interval_hours * 3600)


# ── CLI entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Sports Buzz Web Crawler")
    ap.add_argument("--sport",    help="Filter by sport (Cricket, Football, Basketball, Tennis)")
    ap.add_argument("--source",   type=int, nargs="+", help="Crawl specific source IDs only")
    ap.add_argument("--schedule", type=int, metavar="HOURS",
                    help="Run on a repeating schedule every N hours")
    ap.add_argument("--no-parallel", action="store_true", help="Disable parallel crawling")
    args = ap.parse_args()

    if args.schedule:
        start_scheduler(
            interval_hours = args.schedule,
            sport_filter   = args.sport,
            source_ids     = args.source,
            parallel       = not args.no_parallel,
        )
    else:
        run_crawl(
            sport_filter = args.sport,
            source_ids   = args.source,
            parallel     = not args.no_parallel,
        )
