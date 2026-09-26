# duongdep — Đường Đẹp

> Chọn lộ trình **dễ đi** cho ô tô ở Việt Nam, thay vì chỉ "nhanh nhất".

`duongdep` là một dự án OSS nhỏ, **phục vụ bản thân trước**: tự tìm tuyến tránh ngõ nhỏ /
đường xấu, ưu tiên đường rộng thoáng (chấp nhận xa hơn chút), **khảo sát tuyến trước khi đi**,
và **không bị tự đổi lộ trình** khi đang lái. Nền tảng là OpenStreetMap + Python.

---

## Vì sao

Google Maps tối ưu thời gian nên hay dồn vào ngõ nhỏ, đường xấu, và tự đổi lộ trình khi mình
đang lái. Nó không có — và không expose — khái niệm "đường rộng / dễ đi / thoáng".
`duongdep` bổ sung đúng chỗ đó, ở phạm vi Việt Nam.

Xem nghiên cứu đầy đủ trong [`docs/`](docs/) (thị trường, engine OSS, dữ liệu, thiết kế).

---

## Trạng thái

Phase 1 (scaffold) — pipeline chạy được end-to-end:

- [x] Ingest OSM (Overpass, fallback OSM API) → graph đường
- [x] Suy **corridor width** từ building footprints
- [x] Gán điểm "dễ đi" (`car` / `bike`) + A*
- [x] Xuất **Google Maps deep link** (waypoint) + **GPX**
- [x] Webapp MapLibre + API (FastAPI)
- [x] Vòng **xác nhận** sau chuyến (SQLite, có TTL)
- [ ] Khảo sát tuyến đầy đủ (Street View / độ cao / POI / rủi ro)
- [ ] Overture / building ngoài OSM để phủ dày hơn
- [ ] Đóng gói profile cho OsmAnd / BRouter + dataset cho cộng đồng

---

## Quickstart

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[api,dev]"

# 1) Precompute graph cho một vùng nhỏ (OSM API; dùng khi Overpass quá tải)
duongdep precompute --source osm-api \
  --bbox 20.996,105.827,21.004,105.836 --out data/test_area.json

# 2) Tính tuyến
duongdep route --graph data/test_area.json \
  --from 20.9962,105.8363 --to 20.9977,105.8230 --gmaps --gpx route.gpx

# 3) Webapp
export DUONGDEP_GRAPH=data/test_area.json
uvicorn duongdep.api.app:app --reload   # mở http://127.0.0.1:8000
```

Hoặc dùng `make`:

```bash
make install
make precompute      # vùng nhỏ mặc định
make test
make api
```

### Nguồn dữ liệu

- `--source auto` (mặc định): Overpass, tự fallback OSM API nếu Overpass lỗi.
- `--source osm-api`: dùng OSM API `/map` — **chỉ cho vùng nhỏ** (≤ ~50k node).
- `--source overpass`: bắt buộc Overpass — cần cho **cả thành phố**.

---

## Cách hoạt động

```
OSM (đường + nhà)
      │
      ├─ highway class ──┐
      ├─ surface ────────┤
      ├─ lanes ──────────┤──►  score mỗi cạnh  ──►  A*  ──►  tuyến
      └─ corridor width ─┘        (0 = cấm)
        (từ building footprints)
```

- **Ô tô**: ưu tiên đường lớn + mặt nhựa + nhiều làn + hành lang rộng.
- **Xe máy/xe đạp**: ưu tiên đường nhỏ ít xe to, **chấp nhận ngõ hẹp**, tránh `primary`/`trunk`.

Điểm nằm trong [`src/duongdep/config.py`](src/duongdep/config.py) — đây là chỗ tinh chỉnh
"cảm giác lái", mọi thứ khác chỉ là hạ tầng.

---

## Cấu trúc

```
duongdep/
├── src/duongdep/
│   ├── ingest/     overpass.py, osm_api.py, buildings.py   # nạp & suy width
│   ├── score/      car.py                                  # điểm dễ đi
│   ├── route/      engine.py                               # A*
│   ├── export/     gmaps.py, gpx.py                        # bàn giao
│   ├── feedback/   store.py                                # xác nhận + TTL
│   ├── api/        app.py                                  # FastAPI
│   ├── pipeline.py + cli.py
├── web/index.html   # MapLibre
├── scripts/check_street_coverage.py   # đo độ phủ ảnh street-level
├── tests/
└── docs/            # research + hướng dẫn API
```

---

## Giới hạn (nói thẳng)

- **`width_proxy_m` là heuristic**, không phải chiều rộng mặt đường: nó đo khoảng cách giữa hai
  dãy nhà (facade-to-facade), gồm cả vỉa hè/sân. Chỉ đáng tin khi OSM có nhiều building; nơi
  thưa building thì bỏ trống. `width` thật trong OSM chỉ có ~0,37% số đường.
- **Google Maps không nhận GPX/polyline để điều hướng.** Deep link chỉ điều khiển được tối đa
  **3 waypoint trên mobile browser / 9 trên app** → tuyến dài chỉ "gần đúng". Muốn đi đúng tuyến,
  dùng GPX + OsmAnd ("Navigate by track").
- **Chưa có dữ liệu ngập realtime.** Vòng xác nhận có TTL (tĩnh 6–24 tháng, động 6–48 giờ) nhưng
  cần người dùng thật báo.
- OSM API `/map` **không dùng được cho cả thành phố**; cần Overpass.
- Profile `bike` mới ở mức cơ bản.

---

## Roadmap

1. Khảo sát tuyến: Street View (deep link không cần key) + độ cao (Open-Meteo) + POI (Overpass).
2. Phủ building dày hơn (Microsoft / Google Open Buildings) cho vùng OSM thưa.
3. Xuất profile OsmAnd/BRouter + dataset `vn-road-comfort` cho cộng đồng.
4. Vùng ngập thủ công + cộng đồng, có TTL.

---

## Tài liệu

- [`docs/ROUTING-COMFORT-RESEARCH.md`](docs/ROUTING-COMFORT-RESEARCH.md) — research đầy đủ (có nguồn + số liệu đo thật)
- [`docs/STREET-LEVEL-API-SETUP.md`](docs/STREET-LEVEL-API-SETUP.md) — lấy credential Mapillary / KartaView / Street View
- [`docs/README.md`](docs/README.md) — tóm tắt research

## License

MIT — xem [`LICENSE`](LICENSE). Dữ liệu OpenStreetMap © cộng tác viên OSM, giấy phép ODbL.
