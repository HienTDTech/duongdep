"""Hàm hình học cơ bản (không phụ thuộc thư viện ngoài)."""

from __future__ import annotations

import math

EARTH_R = 6371000.0


def haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Khoảng cách (m) giữa 2 điểm (lat, lon)."""
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_R * math.asin(math.sqrt(h))


def local_xy(point: tuple[float, float], ref: tuple[float, float]) -> tuple[float, float]:
    """Chiếu (lat, lon) sang mặt phẳng mét quanh `ref` (đủ tốt ở quy mô vài km)."""
    lat0 = math.radians(ref[0])
    x = (point[1] - ref[1]) * 111320.0 * math.cos(lat0)
    y = (point[0] - ref[0]) * 110540.0
    return x, y


def point_seg_distance_m(
    p: tuple[float, float], a: tuple[float, float], b: tuple[float, float]
) -> float:
    """Khoảng cách (m) từ điểm p tới đoạn thẳng a-b (toạ độ lat/lon)."""
    px, py = local_xy(p, p)
    ax, ay = local_xy(a, p)
    bx, by = local_xy(b, p)
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    cx, cy = ax + t * dx, ay + t * dy
    return math.hypot(px - cx, py - cy)


def polygon_distance_m(p: tuple[float, float], poly: list[tuple[float, float]]) -> float:
    """Khoảng cách (m) từ p tới biên polygon; 0 nếu p nằm trong polygon."""
    if point_in_polygon(p, poly):
        return 0.0
    if len(poly) < 2:
        return float("inf")
    return min(point_seg_distance_m(p, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))


def point_in_polygon(p: tuple[float, float], poly: list[tuple[float, float]]) -> bool:
    """Ray casting."""
    x, y = p[1], p[0]
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i][1], poly[i][0]
        x2, y2 = poly[(i + 1) % n][1], poly[(i + 1) % n][0]
        if (y1 > y) != (y2 > y):
            xint = (x2 - x1) * (y - y1) / (y2 - y1) + x1
            if x < xint:
                inside = not inside
    return inside


def midpoint_xy(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
    return (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
