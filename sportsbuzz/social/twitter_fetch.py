"""
Twitter / X API v2 — recent tweets for a username.

Set TWITTER_BEARER_TOKEN in the environment (Twitter Developer Portal).
"""

from __future__ import annotations

import os
from typing import Any

import requests


def fetch_tweet_envelopes(username: str, max_results: int = 10) -> list[dict[str, Any]]:
    """
    Returns payloads suitable for sports-data-backend generic JSON normalizer
    (content + platform + platform_id + author + published_at + url).
    """
    token = os.environ.get("TWITTER_BEARER_TOKEN", "").strip()
    if not token:
        raise RuntimeError("TWITTER_BEARER_TOKEN is not set")

    user = username.lstrip("@").strip()
    h = {"Authorization": f"Bearer {token}"}
    r = requests.get(
        f"https://api.twitter.com/2/users/by/username/{user}",
        headers=h,
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    uid = data.get("data", {}).get("id")
    if not uid:
        raise RuntimeError(f"User not found: {user} — {data}")

    tr = requests.get(
        f"https://api.twitter.com/2/users/{uid}/tweets",
        headers=h,
        params={
            "max_results": min(max(5, max_results), 100),
            "tweet.fields": "created_at,author_id",
        },
        timeout=30,
    )
    tr.raise_for_status()
    blob = tr.json()
    tweets = blob.get("data") or []

    out: list[dict[str, Any]] = []
    for tw in tweets:
        tid = tw.get("id")
        text = tw.get("text") or ""
        ts = tw.get("created_at")
        out.append(
            {
                "platform": "twitter",
                "platform_id": tid,
                "content": text,
                "author": user,
                "published_at": ts,
                "url": f"https://twitter.com/i/web/status/{tid}",
                "raw_twitter_v2": tw,
            }
        )
    return out
