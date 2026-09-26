# Routing "dễ chịu" — research thị trường & đánh giá OSS

Ngày research: 24/09/2026 · Người làm: Trần Doãn Hiển
Trạng thái: **research xong — có khuyến nghị, chưa build**

> Câu hỏi gốc: Google Maps hay dồn vào đường bé/ngõ nhỏ, báo ngập sai rồi tự đổi lộ trình,
> và không cho ưu tiên "đường to – đẹp – vắng". Đã có sản phẩm free/OSS nào giải đúng
> hoặc gần đúng chưa? Nếu mình làm OSS thì có khả thi, có kéo được người dùng, có lợi cho brand không?

---

## 0. TL;DR (đọc cái này là đủ)

| Câu hỏi | Trả lời ngắn |
|---|---|
| Có app free nào giải **đúng trọn vẹn** (tránh ngõ nhỏ + tránh ngập + ưu tiên to/đẹp/vắng + không tự reroute) không? | **Không.** Không có cái nào gói đủ 4 thứ, đặc biệt ở chất lượng dữ liệu Việt Nam. |
| Có OSS nào **gần đúng** không? | **Có, nhiều.** OsmAnd + Organic Maps (app), Valhalla / GraphHopper / OpenRouteService / BRouter (engine). Xem §3. |
| Phần "tránh ngõ nhỏ" giải được bằng máy chưa? | Engine **đã làm được**, nhưng **dữ liệu `width` gần như không có** (0,37% số đường ở Hà Đông). Phải suy luận từ `highway` class + `surface` + `lanes` — tức là "đoán", không phải "biết". |
| Phần "tránh ngập" giải được chưa? | **Chưa có sản phẩm OSS tử tế.** Chỉ có demo sinh viên + nghiên cứu. Google mới có ở một số nước (Ask Maps, PH 9/2026). Đây là **nút cổ chai về dữ liệu + độ tin cậy**, không phải thuật toán. |
| Nếu mình làm OSS thì khả thi? | **Kỹ thuật: khả thi** (engine có sẵn 70–80%). **Thương mại/đại chúng: rất khó.** Niche: được. Xem §6. |
| Có kéo được người dùng không? | Đại chúng: gần như không (Google free + network effect). Niche (dân đi xe máy HN/HCM, dân hay ngập, moto tour): **có, nếu chọn đúng niche và có dữ liệu**. |
| Có lợi cho brand cá nhân? | **Có — nhưng bài viết kèm dữ liệu thật có giá trị/giờ cao hơn bản thân cái app.** Xem §7. |

**Khuyến nghị số 1:** đừng làm app điều hướng đầy đủ. Làm **một bài phân tích kèm số liệu OSM thật + một demo nhỏ** (web planner trên Valhalla/ORS, Python backend, có "comfort slider" + nhập vùng ngập).
Đúng stack của mình, đúng brand "agentic AI", rủi ro thấp, và **bài viết mới là thứ được share**.

