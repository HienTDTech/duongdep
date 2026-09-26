# Hướng dẫn lấy credential cho ảnh street-level (Mapillary / KartaView / Google Street View)

Ngày: 24/09/2026. Kèm `ROUTING-COMFORT-RESEARCH.md` (§13–§14) và `tools/check_street_coverage.py`.

---

## 0. Chốt nhanh — cái nào cần gì

| Nguồn | Cần credential? | Loại | Coverage VN (đo/ghi nhận) |
|---|---|---|---|
| **KartaView** (OpenStreetCam) | ❌ **Không** cho endpoint public | — | **Thưa** (9/16 điểm trung tâm HN có ảnh, mỗi điểm 0–6 ảnh) |
| **Mapillary** | ✅ Có | **Client token** (free, read-only) | Chưa đo (cần token) |
| **Google Street View** | ✅ Có | **API key** (billing, có free tier) | **Tốt nhất** — full coverage từ 2025, có cả ảnh hẻm |

> Thứ tự khuyến nghị để làm recon: **Google Street View** (chất lượng) → **KartaView** (miễn phí, dự phòng) → **Mapillary** (nếu đã có token).

---

## 1. KartaView — KHÔNG cần credential

Đây là phát hiện của lần test: KartaView có **endpoint public** không cần token. Lỗi trước đó là do dùng sai tên tham số.

### 1.1 Endpoint đúng

```bash
# ✅ ĐÚNG — tham số là `radius` (mét)
curl "https://api.openstreetcam.org/2.0/photo/?lat=21.0285&lng=105.8542&radius=150"

# ❌ SAI — `distance` trả về rỗng
curl "https://api.openstreetcam.org/2.0/photo/?lat=21.0285&lng=105.8542&distance=150"
```

Kết quả trả về `result.data[]` là danh sách ảnh gần đó.

### 1.2 Khi nào cần token

