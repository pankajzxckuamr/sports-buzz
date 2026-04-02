"""
parser.py — HTML parser & NLP utilities for Sports Buzz Crawler

Responsibilities:
  - Extract article title, body text, links from raw HTML
  - Detect which players are mentioned in a piece of text
  - Compute a lightweight sentiment score (no heavy ML deps needed)
  - Pull a publication date from common meta tags
"""

import re
from html.parser import HTMLParser
from datetime import datetime


# ── Lightweight HTML → text extractor ─────────────────────────────────────────

class _TextExtractor(HTMLParser):
    """Strip all tags and collect visible text."""

    SKIP_TAGS = {"script", "style", "noscript", "head", "meta",
                 "link", "iframe", "svg", "nav", "footer", "aside"}

    def __init__(self):
        super().__init__()
        self._skip  = False
        self._depth = 0
        self.chunks = []
        self.links  = []       # list of (href, anchor_text)
        self._cur_href = None
        self._cur_anchor = []
        self.title  = ""
        self._in_title = False
        self.meta   = {}       # og:title, description, published_time, etc.

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)

        if tag in self.SKIP_TAGS:
            self._skip  = True
            self._depth = 1
            return

        if self._skip:
            self._depth += 1
            return

        if tag == "title":
            self._in_title = True

        if tag == "a" and "href" in attrs:
            self._cur_href   = attrs["href"]
            self._cur_anchor = []

        if tag == "meta":
            prop    = attrs.get("property", attrs.get("name", ""))
            content = attrs.get("content", "")
            if prop and content:
                self.meta[prop] = content

    def handle_endtag(self, tag):
        if self._skip:
            self._depth -= 1
            if self._depth == 0:
                self._skip = False
            return

        if tag == "title":
            self._in_title = False

        if tag == "a" and self._cur_href:
            anchor = " ".join(self._cur_anchor).strip()
            if anchor:
                self.links.append((self._cur_href, anchor))
            self._cur_href   = None
            self._cur_anchor = []

    def handle_data(self, data):
        if self._skip:
            return
        text = data.strip()
        if not text:
            return
        if self._in_title:
            self.title += text
        if self._cur_href is not None:
            self._cur_anchor.append(text)
        self.chunks.append(text)

    def get_text(self) -> str:
        return " ".join(self.chunks)


def parse_html(html: str) -> dict:
    """
    Parse raw HTML and return:
      {
        'title':        str,
        'text':         str,   # full visible text
        'summary':      str,   # first ~300 chars of body text
        'links':        [(href, anchor), ...],
        'published_at': str | None,
        'meta':         dict,
      }
    """
    extractor = _TextExtractor()
    try:
        extractor.feed(html)
    except Exception:
        pass    # partial HTML is fine

    title = (
        extractor.title.strip()
        or extractor.meta.get("og:title", "")
        or extractor.meta.get("twitter:title", "")
    )

    full_text = extractor.get_text()

    # Best-effort: grab first 300 chars after the title as summary
    summary = ""
    if full_text:
        # skip the title if it appears at the start
        body_start = full_text.find(title)
        body = full_text[body_start + len(title):].strip() if body_start != -1 else full_text
        summary = body[:300].rsplit(" ", 1)[0] + "…" if len(body) > 300 else body

    # Publication date — try common meta fields
    pub_date = None
    for key in ("article:published_time", "datePublished",
                "pubdate", "og:updated_time", "date"):
        val = extractor.meta.get(key)
        if val:
            pub_date = _normalise_date(val)
            break

    return {
        "title":        title,
        "text":         full_text,
        "summary":      summary,
        "links":        extractor.links,
        "published_at": pub_date,
        "meta":         extractor.meta,
    }


