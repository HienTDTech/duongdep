# PLAN — duongdep

Kế hoạch việc cần làm / nên làm. Cập nhật: 24/09/2026.
Dùng như checklist: review định kỳ, tick dần, đổi thứ tự khi có dữ liệu mới.

**Ký hiệu:** `P0` bắt buộc · `P1` nên làm · `P2` để sau · ước lượng `S` (≤1 ngày) `M` (2–5 ngày) `L` (>1 tuần).

---

## 0. Nguyên tắc (giữ nguyên khi mọi thứ rối)

1. **Self-first** — giải vấn đề của mình trước, cộng đồng sau.
2. **Viết/đo trước, build sau** — với thứ chưa chắc thì đo cầu bằng bài viết hoặc thí nghiệm nhỏ.
3. **Không làm app mobile đầy đủ** (trừ khi có lý do rất mạnh).
4. **Không hứa "chính xác"** khi dữ liệu chưa đủ; luôn hiện độ tin cậy.
5. Mỗi phase có **definition of done** rõ.

---

## 1. Phase 0 — Nền (ĐÃ XONG)

- [x] Research thị trường + engine OSS + dữ liệu (xem `ROUTING-COMFORT-RESEARCH.md`)
- [x] Đo thật: OSM `width` 0,37% / Overture 0,31% ở Hà Đông
- [x] Đo coverage ảnh street-level (Google Street View có ở VN; KartaView thưa)
- [x] Scaffold: ingest OSM → graph → corridor width → score → A* → export → API/web → feedback
- [x] Repo OSS công khai: https://github.com/HienTDTech/duongdep

---

## 2. Phase 1 — MVP tự dùng được (ĐANG LÀM)

**Mục tiêu:** dùng thật ≥5 chuyến, có số liệu so sánh với Google Maps.

| # | Việc | Ưu tiên | Ước lượng | Ghi chú |
|---|---|---|---|---|
| 1.1 | Precompute vùng Hà Nội rộng hơn (Overpass khi ổn định) | P0 | M | OSM API chỉ vùng nhỏ |
| 1.2 | Kiểm tra chất lượng `width_proxy` trên vài tuyến mình hay đi | P0 | S | biết chỗ nào tin được |
| 1.3 | Tab **"Khảo sát tuyến"** tối thiểu: độ cao + Street View deep link + POI | P0 | M | chưa cần ảnh nhúng |
| 1.4 | So sánh tuyến comfort vs Google trên 5 chuyến thật (km, phút, số đoạn ngõ) | P0 | S | **quyết định dự án có giá trị không** |
| 1.5 | Xác nhận sau chuyến ở mức **đoạn** (chạm đoạn trên bản đồ) | P1 | M | hiện mới mức tuyến |
| 1.6 | Lưu/chia sẻ tuyến bằng link (không cần tài khoản) | P1 | S | |
| 1.7 | Log chỉ số: số đoạn ngõ tránh được, chênh thời gian | P1 | S | để trả lời "có đáng không" |
| 1.8 | `expire_old()` chạy định kỳ (cron/APScheduler) | P1 | S | TTL đã có sẵn |
| 1.9 | README + screenshot thật của webapp | P1 | S | repo trông nghiêm túc hơn |

**Definition of done Phase 1:** đã dùng thật ≥5 chuyến; có bảng so sánh comfort-route vs Google; quyết định tiếp hay dừng.

---

## 3. Phase 2 — Dữ liệu tốt hơn (nên làm)

Vấn đề gốc: `width` gần như không có trong OSM → phải suy từ building; building cũng thưa.

| # | Việc | Ưu tiên | Ước lượng | Ghi chú |
|---|---|---|---|---|
| 2.1 | Đo độ phủ building OSM ngoài Hà Nội (vài tỉnh) | P1 | S | quyết định có cần nguồn ngoài |
| 2.2 | Thêm **Microsoft Building Footprints** (tải theo quadkey) | P1 | M | VN có, CDLA-Permissive |
| 2.3 | Thêm **Google Open Buildings** (theo region) | P2 | M | CC BY-4.0/ODbL, phủ ĐNÁ |
| 2.4 | Cải thiện `width_proxy`: confidence, bỏ case một bên quá xa | P1 | M | giảm false "rộng" |
| 2.5 | Surface: thử **Mapillary** cho trục chính (cần token) | P2 | M | coverage chưa rõ |
| 2.6 | Thử **Overture** transportation (surface 36%) | P2 | S | đo trước, biết đâu |
| 2.7 | **Ngập thủ công**: nhập polygon + TTL động | P1 | M | chưa cần tự động |
| 2.8 | Bộ nhớ đệm/nén graph cho vùng lớn (parquet/pickle) | P2 | M | JSON sẽ phình |

