"""Xuất lộ trình sang Google Maps.

Google Maps KHÔNG nhận polyline/GPX để điều hướng turn-by-turn.
Cách khả thi: deep link `dir` với các waypoint dọc tuyến.
Giới hạn thật của Google: mobile browser ≤ 3 waypoint, app/desktop ≤ 9; URL ≤ 2048 ký tự.
"""

from __future__ import annotations

from urllib.parse import urlencode


def select_waypoints(
    coords: list[tuple[float, float]], max_waypoints: int
) -> list[tuple[float, float]]:
    """Chọn waypoint rải đều dọc tuyến (bỏ điểm đầu/cuối)."""
    if max_waypoints <= 0 or len(coords) <= 2:
        return []
    interior = coords[1:-1]
    if not interior:
        return []
    k = min(max_waypoints, len(interior))
    if k == 1:
        return [interior[len(interior) // 2]]
    idxs = sorted({round(i * (len(interior) - 1) / (k - 1)) for i in range(k)})
    return [interior[i] for i in idxs]


def gmaps_url(coords: list[tuple[float, float]], platform: str = "app") -> str:
    """platform: 'app' (≤9 waypoint) hoặc 'mobile' (≤3 waypoint)."""
    if len(coords) < 2:
        raise ValueError("Cần ít nhất 2 điểm")
    max_wp = 3 if platform == "mobile" else 9
    origin, dest = coords[0], coords[-1]
    wps = select_waypoints(coords, max_wp)
    params = {
        "api": "1",
        "origin": f"{origin[0]:.6f},{origin[1]:.6f}",
        "destination": f"{dest[0]:.6f},{dest[1]:.6f}",
        "travelmode": "driving",
    }
    if wps:
        params["waypoints"] = "|".join(f"{a:.6f},{b:.6f}" for a, b in wps)
    return "https://www.google.com/maps/dir/?" + urlencode(params)


def gsv_url(coords: list[tuple[float, float]], index: int = 0) -> str:
    """Deep link mở Street View tại 1 điểm (không cần API key) — cho tab Khảo sát."""
    p = coords[index]
    return f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={p[0]:.6f},{p[1]:.6f}"
