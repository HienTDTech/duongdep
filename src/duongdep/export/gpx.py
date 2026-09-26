"""Xuất GPX (cho OsmAnd / Organic Maps / My Maps)."""

from __future__ import annotations

from html import escape


def to_gpx(coords: list[tuple[float, float]], name: str = "duongdep route") -> str:
    pts = "\n".join(f'      <trkpt lat="{lat:.6f}" lon="{lon:.6f}"></trkpt>' for lat, lon in coords)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<gpx version="1.1" creator="duongdep" xmlns="http://www.topografix.com/GPX/1/1">\n'
        f"  <trk>\n    <name>{escape(name)}</name>\n    <trkseg>\n{pts}\n    </trkseg>\n  </trk>\n"
        "</gpx>\n"
    )
