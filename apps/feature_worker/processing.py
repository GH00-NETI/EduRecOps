from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Protocol

from edurec_core import CATALOG
from edurec_core.events import LearningEvent

DEDUP_TTL_SECONDS = 7 * 24 * 3600
INTEREST_EVENTS = frozenset({"click", "enroll", "complete", "assessment"})


class RedisLike(Protocol):
    def exists(self, key: str) -> int: ...
    def set(self, key: str, value: str, ex: int | None = None, nx: bool = False) -> bool: ...
    def pipeline(self, transaction: bool = True) -> Any: ...


class PgConnLike(Protocol):
    def transaction(self) -> Any: ...
    def cursor(self) -> Any: ...


def course_lookups() -> tuple[dict[str, str], dict[str, tuple[str, ...]]]:
    """Build course metadata from the shared catalog (single source of truth)."""
    categories = {course.course_id: course.category for course in CATALOG}
    concepts = {course.course_id: course.concepts for course in CATALOG}
    return categories, concepts


def validate_event_payload(raw: dict[str, Any]) -> dict[str, Any]:
    """Validate the Kafka payload against the learning-event contract."""
    event = LearningEvent(
        event_id=str(raw["event_id"]),
        event_type=str(raw["event_type"]),
        user_id=str(raw["user_id"]),
        course_id=str(raw["course_id"]),
        session_id=str(raw["session_id"]),
        event_time=str(raw["event_time"]),
        schema_version=str(raw.get("schema_version", "1.0")),
    )
    event.validate()
    payload = dict(raw)
    payload.update(
        {
            "event_id": event.event_id,
            "event_type": event.event_type,
            "user_id": event.user_id,
            "course_id": event.course_id,
            "session_id": event.session_id,
            "event_time": event.event_time,
            "schema_version": event.schema_version,
        }
    )
    return payload


def persist_event(conn: PgConnLike, event: dict[str, Any]) -> bool:
    """Insert the event. Returns True only when a new row was written."""
    with conn.transaction(), conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO learning_events
                (event_id, event_type, user_id, course_id, session_id, event_time, device, payload)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (event_id) DO NOTHING
            """,
            (
                event["event_id"],
                event["event_type"],
                event["user_id"],
                event["course_id"],
                event["session_id"],
                event["event_time"],
                event.get("device"),
                json.dumps(event),
            ),
        )
        return cur.rowcount == 1


def apply_online_features(
    rdb: RedisLike,
    event: dict[str, Any],
    categories: dict[str, str],
    concepts: dict[str, tuple[str, ...]],
    *,
    now: datetime | None = None,
) -> None:
    """Apply Redis feature updates for a newly accepted event."""
    user = event["user_id"]
    course = event["course_id"]
    event_type = event["event_type"]
    category = categories.get(course)
    course_concepts = concepts.get(course, ())
    updated_at = (now or datetime.now(timezone.utc)).isoformat()

    pipe = rdb.pipeline(transaction=True)
    pipe.hincrby(f"user:{user}:counts", event_type, 1)
    pipe.zincrby("courses:trending", 1.0, course)
    pipe.set(f"user:{user}:features_updated_at", updated_at)
    pipe.set(f"dedup:event:{event['event_id']}", "1", ex=DEDUP_TTL_SECONDS)

    if category:
        pipe.lpush(f"user:{user}:recent_categories", category)
        pipe.ltrim(f"user:{user}:recent_categories", 0, 19)
    if category and event_type in INTEREST_EVENTS:
        pipe.sadd(f"user:{user}:categories", category)
    if event_type == "complete":
        pipe.sadd(f"user:{user}:completed", course)
        for concept in course_concepts:
            pipe.hset(f"user:{user}:mastery", concept, 0.85)
    if event_type == "assessment" and "score" in event:
        score = max(0.0, min(1.0, float(event["score"])))
        for concept in course_concepts:
            pipe.hset(f"user:{user}:mastery", concept, score)
    pipe.execute()


def process_message(
    conn: PgConnLike,
    rdb: RedisLike,
    raw: dict[str, Any],
    categories: dict[str, str],
    concepts: dict[str, tuple[str, ...]],
) -> str:
    """
    Process one event.

    Returns:
      - "applied" when Postgres accepted a new event and Redis features were updated
      - "duplicate" when the event was already durable (safe no-op)
    """
    event = validate_event_payload(raw)
    event_id = event["event_id"]

    # Fast path: Redis marker only skips work when Postgres already owns the event.
    if rdb.exists(f"dedup:event:{event_id}"):
        return "duplicate"

    inserted = persist_event(conn, event)
    if not inserted:
        # Durable duplicate (e.g. after Redis loss). Refresh the marker only.
        rdb.set(f"dedup:event:{event_id}", "1", ex=DEDUP_TTL_SECONDS)
        return "duplicate"

    apply_online_features(rdb, event, categories, concepts)
    return "applied"