def _normalise_date(raw: str) -> str | None:
    """Try several common date formats and return YYYY-MM-DD or None."""
    raw = raw.strip()[:30]
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%d", "%d/%m/%Y", "%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(raw[:len(fmt) + 6], fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    # Fallback: grab first 10 chars if they look like a date
    if re.match(r"\d{4}-\d{2}-\d{2}", raw):
        return raw[:10]
    return None


# ── Player mention detector ────────────────────────────────────────────────────

def find_mentions(text: str, players: list) -> list:
    """
    Scan `text` for each player's name and aliases.
    `players` is a list of dicts from database.get_all_players().

    Returns a list of:
      {
        'player_id':     int,
        'player_name':   str,
        'mention_count': int,
        'sentiment':     float,   # -1.0 .. +1.0
        'context':       str,     # first snippet where mentioned
      }
    """
    results = []
    text_lower = text.lower()

    for player in players:
        import json
        aliases = json.loads(player.get("aliases") or "[]")
        names_to_check = [player["name"]] + aliases

        total_count = 0
        first_context = ""

        for name in names_to_check:
            if not name:
                continue
            pattern = re.compile(r'\b' + re.escape(name) + r'\b', re.IGNORECASE)
            matches = list(pattern.finditer(text))
            if matches:
                total_count += len(matches)
                if not first_context:
                    m = matches[0]
                    start = max(0, m.start() - 80)
                    end   = min(len(text), m.end() + 80)
                    first_context = "…" + text[start:end].strip() + "…"

        if total_count > 0:
            sentiment = compute_sentiment(first_context or text[:500])
            results.append({
                "player_id":     player["id"],
                "player_name":   player["name"],
                "mention_count": total_count,
                "sentiment":     sentiment,
                "context":       first_context,
            })

    return results


# ── Lightweight sentiment scorer ───────────────────────────────────────────────
# Uses a curated word list — good enough for sports buzz without any ML deps.

_POSITIVE = {
    "win", "wins", "won", "victory", "champion", "champions", "title",
    "brilliant", "great", "excellent", "outstanding", "best", "top",
    "record", "milestone", "praised", "praise", "starred", "star",
    "goals", "scored", "hat-trick", "heroic", "dominant", "dominates",
    "rises", "rise", "comeback", "award", "man of the match", "motm",
    "healthy", "fit", "returns", "return", "impressive", "clutch",
    "legend", "iconic", "elite", "formidable", "unstoppable"
}

_NEGATIVE = {
    "loss", "loses", "lost", "defeat", "injured", "injury", "ban",
    "banned", "suspended", "suspension", "poor", "bad", "worst",
    "criticised", "criticism", "controversy", "scandal", "failed",
    "fail", "miss", "missed", "blow", "crisis", "retire", "retired",
    "drop", "dropped", "benched", "sacked", "fined", "charged",
    "arrest", "arrested", "doping", "cheat", "cheated", "slump",
    "struggles", "struggling", "doubt", "doubtful", "out",
}

def compute_sentiment(text: str) -> float:
    """
    Returns a score from -1.0 (very negative) to +1.0 (very positive).
    Simple bag-of-words; fast, no dependencies.
    """
    words = re.findall(r'\b\w+\b', text.lower())
    if not words:
        return 0.0

    pos = sum(1 for w in words if w in _POSITIVE)
    neg = sum(1 for w in words if w in _NEGATIVE)
    total = pos + neg
    if total == 0:
        return 0.0
    return round((pos - neg) / total, 4)


# ── Link extractor / URL normaliser ───────────────────────────────────────────

def extract_links(html: str, base_url: str) -> list[str]:
    """
    Return a deduplicated list of absolute URLs found in `html`,
    staying within the same domain as `base_url`.
    """
    parsed = parse_html(html)
    scheme_host = _get_scheme_host(base_url)
    if not scheme_host:
        return []

    seen = set()
    result = []
    for href, _ in parsed["links"]:
        url = _resolve_url(href, base_url, scheme_host)
        if url and url not in seen:
            seen.add(url)
            result.append(url)
    return result


def _get_scheme_host(url: str) -> str | None:
    if "://" not in url:
        return None
    scheme, rest = url.split("://", 1)
    host = rest.split("/")[0]
    return f"{scheme}://{host}"


def _resolve_url(href: str, base_url: str, scheme_host: str) -> str | None:
    """Turn a possibly-relative href into an absolute URL on the same domain."""
    if not href or href.startswith(("mailto:", "javascript:", "#", "tel:")):
        return None
    if href.startswith("http://") or href.startswith("https://"):
        # Only keep same-domain links
        if href.startswith(scheme_host):
            return href.split("#")[0] or None
        return None
    if href.startswith("//"):
        scheme = base_url.split("://")[0]
        return f"{scheme}:{href}".split("#")[0]
    if href.startswith("/"):
        return (scheme_host + href).split("#")[0]
    # relative path — simplistic join
    base_path = "/".join(base_url.rstrip("/").split("/")[:-1])
    return f"{base_path}/{href}".split("#")[0]
