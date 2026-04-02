"""
database.py — SQLite database manager for Sports Buzz Crawler
Handles all storage: players, articles, mentions, stats, buzz scores.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional


DB_PATH = Path(__file__).parent / "sports_buzz.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row          # rows behave like dicts
    conn.execute("PRAGMA journal_mode=WAL") # better concurrency
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create all tables if they don't exist yet."""
    conn = get_conn()
    c = conn.cursor()

    # ── Players ──────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            sport       TEXT    NOT NULL,
            nationality TEXT,
            aliases     TEXT,           -- JSON list of alternate names / nicknames
            created_at  TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── Crawl sources (sites we scrape) ──────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS sources (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            base_url    TEXT    NOT NULL UNIQUE,
            sport       TEXT,           -- NULL = general / multi-sport
            source_type TEXT    NOT NULL  -- 'news' | 'stats' | 'social'
        )
    """)

    # ── Articles ─────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            url         TEXT    NOT NULL UNIQUE,
            title       TEXT,
            summary     TEXT,
            full_text   TEXT,
            source_id   INTEGER REFERENCES sources(id),
            published_at TEXT,
            crawled_at  TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── Mentions: which player appears in which article ───────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS mentions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id   INTEGER NOT NULL REFERENCES players(id),
            article_id  INTEGER NOT NULL REFERENCES articles(id),
            mention_count INTEGER DEFAULT 1,
            sentiment   REAL,           -- -1.0 (negative) to +1.0 (positive)
            context     TEXT,           -- short snippet around the mention
            UNIQUE(player_id, article_id)
        )
    """)

    # ── Match stats ───────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS match_stats (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id   INTEGER NOT NULL REFERENCES players(id),
            match_date  TEXT,
            opponent    TEXT,
            competition TEXT,
            sport       TEXT,
            stats_json  TEXT,           -- flexible JSON blob per sport
            source_url  TEXT,
            crawled_at  TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── Daily buzz scores ─────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS buzz_scores (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id   INTEGER NOT NULL REFERENCES players(id),
            date        TEXT    NOT NULL,
            mention_count   INTEGER DEFAULT 0,
            article_count   INTEGER DEFAULT 0,
            avg_sentiment   REAL    DEFAULT 0.0,
            buzz_score      REAL    DEFAULT 0.0,  -- composite score 0-100
            UNIQUE(player_id, date)
        )
    """)

    # ── Crawl log (track what was visited & when) ─────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS crawl_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            url         TEXT    NOT NULL,
            status      TEXT    NOT NULL,  -- 'ok' | 'error' | 'skip'
            error_msg   TEXT,
            crawled_at  TEXT    DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    conn.close()
    print(f"[DB] Initialised at {DB_PATH}")


# ── Player helpers ─────────────────────────────────────────────────────────────

def upsert_player(name: str, sport: str, nationality: str = None, aliases: list = None) -> int:
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM players WHERE name = ? AND sport = ?", (name, sport))
    row = c.fetchone()
    if row:
        conn.close()
        return row["id"]
    c.execute(
        "INSERT INTO players (name, sport, nationality, aliases) VALUES (?,?,?,?)",
        (name, sport, nationality, json.dumps(aliases or []))
    )
    pid = c.lastrowid
    conn.commit()
    conn.close()
    return pid


def get_all_players():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM players ORDER BY sport, name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Source helpers ─────────────────────────────────────────────────────────────

def get_all_sources(sport_filter: Optional[str] = None) -> list:
    """All crawl sources; optional sport filter keeps multi-sport (NULL) rows."""
    conn = get_conn()
    if sport_filter:
        rows = conn.execute(
            "SELECT * FROM sources WHERE sport = ? OR sport IS NULL",
            (sport_filter,),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM sources").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def upsert_source(
    name: str,
    base_url: str,
    sport: Optional[str],
    source_type: str,
) -> int:
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM sources WHERE base_url = ?", (base_url,))
    row = c.fetchone()
    if row:
        conn.close()
        return row["id"]
    c.execute(
        "INSERT INTO sources (name, base_url, sport, source_type) VALUES (?,?,?,?)",
        (name, base_url, sport, source_type)
    )
    sid = c.lastrowid
    conn.commit()
    conn.close()
    return sid


# ── Article helpers ────────────────────────────────────────────────────────────

def save_article(url, title, summary, full_text, source_id, published_at=None) -> int | None:
    """Returns article id, or None if URL already exists."""
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute(
            """INSERT INTO articles (url, title, summary, full_text, source_id, published_at)
               VALUES (?,?,?,?,?,?)""",
            (url, title, summary, full_text, source_id, published_at)
        )
        aid = c.lastrowid
        conn.commit()
        return aid
    except sqlite3.IntegrityError:
        return None     # duplicate URL
    finally:
        conn.close()


# ── Mention helpers ────────────────────────────────────────────────────────────

def save_mention(player_id, article_id, mention_count, sentiment, context):
    conn = get_conn()
    try:
        conn.execute(
            """INSERT OR REPLACE INTO mentions
               (player_id, article_id, mention_count, sentiment, context)
               VALUES (?,?,?,?,?)""",
            (player_id, article_id, mention_count, sentiment, context)
        )
        conn.commit()
    finally:
        conn.close()


# ── Stats helpers ──────────────────────────────────────────────────────────────

def save_match_stats(player_id, match_date, opponent, competition, sport, stats_dict, source_url):
    conn = get_conn()
    conn.execute(
        """INSERT INTO match_stats
           (player_id, match_date, opponent, competition, sport, stats_json, source_url)
           VALUES (?,?,?,?,?,?,?)""",
        (player_id, match_date, opponent, competition, sport, json.dumps(stats_dict), source_url)
    )
    conn.commit()
    conn.close()


# ── Buzz score computation ─────────────────────────────────────────────────────

def compute_buzz_scores(date: str = None):
    """
    Re-compute buzz scores for all players for a given date (default: today).
    Buzz score = weighted composite of mention count + article count + sentiment.
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    conn = get_conn()
    c = conn.cursor()

    c.execute("SELECT DISTINCT player_id FROM mentions")
    player_ids = [r[0] for r in c.fetchall()]

    for pid in player_ids:
        # Articles crawled on `date` that mention this player
        c.execute("""
            SELECT COUNT(DISTINCT m.article_id) AS art_cnt,
                   SUM(m.mention_count) AS men_cnt,
                   AVG(m.sentiment) AS avg_sent
            FROM mentions m
            JOIN articles a ON a.id = m.article_id
            WHERE m.player_id = ?
              AND DATE(a.crawled_at) = ?
        """, (pid, date))
        row = c.fetchone()
        if not row or row["art_cnt"] == 0:
            continue

        art_cnt  = row["art_cnt"]  or 0
        men_cnt  = row["men_cnt"]  or 0
        avg_sent = row["avg_sent"] or 0.0

        # Simple buzz formula (tune weights as you grow)
        # mention volume (60%) + article diversity (30%) + sentiment boost (10%)
        raw = (men_cnt * 0.6) + (art_cnt * 3.0 * 0.3) + ((avg_sent + 1) * 5 * 0.1)
        buzz = min(round(raw, 2), 100.0)

        c.execute(
            """INSERT OR REPLACE INTO buzz_scores
               (player_id, date, mention_count, article_count, avg_sentiment, buzz_score)
               VALUES (?,?,?,?,?,?)""",
            (pid, date, men_cnt, art_cnt, round(avg_sent, 4), buzz)
        )

    conn.commit()
    conn.close()
    print(f"[DB] Buzz scores updated for {date}")


