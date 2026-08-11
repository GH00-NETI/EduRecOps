from __future__ import annotations

import json
import os

import psycopg
import redis
from kafka import KafkaConsumer

bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:19092")
topic = os.getenv("EVENT_TOPIC", "learning-events")
rdb = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)
consumer = KafkaConsumer(
    topic,
    bootstrap_servers=bootstrap,
    group_id="edurec-feature-worker-v2",
    auto_offset_reset="earliest",
    enable_auto_commit=False,
    value_deserializer=lambda payload: json.loads(payload.decode()),
)
category_by_course = {
    "c-101": "programming", "c-102": "data", "c-103": "ai", "c-104": "devops",
    "c-105": "data", "c-106": "ai", "c-107": "data", "c-108": "programming",
    "c-109": "devops", "c-110": "ai", "c-111": "mlops", "c-112": "devops",
}
concept_by_course = {
    "c-101": "python", "c-102": "sql", "c-103": "ml", "c-104": "docker",
    "c-105": "data-modeling", "c-106": "mlops", "c-107": "streaming", "c-108": "api",
    "c-109": "linux", "c-110": "probability", "c-111": "feature-store", "c-112": "observability",
}

with psycopg.connect(os.getenv("DATABASE_URL")) as conn:
    for msg in consumer:
        event = msg.value
        event_id = event["event_id"]
        if not rdb.set(f"dedup:event:{event_id}", "1", nx=True, ex=7 * 24 * 3600):
            consumer.commit()
            continue
        with conn.transaction(), conn.cursor() as cur:
            cur.execute(
                """INSERT INTO learning_events
                (event_id,event_type,user_id,course_id,session_id,event_time,device,payload)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (event_id) DO NOTHING""",
                (event_id, event["event_type"], event["user_id"], event["course_id"],
                 event["session_id"], event["event_time"], event.get("device"), json.dumps(event)),
            )
        user, course, event_type = event["user_id"], event["course_id"], event["event_type"]
        category, concept = category_by_course.get(course), concept_by_course.get(course)
        pipe = rdb.pipeline(transaction=True)
        pipe.hincrby(f"user:{user}:counts", event_type, 1)
        pipe.zincrby("courses:trending", 1.0, course)
        if category:
            pipe.lpush(f"user:{user}:recent_categories", category)
            pipe.ltrim(f"user:{user}:recent_categories", 0, 19)
        if category and event_type in {"click", "enroll", "complete", "assessment"}:
            pipe.sadd(f"user:{user}:categories", category)
        if event_type == "complete":
            pipe.sadd(f"user:{user}:completed", course)
            if concept:
                pipe.hset(f"user:{user}:mastery", concept, 0.85)
        if event_type == "assessment" and concept and "score" in event:
            pipe.hset(f"user:{user}:mastery", concept, max(0.0, min(1.0, float(event["score"]))))
        pipe.execute()
        consumer.commit()
