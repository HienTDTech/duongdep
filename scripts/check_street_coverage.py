#!/usr/bin/env python3
"""
check_street_coverage.py — kiểm tra độ phủ ảnh street-level (Mapillary / Google Street View)
dọc một tuyến hoặc trong một bbox. Dùng cho tính năng "khảo sát tuyến trước khi đi".

Không phụ thuộc thư viện ngoài (chỉ stdlib). Python 3.9+.

------------------------------------------------------------------
CÁCH DÙNG
------------------------------------------------------------------
# 0) KartaView — KHÔNG cần credential (endpoint public)
python3 check_street_coverage.py --source kartaview \
    --bbox 105.72,20.93,105.85,21.03 --grid 6 --csv hanoi_kv.csv

# 1) Mapillary (cần token miễn phí: https://www.mapillary.com/dashboard/developers)
export MAPILLARY_TOKEN='MLY|xxxxx|yyyyy'
python3 check_street_coverage.py --source mapillary \
    --bbox 105.72,20.93,105.85,21.03 --step 500

# 2) Google Street View (cần API key: bật "Street View Static API")
export GOOGLE_MAPS_API_KEY='AIza...'
python3 check_street_coverage.py --source gsv \
    --points "21.0285,105.8542;21.0012,105.8410"

# 3) Theo một tuyến GPX (lấy mọi <trkpt lat= lon=>)
python3 check_street_coverage.py --source gsv --gpx route.gpx --step 1000

# 4) Xuất CSV để xem chi tiết
python3 check_street_coverage.py --source mapillary --bbox ... --csv out.csv
------------------------------------------------------------------
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

UA = "route-comfort-coverage-check/0.1 (research)"


# ---------------------------------------------------------------- geo utils
def haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    R = 6371000.0
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def sample_line(points: list[tuple[float, float]], step_m: float) -> list[tuple[float, float]]:
    """Lấy mẫu dọc polyline, mỗi ~step_m một điểm (luôn gồm điểm đầu/cuối)."""
    if len(points) < 2:
        return points
    out = [points[0]]
    acc = 0.0
    for i in range(1, len(points)):
        seg = haversine_m(points[i - 1], points[i])
        if seg == 0:
            continue
        # nội suy các mẫu trong đoạn
        t = step_m - acc
        while t < seg:
            r = t / seg
            lat = points[i - 1][0] + (points[i][0] - points[i - 1][0]) * r
            lon = points[i - 1][1] + (points[i][1] - points[i - 1][1]) * r
            out.append((lat, lon))
            t += step_m
        acc = (acc + seg) % step_m
    out.append(points[-1])
    return out


def bbox_grid(min_lon, min_lat, max_lon, max_lat, n: int) -> list[tuple[float, float]]:
    """Lưới n x n điểm trong bbox."""
    pts = []
    for i in range(n):
        for j in range(n):
            lat = min_lat + (max_lat - min_lat) * (i + 0.5) / n
            lon = min_lon + (max_lon - min_lon) * (j + 0.5) / n
            pts.append((lat, lon))
    return pts


def parse_points(s: str) -> list[tuple[float, float]]:
    out = []
    for chunk in s.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        lat, lon = chunk.split(",")
        out.append((float(lat), float(lon)))
    return out


def parse_gpx(path: str) -> list[tuple[float, float]]:
    import re

    txt = open(path, encoding="utf-8", errors="ignore").read()
    return [(float(a), float(b)) for a, b in re.findall(r'<trkpt[^>]*lat="([-0-9.]+)"[^>]*lon="([-0-9.]+)"', txt)]


def get_json(url: str, headers: dict | None = None, timeout: int = 20):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


# ---------------------------------------------------------------- providers
def mapillary_count(token: str, lat: float, lon: float, radius_m: float = 150) -> int:
    """Đếm số ảnh Mapillary quanh 1 điểm (bbox vuông ±radius)."""
    dlat = radius_m / 111_320.0
    dlon = radius_m / (111_320.0 * max(0.2, math.cos(math.radians(lat))))
    bbox = f"{lon - dlon},{lat - dlat},{lon + dlon},{lat + dlat}"
    q = urllib.parse.urlencode(
        {"access_token": token, "fields": "id", "bbox": bbox, "limit": 200}
    )
    try:
        d = get_json(f"https://graph.mapillary.com/images?{q}")
        return len(d.get("data", []))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:200]
        raise RuntimeError(f"Mapillary HTTP {e.code}: {body}") from None


def gsv_status(key: str, lat: float, lon: float) -> str:
    """Trả về status của Google Street View metadata tại 1 điểm."""
    q = urllib.parse.urlencode({"location": f"{lat},{lon}", "key": key, "source": "outdoor"})
    try:
        d = get_json(f"https://maps.googleapis.com/maps/api/streetview/metadata?{q}")
        return d.get("status", "UNKNOWN")
    except urllib.error.HTTPError as e:
        return f"HTTP_{e.code}"


def kartaview_count(lat: float, lon: float, radius_m: float = 150) -> int:
    """Đếm ảnh KartaView quanh 1 điểm. KHÔNG cần token.
    Lưu ý: param đúng là `radius` (không phải `distance`)."""
    q = urllib.parse.urlencode({"lat": lat, "lng": lon, "radius": radius_m})
    d = get_json(f"https://api.openstreetcam.org/2.0/photo/?{q}")
    r = d.get("result") or {}
    return len(r.get("data") or [])


# ---------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description="Kiểm tra độ phủ ảnh street-level.")
    ap.add_argument("--source", choices=["mapillary", "kartaview", "gsv"], required=True)
    ap.add_argument("--bbox", help="minLon,minLat,maxLon,maxLat (lấy mẫu theo lưới)")
    ap.add_argument("--grid", type=int, default=6, help="số điểm mỗi chiều khi dùng --bbox (mặc định 6)")
    ap.add_argument("--points", help='"lat,lng;lat,lng;..."')
    ap.add_argument("--gpx", help="file GPX (dùng track points)")
    ap.add_argument("--step", type=float, default=500.0, help="khoảng cách lấy mẫu dọc tuyến (m)")
    ap.add_argument("--radius", type=float, default=150.0, help="bán kính tìm ảnh Mapillary (m)")
    ap.add_argument("--sleep", type=float, default=0.15, help="nghỉ giữa các request (giây)")
    ap.add_argument("--csv", help="xuất CSV")
    args = ap.parse_args()

    # --- lấy danh sách điểm
    pts: list[tuple[float, float]] = []
    if args.bbox:
        mn_lon, mn_lat, mx_lon, mx_lat = map(float, args.bbox.split(","))
        pts = bbox_grid(mn_lon, mn_lat, mx_lon, mx_lat, args.grid)
    elif args.points:
        pts = sample_line(parse_points(args.points), args.step)
    elif args.gpx:
        pts = sample_line(parse_gpx(args.gpx), args.step)
    else:
        ap.error("cần --bbox, --points hoặc --gpx")

    print(f"# source={args.source} | số điểm mẫu = {len(pts)}")

    rows = []
    if args.source == "mapillary":
        token = os.environ.get("MAPILLARY_TOKEN")
        if not token:
            print("!! Thiếu env MAPILLARY_TOKEN (lấy free ở mapillary.com/dashboard/developers)", file=sys.stderr)
            return 2
        covered = 0
        for i, (lat, lon) in enumerate(pts, 1):
            try:
                n = mapillary_count(token, lat, lon, args.radius)
            except RuntimeError as e:
                print(f"[{i}/{len(pts)}] {lat:.5f},{lon:.5f} -> LỖI {e}")
                return 2
            covered += n > 0
            rows.append({"lat": lat, "lon": lon, "images": n})
            print(f"[{i}/{len(pts)}] {lat:.5f},{lon:.5f} -> {n} ảnh")
            time.sleep(args.sleep)
        print(f"\n# KẾT LUẬN: {covered}/{len(pts)} điểm có ảnh Mapillary "
              f"({100*covered/len(pts):.0f}%)")
    elif args.source == "kartaview":
        covered = 0
        for i, (lat, lon) in enumerate(pts, 1):
            try:
                n = kartaview_count(lat, lon, args.radius)
            except Exception as e:
                print(f"[{i}/{len(pts)}] {lat:.5f},{lon:.5f} -> LỖI {e}")
                n = 0
            covered += n > 0
            rows.append({"lat": lat, "lon": lon, "images": n})
            print(f"[{i}/{len(pts)}] {lat:.5f},{lon:.5f} -> {n} ảnh")
            time.sleep(args.sleep)
        print(f"\n# KẾT LUẬN: {covered}/{len(pts)} điểm có ảnh KartaView "
              f"({100*covered/len(pts):.0f}%)")
    else:  # gsv
        key = os.environ.get("GOOGLE_MAPS_API_KEY")
        if not key:
            print("!! Thiếu env GOOGLE_MAPS_API_KEY (bật Street View Static API)", file=sys.stderr)
            return 2
        ok = 0
        for i, (lat, lon) in enumerate(pts, 1):
            st = gsv_status(key, lat, lon)
            ok += st == "OK"
            rows.append({"lat": lat, "lon": lon, "status": st})
            print(f"[{i}/{len(pts)}] {lat:.5f},{lon:.5f} -> {st}")
            time.sleep(args.sleep)
        print(f"\n# KẾT LUẬN: {ok}/{len(pts)} điểm có Google Street View "
              f"({100*ok/len(pts):.0f}%)")
        if ok == 0:
            print("# Gợi ý: kiểm tra API key đã bật 'Street View Static API' chưa.")

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"# đã ghi {args.csv}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
