"""
Load config/social_accounts.yaml and ingest JSON into sports-data-backend.

Run from the sportsbuzz folder:
  python -m social.run
  python run.py social
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except ImportError:
    pass

from backend_client import ingest_json, is_backend_configured
from config_loader import SOCIAL_ACCOUNTS_PATH, load_social_accounts

from .instagram_fetch import fetch_recent_media
from .twitter_fetch import fetch_tweet_envelopes
from .youtube_fetch import fetch_recent_videos


def run_social_ingest() -> None:
    if not is_backend_configured():
        print(
            "[Social] SPORTS_BACKEND_URL is not set — export it to push JSON to sports-data-backend.",
        )
        return

    accounts = load_social_accounts()
    if not accounts:
        print(f"[Social] No {SOCIAL_ACCOUNTS_PATH.name} or empty file.")
        return

    source_label = os.environ.get("SOCIAL_INGEST_SOURCE", "social_pipeline")

    for row in accounts.get("twitter") or []:
        if not isinstance(row, dict) or not row.get("enabled", False):
            continue
        user = (row.get("username") or "").strip().lstrip("@")
        if not user:
            continue
        print(f"[Social] Twitter @{user} …")
        try:
            envelopes = fetch_tweet_envelopes(user, max_results=10)
            for env in envelopes:
                ingest_json(
                    source_label,
                    "twitter",
                    env,
                    idempotency_key=f"twitter|{env.get('platform_id')}",
                )
            print(f"         → {len(envelopes)} tweets ingested")
        except Exception as e:
            print(f"         ✗ {e}")

    for row in accounts.get("youtube") or []:
        if not isinstance(row, dict) or not row.get("enabled", False):
            continue
        cid = (row.get("channel_id") or "").strip()
        if not cid:
            continue
        label = row.get("label") or cid
        print(f"[Social] YouTube {label} …")
        try:
            vids = fetch_recent_videos(cid, max_results=10)
            for payload in vids:
                vid = payload.get("id")
                ingest_json(
                    source_label,
                    "youtube",
                    payload,
                    idempotency_key=f"youtube|{vid}",
                )
            print(f"         → {len(vids)} videos ingested")
        except Exception as e:
            print(f"         ✗ {e}")

    for row in accounts.get("instagram") or []:
        if not isinstance(row, dict) or not row.get("enabled", False):
            continue
        ig_id = (row.get("ig_user_id") or "").strip()
        if not ig_id:
            continue
        print(f"[Social] Instagram {row.get('label') or ig_id} …")
        try:
            media = fetch_recent_media(ig_id, max_results=10)
            for m in media:
                mid = m.get("id")
                ingest_json(
                    source_label,
                    "instagram",
                    m,
                    idempotency_key=f"instagram|{mid}",
                )
            print(f"         → {len(media)} media ingested")
        except Exception as e:
            print(f"         ✗ {e}")

    print("[Social] Done.")


if __name__ == "__main__":
    run_social_ingest()
