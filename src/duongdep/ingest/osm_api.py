"""Fallback: OSM API `/api/0.6/map` (XML) cho vùng nhỏ khi Overpass quá tải.

Giới hạn của OSM API: bbox ≤ 0.25 độ² và ~50k node. Phù hợp để test / vùng nhỏ,
KHÔNG dùng cho cả thành phố (dùng Overpass).
"""

from __future__ import annotations

import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from ..config import USER_AGENT

OSM_MAP_API = "https://api.openstreetmap.org/api/0.6/map"


def fetch_map_elements(bbox: tuple[float, float, float, float], timeout: int = 180) -> dict:
    """bbox = (south, west, north, east). Trả về dạng {'elements': [...]} giống Overpass."""
    s, w, n, e = bbox
    q = urllib.parse.urlencode({"bbox": f"{w},{s},{e},{n}"})
    req = urllib.request.Request(f"{OSM_MAP_API}?{q}", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        xml = r.read()
    return parse_osm_xml(xml)


def parse_osm_xml(xml_bytes: bytes) -> dict:
    root = ET.fromstring(xml_bytes)
    elements: list[dict] = []
    for el in root:
        if el.tag == "node":
            d = {
                "type": "node",
                "id": int(el.get("id")),
                "lat": float(el.get("lat")),
                "lon": float(el.get("lon")),
            }
            tags = {t.get("k"): t.get("v") for t in el.findall("tag")}
            if tags:
                d["tags"] = tags
            elements.append(d)
        elif el.tag == "way":
            d = {
                "type": "way",
                "id": int(el.get("id")),
                "nodes": [int(nd.get("ref")) for nd in el.findall("nd")],
            }
            tags = {t.get("k"): t.get("v") for t in el.findall("tag")}
            if tags:
                d["tags"] = tags
            elements.append(d)
    return {"elements": elements}


def split_elements(elements: list[dict]) -> tuple[dict, dict]:
    """Tách elements thành (đường, nhà), mỗi bên gồm way liên quan + tất cả node."""
    nodes = [el for el in elements if el.get("type") == "node"]
    roads = [el for el in elements if el.get("type") == "way" and el.get("tags", {}).get("highway")]
    buildings = [el for el in elements if el.get("type") == "way" and el.get("tags", {}).get("building")]
    return {"elements": nodes + roads}, {"elements": nodes + buildings}
