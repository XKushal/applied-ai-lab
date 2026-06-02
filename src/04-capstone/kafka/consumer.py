"""
Ingest worker. Consumes sensor events from Kafka and writes them to SQLite.

Run (standalone):
    KAFKA_BOOTSTRAP=localhost:9092 \\
    uv run python -m kafka.consumer

Or in docker-compose as the `ingest` service.

Production notes:
  • Auto-offset-reset = "earliest" so a fresh consumer reads the backlog.
    In real prod you'd use a consumer group + checkpointing.
  • One topic / one partition is fine for the demo. At scale you'd partition
    by sensor_id so all readings for one sensor land on the same consumer.
  • The consumer is fault-tolerant in shape (will reconnect on broker
    restart) but does NOT exactly-once. For real telemetry that's fine —
    duplicate sensor readings are idempotent at the storage layer (last
    write wins on the same (sensor_id, ts) key in a real time-series DB).
"""

from __future__ import annotations

import json
import os
import sys

from kafka import KafkaConsumer

from . import store

KAFKA_BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP", "localhost:9092")
TOPIC = os.environ.get("KAFKA_TOPIC", "bms.sensor.events")
GROUP = os.environ.get("KAFKA_GROUP", "ingest-worker")


def main() -> None:
    store.init_schema()
    print(f"[consumer] schema ready at {store.DB_PATH}", flush=True)
    print(f"[consumer] connecting to {KAFKA_BOOTSTRAP} (group={GROUP})", flush=True)
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        group_id=GROUP,
        auto_offset_reset="earliest",
        value_deserializer=lambda b: json.loads(b.decode()),
        enable_auto_commit=True,
        consumer_timeout_ms=0,  # block forever
    )
    print(f"[consumer] consuming topic {TOPIC}", flush=True)
    try:
        for msg in consumer:
            e = msg.value
            try:
                store.insert_reading(
                    sensor_id=e["sensor_id"],
                    ts=e["ts"],
                    reading_f=e["reading_f"],
                    baseline_f=e["baseline_f"],
                )
                print(f"  ✓ stored {e['sensor_id']} {e['reading_f']}F @ {e['ts']}", flush=True)
            except Exception as ex:  # noqa: BLE001
                print(f"  ✗ store error: {ex}; event={e}", flush=True)
    except KeyboardInterrupt:
        consumer.close()
        sys.exit(0)


if __name__ == "__main__":
    main()
