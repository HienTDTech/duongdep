"""CLI: precompute + route."""

from __future__ import annotations

import argparse
import sys

from .config import HANOI_BBOX
from .export import gmaps_url, to_gpx
from .graph import Graph
from .route.engine import astar
from .score import score_graph


def _parse_bbox(s: str) -> tuple[float, float, float, float]:
    parts = [float(x) for x in s.split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("bbox phải là: south,west,north,east")
    return parts[0], parts[1], parts[2], parts[3]


def _parse_ll(s: str) -> tuple[float, float]:
    lat, lon = s.split(",")
    return float(lat), float(lon)


def cmd_precompute(args) -> int:
    from .pipeline import precompute

    precompute(
        bbox=args.bbox,
        out=args.out,
        use_buildings=not args.no_buildings,
        mode=args.mode,
        source=args.source,
    )
    return 0


def cmd_route(args) -> int:
    g = Graph.load(args.graph)
    score_graph(g, args.mode)
    start = g.nearest_node(*args.src)
    goal = g.nearest_node(*args.dst)
    route = astar(g, start, goal)
    if route is None:
        print("Không tìm thấy tuyến.", file=sys.stderr)
        return 1

    print(f"mode={args.mode}  dài {route.length_km:.2f} km  ({len(route.edges)} đoạn)")
    if args.gmaps:
        print("Google Maps (app, ≤9 waypoint):")
        print(" ", gmaps_url(route.coords, platform="app"))
        print("Google Maps (mobile browser, ≤3 waypoint):")
        print(" ", gmaps_url(route.coords, platform="mobile"))
    if args.gpx:
        with open(args.gpx, "w", encoding="utf-8") as f:
            f.write(to_gpx(route.coords))
        print(f"Đã ghi GPX -> {args.gpx}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="duongdep", description="Chọn đường dễ đi (OSS, VN)")
    sub = p.add_subparsers(dest="cmd", required=True)

    pp = sub.add_parser("precompute", help="Tải OSM + gán điểm, lưu graph")
    pp.add_argument("--bbox", type=_parse_bbox, default=HANOI_BBOX, help="south,west,north,east")
    pp.add_argument("--out", default="data/graph.json")
    pp.add_argument("--no-buildings", action="store_true", help="bỏ qua bước suy width")
    pp.add_argument("--mode", default="car", choices=["car", "bike"])
    pp.add_argument("--source", default="auto", choices=["auto", "overpass", "osm-api"],
                    help="nguồn dữ liệu; 'osm-api' cho vùng nhỏ khi Overpass quá tải")
    pp.set_defaults(func=cmd_precompute)

    rp = sub.add_parser("route", help="Tính tuyến từ graph đã precompute")
    rp.add_argument("--from", dest="src", type=_parse_ll, required=True, help="lat,lng")
    rp.add_argument("--to", dest="dst", type=_parse_ll, required=True, help="lat,lng")
    rp.add_argument("--graph", default="data/graph.json")
    rp.add_argument("--mode", default="car", choices=["car", "bike"])
    rp.add_argument("--gmaps", action="store_true", help="in URL Google Maps")
    rp.add_argument("--gpx", help="ghi file GPX")
    rp.set_defaults(func=cmd_route)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
