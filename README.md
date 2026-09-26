# duongdep — Đường Đẹp

> Chọn lộ trình **dễ đi** cho ô tô ở Việt Nam, thay vì chỉ "nhanh nhất".

## Vấn đề

Google Maps tối ưu thời gian nên hay dồn vào **ngõ nhỏ, đường xấu, đường tắc**,
đôi khi báo ngập sai rồi tự đổi lộ trình mà không hỏi. Người lái muốn:

- Tránh đường bé / ngõ nhỏ / đường xấu
- Tránh khu vực ngập (dựa trên báo cáo cộng đồng có kiểm chứng)
- Ưu tiên đường rộng, thoáng — chấp nhận xa hơn một chút
- **Khảo sát tuyến trước khi đi** (ảnh đường, độ cao, POI, rủi ro) khi đi nơi lạ/xa
- **Không bị tự đổi lộ trình** khi đang lái

## Phạm vi (Phase 1)

- **Việt Nam**, ưu tiên **ô tô** (xe máy/xe đạp là nice-to-have)
- **Webapp** dùng được ngay trên điện thoại
- Xuất lộ trình sang **Google Maps** (deep link waypoint) và **OsmAnd/GPX**
- Vòng **kiểm chứng/xác nhận** sau mỗi chuyến

## Cách tiếp cận dữ liệu

- Bản đồ nền: OpenStreetMap (Việt Nam extract)
- `width` gần như không có trong OSM (0,37%) → suy ra **corridor width từ building footprints**
- Không dùng ảnh vệ tinh cho width (quá thô hoặc paywall)
- Ảnh đường để khảo sát: **Google Street View** (chính), KartaView (dự phòng)
- Ngập: nhập/chọn vùng cấm thủ công + cộng đồng, **có TTL** để tránh báo cũ

## Kiến trúc dự kiến

```
duongdep/
├── ingest/    OSM PBF -> graph + corridor width từ building footprints
├── score/     car_score (ưu tiên rộng) / bike_score (ưu tiên ít xe to, cho phép ngõ)
├── route/     A* / k-shortest
├── export/    Google Maps deep link, GPX, OsmAnd, profile BRouter/routing.xml
├── api/       FastAPI: /route, /export/*, /confirm
├── web/       MapLibre + form + tab "Khảo sát tuyến"
└── cli.py
```

## Tài liệu research (đang ở repo research riêng)

- `ROUTING-COMFORT-RESEARCH.md` — thị trường, engine, dữ liệu, thiết kế
- `STREET-LEVEL-API-SETUP.md` — lấy credential Mapillary/KartaView/Street View
- `tools/check_street_coverage.py` — đo độ phủ ảnh street-level

## Trạng thái

- [x] Research thị trường & dữ liệu
- [ ] Phase 1: precompute graph Hà Nội + `car_score`
- [ ] Phase 1: API + webapp
- [ ] Phase 1: export Google Maps / OsmAnd
- [ ] Phase 1: feedback loop
- [ ] Đóng gói profile + dataset cho cộng đồng

## License

MIT (dự kiến)
