"""
Instagram Graph API — recent media for an IG user id.

Requires INSTAGRAM_ACCESS_TOKEN (long-lived user token) and the Instagram Business
account's numeric id (social_accounts.yaml → ig_user_id).

Docs: https://developers.facebook.com/docs/instagram-api/
"""

from __future__ import annotations

import os
from typing import Any

import requests


def fetch_recent_media(ig_user_id: str, max_results: int = 10) -> list[dict[str, Any]]:
    token = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "").strip()
    if not token:
        raise RuntimeError("INSTAGRAM_ACCESS_TOKEN is not set")
    uid = (ig_user_id or "").strip()
    if not uid:
        raise RuntimeError("ig_user_id is empty")

    r = requests.get(
        f"https://graph.instagram.com/{uid}/media",
        params={
            "fields": "id,caption,media_type,media_url,permalink,thumbnail_url,timestamp,username,like_count,comments_count",
            "limit": min(max(1, max_results), 50),
            "access_token": token,
        },
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    items = data.get("data") or []
    out: list[dict[str, Any]] = []
    for m in items:
        # Align with jsonNormalizer.instagramMedia
        out.append(
            {
                "id": m.get("id"),
                "caption": m.get("caption") or "",
                "timestamp": m.get("timestamp"),
                "username": m.get("username"),
                "media_url": m.get("media_url") or m.get("permalink"),
                "like_count": m.get("like_count"),
                "comments_count": m.get("comments_count"),
                "raw": m,
            }
        )
    return out
