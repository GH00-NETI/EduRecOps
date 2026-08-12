from __future__ import annotations

import json
import os
import random
import time
import uuid
from datetime import datetime, timezone

from kafka import KafkaProducer


def build_event(rng: random.Random, users: list[str], courses: list[str], event_types: list[str]) -> dict:
    event_type = rng.choice(event_types)
    user_id = rng.choice(users)
    event = {
        "schema_version": "1.0",
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "user_id": user_id,
        "course_id": rng.choice(courses),
        "session_id": str(uuid.uuid4()),
        "event_time": datetime.now(timezone.utc).isoformat(),
        "device": rng.choice(["web", "ios", "android"]),
        "position": rng.randint(1, 20),
        "dwell_seconds": rng.randint(3, 600),
    }
    if event_type == "assessment":
        event["score"] = round(rng.betavariate(4, 2), 3)
    return event


def main() -> None:
    rng = random.Random(int(os.getenv("RANDOM_SEED", "42")))
    topic = os.getenv("EVENT_TOPIC", "learning-events")
    producer = KafkaProducer(
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:19092"),
        value_serializer=lambda value: json.dumps(value).encode(),
        key_serializer=lambda value: value.encode() if value is not None else None,
        acks="all",
    )
    users = [f"u-{1000 + index}" for index in range(100)]
    courses = [f"c-{101 + index}" for index in range(12)]
    event_types = (
        ["view"] * 54
        + ["click"] * 22
        + ["enroll"] * 10
        + ["complete"] * 7
        + ["rate"] * 3
        + ["assessment"] * 4
    )

    count = int(os.getenv("EVENT_COUNT", "500"))
    interval = float(os.getenv("EVENT_INTERVAL_SECONDS", "0.02"))
    for _ in range(count):
        event = build_event(rng, users, courses, event_types)
        # Partition by user_id so per-learner ordering is preserved.
        producer.send(topic, key=event["user_id"], value=event)
        time.sleep(interval)
    producer.flush()
    print(f"generated {count} learning events", flush=True)


if __name__ == "__main__":
    main()
