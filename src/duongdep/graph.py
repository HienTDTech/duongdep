"""Graph đường bộ + điểm "dễ đi" cho từng cạnh."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .geo import haversine_m


@dataclass
class Edge:
    id: int
    u: int
    v: int
    way_id: int
    length_m: float
    highway: str
    surface: str | None = None
    lanes: int | None = None
    name: str | None = None
    oneway: bool = False
    width_proxy_m: float | None = None
    score: float = 1.0
    # hình học của riêng đoạn u->v (2 điểm)
    geometry: list[list[float]] = field(default_factory=list)

    @property
    def coord_u(self) -> tuple[float, float]:
        return self.geometry[0][0], self.geometry[0][1]

    @property
    def coord_v(self) -> tuple[float, float]:
        return self.geometry[-1][0], self.geometry[-1][1]


@dataclass
class Graph:
    nodes: dict[int, tuple[float, float]] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)
    adj: dict[int, list[tuple[int, int]]] = field(default_factory=lambda: defaultdict(list))

    # ------------------------------------------------------------------ build
    @classmethod
    def from_overpass(cls, roads_json: dict) -> "Graph":
        nodes: dict[int, tuple[float, float]] = {}
        ways: list[dict] = []
        for el in roads_json.get("elements", []):
            if el.get("type") == "node":
                nodes[el["id"]] = (el["lat"], el["lon"])
            elif el.get("type") == "way":
                ways.append(el)

        g = cls()
        used: set[int] = set()
        for w in ways:
            if w.get("tags", {}).get("highway"):
                used.update(w.get("nodes") or [])
        g.nodes = {k: v for k, v in nodes.items() if k in used}
        eid = 0
        for w in ways:
            nds = w.get("nodes") or []
            if len(nds) < 2 or any(n not in nodes for n in nds):
                continue
            tags = w.get("tags", {})
            highway = tags.get("highway")
            if not highway:
                continue
            oneway = tags.get("oneway") in ("yes", "1", "true", "-1")
            reverse_only = tags.get("oneway") == "-1"
            lanes = _int_or_none(tags.get("lanes"))
            for i in range(len(nds) - 1):
                a, b = nds[i], nds[i + 1]
                ca, cb = nodes[a], nodes[b]
                length = haversine_m(ca, cb)
                geom = [[ca[0], ca[1]], [cb[0], cb[1]]]
                if reverse_only:
                    forward, backward = False, True
                elif oneway:
                    forward, backward = True, False
                else:
                    forward, backward = True, True
                if forward:
                    g._add_edge(eid, a, b, w["id"], length, highway, tags, lanes, oneway, geom)
                    eid += 1
                if backward:
                    g._add_edge(eid, b, a, w["id"], length, highway, tags, lanes, oneway, geom)
                    eid += 1
        return g

    def _add_edge(self, eid, u, v, way_id, length, highway, tags, lanes, oneway, geom):
        e = Edge(
            id=eid,
            u=u,
            v=v,
            way_id=way_id,
            length_m=length,
            highway=highway,
            surface=tags.get("surface"),
            lanes=lanes,
            name=tags.get("name"),
            oneway=oneway,
            geometry=geom,
        )
        self.edges.append(e)
        self.adj[u].append((v, eid))

    # ------------------------------------------------------------------ query
    def nearest_node(self, lat: float, lon: float, routable_only: bool = True) -> int:
        """Node gần nhất. Mặc định chỉ xét node có ít nhất 1 cạnh đi được (score>0)."""
        ids = list(self.adj.keys())
        if routable_only:
            ids = [
                n
                for n in ids
                if any(self.edges[eid].score > 0 for _, eid in self.adj[n])
            ] or ids
        best, best_d = -1, float("inf")
        for nid in ids:
            nlat, nlon = self.nodes[nid]
            d = (nlat - lat) ** 2 + (nlon - lon) ** 2
            if d < best_d:
                best, best_d = nid, d
        return best

    # ------------------------------------------------------------------ io
    def to_dict(self) -> dict:
        return {
            "nodes": {str(k): list(v) for k, v in self.nodes.items()},
            "edges": [asdict(e) for e in self.edges],
        }

    def save(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False)

    @classmethod
    def load(cls, path: str | Path) -> "Graph":
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        g = cls()
        g.nodes = {int(k): (v[0], v[1]) for k, v in d["nodes"].items()}
        g.edges = [Edge(**e) for e in d["edges"]]
        g.adj = defaultdict(list)
        for e in g.edges:
            g.adj[e.u].append((e.v, e.id))
        return g


def _int_or_none(v) -> int | None:
    try:
        return int(v)
    except (TypeError, ValueError):
        return None
