"""
Push crawled HTML and API JSON payloads to sports-data-backend (Node ingest API).

Set SPORTS_BACKEND_URL (e.g. http://localhost:3000). If unset, pushes are skipped.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any


def _backend_base() -> str | None:
    return os.environ.get("SPORTS_BACKEND_URL", "").strip().rstrip("/") or None


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def ingest_html(
    source: str,
    url: str,
    html: str,
    fetched_at: str | None = None,
    *,
    idempotency_key: str | None = None,
) -> dict | None:
    """
    POST /v1/ingest/html — returns backend JSON or None if backend not configured.
    """
    base = _backend_base()
    if not base:
        return None
    body = {
        "source": source,
        "url": url,
        "html": html,
        "fetched_at": fetched_at or _iso_now(),
    }
    if idempotency_key:
        body["idempotency_key"] = idempotency_key
    return _post_json(f"{base}/v1/ingest/html", body)


def ingest_json(
    source: str,
    platform: str,
    payload: dict[str, Any],
    fetched_at: str | None = None,
    *,
    idempotency_key: str | None = None,
) -> dict | None:
    """POST /v1/ingest/json — raw JSON from X / YouTube / Instagram APIs."""
    base = _backend_base()
    if not base:
        return None
    body = {
        "source": source,
        "platform": platform,
        "payload": payload,
        "fetched_at": fetched_at or _iso_now(),
    }
    if idempotency_key:
        body["idempotency_key"] = idempotency_key
    return _post_json(f"{base}/v1/ingest/json", body)


def _post_json(url: str, body: dict) -> dict:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Backend HTTP {e.code}: {err}") from e


def is_backend_configured() -> bool:
    return _backend_base() is not None