---

## 4. Phase 3 — Client & tích hợp (sau khi Phase 1 có số liệu)

| # | Việc | Ưu tiên | Ước lượng | Ghi chú |
|---|---|---|---|---|
| 3.1 | Hướng dẫn GPX + OsmAnd "Navigate by track" trong README | P1 | S | đi đúng tuyến, mất traffic |
| 3.2 | Thử **GraphHopper/ORS custom model** `car_score` → OsmAnd online routing | P2 | L | cắm thẳng engine |
| 3.3 | Profile **BRouter `.brf`** cho xe máy VN | P2 | M | đóng gói ngách |
| 3.4 | `routing.xml` cho OsmAnd | P2 | M | |
| 3.5 | Chọn waypoint thông minh: điểm phân kỳ so với tuyến nhanh nhất | P2 | M | tăng độ khớp Google Maps |

---

## 5. Phase 4 — Cộng đồng (khi Phase 1 đã chứng minh có giá trị)

| # | Việc | Ưu tiên | Ước lượng |
|---|---|---|---|
| 4.1 | Xuất **dataset `vn-road-comfort`** (GeoJSON/Parquet) | P1 | M |
| 4.2 | `CONTRIBUTING.md` + issue templates + good-first-issue | P1 | S |
| 4.3 | Multi-user: consensus + reputation + chống lạm dụng | P2 | L |
| 4.4 | Đóng góp ngược OSM (OSM note / changeset) từ xác nhận | P2 | M |
| 4.5 | Mở rộng thành phố khác (Đà Nẵng/HCM) sau khi Hà Nội ổn | P2 | M |

---

## 6. Việc "nên làm" xuyên suốt

- [ ] README luôn đúng với thực tế code
- [ ] Giữ `pytest` xanh trước mỗi lần push
- [ ] Mỗi lần đo gì đó → ghi số vào `docs/` (đừng để trong đầu)
- [ ] Luôn giữ attribution OSM (ODbL)
- [ ] Không commit token/key (`.env`)
- [ ] Một repo có người dùng > năm repo đồ chơi

---

## 7. KHÔNG làm (cho tới khi có lý do mạnh)

- ❌ App mobile điều hướng đầy đủ (6–18 tháng, lệch định vị)
- ❌ Segmentation ảnh vệ tinh toàn quốc (free quá thô, nét bị paywall/ToS)
- ❌ Tự sinh dữ liệu ngập realtime (rủi ro false-positive = mất niềm tin)
- ❌ Mở nhiều tỉnh/thành trước khi Hà Nội chạy tốt
- ❌ Rewrite engine (OSRM/Valhalla/GraphHopper) — dùng cái có sẵn

---

## 8. Rủi ro & câu hỏi mở (review lại sau mỗi phase)

| Rủi ro / câu hỏi | Cách xử lý |
|---|---|
| Overpass công cộng không ổn định | fallback OSM API (đã có); tự host Overpass nếu cần |
| Building OSM thưa → width sai | thêm MS/Google footprints; hiện confidence |
| Google Maps giới hạn 3/9 waypoint | UI nói rõ "gần đúng"; GPX + OsmAnd nếu cần khớp |
| **Có thực sự đỡ khó chịu hơn không?** | đo ở 1.4 — đây là câu hỏi sống còn |
| Liệu có ai khác dùng? | chưa cần ở Phase 1; để bài viết trả lời (xem `CONTENT-IDEAS.md`) |

---

## 9. Mốc thời gian đề xuất

| Tuần | Việc chính |
|---|---|
| 1 | 1.1 + 1.2 + 1.4 (precompute, kiểm width, đo 5 chuyến) |
| 2 | 1.3 (tab Khảo sát) + 1.5 (xác nhận mức đoạn) |
| 3 | 2.1 + 2.2 (building footprint tốt hơn) |
| 4 | 2.7 (ngập thủ công) + viết bài #1 |
| 5+ | tuỳ kết quả 1.4: mở Phase 3 hoặc dừng/pivot |

> **Cổng quyết định (sau tuần 1):** nếu tuyến comfort không tốt hơn Google rõ rệt → **dừng build, chuyển sang viết bài** (nội dung vẫn có giá trị).

---

## 10. Bài viết / nội dung

Backlog bài viết **không nằm trong repo này** (repo duongdep chỉ chứa code + tài liệu kỹ thuật).
Nó thuộc kế hoạch brand cá nhân:

```
~/Projects/Work/personal/research-personal/BLOG-BACKLOG-duongdep.md
```
