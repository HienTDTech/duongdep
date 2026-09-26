"""A* trên graph đã gán điểm."""

from __future__ import annotations

import heapq
from dataclasses import dataclass

from ..config import MAX_SCORE
from ..geo import haversine_m
from ..graph import Graph


@dataclass
class Route:
    coords: list[tuple[float, float]]
    edges: list[int]
    length_m: float
    cost: float

    @property
    def length_km(self) -> float:
        return self.length_m / 1000.0


def edge_cost(e) -> float:
    return e.length_m / max(e.score, 1e-6)


def astar(graph: Graph, start: int, goal: int) -> Route | None:
    if start == goal:
        return Route(coords=[graph.nodes[start]], edges=[], length_m=0.0, cost=0.0)

    goal_pt = graph.nodes[goal]
    open_heap: list[tuple[float, int]] = [(0.0, start)]
    g_cost: dict[int, float] = {start: 0.0}
    came: dict[int, tuple[int, int]] = {}  # node -> (prev_node, edge_id)

    while open_heap:
        f, node = heapq.heappop(open_heap)
        if node == goal:
            break
        for nbr, eid in graph.adj.get(node, ()):
            e = graph.edges[eid]
            if e.score <= 0:
                continue
            tentative = g_cost[node] + edge_cost(e)
            if tentative < g_cost.get(nbr, float("inf")):
                g_cost[nbr] = tentative
                came[nbr] = (node, eid)
                h = haversine_m(graph.nodes[nbr], goal_pt) / MAX_SCORE
                heapq.heappush(open_heap, (tentative + h, nbr))

    if goal not in came and goal != start:
        return None

    # dựng lại đường
    edges_rev: list[int] = []
    nodes_rev: list[int] = [goal]
    cur = goal
    while cur != start:
        prev, eid = came[cur]
        edges_rev.append(eid)
        nodes_rev.append(prev)
        cur = prev
    edges_rev.reverse()
    nodes_rev.reverse()

    coords = [graph.nodes[n] for n in nodes_rev]
    length = sum(graph.edges[eid].length_m for eid in edges_rev)
    return Route(coords=coords, edges=edges_rev, length_m=length, cost=g_cost[goal])
