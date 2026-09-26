"""Suy chiều rộng hành lang đường từ building footprints.

Ý tưởng: trong đô thị, độ rộng "cảm nhận" của đường ~ khoảng cách giữa hai dãy nhà.
Với mỗi cạnh đường, chiếu hai bên và lấy khoảng cách tới building gần nhất mỗi bên,
rồi cộng lại (facade-to-facade).

Đây là **heuristic**, không phải chiều rộng mặt đường thật:
- gồm cả vỉa hè / sân trước nhà
- đường không có nhà (ven đô, cao tốc) -> không đo được, để None
- building thiếu/sai trong OSM -> nhiễu

Chạy trong `precompute`, không chạy lúc routing.
"""

from __future__ import annotations

import math
from collections import defaultdict

from ..geo import haversine_m, local_xy, polygon_distance_m

MAX_SEARCH_M = 45.0
# Chỉ coi là "hành lang" khi cả hai bên đều có nhà gần; nếu một bên quá xa -> open/unknown
MAX_SIDE_M = 35.0
MAX_WIDTH_M = 40.0


def parse_buildings(json_data: dict) -> list[list[tuple[float, float]]]:
    nodes: dict[int, tuple[float, float]] = {}
    polys: list[list[tuple[float, float]]] = []
    for el in json_data.get("elements", []):
        if el.get("type") == "node":
            nodes[el["id"]] = (el["lat"], el["lon"])
        elif el.get("type") == "way":
            nds = el.get("nodes") or []
            if len(nds) >= 3 and all(n in nodes for n in nds):
                polys.append([nodes[n] for n in nds])
    return polys


def _centroid(poly: list[tuple[float, float]]) -> tuple[float, float]:
    return (sum(p[0] for p in poly) / len(poly), sum(p[1] for p in poly) / len(poly))


class BuildingIndex:
    """Lưới không gian đơn giản để tìm building gần một điểm."""

    def __init__(self, polys: list[list[tuple[float, float]]], cell_deg: float = 0.0005):
        self.polys = polys
        self.cell = cell_deg
        self.grid: dict[tuple[int, int], list[int]] = defaultdict(list)
        for i, p in enumerate(polys):
            c = _centroid(p)
            self.grid[self._key(c)].append(i)

    def _key(self, c: tuple[float, float]) -> tuple[int, int]:
        return int(c[0] // self.cell), int(c[1] // self.cell)

    def candidates(self, point: tuple[float, float], radius_m: float) -> list[int]:
        k = int(radius_m / (self.cell * 111000.0)) + 1
        base = self._key(point)
        out: list[int] = []
        for dx in range(-k, k + 1):
            for dy in range(-k, k + 1):
                out.extend(self.grid.get((base[0] + dx, base[1] + dy), ()))
        return out


def _nearest_vertex(p: tuple[float, float], poly: list[tuple[float, float]]):
    best, best_d = None, float("inf")
    for v in poly:
        d = haversine_m(p, v)
        if d < best_d:
            best, best_d = v, d
    return best


def annotate_width(graph, buildings: list[list[tuple[float, float]]], max_search_m: float = MAX_SEARCH_M) -> int:
    """Gán `width_proxy_m` cho từng cạnh. Trả về số cạnh đo được."""
    idx = BuildingIndex(buildings)
    measured = 0
    for e in graph.edges:
        mid = (
            (e.geometry[0][0] + e.geometry[-1][0]) / 2,
            (e.geometry[0][1] + e.geometry[-1][1]) / 2,
        )
        ax, ay = local_xy(e.coord_u, mid)
        bx, by = local_xy(e.coord_v, mid)
        dx, dy = bx - ax, by - ay
        norm = math.hypot(dx, dy)
        if norm == 0:
            continue
        dx, dy = dx / norm, dy / norm

        d_left = d_right = None
        for ci in idx.candidates(mid, max_search_m):
            poly = buildings[ci]
            d = polygon_distance_m(mid, poly)
            if d > max_search_m:
                continue
            v = _nearest_vertex(mid, poly)
            if v is None:
                continue
            px, py = local_xy(v, mid)
            cross = dx * py - dy * px  # >0 một bên, <0 bên kia
            if cross > 0:
                d_left = d if d_left is None else min(d_left, d)
            elif cross < 0:
                d_right = d if d_right is None else min(d_right, d)

        if d_left is not None and d_right is not None and d_left <= MAX_SIDE_M and d_right <= MAX_SIDE_M:
            e.width_proxy_m = round(min(MAX_WIDTH_M, d_left + d_right), 1)
            measured += 1
    return measured
