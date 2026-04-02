"""
Load crawl_sites.yaml / social_accounts.yaml and sync crawl sites into SQLite.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from database import get_all_sources, init_db, upsert_source

CONFIG_DIR = Path(__file__).parent / "config"
CRAWL_SITES_PATH = CONFIG_DIR / "crawl_sites.yaml"
SOCIAL_ACCOUNTS_PATH = CONFIG_DIR / "social_accounts.yaml"


def yaml_safe_load(path: Path) -> dict | None:
    if not path.exists():
        return None
    raw = path.read_text(encoding="utf-8")
    if not raw.strip():
        return None
    return yaml.safe_load(raw) or {}


def load_crawl_sites_yaml() -> list[dict] | None:
    """
    Returns list of site dicts from YAML, or None if file missing.
    Empty `sites:` list returns [].
    """
    data = yaml_safe_load(CRAWL_SITES_PATH)
    if data is None:
        return None
    sites = data.get("sites") or []
    if not isinstance(sites, list):
        return []
    return [s for s in sites if isinstance(s, dict)]


def sync_crawl_sites_to_db() -> int:
    """
    Upsert each enabled site from crawl_sites.yaml into SQLite.
    Returns number of sites synced.
    """
    sites = load_crawl_sites_yaml()
    if sites is None:
        return 0
    init_db()
    n = 0
    for s in sites:
        if not s.get("enabled", True):
            continue
        name = (s.get("name") or "").strip()
        base_url = (s.get("base_url") or "").strip().rstrip("/")
        if not name or not base_url:
            continue
        sport = s.get("sport")
        if sport is not None and str(sport).strip() == "":
            sport = None
        stype = (s.get("source_type") or "news").strip()
        upsert_source(name, base_url, sport, stype)
        n += 1
    return n


def get_sources_for_crawl(sport_filter: str | None) -> list[dict]:
    """
    If crawl_sites.yaml exists and defines at least one enabled site, only those
    base URLs (after sync) are crawled. Otherwise all sources from DB are used.
    """
    yaml_sites = load_crawl_sites_yaml()
    if yaml_sites is not None:
        enabled_urls = set()
        for s in yaml_sites:
            if not s.get("enabled", True):
                continue
            bu = (s.get("base_url") or "").strip().rstrip("/")
            if bu:
                enabled_urls.add(bu)
        if enabled_urls:
            sync_crawl_sites_to_db()
            all_rows = get_all_sources(sport_filter)
            return [
                r
                for r in all_rows
                if r["base_url"].rstrip("/") in enabled_urls
            ]
        # YAML empty => fall through to DB-only
    init_db()
    return get_all_sources(sport_filter)


def load_social_accounts() -> dict:
    """Returns parsed social_accounts.yaml or empty dict."""
    data = yaml_safe_load(SOCIAL_ACCOUNTS_PATH)
    return data if isinstance(data, dict) else {}
