"""Pipeline precompute: OSM -> graph -> (width từ building) -> điểm -> lưu."""

from __future__ import annotations

from .config import OVERPASS_URL
from .graph import Graph
from .ingest import osm_api, overpass
from .ingest.buildings import annotate_width, parse_buildings
from .score import score_graph


def _load(
    bbox: tuple[float, float, float, float], url: str | None, source: str = "auto"
) -> tuple[dict, dict]:
    """Trả về (roads_elements, buildings_elements).

    source: 'auto' | 'overpass' | 'osm-api'.
    """
    if source == "osm-api":
        elements = osm_api.fetch_map_elements(bbox)["elements"]
        return osm_api.split_elements(elements)
    try:
        roads = overpass.fetch_roads(bbox, url)
        try:
            buildings = overpass.fetch_buildings(bbox, url)
        except Exception as exc:  # noqa: BLE001
            print(f"      (không lấy được building qua Overpass: {exc})")
            buildings = {"elements": []}
        return roads, buildings
    except Exception as exc:  # noqa: BLE001
        if source == "overpass":
            raise
        print(f"      Overpass lỗi ({exc}); fallback OSM API /map ...")
        elements = osm_api.fetch_map_elements(bbox)["elements"]
        return osm_api.split_elements(elements)


def precompute(
    bbox: tuple[float, float, float, float],
    out: str = "data/graph.json",
    use_buildings: bool = True,
    mode: str = "car",
    url: str | None = OVERPASS_URL,
    source: str = "auto",
) -> Graph:
    print(f"[1/4] Tải đường OSM cho bbox={bbox} (source={source}) ...")
    roads, buildings = _load(bbox, url, source)
    g = Graph.from_overpass(roads)
    print(f"      {len(g.nodes):,} node, {len(g.edges):,} cạnh")

    if use_buildings:
        print("[2/4] Suy chiều rộng hành lang từ building footprints ...")
        polys = parse_buildings(buildings)
        measured = annotate_width(g, polys)
        print(f"      {len(polys):,} building, đo được width cho {measured:,} cạnh")
    else:
        print("[2/4] Bỏ qua building (--no-buildings)")

    print(f"[3/4] Gán điểm cho mode={mode} ...")
    score_graph(g, mode)

    print(f"[4/4] Lưu -> {out}")
    g.save(out)
    return g
