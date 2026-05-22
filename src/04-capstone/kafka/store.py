"""
SQLite-backed "time-series-like" store for sensor readings.

In real production this would be Timescale, InfluxDB, Druid, or a cloud
warehouse. SQLite is fine for a demo of the pattern; the architectural
point — events on Kafka → durable store → tool queries store — is what
matters and translates 1:1 to a serious storage tier.

Schema is intentionally minimal:
    readings(sensor_id TEXT, ts TEXT, reading_f REAL, baseline_f REAL)

We index on (sensor_id, ts DESC) so "latest reading for sensor X" is fast.
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

# Default path: under data/ at the repo root so it persists between runs
# in dev. The docker-compose service mounts /data as a shared volume.
DEFAULT_DB = Path(__file__).parent.parent.parent.parent / "data" / "telemetry.sqlite"
DB_PATH = Path(os.environ.get("TELEMETRY_DB", str(DEFAULT_DB)))

SCHEMA = """
CREATE TABLE IF NOT EXISTS readings (
    sensor_id   TEXT NOT NULL,
    ts          TEXT NOT NULL,
    reading_f   REAL NOT NULL,
    baseline_f  REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_readings_sensor_ts
    ON readings(sensor_id, ts DESC);
"""


@contextmanager
def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    conn.execute("PRAGMA journal_mode=WAL;")  # safe concurrent reads + writes
    try:
        yield conn
    finally:
        conn.close()


def init_schema() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)
        conn.commit()


def insert_reading(sensor_id: str, ts: str, reading_f: float, baseline_f: float) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO readings (sensor_id, ts, reading_f, baseline_f) VALUES (?, ?, ?, ?)",
            (sensor_id, ts, reading_f, baseline_f),
        )
        conn.commit()


def latest_reading(sensor_id: str) -> dict | None:
    """Return the most recent reading for a sensor, or None if no rows."""
    with connect() as conn:
        row = conn.execute(
            "SELECT sensor_id, ts, reading_f, baseline_f "
            "FROM readings WHERE sensor_id = ? ORDER BY ts DESC LIMIT 1",
            (sensor_id,),
        ).fetchone()
    if row is None:
        return None
    sid, ts, reading_f, baseline_f = row
    return {
        "sensor_id": sid,
        "timestamp": ts,
        "reading_f": reading_f,
        "baseline_f": baseline_f,
    }
