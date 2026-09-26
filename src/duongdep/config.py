"""Cấu hình điểm số (score) cho từng loại đường.

Điểm càng cao = càng "dễ đi" = càng được ưu tiên.
Đây là chỗ để tinh chỉnh cảm giác lái; mọi thứ khác chỉ là hạ tầng.
"""

from __future__ import annotations

import os

OVERPASS_URL = os.environ.get(
    "DUONGDEP_OVERPASS_URL", "https://overpass.private.coffee/api/interpreter"
)
USER_AGENT = "duongdep/0.0.1 (OSS; comfortable routing VN)"

# Bbox mặc định: Hà Đông / Thanh Xuân (nam = south, west, north, east)
HANOI_BBOX = (20.93, 105.72, 21.03, 105.85)

# Điểm nền theo `highway` — ô tô. 0 = không cho đi.
CAR_HIGHWAY_WEIGHT: dict[str, float] = {
    "motorway": 1.30,
    "motorway_link": 1.10,
    "trunk": 1.20,
    "trunk_link": 1.05,
    "primary": 1.10,
    "primary_link": 1.00,
    "secondary": 1.00,
    "secondary_link": 0.95,
    "tertiary": 0.90,
    "tertiary_link": 0.85,
    "unclassified": 0.60,
    "residential": 0.55,
    "living_street": 0.35,
    "service": 0.18,
    "track": 0.10,
    "road": 0.50,
    # loại trừ rõ ràng cho ô tô
    "footway": 0.0,
    "path": 0.0,
    "steps": 0.0,
    "cycleway": 0.0,
    "pedestrian": 0.0,
    "bridleway": 0.0,
    "corridor": 0.0,
    "elevator": 0.0,
    "construction": 0.0,
    "proposed": 0.0,
}

# Xe máy / xe đạp: thích đường nhỏ, tránh đường lớn nhiều xe to.
BIKE_HIGHWAY_WEIGHT: dict[str, float] = {
    "motorway": 0.0,
    "motorway_link": 0.0,
    "trunk": 0.20,
    "trunk_link": 0.25,
    "primary": 0.35,
    "primary_link": 0.40,
    "secondary": 0.55,
    "secondary_link": 0.60,
    "tertiary": 0.80,
    "tertiary_link": 0.80,
    "unclassified": 0.90,
    "residential": 1.00,
    "living_street": 1.00,
    "service": 0.90,
    "track": 0.80,
    "path": 0.95,
    "cycleway": 1.00,
    "footway": 0.70,
    "pedestrian": 0.70,
}

# Hệ số theo `surface` (nhân vào điểm).
SURFACE_MULT: dict[str, float] = {
    "asphalt": 1.00,
    "concrete": 1.00,
    "concrete:plates": 0.95,
    "paving_stones": 0.95,
    "chipseal": 0.95,
    "paved": 1.00,
    "cobblestone": 0.65,
    "sett": 0.65,
    "compacted": 0.60,
    "fine_gravel": 0.55,
    "gravel": 0.55,
    "pebblestone": 0.55,
    "ground": 0.50,
    "dirt": 0.50,
    "earth": 0.50,
    "mud": 0.35,
    "sand": 0.35,
    "grass": 0.45,
    "unpaved": 0.50,
}
UNKNOWN_SURFACE_MULT = 0.80

# Điểm tối đa (dùng cho heuristic A* — phải admissible).
MAX_SCORE = 1.5

# width proxy từ building footprints: rộng hơn thì cộng điểm, hẹp thì trừ.
# Lưu ý: đây là tín hiệu chính để PHÁT HIỆN NGÕ NHỎ, không phải đo chiều rộng thật.
WIDTH_REF_M = 6.0       # coi ~6 m là "đủ rộng"
WIDTH_MIN_MULT = 0.50   # ngõ rất hẹp
WIDTH_MAX_MULT = 1.15   # đường rộng (không thưởng quá nhiều)
