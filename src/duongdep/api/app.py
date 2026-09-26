"""FastAPI app: webapp + xuất Google Maps/GPX + nhận xác nhận.

Chạy:
    pip install -e ".[api]"
    duongdep precompute --bbox 20.97,105.79,21.02,105.84 --out data/graph.json
    uvicorn duongdep.api.app:app --reload
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel

from ..export import gmaps_url, to_gpx
from ..feedback.store import FeedbackStore
from ..graph import Graph
from ..route.engine import astar
from ..score import score_graph

GRAPH_PATH = os.environ.get("DUONGDEP_GRAPH", "data/graph.json")
WEB_DIR = Path(__file__).resolve().parents[3] / "web"

app = FastAPI(title="duongdep", version="0.0.1")
_store: FeedbackStore | None = None
_graph: Graph | None = None


def get_store() -> FeedbackStore:
    global _store
    if _store is None:
        _store = FeedbackStore()
    return _store


def get_graph() -> Graph:
    global _graph
    if _graph is None:
        if not Path(GRAPH_PATH).exists():
            raise HTTPException(
                status_code=503,
                detail=f"Chưa có graph tại {GRAPH_PATH}. Chạy: duongdep precompute --out {GRAPH_PATH}",
            )
        _graph = Graph.load(GRAPH_PATH)
    return _graph


def _parse_ll(s: str) -> tuple[float, float]:
    lat, lon = s.split(",")
    return float(lat), float(lon)


def _route_payload(origin: tuple[float, float], dest: tuple[float, float], mode: str) -> dict:
    g = get_graph()
    score_graph(g, mode)
    s = g.nearest_node(*origin)
    t = g.nearest_node(*dest)
    route = astar(g, s, t)
    if route is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy tuyến")

    segments = []
    for eid in route.edges:
        e = g.edges[eid]
        segments.append(
            {
                "osm_way_id": e.way_id,
                "highway": e.highway,
                "surface": e.surface,
                "width_proxy_m": e.width_proxy_m,
                "score": e.score,
                "length_m": round(e.length_m, 1),
                "geometry": e.geometry,
            }
        )
    return {
        "coords": [[lat, lon] for lat, lon in route.coords],
        "segments": segments,
        "length_km": round(route.length_km, 2),
        "gmaps_url": gmaps_url(route.coords, platform="app"),
        "gmaps_url_mobile": gmaps_url(route.coords, platform="mobile"),
    }


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    f = WEB_DIR / "index.html"
    if not f.exists():
        return "<h1>duongdep</h1><p>Thiếu web/index.html</p>"
    return f.read_text(encoding="utf-8")


@app.get("/api/route")
def api_route(
    from_: str = Query(..., alias="from", description="lat,lng"),
    to: str = Query(..., description="lat,lng"),
    mode: str = Query("car", pattern="^(car|bike)$"),
) -> dict:
    return _route_payload(_parse_ll(from_), _parse_ll(to), mode)


@app.get("/api/export/gpx", response_class=PlainTextResponse)
def api_export_gpx(
    from_: str = Query(..., alias="from"),
    to: str = Query(...),
    mode: str = Query("car", pattern="^(car|bike)$"),
) -> str:
    payload = _route_payload(_parse_ll(from_), _parse_ll(to), mode)
    return to_gpx([(c[0], c[1]) for c in payload["coords"]], name="duongdep")


class SegmentIn(BaseModel):
    osm_way_id: int
    kind: str
    note: str = ""
    value: str = "bad"


class ConfirmIn(BaseModel):
    trip_id: int | None = None
    verdict: str = "good"  # good | mixed | bad
    note: str = ""
    segments: list[SegmentIn] = []


@app.post("/api/confirm")
def api_confirm(body: ConfirmIn) -> dict:
    store = get_store()
    trip_id = body.trip_id or store.create_trip()
    store.add_route_verdict(trip_id, body.verdict, body.note)
    for seg in body.segments:
        store.add_segment_verdict(trip_id, seg.osm_way_id, seg.kind, seg.note, seg.value)
    return {"ok": True, "trip_id": trip_id, "n_segments": len(body.segments)}