> **Cập nhật 24/09 (bổ sung #2)** — hướng đã chốt: **chỉ Việt Nam, ưu tiên ô tô, OSS phục vụ bản thân trước,
> và dữ liệu width sẽ suy ra từ building footprints (không dùng ảnh vệ tinh hàng loạt).**
> Xem **§11** ở cuối — có số đo Overture, đánh giá ảnh vệ tinh + AI, và kiến trúc OSS self-first.
>
> **Cập nhật 24/09 (bổ sung #3):** Phase 1 = **webapp dùng ngay** + **xuất lộ trình sang Google Maps**
> + **vòng kiểm chứng/xác nhận**. Xem **§12** — kèm giới hạn thật của Google Maps (3 waypoint trên mobile / 9 trên app)
> và schema feedback.

---

## 1. Tách vấn đề thành 4 nhu cầu riêng biệt

Vấn đề của mình thực ra là **4 bài toán khác nhau**, mức khó rất khác nhau:

| # | Nhu cầu | Bản chất | Mức khó |
|---|---|---|---|
| A | **Tránh đường bé / ngõ nhỏ** | Bài toán *routing preference* trên dữ liệu OSM | 🟡 Trung bình — engine làm được, dữ liệu là vấn đề |
| B | **Tránh khu vực ngập** | *Dynamic constraints* (vùng cấm theo thời gian thực) | 🔴 Khó — cần dữ liệu ngập đáng tin |
| C | **Ưu tiên to / đẹp / vắng** | *Scenic / comfort routing* (đa mục tiêu, chủ quan) | 🟡 Trung bình — moto tour đã làm |
| D | **Không tự ý đổi lộ trình khi mình đang lái** | **UX / product**, không phải thuật toán | 🟢 Dễ — nhưng không can thiệp được vào Google Maps |

Điểm quan trọng: **D không phải vấn đề kỹ thuật**. Google Maps không có tuỳ chọn tắt auto-reroute.
Cách duy nhất giải D là **đổi app** (OsmAnd có cấu hình recalc) hoặc tự viết app. Đây là lý do
"A + B + C" và "D" nên tách ra khi đánh giá.

---

## 2. Vì sao Google Maps lại thích dẫn vào đường bé?

Ghi nhanh để không quên bản chất:

- Google tối ưu **thời gian dự kiến**. Trong nội đô, đường bé đôi khi nhanh hơn *trên giấy*
  vì ít đèn, ít xe — dù thực tế khó đi.
- Google **không có (và không expose)** khái niệm "đường rộng/đẹp/dễ chịu". Nó có
  *traffic*, *incidents*, chứ không có *road comfort*.
- Báo ngập của Google đến từ **suy đoán mô hình + report cộng đồng** → **false positive là có thật**
  (đúng ca của mình hôm 23/09).
- Các tuỳ chọn Google Maps hiện có chỉ là: **tránh toll / highway / ferry** (+ eco route). **Không có**
  "tránh đường bé", "tránh đường xấu", "ưu tiên đường đẹp". Đây là **nhu cầu có thật nhưng Google
  không phục vụ** (xem bằng chứng §3.5).

---

## 3. Bản đồ giải pháp hiện có (free + OSS + thương mại)

### 3.1 App cho người dùng cuối

| App | License / giá | Tránh ngõ nhỏ? | Tránh ngập? | Ưu tiên rộng/đẹp/vắng? | Ghi chú |
|---|---|---|---|---|---|
| **Google Maps** | Free | ❌ | ⚠️ có warning/ngập ở vài nước (Ask Maps, PH 9/2026), **không VN** | ❌ | Chỉ tránh toll/highway/ferry |
| **Waze** | Free | ❌ | ❌ (có report, không tránh) | ❌ | Có "avoid dirt roads"/unpaved ở vài bản |
| **Apple Maps** | Free | ❌ | ❌ | ❌ | Chỉ tránh toll/highway |
| **OsmAnd** | OSS (repo 6.0k⭐, offline free/trả phí feature) | ✅ qua `routing.xml` + `avoid_unpaved`, `width` | ⚠️ qua "Avoid roads / nogo points" thủ công | ✅ `prefer smaller/bigger roads`, custom profile | Mạnh nhất về tuỳ biến, **nhưng UI phức tạp cho người thường** |
| **Organic Maps / CoMaps** | OSS (15.5k⭐, offline) | ⚠️ chỉ `avoid_unpaved` | ❌ | ❌ | Đơn giản, đẹp, nhưng routing **ít tuỳ biến** |
| **Magic Earth** | Free (closed source) | ⚠️ có avoid unpaved | ❌ | ❌ | Free nhưng không phải OSS |
| **Kurviger / Calimoto / Scenic** | Freemium | ✅ (tránh motorway/gravel) | ❌ | ✅✅ **"curvy/scenic roads"** — đúng nhu cầu C | Đây là đối thủ mạnh nhất cho nhu cầu C, nhưng **hướng moto touring, không phải đi làm hằng ngày** |
| **Vietmap / Goong** | Thương mại VN | ⚠️ | ❌ | ❌ | Điều hướng VN, dùng cho oto/fleet; không có comfort routing |

### 3.2 Routing engine OSS — cái quan trọng nhất

Đây là "động cơ" bên dưới mọi app. **Năng lực thật của chúng quyết định app nào làm được gì.**

| Engine | Sao (24/09/26) | License | "Tránh đường bé" | "Tránh ngập (vùng cấm)" | "Rộng/đẹp/vắng" | Ghi chú |
|---|---|---|---|---|---|---|
| **OSRM** | 8.1k⭐ | BSD-2 | ❌ | ❌ | ❌ | Rất nhanh, nhưng profile **fix lúc build** — không linh hoạt |
| **GraphHopper** | 6.7k⭐ | Apache-2.0 | ✅ `custom_model` theo `road_class`, `surface`, `smoothness`, `lanes` | ✅ custom areas / block edges | ✅ priority rules; có profile `curvature.json` | Custom model = JSON, dễ dùng |
| **Valhalla** | 6.3k⭐ | (NOASSERTION, thực tế MIT-ish) | ✅ `alley_factor`, `alley_penalty`, `use_highways` | ✅✅ **`exclude_polygons`** (GeoJSON) — mạnh nhất | ✅ `use_highways`, `use_trails` (motorcycle "adventure"), `use_distance` | Dùng bởi nhiều app; `exclude_polygons` gần như sinh ra cho ca ngập |
| **OpenRouteService** | 2.0k⭐ | GPL-3.0 | ⚠️ `custom_model` (road_class/surface), `minimum_width` chỉ cho wheelchair | ✅ `avoid_polygons` | ⚠️ `green`/`quiet` **chỉ cho foot** | Custom model còn **"experimental"**, không bật trên public API |
| **BRouter** | 0.7k⭐ | MIT | ✅ profile **script tự do** (điều kiện theo `surface`, `tracktype`, `highway`…) | ✅ nogo points, elevation | ✅ | Offline Android, cực linh hoạt, **nhưng viết profile như lập trình** |

**Kết luận kỹ thuật:** nhu cầu A và C **engine đã giải**. Nhu cầu B (ngập) engine cũng có
primitive (`exclude_polygons` / `avoid_polygons`) — **cái thiếu là nguồn dữ liệu ngập đáng tin**,
không phải thuật toán.

### 3.3 Feature matrix — "đúng/gần đúng" đến đâu

| Giải pháp | Tránh ngõ nhỏ | Tránh ngập | Ưu tiên đẹp/vắng | Không tự reroute | Offline | Package cho người thường |
|---|:--:|:--:|:--:|:--:|:--:|:--:|
| Google Maps | ❌ | ⚠️ | ❌ | ❌ | ⚠️ | ✅ |
| Waze | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| OsmAnd | ✅ | ⚠️ thủ công | ✅ | ✅ (cấu hình) | ✅ | ❌ (phức tạp) |
| Organic Maps | ⚠️ | ❌ | ❌ | ⚠️ | ✅ | ✅ |
| Kurviger/Calimoto | ✅ | ❌ | ✅✅ | ✅ | ✅ | ✅ (nhưng moto) |
| Build trên Valhalla/GraphHopper | ✅ | ✅ | ✅ | ✅ | tuỳ | **cần tự làm** |

→ **Ô trống thật sự** nằm ở giao của: **tránh ngõ nhỏ + tránh ngập + gói cho người thường + dữ liệu VN.**

### 3.4 Ngập — hiện trạng

| Hướng | Ví dụ | Vấn đề |
|---|---|---|
| Warning ngập thương mại | Google **Ask Maps** (Philippines, 9/2026): hỏi "đường X có ngập không?" | Chỉ một số nước; không có VN; đóng |
| Nghiên cứu / demo | `floodsafe-routing-system` (GraphHopper + Spring Boot), `RescueRoute-AI`, `PetaBencana` (Indonesia) | Hầu hết **0⭐**, demo học tập, không vận hành |
| Ảnh vệ tinh SAR | Sentinel-1 (miễn phí, Copernicus) → bản đồ ngập | **Trễ** (giờ–ngày), chỉ bắt trận lớn, không bắt ngập đường nội đô lúc mưa |
| Dữ liệu cơ quan VN | Công ty thoát nước HN / Trung tâm chống ngập HCM | Không có API mở, rời rạc, không realtime chuẩn |
| Cộng đồng | Nhóm Facebook/Zalo "Ngập đường…", VOV Giao thông | Realtime nhất **nhưng phi cấu trúc, ồn, khó tin** |

→ Nút cổ chai của B là **độ tin cậy**. Một "avoid polygon" sai còn tệ hơn không có: nó đúng là
cái đang làm mình bực với Google. **Không nên tự hứa hẹn "tránh ngập" nếu chưa giải được nguồn.**

### 3.5 Bằng chứng người dùng muốn (demand signal)

Từ Reddit (pullpush.io full-text search, 24/09/2026):

- `r/GoogleMaps` — *"Do you think Maps will add AVOID UNPAVED ROADS option to navigation setting?"* (12↑, 7 comments).
- `r/WesternAustralia` — cần app **phân biệt đường trải nhựa vs không**, Google/Maps.me/OsmAnd đều không đủ rõ.
- `r/OsmAnd` — *"How can I get OsmAnd to prioritize only back roads…"* (7↑); *"custom routing … avoid streets/waypoints"*; *"Importing a custom routing.xml …"* (than phiền app khó dùng khi recalc sai).
- `r/OsmAnd` — nhóm sinh viên làm **"shadow routing"** (tránh nắng) → chứng tỏn "comfort routing" là hướng được quan tâm.
- `r/Triumph400` — tìm **stack điều hướng free/OSS** thay Mapbox (18↑).
- `r/openstreetmap` — *"I built an open source routing app for hiking after frustration with subscriptions"* (105↑, 23c) → **một repo ngách + câu chuyện đúng = được đón nhận**.

→ Nhu cầu **có thật và lặp lại**, nhưng phân tán theo niche. Không có "một cơn đau chung" cho đại chúng.

---

## 4. Vấn đề dữ liệu — phần quyết định thành/bại (đo thật)

Mình đã **đo trực tiếp trên OpenStreetMap** bằng Overpass API, vùng Hà Đông / Thanh Xuân / một phần
Thanh Trì (bbox `20.93,105.72,21.03,105.85`, ~11×14 km), snapshot OSM 2026-07-24:

| Chỉ số | Số way | % trên tổng |
|---|---:|---:|
| Tổng way `highway=*` | **36.980** | 100% |
| Có `width` (chiều rộng) | **137** | **0,37%** ⚠️ |
| Có `lanes` (số làn) | 3.245 | 8,8% |
| Có `surface` (bề mặt) | 12.033 | 32,5% |
| Có `smoothness` | 419 | 1,1% |
| Có `maxspeed` | 778 | 2,1% |
| Đường **lớn** (trunk/primary/secondary/tertiary + link) | 3.863 | 10,4% |
| Đường **nhỏ** (residential/service/living_street/unclassified/track/path/footway/pedestrian) | 32.532 | **88%** |

Và trong từng nhóm:

| | Có `lanes` | Có `surface` |
|---|---:|---:|
| Đường **lớn** | 2.815 / 3.863 = **72,9%** | (cao) |
| Đường **nhỏ** | 357 / 32.532 = **1,1%** | 7.117 / 32.532 = 21,9% |

### Hệ quả — 3 điều phải nhớ

1. **Không thể "tránh đường bé" bằng tag `width`.** 0,37% là quá ít. Mọi engine đều phải
   **suy luận từ `highway` class** (`residential`/`service` = nhỏ, `primary`/`secondary` = to).
   Cách này **đúng phần lớn nhưng không hoàn hảo** — có phố rộng bị tag `residential`, có
   `service` rộng.
2. **88% đường ở Hà Đông là đường nhỏ.** Đây chính là lý do Google có *rất nhiều* lựa chọn "đường bé"
   để dồn vào. Vấn đề là thật và có quy mô.
3. **`surface` chỉ có 32,5%** → "tránh đường xấu/không trải nhựa" cũng chỉ làm được một phần,
   và dễ sai ở VN (nhiều đường bê tông không được tag).

### Nguồn dữ liệu thay thế cho `width` (nếu muốn đi xa hơn)

| Nguồn | Cho gì | Chi phí |
|---|---|---|
| Overture Maps (transportation theme) | Road segments có `class`, `surface`, có nơi có `width` (tổng hợp OSM + TomTom…) | Free, cần xử lý |
| Ảnh vệ tinh + building footprints | Suy ra "street canyon width" | Nặng, ML |
| Mapillary / KartaView | Ảnh đường → suy chiều rộng | Nặng |
| GPS trace / Strava heatmap | Đường nào dân hay đi → proxy "dễ đi" | Vấn đề privacy |
| Dữ liệu Sở GTVT / quy hoạch | Phân loại đường chuẩn | Không mở, khó |

→ Đây là **moat dữ liệu thật** nếu ai làm được cho VN. Nhưng cũng là **6+ tháng**, không phải vibe-code.

---

## 5. "Đúng/gần đúng" — chốt lại

**Không có sản phẩm free/OSS nào giải đủ 4 nhu cầu A–D cho người dùng VN.**

- **Gần nhất về app:** OsmAnd (A + C + D, thủ công) và Organic Maps (đơn giản, thiếu A/C).
- **Gần nhất về engine:** Valhalla (`exclude_polygons` + `alley_factor` + `use_highways`) — chỉ thiếu dữ liệu.
- **Đã giải tốt nhất cho C:** Kurviger / Calimoto / Scenic (moto).
- **B chưa ai giải tử tế.**

---

## 6. Nếu mình build OSS — khả thi không?

### 6.1 Bóc theo 4 hướng sản phẩm

| Hướng | Nội dung | Công sức | Moat | Defend được? | Khớp brand? |
|---|---|---|---|---|---|
| **A. Profile cho BRouter/OsmAnd** | `routing.xml` / `.brf` cho xe máy VN: tránh ngõ, ưu tiên trục lớn, tránh unpaved | **3–10 ngày** | Thấp (ai cũng copy) | ✅ (mình hiểu data) | ⚠️ yếu (không phải backend/AI) |
| **B. Web route planner** (Python + Valhalla/ORS) | Comfort slider (0–100 "thoáng"), nhập vùng ngập → `exclude_polygons`, không tự reroute | **2–4 tuần vibe-code** | Trung bình (UX + data) | ✅ | ✅ **Python backend, dễ gắn câu chuyện agentic AI** |
| **C. Mobile app điều hướng đầy đủ** | Turn-by-turn, offline, report ngập | **6–18 tháng** | Cao (data + network) | ⚠️ | ❌ lệch định vị |
| **D. Thư viện Python "comfort routing"** | Bọc Valhalla/ORS + OSM preprocessing, expose API sạch | 4–8 tuần | Thấp–TB | ✅ | ✅ |

### 6.2 Khả thi kỹ thuật: **CÓ** (70–80% có sẵn)

Không cần viết lại engine. Cần: OSM extract VN → Valhalla/ORS → một lớp suy luận
"comfort score" theo `highway`/`surface`/`lanes` → UI. Phần khó nằm ở **dữ liệu**, không phải code.

### 6.3 Khả thi thương mại/đại chúng: **RẤT KHÓ**

- Google/Waze **miễn phí**, tốt, đã có network effect. Người dùng không tự chuyển app điều hướng.
- Điều hướng là thị trường **winner-take-most**: dữ liệu giao thông, POI, địa chỉ — mình không có.
- Mobile nav = gánh nặng vận hành (map tiles, battery, offline, review app store).

### 6.4 Nhưng niche thì **được**

| Niche | Quy mô | Vì sao hợp |
|---|---|---|
| **Xe máy đi làm HN/HCM** | Rất lớn | Google Maps vốn nổi tiếng dồn xe máy vào ngõ; đau đúng ý mình |
| **Moto touring / phượt** | Trung bình, đam mê cao | Nhu cầu C cực rõ; nhưng Kurviger/Calimoto đã chiếm |
| **Dân hay gặp ngập (HCM/HN/ĐN/CT)** | Lớn | Đau nhất, nhưng phụ thuộc dữ liệu ngập |
| **Cyclist / hiker** | Nhỏ | BRouter/OsmAnd đã đủ |

→ Nếu làm cho **xe máy VN tránh ngõ** và kể đúng câu chuyện, **có cửa**. Nhưng đây là *marketing niche*,
không phải *thị trường đại chúng*.

### 6.5 Có kéo được người dùng không?

- **Kỳ vọng đúng:** repo OSS ngách chất lượng + bài viết tốt → vài trăm → vài nghìn người dùng,
  vài trăm ⭐. **Không** phải triệu người.
- **Cần phân phối:** r/openstreetmap, r/OsmAnd, r/GoogleMaps, Hacker News, Viblo, group xe máy/phượt,
  báo VN (VnExpress/GenK hay viết về "Google Maps dẫn vào ngõ").
- **Repo không tự lan.** Phải có: README tốt + demo chạy được + 1 bài viết kể đúng vấn đề.
- **Nguyên tắc của mình (từ `OSS-AND-WRITING-PLAN.md`) vẫn đúng:** *một repo có người dùng > năm repo đồ chơi*.

### 6.6 Rủi ro

| Rủi ro | Mức | Xử lý |
|---|---|---|
| Dữ liệu `width`/`surface` thiếu → tránh ngõ sai | **Cao** | Dùng `highway` class + nói rõ giới hạn; đừng hứa chính xác |
| Ngập: false positive → mất niềm tin | **Rất cao** | Không tự sinh dữ liệu ngập; để người dùng nhập/chọn nguồn |
| Thị trường đã loãng (OSM routing) | Trung bình | Khác biệt ở **dữ liệu VN + UX "comfort", không phải thuật toán** |
| Lệch định vị (GIS/mobile ≠ Python backend/AI) | Trung bình | Đóng khung là "agentic engineering + Python backend", không phải "app GIS" |
| Tốn thời gian | Cao | Chọn hướng B (2–4 tuần), không phải C |

---

## 7. Đánh giá cho **brand cá nhân**

| Kênh | Giá trị brand / giờ | Ghi chú |
|---|---|---|
| **Bài viết "Vì sao Google Maps thích dẫn vào ngõ" + số liệu OSM thật** | ⭐⭐⭐⭐⭐ | Số liệu này **chưa ai public cho Hà Nội** → độc, dễ được share, không thể bị vặn (là dữ liệu tự đo) |
| **Repo profile/demo nhỏ (B/D)** | ⭐⭐⭐⭐ | Có artifact thật để trưng; đúng công thức "vấn đề tôi gặp → cách giải → kết quả → limits" |
| **Mobile app đầy đủ** | ⭐⭐ | Tốn 6–18 tháng, rủi ro cao, lệch brand |
| **Chỉ viết bài, không repo** | ⭐⭐⭐ | Vẫn tốt; nhưng có repo + bài = mạnh hơn |

**Điểm khớp brand mình (Tech Lead | Python · Django | Agentic AI):**
- Hướng **B/D là Python backend** → khớp.
- Có thể kể: *"tôi thiết kế, rồi điều khiển AI agent dựng demo"* → khớp "agentic engineering" (giống softsoil).
- **Không** nên kể như "tôi làm app bản đồ" — đó là claim không defend được về mobile/GIS.

**Cái bẫy cần tránh:** dùng 3 tháng làm app mobile rồi không ai dùng → vừa mất thời gian, vừa không
có gì để khoe. **Bài viết + demo 2 tuần, đăng đúng chỗ, an toàn hơn nhiều.**

---

## 8. Khuyến nghị (xếp hạng)

| Ưu tiên | Việc | Vì sao | Thời gian |
|---|---|---|---|
| **1** | **Bài phân tích + số liệu OSM thật** ("Google Maps và những con ngõ Hà Nội") + demo web planner Python trên Valhalla/ORS | Đúng brand, rủi ro thấp, **nội dung mới chưa ai có**, share được | 1 tuần viết + 1–2 tuần demo |
| **2** | **`routing.xml`/BRouter profile cho xe máy VN** (tránh ngõ, ưu tiên trục lớn, tránh unpaved) | Artifact ngách, hữu ích thật cho cộng đồng VN, nhỏ | 3–10 ngày |
| **3** | **Pipeline dữ liệu ngập mở cho VN** (report cộng đồng + Sentinel-1) — *chỉ khi #1 xác nhận có cầu* | Giá trị cao, độc, nhưng **rủi ro độ tin cậy cao** | 1–3 tháng |
| **4** | **App mobile điều hướng đầy đủ** | Không nên, trừ khi có lý do rất mạnh | ❌ |

**Nguyên tắc giữ nguyên (từ plan cũ):** *viết bài **trước**, build **sau***. Bài viết kiểm tra cầu
miễn phí; build sai thứ = mất vài tháng.

**Việc tuần này nếu muốn đi tiếp:**
1. [ ] Viết bài #1 với số liệu Overpass ở §4 (bài này tự nó đã là nội dung tốt).
2. [ ] Dựng demo 1 trang: nhập điểm đi/đến + kéo "comfort slider" + dán polygon ngập → gọi Valhalla.
3. [ ] Đăng thử ở nơi không ai biết mình (blog riêng / r/openstreetmap) trước khi lên LinkedIn.

---

## 9. Giới hạn của research này (mình tự nói trước)

- **Search engine bị chặn** trong môi trường research (DuckDuckGo/Google/Bing bị block). Nên:
  - Dữ liệu GitHub: **từ GitHub API, xác thực** (sao, license, ngày push).
  - Tính năng engine: **từ tài liệu chính thức trong repo** (GraphHopper `custom-models.md`, Valhalla `openapi.yaml`, ORS `routing-options.md`, OsmAnd `routing.xml`, Organic Maps `strings.txt`, BRouter docs).
  - **Tính năng app thương mại** (Google/Waze/Apple/Kurviger/TomTom/HERE) một phần từ **hiểu biết sản phẩm**, chưa đối chiếu được hết tài liệu chính thức vì trang bị chặn → **cần kiểm chứng lại** trước khi trích dẫn công khai.
- **Số liệu OSM** chỉ từ **một bbox Hà Đông/Thanh Xuân**, snapshot 2026-07-24. Không đại diện toàn VN (nông thôn còn thưa dữ liệu hơn, `width` còn ít hơn).
- **Reddit** search bằng pullpush.io, relevance kém ở tiếng Việt → demand signal lấy từ các thread tiếng Anh, **chưa đo được cầu người dùng VN** (cần khảo sát group/Facebook/Viblo).
- **Chưa benchmark thực tế** Valhalla/ORS trên dữ liệu VN (chưa build graph). Đánh giá "engine làm được" là **theo tài liệu**, chưa chạy thử.
- **Chưa có số chi phí vận hành** (map tiles, server, offline packaging) nếu làm app.

---

## 10. Nguồn

**Routing engine / tài liệu chính thức**
- GraphHopper custom models — https://github.com/graphhopper/graphhopper/blob/master/docs/core/custom-models.md
- GraphHopper `curvature.json` — https://github.com/graphhopper/graphhopper/blob/master/core/src/main/resources/com/graphhopper/custom_models/curvature.json
- Valhalla API reference (costing options, `exclude_polygons`, `alley_factor`, `use_highways`) — https://github.com/valhalla/valhalla/blob/master/docs/docs/api/openapi.yaml
- OpenRouteService routing options (`avoid_polygons`, `avoid_features`, restrictions) — https://github.com/GIScience/openrouteservice/blob/main/docs/api-reference/endpoints/directions/routing-options.md
- OpenRouteService custom models — https://github.com/GIScience/openrouteservice/blob/main/docs/api-reference/endpoints/directions/custom-models.md
- BRouter cost functions ("freely configurable routing profiles") — https://github.com/abrensch/brouter/blob/master/docs/features/costfunctions.md
- OsmAnd `routing.xml` (`avoid_unpaved`, `prefer_unpaved`, `width`) — https://github.com/osmandapp/OsmAnd-resources/blob/master/routing/routing.xml
- Organic Maps strings (`avoid_unpaved`, `avoid_tolls`, `define roads to avoid`) — https://github.com/organicmaps/organicmaps/blob/master/data/strings/strings.txt

**Số liệu OSM (tự đo)**
- Overpass API (mirror `overpass.kumi.systems`), snapshot `2026-07-24T11:04:51Z`, bbox `20.93,105.72,21.03,105.85`.

**Demand signal**
- Reddit qua pullpush.io (24/09/2026): r/GoogleMaps (avoid unpaved, 12↑), r/WesternAustralia (paved/unpaved), r/OsmAnd (prioritize back roads; custom routing.xml), r/Triumph400 (OSS nav stack, 18↑), r/openstreetmap (Crestr hiking app, 105↑), r/Tek_Philippines (Google Ask Maps flood, PH).

**Ngập / thương mại**
- Google Maps "Ask Maps" flood updates, Philippines (Technobaboy, 15/09/2026) — https://www.technobaboy.com/2026/09/15/google-maps-launches-ask-maps-in-ph-with-live-route-updates-to-avoid-floods/
- HERE Routing v8 `avoid[features]` = seasonalClosure, tollRoad, controlledAccessHighway, ferry, carShuttleTrain, tunnel, `dirtRoad`, uTurns; `avoid[areas]` — https://docs.here.com/routing/reference/routing-api-v8-calculateroutes.md

**Star/license (GitHub API, 24/09/2026)**
- OSRM 8.105⭐ BSD-2 · GraphHopper 6.703⭐ Apache-2.0 · Valhalla 6.251⭐ · OpenRouteService 1.975⭐ GPL-3.0 · BRouter 722⭐ MIT · OsmAnd 6.035⭐ · Organic Maps 15.491⭐

---

# 11. Bổ sung #2 (24/09/2026) — VN-only, ô tô-first, self-first, và câu chuyện dữ liệu width

Bốn chốt mới từ trao đổi:

1. Chỉ cần bản đồ đường xá **Việt Nam**. → Phạm vi nhỏ hơn rất nhiều, precompute được.
2. **Ưu tiên ô tô**; xe máy/xe đạp là nice-to-have (và có mục tiêu **ngược**: thích đường dễ đi, an toàn, ít xe to, **chấp nhận ngõ nhỏ**).
3. Dữ liệu `width`/`surface` thiếu → cân nhắc **ảnh vệ tinh + AI**. Không cần làm hàng loạt, làm cho route cá nhân trước.
4. **OSS, phục vụ bản thân trước.**

## 11.1 Kiểm chứng: Overture Maps có cứu được `width` không? → **KHÔNG**

Overture Maps transportation theme có cả `width_rules` (chiều rộng edge-to-edge, mét) và `road_surface`,
được dựng từ OSM + TomTom + nguồn địa phương. Nghe rất hứa hẹn. Mình đã **query trực tiếp** release
`2026-09-23.0` bằng DuckDB, đúng bbox Hà Đông/Thanh Xuân như §4:

| Overture `transportation/segment`, subtype=road | Số segment | % |
|---|---:|---:|
| Tổng | **40.901** | 100% |
| Có `width_rules` | **127** | **0,31%** ⚠️ |
| Có `road_surface` | 14.855 | 36,3% |
| Có `speed_limits` | 2.899 | 7,1% |

→ `width` của Overture ở VN **y hệt OSM (0,31% vs 0,37%)** — vì nó kế thừa OSM, TomTom không phủ VN.
`surface` khá hơn chút (36% vs 32%). **Kết luận: đừng trông vào Overture để có width.** (Đã đo, không phải phỏng đoán.)

## 11.2 Ảnh vệ tinh + AI để đo `width`: đánh giá thẳng

| Hướng | Độ phân giải / giá | Dùng được cho ngõ 3–5 m? | Cho OSS? |
|---|---|---|---|
| **Sentinel-2** (free, Copernicus) | **10 m/px** | ❌ ngõ 4 m < 1 pixel | ✅ license tốt, nhưng vô dụng cho width |
| **Sentinel-1 SAR** (free) | 10 m/px | ❌ | ✅ nhưng chỉ bắt ngập, không đo width |
| **Landsat** | 30 m/px | ❌ | ✅ nhưng vô dụng |
| **Maxar / Planet / Airbus** | 0,3–0,5 m | ✅ | ❌ **trả tiền**, không redistribute được |
| **Google/Bing map tiles** | 0,3–0,6 m | ✅ | ❌ **ToS cấm bulk download + tạo derived data** |
| **Ảnh hàng không VN (TNMT)** | tốt | ✅ | ❌ không mở |

**Kết luận:** muốn đo width trực tiếp bằng điểm ảnh thì **hoặc quá thô (free), hoặc bị khoá sau paywall/ToS (nét).**
Với một dự án OSS, **ảnh vệ tinh không phải con đường rẻ và sạch.** Đó là lý do nên bỏ hướng "segmentation ảnh vệ tinh toàn quốc".

### AI dùng ở đâu cho hợp lý (và không)

| Bài toán | Cách nên làm |
|---|---|
| **Width / độ lớn đường** | ❌ Không dùng pixel ảnh. → **hình học building footprints** (§11.3) |
| **Surface (nhựa vs đất)** | ⚠️ Ảnh vệ tinh yếu. → OSM `surface` + Overture + **Mapillary/KartaView** (ảnh ngang, phân loại bằng model có sẵn) cho các trục cần thiết |
| **Phát hiện ngõ/đường mới** | Mapillary/street-level + OSM thiếu → có thể dùng ML ảnh, nhưng ưu tiên thấp |

→ **AI hữu ích nhất ở ảnh street-level (Mapillary) cho surface, không phải ở ảnh vệ tinh cho width.**

## 11.3 Cách đúng: **building footprints → corridor width** (không cần ML)

Ý tưởng: trong đô thị, **độ rộng ngõ ≈ khoảng cách giữa hai dãy nhà**. Lấy tim đường OSM, tại nhiều điểm,
chiếu tia vuông góc sang hai bên, tìm mặt building gần nhất mỗi bên → **facade-to-facade width**.
Thuật toán **tất định, giải thích được, chạy trên laptop, không train model.**

**Nguồn building footprints:**

| Nguồn | License | Phủ VN | Ghi chú |
|---|---|---|---|
| **OSM `building=*`** | ODbL | ✅ | Trong bbox Hà Đông: **31.846 building way + 94 relation** — **đủ dùng cho cá nhân, không cần tải gì thêm** |
| **Google Open Buildings v3** | **CC BY 4.0 *hoặc* ODbL** (chọn 1) | ✅ Đông Nam Á | 1,8 tỷ building, suy từ **ảnh 50 cm**; có trên Earth Engine + GCS |
| **Microsoft GlobalMLBuildingFootprints** | CDLA Permissive 2.0 | ✅ (226 region) | Tile Hà Nội `quadkey=132210112` = **123,5 MB** gz; tải đúng tile cần |

**Vì sao hợp với self-first:** chỉ cần OSM (đã có sẵn) là bắt đầu được ngay. Khi cần đầy hơn thì
thêm tile Microsoft/Google cho đúng khu vực — **không cần xử lý toàn quốc ngay.**

**Giới hạn phải ghi rõ (để không bị vặn):**
- Đây là *facade-to-facade*, gồm cả vỉa hè/sân — **không phải width mặt đường**. Với xếp hạng "to vs nhỏ" thì ổn.
- Đường ven đô/không có nhà → không đo được; dùng `highway` class bù.
- Building thiếu/sai trong OSM → nhiễu; dùng confidence score của Google/MS để lọc.
- Ngõ có nhà lùi sâu → width bị đo rộng hơn thực tế.

## 11.4 Kiến trúc OSS self-first (đề xuất)

```
route-comfort/                 # repo OSS, Python
├── ingest/                     # OSM PBF (Vietnam extract) -> graph
│   ├── osm.py                  # pyosmium / osmnx, lọc highway + building
│   └── buildings.py            # corridor width từ building footprints
├── score/                      # gán điểm cho từng edge
│   ├── car.py                  # CAR: ưu tiên rộng, tránh ngõ/service/alley
│   └── bike.py                 # BIKE/MOTO: ưu tiên ít xe to, cho phép ngõ nhỏ
├── route/                      # A* / k-shortest trên graph đã gán điểm
│   └── engine.py               # (rustworkx/igraph) hoặc gọi Valhalla/ORS
├── export/                     # xuất profile cho OsmAnd/BRouter, tile cho Valhalla
└── cli.py                      # `rcomfort route --from ... --to ... --mode car`
```

**Hai profile — điểm bán được:**
- **Ô tô:** tối đa hoá width + `highway` class lớn + `surface` nhựa; phạt nặng `service`/`alley`/`living_street`.
- **Xe máy/xe đạp:** tối thiểu hoá "stress" (LTS — Level of Traffic Stress): **tránh `primary`/`trunk`**, chấp nhận `residential`/ngõ nhỏ, ưu tiên `surface` tốt.

```
car_score  = w1*width + w2*road_class + w3*surface      (càng lớn càng tốt)
bike_score = -w1*traffic_stress - w2*bad_surface         (cho phép width nhỏ)
```

> Có tiền lệ OSS cho bike: `SustainableMobility/bicycling-lts-classification` (MIT),
> `anerv/dk_bicycle_network`, `dvrpc/low-stress-bike-routing`. → **không phải tự phát minh,**
> nhưng **chưa ai làm cho VN + gộp cả car comfort.**

## 11.5 Lộ trình 4 giai đoạn (self-first → community)

| GĐ | Việc | Kết quả | Thời gian |
|---|---|---|---|
| **1. Self** | OSM extract Hà Nội → graph → gán `car_score`/`bike_score` (dùng building OSM cho width) → CLI in tuyến + so sánh với Google | Tự dùng được, có số liệu | 1–2 tuần |
| **2. Demo** | 1 trang web: nhập A/B, chọn mode, vẽ tuyến + hiện điểm "comfort" từng đoạn | Có artifact để khoe | +1 tuần |
| **3. Đóng góp** | Export dataset `vn-road-comfort` (GeoJSON/Parquet) + profile `routing.xml`/`.brf` | Cộng đồng VN dùng | +2 tuần |
| **4. Mở rộng** | Thêm tile Microsoft/Google để phủ ngoài OSM; thêm surface qua Mapillary; thêm vùng ngập thủ công | Nếu #1 có cầu | tuỳ |

**Điều KHÔNG làm:** app mobile đầy đủ; segmentation ảnh vệ tinh toàn quốc; tự sinh dữ liệu ngập.

## 11.6 Trả lời trực tiếp 4 ý của bạn

1. **VN-only:** ✅ dễ hơn nhiều; `vietnam-latest.osm.pbf` (Geofabrik) hoặc bbox Hà Nội là đủ để bắt đầu.
2. **Ô tô-first, xe máy nice-to-have:** ✅ hợp lý — và việc "2 profile mục tiêu ngược nhau" là **điểm khác biệt đẹp** để kể.
3. **Ảnh vệ tinh + AI cho width?** ⚠️ **Không nên** cho width: free quá thô, nét quá đắt/bị ToS. Thay bằng **building footprints → corridor width** (tất định, free, chạy laptop). AI để dành cho **surface từ ảnh street-level (Mapillary)** nếu cần.
4. **OSS self-first:** ✅ đúng hướng. Bắt đầu bằng CLI chạy trên Hà Nội, có số liệu so với Google, rồi mới share.

## 11.7 Nguồn bổ sung

- Overture Maps transportation schema (`width_rules`, `road_surface`) — https://docs.overturemaps.org/schema/reference/transportation/segment/
- Overture query: DuckDB 1.5.5, release `2026-09-23.0`, `s3://overturemaps-us-west-2/.../theme=transportation/type=segment/*`, bbox `105.72,20.93,105.85,21.03`
- Google Open Buildings (1,8 tỷ building, ảnh 50 cm, **CC BY-4.0 / ODbL**, phủ Đông Nam Á) — https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_Research_open-buildings_v3_polygons
- Microsoft GlobalMLBuildingFootprints (**CDLA Permissive 2.0**, 226 region, VN có tile Hà Nội) — https://github.com/microsoft/GlobalMLBuildingFootprints
- Bike Level of Traffic Stress: SustainableMobility/bicycling-lts-classification (MIT), anerv/dk_bicycle_network (AGPL-3.0), dvrpc/low-stress-bike-routing (GPL-3.0)
- Mapillary/OSM road surface pipeline — https://github.com/erennere/Mapillary-OSM-Road-Surface-Pipeline

## 11.8 Giới hạn của bổ sung #2

- Số Overture là **1 bbox Hà Nội**, 1 release; nơi khác có thể khác (§11.1 chỉ khẳng định "ở VN kế thừa OSM").
- Chưa chạy thử **geometry building → width** trên dữ liệu thật; đánh giá độ chính xác vẫn là **giả thuyết** cho tới khi làm GĐ 1.
- Chưa đo **độ phủ building của OSM ngoài Hà Nội** (nông thôn có thể thưa) → cần kiểm khi mở rộng.
- Mapillary coverage ở VN **chưa kiểm chứng**.

---

# 12. Bổ sung #3 (24/09/2026) — Phase 1: webapp + bàn giao Google Maps + vòng kiểm chứng

Chốt phạm vi mới: **giai đoạn đầu chỉ cần webapp để dùng ngay**, **xuất ra lộ trình để import vào Google Maps**,
**sau đó có cơ chế kiểm chứng/xác nhận**.

## 12.1 Phạm vi Phase 1 (chốt)

| Hạng mục | Quyết định |
|---|---|
| Giao diện | **Webapp** (không phải CLI), dùng được trên điện thoại (PWA) |
| Vùng | **1 bbox Hà Nội** trước |
| Mode | **Ô tô-first**; xe máy/bike để sau |
| Đầu ra | Tuyến + điểm "dễ đi" từng đoạn + **nút mở Google Maps** + tải GPX |
| Vòng phản hồi | **Xác nhận sau chuyến** (self trước, multi-user sau) |

## 12.2 Xuất sang Google Maps — thực tế & giới hạn (phải biết trước khi thiết kế)

> **Google Maps KHÔNG nhận polyline/GPX để điều hướng turn-by-turn.** Đây là ràng buộc cứng.

Ba cách bàn giao:

| Cách | Turn-by-turn? | Đúng tuyến? | Giới hạn |
|---|:--:|:--:|---|
| **Deep link** `https://www.google.com/maps/dir/?api=1&origin=..&destination=..&travelmode=driving&waypoints=lat,lng\|lat,lng` | ✅ (trong Google Maps, có traffic thật) | ⚠️ gần đúng, tùy số waypoint | **mobile browser: tối đa 3 waypoint; app/desktop: tối đa 9**; URL ≤ **2.048 ký tự**; thêm được `avoid=highways,tolls,ferries` |
| **GPX/KML → My Maps** | ❌ chỉ xem | ✅ chính xác | My Maps import **KML/KMZ ≤ 5MB**, **GPX/CSV/XLSX ≤ 40MB**, **≤ 2.000 dòng** |
| **GPX → OsmAnd / Organic Maps** | ✅ | ✅ chính xác | phải dùng app khác (không phải Google) |

**Hệ quả thiết kế:** nút chính là **"Mở trong Google Maps"** (deep link waypoint). GPX/KML là đường phụ.
Vì Google chỉ cho 3–9 waypoint, tuyến dài sẽ chỉ **"ép" Google đi gần đúng hành lang** — phải nói rõ trong UI,
đừng để user hiểu nhầm là khớp từng mét.

## 12.3 Chọn waypoint để Google đi đúng hành lang (thuật toán)

1. Lấy polyline tuyến comfort.
2. **Douglas–Peucker** rút gọn → còn các đỉnh "góc"/điểm quyết định.
3. Ưu tiên **điểm phân kỳ** giữa tuyến comfort và tuyến nhanh nhất (chỗ comfort rẽ khác Google).
4. Nếu vượt giới hạn (3 mobile / 9 app): giữ các điểm có **độ lệch lớn nhất** so với đường thẳng nối các waypoint còn lại.
5. (Tuỳ chọn) cho user **kéo/sửa waypoint** trước khi mở.
6. Thêm `avoid=highways` nếu profile đang tránh đường lớn.

## 12.4 Cơ chế kiểm chứng / xác nhận — 2 lớp

### Lớp A — Trước khi đi: hiển thị độ tin cậy

Mỗi đoạn có badge **nguồn dữ liệu** (không giấu):

| Nguồn | Ý nghĩa | Tin cậy |
|---|---|---|
| `tag OSM` | có `surface`/`lanes` thật | Cao |
| `suy từ building` | corridor width tính từ footprints | Trung bình |
| `user đã xác nhận` | có người đi rồi xác nhận | Cao (theo độ mới) |
| `không rõ` | chỉ suy từ `highway` class | Thấp |

UI hiện **lý do**: *"tránh đoạn này vì `service/alley`, width ước lượng 4 m"* → để user tự đánh giá.

### Lớp B — Sau khi đi: feedback loop (xác nhận)

- Màn hình cuối chuyến: *"Chuyến vừa rồi thế nào?"* → **1 tap** Tốt / Có vấn đề.
- Nếu "có vấn đề": chạm vào **đoạn cụ thể** trên bản đồ + chọn nhãn:
  `vẫn bé` · `xấu/ổ gà` · `ngập` · `chặn/cấm` · `khác`.
- Ghi theo **OSM way id** (khớp lại được với dữ liệu gốc).

**Schema đề xuất (SQLite/Postgres):**

```sql
-- thô: người dùng báo gì
CREATE TABLE trip (id, user_id, mode, started_at, ended_at, planned_geojson, actual_geojson);
CREATE TABLE route_verdict (trip_id, verdict, note, created_at);            -- good | mixed | bad
CREATE TABLE segment_verdict (
  trip_id, osm_way_id, kind, note, created_at
);  -- kind: narrow | bad_surface | flood | blocked | ok

-- tổng hợp: trạng thái đường (để routing dùng lại)
CREATE TABLE road_status (
  osm_way_id, kind,          -- comfort | surface | flood | blocked
  value, n_confirm, confidence,
  first_seen_at, last_confirmed_at, ttl_seconds
);
```

**Hai loại TTL — rất quan trọng:**

| Loại | Ví dụ | TTL |
|---|---|---|
| **Tĩnh** | width/comfort, surface | 6–24 tháng |
| **Động** | ngập, chặn, cấm tạm | vài giờ – vài ngày |

(TTL là cách tránh đúng lỗi của Google: một báo ngập cũ không được ép tuyến mãi mãi.)

**Confidence** = f(số xác nhận, độ mới, uy tín người báo). Nhiều người → consensus;
chỉ đổi `road_status` khi vượt **ngưỡng tối thiểu**.

### Lớp C — Đóng góp ngược về OSM (giai đoạn sau)

Nếu user xác nhận `surface`/`width`, tạo **OSM note** hoặc changeset (tuỳ mức độ tự động).
Đây là phần biến tool cá nhân thành **đóng góp cộng đồng** mà không cần tự sinh dữ liệu.

## 12.5 Kiến trúc webapp Phase 1

```
[ MapLibre + form nhập A/B ]
        │ HTTP
        ▼
[ FastAPI ]
   ├─ POST /route        → chạy A* trên graph đã gán điểm → trả GeoJSON + điểm/đoạn + lý do
   ├─ GET  /export/gmaps → 302 sang deep link Google Maps (waypoint đã chọn)
   ├─ GET  /export/gpx   → file GPX (cho OsmAnd/My Maps)
   ├─ POST /confirm      → ghi route_verdict / segment_verdict
   └─ GET  /status       → gộp road_status để vẽ badge tin cậy

Precompute (offline, 1 lần):
   OSM Hà Nội  →  graph (highway)  +  building footprints  →  car_score mỗi edge
              →  lưu parquet/pickle (load nhanh khi server khởi động)
```

| Thành phần | Chọn | Lý do |
|---|---|---|
| Backend | **FastAPI + SQLite** | deploy 1 docker, đủ cho self-first |
| Routing v1 | **A\* tự viết** (rustworkx/igraph) trên `car_score` | không cần Valhalla/OSRM ở v1; kiểm soát hoàn toàn |
| Geocoding | Nominatim (self-host hoặc public) + **cho chọn trên bản đồ** | Nominatim VN đôi khi kém → không phụ thuộc text search |
| Bản đồ | MapLibre + raster OSM tiles (dev); PMTiles tự host khi share | nhanh, không khoá API |
| PWA | `manifest.json` để "Add to Home Screen" | dùng như app trên điện thoại |

## 12.6 MVP tối thiểu — làm gì / chưa làm

**Làm ngay:**
- Bbox Hà Nội; nhập A–B (chọn trên bản đồ); mode **Ô tô**.
- Trả tuyến + điểm dễ đi từng đoạn + **lý do**.
- Nút **Mở Google Maps** (waypoint) + **tải GPX**.
- **Xác nhận cuối chuyến** (route-level bắt buộc; segment-level nếu kịp).

**Chưa làm (để sau):** turn-by-turn riêng; tài khoản/multi-user; ngập realtime; app mobile; profile xe máy.

## 12.7 Rủi ro riêng của Phase 1

| Rủi ro | Mức | Cách xử lý |
|---|---|---|
| Google chỉ cho **3 waypoint trên mobile browser** → không ép đúng hành lang | **Cao** | UI nói rõ "gần đúng"; mở trong **app Google Maps** (9 waypoint) bằng nút riêng; GPX→OsmAnd nếu cần khớp |
| Geocoding VN kém | Trung bình | Chọn điểm trên bản đồ; cho dán toạ độ |
| Feedback cần người dùng thật | Trung bình | v1: mình tự dùng + tự xác nhận; đủ để validate |
| GPS trace khi web ở nền không ổn | Trung bình | v1 xác nhận **thủ công**, không auto-detect; auto GPS để sau |
| Bản đồ tiles/rate limit khi share | Thấp | self-host PMTiles hoặc dùng nhà cung cấp free tier |

## 12.8 Nguồn bổ sung #3

- Maps URLs — `waypoints` (mobile browser **≤3**, nền tảng khác **≤9**), `avoid=ferries,highways,tolls`, giới hạn **2.048 ký tự** — https://developers.google.com/maps/documentation/urls/get-started
- My Maps import — **CSV/KML/KMZ/GPX/XLSX**, KML/KMZ ≤5MB, file khác ≤40MB, ≤2.000 dòng — https://support.google.com/mymaps/answer/3024836
- Google Maps số điểm dừng (tối đa **9**, gồm cả đích) — https://support.google.com/maps/answer/144339

---

# 13. Bổ sung #4 (24/09/2026) — Thay client điều hướng + tính năng "khảo sát tuyến trước khi đi"

Hai yêu cầu mới: (a) **có thể thay Google Maps bằng client phù hợp hơn**, (b) thêm phương án **khảo sát tuyến trước khi đi thật**, nhất là đi nơi lạ/xa.

## 13.1 Client điều hướng — so sánh

| Client | Đi theo lộ trình tự chọn | Tránh ngõ nhỏ / unpaved | Cắm engine riêng | Offline | Traffic | OSS | Khảo sát (street view/elevation) |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| **Google Maps** | ❌ (chỉ waypoint, ≤3–9) | ❌ | ❌ | ⚠️ | ✅✅ | ❌ | ⚠️ Street View thủ công |
| Waze | ❌ | ❌ | ❌ | ❌ | ✅✅ | ❌ | ❌ |
| **OsmAnd** | ✅ **Navigate by track (GPX)** | ✅ toll/unpaved/tunnel/4WD/motorway/ford… | ✅ **GraphHopper / OSRM / ORS** | ✅ | ⚠️ yếu hơn | ✅ | ✅ **Mapillary + contour/elevation** |
| Organic Maps / CoMaps | ⚠️ import track (yếu hơn) | ⚠️ avoid unpaved | ❌ | ✅ | ❌ | ✅ | ❌ |
| Locus Map | ✅ | ⚠️ | ✅ (addon GraphHopper) | ✅ | ⚠️ | ⚠️ | ✅ |
| Magic Earth | ⚠️ | ⚠️ | ❌ | ✅ | ✅ (crowd) | ❌ | ❌ |
| TomTom AmiGO / HERE WeGo | ❌ | ⚠️ | ❌ | ✅ | ✅ | ❌ | ❌ |
| Kurviger / Calimoto | ✅ GPX | ✅ | ⚠️ | ✅ | ❌ | ❌ | ⚠️ |

**Kết luận: OsmAnd là client thay thế tốt nhất cho mục tiêu này.** Google Maps chỉ nên giữ cho ca "đường đơn giản, cần traffic".

## 13.2 OsmAnd làm được gì (dẫn chứng từ docs chính thức)

- **Route parameters cho Car** (Menu → Settings → App profiles → Navigation settings → Route parameters):
  Avoid roads (chọn trên bản đồ hoặc theo loại): `No toll roads`, **`No unpaved roads`**, `No border crossings`,
  `Avoid ice roads/fords`, `No ferries`, `No motorways`, `Avoid low emission zones`, `No shuttle train`,
  `Avoid tunnels`, **`Avoid 4WD roads`**; `Prefer unpaved over paved`; `Allow private access`;
  `Fuel-efficient way`; route calc method. Docs nói rõ mục tiêu là "avoid roads that are not suitable for cars, **such as narrow roads**".
- **Navigate by track (GPX)**: OsmAnd điều hướng turn-by-turn **theo đúng track của mình** — đây là cách
  ép client đi đúng tuyến comfort mà không phụ thuộc waypoint.
- **Custom Online Routing**: thêm engine online ngoài, chọn **GraphHopper / OSRM / OpenRouteService**.
  → **cắm được backend của mình vào OsmAnd** (nếu mình chạy GH/ORS với profile tùy biến).
- **BRouter** (Android): engine offline, profile tùy biến → có thể đóng gói profile VN.
- **Plugin Mapillary**: xem ảnh đường **"along the route you have planned"** — chính là recon, có sẵn.
- **Contour lines / elevation**: xem địa hình, độ cao dọc tuyến.
- Android Auto / CarPlay.
- **Nhược điểm:** traffic/incident yếu hơn Google/Waze; UI phức tạp; iOS thiếu online routing & BRouter.

## 13.3 Kiến trúc cập nhật — backend phục vụ CẢ webapp và OsmAnd

Điểm hay: **cùng một backend** có thể vừa là webapp, vừa là routing engine cho OsmAnd.

```
              ┌─────────────────────────────┐
[Webapp] ────▶│  FastAPI + graph car_score  │
              │  (A* hoặc bọc GH/ORS)       │◀──── [OsmAnd]
              └─────────────────────────────┘        "Add online routing engine"
                 │ export GPX                            (GraphHopper/ORS API)
                 ▼
              [OsmAnd: Navigate by track]  ← ép đúng tuyến, offline
              [Google Maps: waypoint link]  ← fallback khi cần traffic
```

- **Cách tích hợp chặt:** chạy **GraphHopper** (hoặc ORS) với custom model / encoded value `car_score`,
  rồi trỏ OsmAnd vào API đó → OsmAnd vừa điều hướng vừa dùng tiêu chí comfort.
- **Cách nhẹ:** webapp trả **GPX** → mở bằng OsmAnd → Navigate by track.
- **Google Maps waypoint link**: giữ làm lựa chọn "cần traffic".

## 13.4 Tính năng "Khảo sát tuyến" (Recon) — thiết kế

Mục tiêu: **xem trước tuyến như thể đã đi rồi**, trước khi thực sự đi — nhất là tuyến lạ/xa nhà.

"Hồ sơ tuyến" gồm 7 khối:

| # | Khối | Dữ liệu |
|---|---|---|
| 1 | Bản đồ + comfort từng đoạn + width/surface | graph `car_score` |
| 2 | **Biểu đồ độ cao** (elevation gain, đèo dốc) | Open-Meteo Elevation / OpenTopoData / SRTM |
| 3 | **Filmstrip ảnh đường** (bước qua từng km) | Mapillary API; trong OsmAnd = Mapillary plugin |
| 4 | **POI dọc tuyến**: cây xăng, quán, nghỉ, y tế, sửa xe | Overpass |
| 5 | **Điểm rủi ro**: ngập (cộng đồng), thi công (OSM), điểm đen (tuỳ) | OSM + community |
| 6 | **Tóm tắt**: km, ETA, độ cao, # đoạn ngõ, # đoạn unpaved, phí | tổng hợp |
| 7 | **Lưu/chia sẻ**: link hồ sơ + GPX + nút OsmAnd + nút Google Maps | export |

**Trong OsmAnd** có sẵn 1 phần: Mapillary plugin (street-level dọc tuyến) + contour/elevation.
**Trong webapp** làm đủ 7 khối → đây là giá trị "không đâu có" cho VN.

## 13.5 Đối thủ cho recon (để biết mình không phát minh lại)

| Tool | Có gì |
|---|---|
| **inRoute** | weather + elevation + curvy roads dọc tuyến (iOS) |
| **Kurviger / Calimoto / Furkot** | route planner moto, elevation, GPX |
| **Roadtrippers** | lên trip, stops, POI |
| **Google Earth + Street View** | xem thủ công, không gắn routing |
| **Mapillary web** | ảnh street-level |

→ Từng mảnh đã có, **nhưng chưa ai gộp "comfort dữ liệu VN + recon đầy đủ"**. Đó là chỗ đứng.

## 13.6 Cập nhật MVP (từ §12)

Thêm vào Phase 1:
- Tab **"Khảo sát"**: map + elevation + filmstrip ảnh + POI + rủi ro + tóm tắt.
- Nút **"Mở bằng OsmAnd"** (`.gpx` + deep link) bên cạnh **"Mở Google Maps"**.
- (Tuỳ chọn, giai đoạn sau) chạy GraphHopper với `car_score` để OsmAnd dùng online routing.

**Vẫn chưa làm:** turn-by-turn tự viết, multi-user, ngập realtime, app mobile.

## 13.7 Nguồn bổ sung #4

- OsmAnd Car routing (route parameters, tránh narrow/unpaved/4WD…) — https://osmand.net/docs/user/navigation/routing/car-based-routing
- OsmAnd Online routing (custom GraphHopper/OSRM/ORS) — https://osmand.net/docs/user/navigation/routing/online-routing
- OsmAnd BRouter (offline, profile tùy biến) — https://osmand.net/docs/user/navigation/routing/brouter
- OsmAnd Navigate by track (GPX) — https://osmand.net/docs/user/navigation/setup/gpx-navigation
- OsmAnd Mapillary plugin (street-level "along the route you have planned") — https://osmand.net/docs/user/plugins/mapillary
- Open-Meteo Elevation API (free, no key) — https://api.open-meteo.com/v1/elevation
- OpenTopoData (SRTM) — https://api.opentopodata.org/v1/srtm90m
- Mapillary Images API (cần token; **coverage VN chưa kiểm chứng**) — https://www.mapillary.com/developer/api-documentation

## 13.8 Giới hạn của bổ sung #4

- Tính năng OsmAnd lấy từ docs chính thức (**Android**); iOS thiếu online routing + BRouter.
- **Chưa xác minh coverage Mapillary/Street View ở VN** — cần test bằng API/ứng dụng thật.
- OsmAnd **traffic yếu hơn Google** — đây là trade-off thật, không phải giải được bằng code.
- "Custom online routing" của OsmAnd chỉ nhận **GraphHopper/OSRM/ORS** (Valhalla không có trong danh sách).

---

# 14. Test coverage street-level ở VN (24/09/2026)

Yêu cầu: kiểm tra thật xem Mapillary / Street View có phủ VN không.

## 14.1 Kết quả test

| Nguồn | Kết quả | Bằng chứng |
|---|---|---|
| **Google Street View** | ✅ **CÓ — coverage toàn quốc (từ 2025)** | Wikipedia + VirtualStreets 29/06/2025 |
| Mapillary | ⚠️ **chưa test được** — API đòi OAuth token | `Invalid OAuth 2.0 Access Token`; web app trả 400; vector tile 403 |
| KartaView / OpenStreetCam | ✅ **KHÔNG cần cred** cho endpoint public — nhưng coverage **thưa** | endpoint đúng `?lat&lng&radius`; đo: 8/19 điểm có ảnh |
| Google `cbk` metadata (không key) | ❌ endpoint đã chết | HTTP 404 |

→ **Tin tốt: Google Street View có ở VN, lại có cả ảnh hẻm — không cần phụ thuộc Mapillary.**

## 14.2 Google Street View ở VN — chi tiết (có nguồn)

- **VirtualStreets (29/06/2025):** Google "officially added **full coverage to Vietnam**" — nước thứ **7** ở Đông Nam Á có Street View.
  Công bố lần đầu ảnh chụp từ **2017**; có cả ảnh **trekker** tại điểm du lịch và **hẻm/ngõ** trong đô thị
  nơi xe không vào được. Google cũng mở văn phòng tại **TP.HCM** đầu 2025.
- **Danh sách cũ (2020):** TP.HCM, Hà Nội, một phần Hải Phòng / Hạ Long / Móng Cái / Yên Bái / Đà Nẵng / Sông Cầu, Huế + 8 thành phố khác.
- **Wikipedia "Google Street View in Asia"** xác nhận VN nằm trong danh sách quốc gia có Street View.

**Ý nghĩa cho tính năng "Khảo sát tuyến":** dùng được **Google Street View** làm filmstrip chính.
Đặc biệt tốt cho ca **ngõ nhỏ** (trekker đã chụp) — đúng thứ mình cần để khảo sát trước.

## 14.3 Vì sao Mapillary/KartaView chưa kiểm được ở đây

- Mapillary Graph API yêu cầu `access_token` riêng (OAuth) → không có token là không query được.
- Mapillary web app chặn bot (HTTP 400); vector tiles công khai trả 403.
- KartaView: endpoint public **không cần token**; mình từng báo sai do dùng tham số `distance` — đúng phải là **`radius`** (xem §14.8).
- Google Street View metadata không key trả `You must use an API key`.

→ Đây là **giới hạn môi trường** (thiếu credential), không phải Mapillary hết coverage.

## 14.4 Tự test trong 5 phút (script kèm theo)

File: **`research/tools/check_street_coverage.py`** (chỉ dùng stdlib Python).

```bash
cd research/tools

# Mapillary — token miễn phí: mapillary.com/dashboard/developers
export MAPILLARY_TOKEN='MLY|...'
python3 check_street_coverage.py --source mapillary \
    --bbox 105.72,20.93,105.85,21.03 --grid 6 --csv hanoi_mapillary.csv

# Google Street View — bật "Street View Static API"
export GOOGLE_MAPS_API_KEY='AIza...'
python3 check_street_coverage.py --source gsv \
    --points "21.0285,105.8542;21.0012,105.8410;20.9955,105.8700" --csv hanoi_gsv.csv

# Dọc một tuyến GPX
python3 check_street_coverage.py --source gsv --gpx route.gpx --step 1000
```

Script in ra **% điểm có ảnh**, kèm CSV để xem từng điểm.

## 14.5 Thiết kế recon cập nhật (từ §13.4)

| Khối | Nguồn chọn | Ghi chú |
|---|---|---|
| Filmstrip ảnh đường (chính) | **Google Street View** | ✅ có ở VN; dùng deep link **không cần key**: `https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=lat,lng` (zero cost), hoặc Static API nếu muốn ảnh nhúng |
| Filmstrip (phụ) | Mapillary | cần token; coverage chưa rõ |
| Độ cao | Open-Meteo Elevation / OpenTopoData | ✅ đã test chạy |
| POI | Overpass | ✅ |

## 14.6 Nguồn bổ sung #5

- Wikipedia, *Google Street View coverage* (wikitext; dòng `Vietnam*`, tham chiếu VirtualStreets 2025) — https://en.wikipedia.org/wiki/Google_Street_View_coverage
- Wikipedia, *Google Street View in Asia* (VN trong danh sách) — https://en.wikipedia.org/wiki/Google_Street_View_in_Asia
- VirtualStreets, *Google Street View returns to Vietnam* (29/06/2025) — https://virtualstreets.org/index.php/2025/06/29/google-street-view-returns-to-vietnam/
- Test trực tiếp (24/09/2026): Mapillary Graph 500/190, web app 400, vector tile 403; KartaView `Restricted access!`; Google cbk 404; GSV metadata `You must use an API key`.

## 14.7 Giới hạn của bổ sung #5

- Coverage Street View được xác nhận qua **nguồn thứ cấp** (Wikipedia + VirtualStreets), **chưa đo % từng tuyến** bằng API — cái đó script §14.4 sẽ cho số thật.
- Street View là ảnh **theo thời gian** (có thể cũ vài năm); hiện trạng ngập/thi công có thể khác.
- Google Street View Static API **tốn tiền theo request** (có free tier/$200 credit) → nếu share rộng cần tính.
- Mapillary coverage VN vẫn **chưa biết** cho tới khi có token.

## 14.8 Đính chính KartaView + hướng dẫn credential

**Đính chính:** KartaView **không cần credential** cho endpoint public. Lỗi lúc đầu là do dùng sai tên tham số:

```bash
# ✅ ĐÚNG — `radius` (mét)
curl "https://api.openstreetcam.org/2.0/photo/?lat=21.0285&lng=105.8542&radius=150"
# ❌ SAI — `distance` → trả rỗng
```

Theo [kartaview.org/doc](https://kartaview.org/doc): endpoint public = xem ảnh/sequence, coverage tiles, metadata,
query theo vị trí. Token (OAuth Google/Facebook/OSM) chỉ cần cho thao tác user / upload / **rate limit cao hơn**.

**Cập nhật script:** `tools/check_street_coverage.py` đã thêm `--source kartaview` (chạy được ngay, không cần gì):

```bash
cd research/tools
python3 check_street_coverage.py --source kartaview \
    --bbox 105.80,20.99,105.86,21.03 --grid 4 --radius 150
# → 9/16 điểm trung tâm HN có ảnh (0–6 ảnh/điểm) → thưa, chỉ dùng dự phòng
```

**Hướng dẫn lấy credential đầy đủ** (Mapillary client token, KartaView OAuth tùy chọn, Google API key):
→ **`research/STREET-LEVEL-API-SETUP.md`**.

**Kết luận nguồn ảnh:** Google Street View là nguồn chính (coverage tốt, có hẻm); KartaView là dự phòng miễn phí (thưa);
Mapillary cần token và chưa rõ coverage VN.
