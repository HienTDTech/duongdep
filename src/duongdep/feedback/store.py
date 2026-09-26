"""Lưu phản hồi/xác nhận của người dùng (SQLite).

Hai loại dữ liệu:
- Tĩnh  (comfort/surface): TTL dài 6–24 tháng
- Động  (flood/blocked)  : TTL vài giờ – vài ngày

TTL là điểm mấu chốt để không lặp lại lỗi của Google: báo ngập cũ không ép tuyến mãi.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS trip (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    mode TEXT,
    started_at TEXT,
    ended_at TEXT,
    planned_geojson TEXT,
    actual_geojson TEXT
);
CREATE TABLE IF NOT EXISTS route_verdict (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trip_id INTEGER,
    verdict TEXT,
    note TEXT,
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS segment_verdict (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trip_id INTEGER,
    osm_way_id INTEGER,
    kind TEXT,
    note TEXT,
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS road_status (
    osm_way_id INTEGER,
    kind TEXT,
    value TEXT,
    n_confirm INTEGER DEFAULT 0,
    confidence REAL DEFAULT 0,
    first_seen_at TEXT,
    last_confirmed_at TEXT,
    ttl_seconds INTEGER,
    PRIMARY KEY (osm_way_id, kind)
);
"""

# TTL theo loại
STATIC_KINDS = {"comfort", "surface"}
DYNAMIC_TTL = {"flood": 6 * 3600, "blocked": 48 * 3600, "construction": 7 * 24 * 3600}
STATIC_TTL_SECONDS = 180 * 24 * 3600


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ttl_for(kind: str) -> int:
    if kind in DYNAMIC_TTL:
        return DYNAMIC_TTL[kind]
    return STATIC_TTL_SECONDS


class FeedbackStore:
    def __init__(self, path: str | Path = "data/feedback.db"):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path))
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    # -------------------------------------------------------------- writes
    def create_trip(self, user_id: str = "self", mode: str = "car", planned_geojson: str | None = None) -> int:
        cur = self.conn.execute(
            "INSERT INTO trip(user_id, mode, started_at, planned_geojson) VALUES (?,?,?,?)",
            (user_id, mode, _now(), planned_geojson),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def add_route_verdict(self, trip_id: int, verdict: str, note: str = "") -> None:
        self.conn.execute(
            "INSERT INTO route_verdict(trip_id, verdict, note, created_at) VALUES (?,?,?,?)",
            (trip_id, verdict, note, _now()),
        )
        self.conn.commit()

    def add_segment_verdict(
        self, trip_id: int, osm_way_id: int, kind: str, note: str = "", value: str = "bad"
    ) -> None:
        now = _now()
        self.conn.execute(
            "INSERT INTO segment_verdict(trip_id, osm_way_id, kind, note, created_at) VALUES (?,?,?,?,?)",
            (trip_id, osm_way_id, kind, note, now),
        )
        row = self.conn.execute(
            "SELECT n_confirm FROM road_status WHERE osm_way_id=? AND kind=?",
            (osm_way_id, kind),
        ).fetchone()
        if row is None:
            self.conn.execute(
                "INSERT INTO road_status(osm_way_id, kind, value, n_confirm, confidence, first_seen_at,"
                " last_confirmed_at, ttl_seconds) VALUES (?,?,?,?,?,?,?,?)",
                (osm_way_id, kind, value, 1, 0.5, now, now, ttl_for(kind)),
            )
        else:
            self.conn.execute(
                "UPDATE road_status SET n_confirm=n_confirm+1, last_confirmed_at=?, ttl_seconds=?,"
                " confidence=MIN(1.0, 0.5 + 0.1*n_confirm) WHERE osm_way_id=? AND kind=?",
                (now, ttl_for(kind), osm_way_id, kind),
            )
        self.conn.commit()

    # -------------------------------------------------------------- reads
    def active_status(self, osm_way_id: int) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM road_status WHERE osm_way_id=?", (osm_way_id,)
        ).fetchall()
        out = []
        now = datetime.now(timezone.utc)
        for r in rows:
            last = datetime.fromisoformat(r["last_confirmed_at"])
            if now - last <= timedelta(seconds=r["ttl_seconds"] or STATIC_TTL_SECONDS):
                out.append(dict(r))
        return out

    def expire_old(self) -> int:
        """Xoá road_status đã hết TTL. Trả về số dòng đã xoá."""
        now = datetime.now(timezone.utc)
        rows = self.conn.execute("SELECT rowid, last_confirmed_at, ttl_seconds FROM road_status").fetchall()
        n = 0
        for r in rows:
            last = datetime.fromisoformat(r["last_confirmed_at"])
            if now - last > timedelta(seconds=r["ttl_seconds"] or STATIC_TTL_SECONDS):
                self.conn.execute("DELETE FROM road_status WHERE rowid=?", (r["rowid"],))
                n += 1
        self.conn.commit()
        return n


__all__ = ["FeedbackStore", "ttl_for", "STATIC_KINDS"]
