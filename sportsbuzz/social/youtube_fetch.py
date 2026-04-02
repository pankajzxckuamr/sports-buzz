"""
YouTube Data API v3 — recent videos from a channel.

Set YOUTUBE_API_KEY in the environment (Google Cloud Console → APIs → YouTube Data v3).
"""

from __future__ import annotations

import os
from typing import Any

import requests


def fetch_recent_videos(channel_id: str, max_results: int = 10) -> list[dict[str, Any]]:
    key = os.environ.get("YOUTUBE_API_KEY", "").strip()
    if not key:
        raise RuntimeError("YOUTUBE_API_KEY is not set")
    if not channel_id or not channel_id.strip():
        raise RuntimeError("channel_id is empty")

    r = requests.get(
        "https://www.googleapis.com/youtube/v3/search",
        params={
            "part": "snippet",
            "channelId": channel_id.strip(),
            "maxResults": min(max(1, max_results), 50),
            "order": "date",
            "type": "video",
            "key": key,
        },
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    items = data.get("items") or []

    ids = []
    for it in items:
        vid = (it.get("id") or {}).get("videoId")
        if vid:
            ids.append(vid)

    stats_by_id: dict[str, dict] = {}
    if ids:
        sr = requests.get(
            "https://www.googleapis.com/youtube/v3/videos",
            params={
                "part": "snippet,statistics",
                "id": ",".join(ids),
                "key": key,
            },
            timeout=30,
        )
        sr.raise_for_status()
        for v in sr.json().get("items") or []:
            stats_by_id[v["id"]] = v

    out: list[dict[str, Any]] = []
    for vid in ids:
        v = stats_by_id.get(vid)
        if not v:
            continue
        # Shape matches sports-data-backend jsonNormalizer.youtubeVideo
        out.append(v)
    return out
