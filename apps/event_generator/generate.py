from __future__ import annotations

import json
import os
import random
import time
import uuid
from datetime import datetime, timezone

from kafka import KafkaProducer

rng = random.Random(int(os.getenv("RANDOM_SEED", "42")))
producer = KafkaProducer(
    bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:19092"),
    value_serializer=lambda value: json.dumps(value).encode(),
    acks="all",
)
users = [f"u-{1000 + index}" for index in range(100)]
courses = [f"c-{101 + index}" for index in range(12)]
event_types = ["view"] * 54 + ["click"] * 22 + ["enroll"] * 10 + ["complete"] * 7 + ["rate"] * 3 + ["assessment"] * 4

for _ in range(int(os.getenv("EVENT_COUNT", "500"))):
    event_type = rng.choice(event_types)
    event = {
        "schema_version": "1.0",
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "user_id": rng.choice(users),
        "course_id": rng.choice(courses),
        "session_id": str(uuid.uuid4()),
        "event_time": datetime.now(timezone.utc).isoformat(),
        "device": rng.choice(["web", "ios", "android"]),
        "position": rng.randint(1, 20),
        "dwell_seconds": rng.randint(3, 600),
    }
    if event_type == "assessment":
        event["score"] = round(rng.betavariate(4, 2), 3)
    producer.send(os.getenv("EVENT_TOPIC", "learning-events"), event)
    time.sleep(float(os.getenv("EVENT_INTERVAL_SECONDS", "0.02")))
producer.flush()
print("generated learning events", flush=True)