# ── Crawl log ──────────────────────────────────────────────────────────────────

def log_crawl(url, status, error_msg=None):
    conn = get_conn()
    conn.execute(
        "INSERT INTO crawl_log (url, status, error_msg) VALUES (?,?,?)",
        (url, status, error_msg)
    )
    conn.commit()
    conn.close()


def already_crawled_today(url: str) -> bool:
    conn = get_conn()
    row = conn.execute(
        """SELECT 1 FROM crawl_log
           WHERE url = ? AND status = 'ok'
             AND DATE(crawled_at) = DATE('now')""",
        (url,)
    ).fetchone()
    conn.close()
    return row is not None


# ── Query helpers (used by your frontend API) ─────────────────────────────────

def get_player_buzz(player_id: int, days: int = 7):
    conn = get_conn()
    rows = conn.execute(
        """SELECT date, buzz_score, mention_count, article_count, avg_sentiment
           FROM buzz_scores
           WHERE player_id = ?
           ORDER BY date DESC
           LIMIT ?""",
        (player_id, days)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_top_buzz(sport: str = None, date: str = None, limit: int = 10):
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    conn = get_conn()
    if sport:
        rows = conn.execute(
            """SELECT p.name, p.sport, b.buzz_score, b.mention_count, b.date
               FROM buzz_scores b
               JOIN players p ON p.id = b.player_id
               WHERE p.sport = ? AND b.date = ?
               ORDER BY b.buzz_score DESC
               LIMIT ?""",
            (sport, date, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT p.name, p.sport, b.buzz_score, b.mention_count, b.date
               FROM buzz_scores b
               JOIN players p ON p.id = b.player_id
               WHERE b.date = ?
               ORDER BY b.buzz_score DESC
               LIMIT ?""",
            (date, limit)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_recent_articles(player_id: int, limit: int = 20):
    conn = get_conn()
    rows = conn.execute(
        """SELECT a.title, a.url, a.summary, a.crawled_at,
                  m.sentiment, m.mention_count, s.name AS source_name
           FROM mentions m
           JOIN articles a ON a.id = m.article_id
           JOIN sources  s ON s.id = a.source_id
           WHERE m.player_id = ?
           ORDER BY a.crawled_at DESC
           LIMIT ?""",
        (player_id, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


if __name__ == "__main__":
    init_db()
