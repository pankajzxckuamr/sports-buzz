"""
api.py — REST API server for Sports Buzz Crawler

Serves crawled data to the AthleteX React frontend.

Endpoints:
  GET /api/players                    — list all players (?sport=Cricket)
  GET /api/players/<id>/buzz          — buzz history for a player (?days=7)
  GET /api/players/<id>/articles      — recent articles mentioning a player
  GET /api/players/<id>/trend         — buzz trend for charting (?days=30)
  GET /api/buzz/top                   — top buzzing players today (?sport=&limit=10)
  GET /api/buzz/leaderboard           — full leaderboard across all sports
  GET /api/search?q=name              — search players by name
  GET /api/stats                      — crawler stats (total articles, mentions, etc.)

CORS is enabled for all origins so the React dev server (localhost:5173)
can call this API freely without proxy configuration.
"""

import json
import sqlite3
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from database import (
    get_all_players, get_player_buzz,
    get_recent_articles, get_top_buzz, get_conn,
)


# ── CORS headers — required for React dev server (localhost:5173) ──────────────

# Allow all common frontend origins
ALLOWED_ORIGINS = [
    "http://localhost:5173",   # Vite dev server
    "http://localhost:3000",   # Create React App
    "http://localhost:8080",   # Other dev servers
    "*",                       # Fallback wildcard
]

