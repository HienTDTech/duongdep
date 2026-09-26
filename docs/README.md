# Tài liệu dự án duongdep

| File | Nội dung |
|---|---|
| [`ROUTING-COMFORT-RESEARCH.md`](ROUTING-COMFORT-RESEARCH.md) | Research thị trường, engine routing OSS, vấn đề dữ liệu (đo thật trên OSM/Overture), thiết kế webapp + xuất Google Maps + vòng kiểm chứng |
| [`STREET-LEVEL-API-SETUP.md`](STREET-LEVEL-API-SETUP.md) | Hướng dẫn lấy credential Mapillary / KartaView / Google Street View |
| [`tools/check_street_coverage.py`](tools/check_street_coverage.py) | Script đo độ phủ ảnh street-level dọc tuyến/bbox |

## Tóm tắt research (đọc nhanh)

- **Không có sản phẩm free/OSS nào** giải đủ: tránh ngõ nhỏ + tránh ngập + ưu tiên đường rộng/đẹp + không tự reroute, cho người dùng VN.
- **Engine đã có sẵn** (Valhalla `exclude_polygons`, GraphHopper custom model, ORS `avoid_polygons`, BRouter profile). Thiếu **dữ liệu + UX**.
- **`width` gần như không có trong OSM** (0,37% ở Hà Đông) và Overture cũng vậy (0,31%). → suy ra từ **building footprints**, không dùng ảnh vệ tinh.
- **Google Street View có ở VN** (full coverage từ 2025, có cả ảnh hẻm) → dùng cho "khảo sát tuyến". KartaView miễn phí nhưng thưa. Mapillary cần token.
- **OsmAnd** là client tốt nhất để đi theo lộ trình tự chọn (Navigate by track + custom online routing GH/ORS).
- **Google Maps** không nhận GPX/polyline điều hướng → chỉ deep link waypoint (≤3 trên mobile, ≤9 trên app).

Xem `ROUTING-COMFORT-RESEARCH.md` để có đầy đủ nguồn và số liệu.
