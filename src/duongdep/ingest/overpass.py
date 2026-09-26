"""Tải dữ liệu OpenStreetMap qua Overpass API (không cần thư viện ngoài).

Tự thử nhiều mirror vì các endpoint công cộng hay quá tải (504 / timeout).
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request

from ..config import OVERPASS_URL, USER_AGENT

# Thử theo thứ tự; mirror trong config đứng đầu.
MIRRORS = [
    OVERPASS_URL,
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass.osm.ch/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]


def _query(q: str, url: str | None = None, timeout: int = 60, retries: int = 1) -> dict:
    mirrors = [url] if url else MIRRORS
    last: Exception | None = None
    for attempt in range(retries):
        for m in mirrors:
            try:
                full = f"{m}?{urllib.parse.urlencode({'data': q})}"
                req = urllib.request.Request(full, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(req, timeout=timeout) as r:
                    body = r.read()
                data = json.loads(body.decode("utf-8", "replace"))
                if data.get("elements") or "elements" in data:
                    return data
                last = RuntimeError(f"{m}: phản hồi không có elements")
            except Exception as exc:  # noqa: BLE001
                last = exc
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"Overpass thất bại trên mọi mirror sau {retries} vòng: {last}")


def fetch_roads(bbox: tuple[float, float, float, float], url: str | None = None) -> dict:
    """bbox = (south, west, north, east)."""
    s, w, n, e = bbox
    q = f'[out:json][timeout:120];(way["highway"]({s},{w},{n},{e});>;);out body;'
    return _query(q, url)


def fetch_buildings(bbox: tuple[float, float, float, float], url: str | None = None) -> dict:
    """Lấy building footprints để suy chiều rộng hành lang đường."""
    s, w, n, e = bbox
    q = f'[out:json][timeout:120];(way["building"]({s},{w},{n},{e});>;);out body;'
    return _query(q, url)