Theo [kartaview.org/doc](https://kartaview.org/doc):
- **Public (không cần token):** xem ảnh/sequence, coverage tiles, metadata, query theo vị trí.
- **Cần token:** thông tin user, upload, dữ liệu riêng tư, **và để có rate limit cao hơn**.

### 1.3 Nếu muốn token (tùy chọn)

- Auth qua **Google / Facebook / OpenStreetMap OAuth**.
- Token dùng dạng query param: `?access_token=YOUR_ACCESS_TOKEN` (theo doc hiện tại).
- API cũ (OpenStreetCam) dùng `request_token` + `secret_token` sau OAuth trên OSM, truyền qua header `X-Auth-Token` (dùng trong các client cũ như JOSM plugin / Trek View).
- Endpoint mẫu có token: `GET https://api.openstreetcam.org/2.0/user/profile?access_token=...`
- API reference: https://api.openstreetcam.org/api/doc.html

### 1.4 Coverage VN đo thật (24/09/2026, radius = 150 m)

| Địa điểm | Số ảnh | Địa điểm | Số ảnh |
|---|---:|---|---:|
| HN Hoàn Kiếm | 3 | Đà Nẵng | 0 |
| HN Thanh Xuân | 1 | Huế | 0 |
| HN Hà Đông | 7 | Hạ Long | 0 |
| HN Long Biên | 0 | Sa Pa | 0 |
| HN ngõ nhỏ (Tây Sơn) | 0 | Hà Giang | 0 |
| HCM Quận 1 | 5 | Đà Lạt | 1 |
| HCM Quận 7 | 3 | Nha Trang | 1 |
| HCM Thủ Đức | 0 | QL1A Bắc Ninh | 0 |
| Vinh | 2 | Đèo Mã Pí Lèng | 0 |

→ **8/19 điểm có ảnh**, nhưng mỗi điểm rất ít. **Không đủ làm nguồn chính**, chỉ dùng tham khảo/dự phòng.
Test theo lưới trung tâm HN: **9/16 điểm (56%)** có ảnh, 0–6 ảnh/điểm.

---

## 2. Mapillary — Client Token (miễn phí)

### 2.1 Các bước

1. **Tạo tài khoản / đăng nhập:** https://www.mapillary.com
2. **Vào Developer Dashboard:** https://www.mapillary.com/dashboard/developers
3. Bấm **"Register application"** (Đăng ký ứng dụng).
4. Điền:
   - **Application name**: ví dụ `route-comfort-research`
   - **Description**: ngắn gọn
   - **Redirect URI**: có thể để `http://localhost` (chỉ cần khi làm OAuth flow đầy đủ)
5. Sau khi tạo, màn hình app hiện **Client ID** và **Client Token** → bấm **"View"** ở mục **Client Token**.
6. Copy token. Nó có dạng **`MLY|xxxxxxxx|yyyyyyyy`**.

> Trích tài liệu/forum Mapillary: *"You can get your access token by registering an application in the developer dashboard and then click 'View' under 'Client Token'."*
> MapillaryJS: *"Create a Mapillary account → Sign in → Register an application in the developer dashboard → Get the client access token."*

### 2.2 Cách dùng token

Theo [API docs Mapillary](https://www.mapillary.com/developer/api-documentation#authentication):

```bash
# Query param — dùng cho vector tiles
curl "https://graph.mapillary.com/images?access_token=MLY|xxx|yyy&fields=id&bbox=105.84,21.02,105.86,21.04"

# Header — dùng cho Entity API (khuyến nghị hơn cho entity)
curl "https://graph.mapillary.com/images?fields=id&bbox=..." \
     -H "Authorization: OAuth MLY|xxx|yyy"
```

### 2.3 Lưu ý

- **Client token = read-only public data.** Muốn upload ảnh phải dùng **user access token** qua OAuth (`mapillary_tools authenticate`).
- Token vẫn là **secret của application** — đừng commit lên git.
- Có **rate limit**; bị chặn sẽ trả `"Application request limit reached"`.

### 2.4 Gắn vào script

```bash
export MAPILLARY_TOKEN='MLY|xxxxxxxx|yyyyyyyy'
python3 tools/check_street_coverage.py --source mapillary \
    --bbox 105.72,20.93,105.85,21.03 --grid 6 --csv hanoi_mapillary.csv
```

---

## 3. Google Street View — API key

### 3.1 Các bước

1. Vào **Google Cloud Console**: https://console.cloud.google.com
2. **Tạo project** (hoặc chọn project có sẵn).
3. **Bật billing** cho project (Google Maps Platform bắt buộc có billing; có free tier/credit hàng tháng — kiểm tra giá hiện hành).
4. **APIs & Services → Library** → tìm **"Street View Static API"** → **Enable**.
5. **APIs & Services → Credentials → Create credentials → API key.**
6. **Hạn chế key** (rất nên làm):
   - *Application restrictions*: HTTP referrer (nếu web) hoặc IP (nếu server).
   - *API restrictions*: chỉ cho **Street View Static API**.
7. Copy key dạng `AIza...`.

### 3.2 Cách dùng

```bash
# Kiểm tra CÓ panorama hay không (metadata — rẻ hơn)
curl "https://maps.googleapis.com/maps/api/streetview/metadata?location=21.0285,105.8542&key=AIza..."

# Lấy ảnh
curl "https://maps.googleapis.com/maps/api/streetview?size=600x400&location=21.0285,105.8542&key=AIza..."
```

### 3.3 Không cần key — deep link mở panorama

Dùng cho filmstrip "khảo sát tuyến" mà **không tốn phí API**:

```
https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=LAT,LNG
```

### 3.4 Gắn vào script

```bash
export GOOGLE_MAPS_API_KEY='AIza...'
python3 tools/check_street_coverage.py --source gsv \
    --points "21.0285,105.8542;21.0012,105.8410;20.9955,105.8700" --csv hanoi_gsv.csv
```

---

## 4. Bảng tổng hợp cách chạy script

```bash
cd research/tools

# KartaView — chạy được ngay, không cần gì
python3 check_street_coverage.py --source kartaview --bbox 105.72,20.93,105.85,21.03 --grid 6

# Mapillary — cần token
export MAPILLARY_TOKEN='MLY|...'
python3 check_street_coverage.py --source mapillary --gpx route.gpx --step 500

# Google Street View — cần API key
export GOOGLE_MAPS_API_KEY='AIza...'
python3 check_street_coverage.py --source gsv --gpx route.gpx --step 500
```

---

## 5. Bảo mật credential

- **Không commit** token/key. Dùng file `.env` (đã có trong `.gitignore`) hoặc biến môi trường.
- Google: **luôn hạn chế key** theo API + referrer/IP.
- Mapillary: coi client token như secret; nếu lộ → xoá/đổi trong dashboard.
- Nếu key từng bị dán vào chat/log → **rotate** (tạo key mới, xoá key cũ).

---

## 6. Nguồn

- Mapillary — API docs, Authentication (client token từ dashboard/developers) — https://www.mapillary.com/developer/api-documentation
- Mapillary — Developer Dashboard — https://www.mapillary.com/dashboard/developers
- Mapillary Community Forum — "How can I get Access Token" (register app → View Client Token) — https://forum.mapillary.com/t/how-can-i-get-access-token/7167
- MapillaryJS — Getting started / client access token — https://mapillary.github.io/mapillary-js/docs/intro/try/
- KartaView — API doc & authentication — https://kartaview.org/doc
- OpenStreetCam — API reference (request_token/secret_token qua OAuth OSM) — https://api.openstreetcam.org/api/doc.html
- Trek View — Quick Start KartaView API (header `X-Auth-Token`) — https://www.trekview.org/blog/playing-with-kartaview-api/
- Google — Street View Static API — https://developers.google.com/maps/documentation/streetview
- Google — Street View metadata — https://developers.google.com/maps/documentation/streetview/metadata
- Google — Maps URLs (deep link pano) — https://developers.google.com/maps/documentation/urls/get-started
