from __future__ import annotations

import json
import logging
import os
import sys
from typing import Any

import psycopg
import redis
from kafka import KafkaConsumer

from processing import course_lookups, process_message

logger = logging.getLogger("edurec.feature_worker")


def create_consumer() -> KafkaConsumer:
    bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:19092")
    topic = os.getenv("EVENT_TOPIC", "learning-events")
    return KafkaConsumer(
        topic,
        bootstrap_servers=bootstrap,
        group_id=os.getenv("FEATURE_WORKER_GROUP_ID", "edurec-feature-worker-v3"),
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        value_deserializer=lambda payload: json.loads(payload.decode()),
    )


def main() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is required")

    categories, concepts = course_lookups()
    rdb = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)
    consumer = create_consumer()

    with psycopg.connect(database_url) as conn:
        logger.info("feature worker started group=%s", consumer.config.get("group_id"))
        for msg in consumer:
            try:
                raw: Any = msg.value
                if not isinstance(raw, dict):
                    raise ValueError("event payload must be a JSON object")
                result = process_message(conn, rdb, raw, categories, concepts)
                consumer.commit()
                logger.debug("offset committed status=%s event_id=%s", result, raw.get("event_id"))
            except (KeyError, TypeError, ValueError) as exc:
                # Poison / invalid payload: commit to avoid infinite redelivery in the demo worker.
                logger.exception("skipping invalid event: %s", exc)
                consumer.commit()
            except Exception:
                logger.exception("transient failure; will retry message without committing")
                raise


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