def _cors_headers(handler):
    """Add CORS headers to allow the React frontend to call this API."""
    origin = handler.headers.get("Origin", "*")
    handler.send_header("Access-Control-Allow-Origin", origin if origin in ALLOWED_ORIGINS else "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
    handler.send_header("Access-Control-Max-Age", "86400")


# ── JSON response helpers ──────────────────────────────────────────────────────

def _json(data) -> bytes:
    return json.dumps(data, default=str, ensure_ascii=False).encode()


def _ok(handler, data, status=200):
    body = _json(data)
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    _cors_headers(handler)
    handler.end_headers()
    handler.wfile.write(body)


def _error(handler, msg, status=400):
    _ok(handler, {"error": msg}, status)


# ── Route handlers ─────────────────────────────────────────────────────────────

def route_players(handler, params):
    """GET /api/players?sport=Cricket"""
    players = get_all_players()
    sport = params.get("sport", [None])[0]
    if sport:
        players = [p for p in players if p["sport"].lower() == sport.lower()]
    _ok(handler, {"players": players, "count": len(players)})


def route_player_buzz(handler, params, player_id):
    """GET /api/players/<id>/buzz?days=7"""
    days = int(params.get("days", [7])[0])
    buzz = get_player_buzz(player_id, days)
    _ok(handler, {"player_id": player_id, "buzz_history": buzz})


def route_player_articles(handler, params, player_id):
    """GET /api/players/<id>/articles?limit=20"""
    limit = int(params.get("limit", [20])[0])
    articles = get_recent_articles(player_id, limit)
    _ok(handler, {"player_id": player_id, "articles": articles, "count": len(articles)})


def route_top_buzz(handler, params):
    """GET /api/buzz/top?sport=Football&limit=10&date=2024-01-15"""
    sport = params.get("sport", [None])[0]
    limit = int(params.get("limit", [10])[0])
    date  = params.get("date",  [None])[0]
    top   = get_top_buzz(sport=sport, date=date, limit=limit)
    _ok(handler, {"top_players": top, "count": len(top)})


def route_leaderboard(handler, params):
    """GET /api/buzz/leaderboard — ranked players for today"""
    date  = params.get("date",  [None])[0]
    limit = int(params.get("limit", [20])[0])
    sport = params.get("sport", [None])[0]
    conn  = get_conn()

    if sport:
        rows = conn.execute(
            """SELECT p.id AS player_id, p.name, p.sport,
                      b.buzz_score, b.mention_count,
                      b.article_count, b.avg_sentiment, b.date
               FROM buzz_scores b
               JOIN players p ON p.id = b.player_id
               WHERE b.date = COALESCE(?, DATE('now'))
                 AND p.sport = ?
               ORDER BY b.buzz_score DESC
               LIMIT ?""",
            (date, sport, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT p.id AS player_id, p.name, p.sport,
                      b.buzz_score, b.mention_count,
                      b.article_count, b.avg_sentiment, b.date
               FROM buzz_scores b
               JOIN players p ON p.id = b.player_id
               WHERE b.date = COALESCE(?, DATE('now'))
               ORDER BY b.buzz_score DESC
               LIMIT ?""",
            (date, limit)
        ).fetchall()

    conn.close()
    _ok(handler, {"leaderboard": [dict(r) for r in rows]})


def route_search(handler, params):
    """GET /api/search?q=Messi"""
    q = params.get("q", [""])[0].strip()
    if not q:
        _error(handler, "Missing query parameter 'q'")
        return
    conn = get_conn()
    rows = conn.execute(
        """SELECT p.*, COALESCE(b.buzz_score, 0) AS latest_buzz
           FROM players p
           LEFT JOIN buzz_scores b ON b.player_id = p.id
                                   AND b.date = DATE('now')
           WHERE p.name LIKE ? OR p.aliases LIKE ?
           ORDER BY latest_buzz DESC
           LIMIT 20""",
        (f"%{q}%", f"%{q}%")
    ).fetchall()
    conn.close()
    _ok(handler, {"results": [dict(r) for r in rows], "query": q})


def route_stats(handler, params):
    """GET /api/stats — overall crawler health stats"""
    conn = get_conn()
    stats = {}
    stats["total_players"]  = conn.execute("SELECT COUNT(*) FROM players").fetchone()[0]
    stats["total_sources"]  = conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
    stats["total_articles"] = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    stats["total_mentions"] = conn.execute("SELECT COUNT(*) FROM mentions").fetchone()[0]
    stats["articles_today"] = conn.execute(
        "SELECT COUNT(*) FROM articles WHERE DATE(crawled_at) = DATE('now')"
    ).fetchone()[0]
    stats["pages_crawled_today"] = conn.execute(
        "SELECT COUNT(*) FROM crawl_log WHERE DATE(crawled_at) = DATE('now') AND status = 'ok'"
    ).fetchone()[0]
    stats["top_player_today"] = conn.execute(
        """SELECT p.name, b.buzz_score
           FROM buzz_scores b JOIN players p ON p.id = b.player_id
           WHERE b.date = DATE('now')
           ORDER BY b.buzz_score DESC LIMIT 1"""
    ).fetchone()
    if stats["top_player_today"]:
        stats["top_player_today"] = dict(stats["top_player_today"])
    conn.close()
    _ok(handler, stats)


def route_player_trend(handler, params, player_id):
    """GET /api/players/<id>/trend?days=30"""
    days = int(params.get("days", [30])[0])
    conn = get_conn()
    rows = conn.execute(
        """SELECT date, buzz_score, mention_count, avg_sentiment
           FROM buzz_scores
           WHERE player_id = ?
           ORDER BY date ASC
           LIMIT ?""",
        (player_id, days)
    ).fetchall()
    conn.close()
    _ok(handler, {"player_id": player_id, "trend": [dict(r) for r in rows]})


# ── Request router ─────────────────────────────────────────────────────────────

class SportsAPI(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        print(f"[API] {self.address_string()} — {format % args}")

    def do_OPTIONS(self):
        """Handle CORS preflight — required by browsers before cross-origin requests."""
        self.send_response(204)
        _cors_headers(self)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path   = parsed.path.rstrip("/")
        params = parse_qs(parsed.query)

        if path == "/api/players":
            route_players(self, params); return

        m = self._match(path, "/api/players/{id}/buzz")
        if m is not None:
            route_player_buzz(self, params, m); return

        m = self._match(path, "/api/players/{id}/articles")
        if m is not None:
            route_player_articles(self, params, m); return

        m = self._match(path, "/api/players/{id}/trend")
        if m is not None:
            route_player_trend(self, params, m); return

        if path == "/api/buzz/top":
            route_top_buzz(self, params); return

        if path == "/api/buzz/leaderboard":
            route_leaderboard(self, params); return

        if path == "/api/search":
            route_search(self, params); return

        if path == "/api/stats":
            route_stats(self, params); return

        _error(self, f"Unknown endpoint: {path}", 404)

    @staticmethod
    def _match(path: str, pattern: str):
        """
        Match /api/players/{id}/... patterns.
        Returns the integer ID if matched, else None.
        """
        parts = path.split("/")
        pat   = pattern.split("/")
        if len(parts) != len(pat):
            return None
        pid = None
        for p, q in zip(parts, pat):
            if q == "{id}":
                try:
                    pid = int(p)
                except ValueError:
                    return None
            elif p != q:
                return None
        return pid


# ── Server startup ─────────────────────────────────────────────────────────────

def start_api(host="0.0.0.0", port=8081):
    server = HTTPServer((host, port), SportsAPI)
    print(f"[API] Sports Buzz API running on http://localhost:{port}")
    print(f"[API] CORS enabled for React frontend (localhost:5173)")
    print(f"[API] Available endpoints:")
    for ep in [
        "GET /api/players?sport=Cricket",
        "GET /api/players/<id>/buzz?days=7",
        "GET /api/players/<id>/articles",
        "GET /api/players/<id>/trend?days=30",
        "GET /api/buzz/top?sport=Football&limit=10",
        "GET /api/buzz/leaderboard",
        "GET /api/search?q=Messi",
        "GET /api/stats",
    ]:
        print(f"        {ep}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[API] Shutting down.")
        server.server_close()


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Sports Buzz API Server")
    ap.add_argument("--port", type=int, default=8081)
    ap.add_argument("--host", default="0.0.0.0")
    args = ap.parse_args()
    start_api(args.host, args.port)
