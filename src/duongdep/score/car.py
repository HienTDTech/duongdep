"""Gán điểm "dễ đi" cho từng cạnh."""

from __future__ import annotations

from .. import config
from ..graph import Edge, Graph


def score_edge(e: Edge, mode: str = "car") -> float:
    """Điểm càng cao = càng dễ đi. 0 = không cho đi."""
    if mode in ("bike", "motorbike"):
        w = config.BIKE_HIGHWAY_WEIGHT.get(e.highway, 0.5)
        if w <= 0:
            e.score = 0.0
            return 0.0
        w *= config.SURFACE_MULT.get(e.surface or "", config.UNKNOWN_SURFACE_MULT)
        if e.width_proxy_m is not None:
            # xe máy / xe đạp: hẹp KHÔNG sao, thậm chí hơi thích đường nhỏ
            w *= 1.05 if e.width_proxy_m < config.WIDTH_REF_M else 0.95
    else:
        w = config.CAR_HIGHWAY_WEIGHT.get(e.highway, 0.4)
        if w <= 0:
            e.score = 0.0
            return 0.0
        w *= config.SURFACE_MULT.get(e.surface or "", config.UNKNOWN_SURFACE_MULT)
        if e.lanes:
            w *= min(1.30, 1.0 + 0.08 * e.lanes)
        if e.width_proxy_m is not None:
            ratio = e.width_proxy_m / config.WIDTH_REF_M
            w *= min(config.WIDTH_MAX_MULT, max(config.WIDTH_MIN_MULT, ratio))
    e.score = round(w, 5)
    return e.score


def score_graph(graph: Graph, mode: str = "car") -> Graph:
    for e in graph.edges:
        score_edge(e, mode)
    return graph
