"""
Synthetic sensor event producer. Writes one event per sensor per cycle
to the `bms.sensor.events` Kafka topic.

Run (standalone):
    KAFKA_BOOTSTRAP=localhost:9092 \\
    uv run python -m kafka.producer

Or in docker-compose as the `producer` service.

Event schema:
    {
        "sensor_id": "S-12",
        "ts": "2026-05-22T14:03:11Z",
        "reading_f": 71.3,
        "baseline_f": 70.0
    }
"""

from __future__ import annotations

import datetime as dt
import json
import os
import random
import sys
import time

from kafka import KafkaProducer

KAFKA_BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP", "localhost:9092")
TOPIC = os.environ.get("KAFKA_TOPIC", "bms.sensor.events")
SENSORS = ["S-12", "S-47", "S-99", "AHU-3-supply", "AHU-3-return"]
INTERVAL_SECONDS = float(os.environ.get("PRODUCE_INTERVAL_SECONDS", "5"))


def make_event(sensor_id: str) -> dict:
    # baseline 70°F, normal jitter ±3°F. S-47 deliberately runs hot (~88°F)
    # so the demo has a believable "alarming" sensor.
    if sensor_id == "S-47":
        reading = 88.0 + random.uniform(-2, 3)
    else:
        reading = 70.0 + random.uniform(-3, 3)
    return {
        "sensor_id": sensor_id,
        "ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "reading_f": round(reading, 2),
        "baseline_f": 70.0,
    }


def main() -> None:
    print(f"[producer] connecting to {KAFKA_BOOTSTRAP}", flush=True)
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode(),
        retries=10,
        retry_backoff_ms=1000,
    )
    print(f"[producer] producing to topic {TOPIC} every {INTERVAL_SECONDS}s", flush=True)
    try:
        while True:
            for sid in SENSORS:
                event = make_event(sid)
                producer.send(TOPIC, value=event)
                print(f"  → {event}", flush=True)
            producer.flush()
            time.sleep(INTERVAL_SECONDS)
    except KeyboardInterrupt:
        producer.close()
        sys.exit(0)


if __name__ == "__main__":
    main()
