from __future__ import annotations

import sys
import unittest
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages"))
sys.path.insert(0, str(ROOT / "apps" / "feature_worker"))

from edurec_core import CATALOG  # noqa: E402
from processing import (  # noqa: E402
    apply_online_features,
    course_lookups,
    process_message,
    validate_event_payload,
)


class FakeRedis:
    def __init__(self) -> None:
        self.kv: dict[str, str] = {}
        self.hashes: dict[str, dict[str, str]] = {}
        self.lists: dict[str, list[str]] = {}
        self.sets: dict[str, set[str]] = {}
        self.zsets: dict[str, dict[str, float]] = {}

    def exists(self, key: str) -> int:
        return 1 if key in self.kv else 0

    def set(self, key: str, value: str, ex: int | None = None, nx: bool = False) -> bool:
        if nx and key in self.kv:
            return False
        self.kv[key] = value
        return True

    def get(self, key: str) -> str | None:
        return self.kv.get(key)

    def pipeline(self, transaction: bool = True) -> "FakePipe":
        return FakePipe(self)


class FakePipe:
    def __init__(self, rdb: FakeRedis) -> None:
        self.rdb = rdb
        self.ops: list[tuple] = []

    def hincrby(self, key: str, field: str, amount: int) -> "FakePipe":
        self.ops.append(("hincrby", key, field, amount))
        return self

    def zincrby(self, key: str, amount: float, member: str) -> "FakePipe":
        self.ops.append(("zincrby", key, amount, member))
        return self

    def set(self, key: str, value: str, ex: int | None = None) -> "FakePipe":
        self.ops.append(("set", key, value))
        return self

    def lpush(self, key: str, value: str) -> "FakePipe":
        self.ops.append(("lpush", key, value))
        return self

    def ltrim(self, key: str, start: int, end: int) -> "FakePipe":
        self.ops.append(("ltrim", key, start, end))
        return self

    def sadd(self, key: str, value: str) -> "FakePipe":
        self.ops.append(("sadd", key, value))
        return self

    def hset(self, key: str, field: str, value: Any) -> "FakePipe":
        self.ops.append(("hset", key, field, str(value)))
        return self

    def execute(self) -> None:
        for op in self.ops:
            kind = op[0]
            if kind == "hincrby":
                bucket = self.rdb.hashes.setdefault(op[1], {})
                bucket[op[2]] = str(int(bucket.get(op[2], "0")) + op[3])
            elif kind == "zincrby":
                bucket = self.rdb.zsets.setdefault(op[1], {})
                bucket[op[3]] = bucket.get(op[3], 0.0) + float(op[2])
            elif kind == "set":
                self.rdb.kv[op[1]] = op[2]
            elif kind == "lpush":
                self.rdb.lists.setdefault(op[1], []).insert(0, op[2])
            elif kind == "ltrim":
                values = self.rdb.lists.get(op[1], [])
                end = op[3] + 1 if op[3] >= 0 else None
                self.rdb.lists[op[1]] = values[op[2] : end]
            elif kind == "sadd":
                self.rdb.sets.setdefault(op[1], set()).add(op[2])
            elif kind == "hset":
                self.rdb.hashes.setdefault(op[1], {})[op[2]] = op[3]
        self.ops.clear()


class FakeCursor:
    def __init__(self, conn: "FakeConn") -> None:
        self.conn = conn
        self.rowcount = 0

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def execute(self, sql: str, params: tuple) -> None:
        event_id = params[0]
        if event_id in self.conn.events:
            self.rowcount = 0
            return
        self.conn.events.add(event_id)
        self.rowcount = 1


class FakeTransaction:
    def __enter__(self) -> "FakeTransaction":
        return self

    def __exit__(self, *args: object) -> None:
        return None


class FakeConn:
    def __init__(self) -> None:
        self.events: set[str] = set()

    def transaction(self) -> FakeTransaction:
        return FakeTransaction()

    def cursor(self) -> FakeCursor:
        return FakeCursor(self)


def sample_event(event_id: str | None = None, event_type: str = "view") -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "event_id": event_id or str(uuid.uuid4()),
        "event_type": event_type,
        "user_id": "u-1001",
        "course_id": "c-105",
        "session_id": str(uuid.uuid4()),
        "event_time": datetime.now(timezone.utc).isoformat(),
        "device": "web",
    }


class WorkerLogicTests(unittest.TestCase):
    def test_course_lookups_match_catalog(self):
        categories, concepts = course_lookups()
        self.assertEqual(len(categories), len(CATALOG))
        for course in CATALOG:
            self.assertEqual(categories[course.course_id], course.category)
            self.assertEqual(concepts[course.course_id], course.concepts)

    def test_validate_event_rejects_unknown_type(self):
        event = sample_event(event_type="unknown")
        with self.assertRaises(ValueError):
            validate_event_payload(event)

    def test_duplicate_event_does_not_double_count(self):
        conn = FakeConn()
        rdb = FakeRedis()
        categories, concepts = course_lookups()
        event = sample_event(event_type="click")

        first = process_message(conn, rdb, event, categories, concepts)
        second = process_message(conn, rdb, event, categories, concepts)

        self.assertEqual(first, "applied")
        self.assertEqual(second, "duplicate")
        self.assertEqual(rdb.hashes["user:u-1001:counts"]["click"], "1")
        self.assertEqual(rdb.zsets["courses:trending"]["c-105"], 1.0)

    def test_postgres_duplicate_without_redis_marker_is_safe(self):
        conn = FakeConn()
        rdb = FakeRedis()
        categories, concepts = course_lookups()
        event = sample_event(event_type="view")

        self.assertEqual(process_message(conn, rdb, event, categories, concepts), "applied")
        # Simulate Redis loss while Postgres still has the durable row.
        rdb.kv.clear()
        rdb.hashes.clear()
        rdb.zsets.clear()

        self.assertEqual(process_message(conn, rdb, event, categories, concepts), "duplicate")
        self.assertEqual(rdb.hashes, {})
        self.assertIn(f"dedup:event:{event['event_id']}", rdb.kv)

    def test_complete_updates_all_course_concepts(self):
        rdb = FakeRedis()
        categories, concepts = course_lookups()
        event = sample_event(event_type="complete")
        apply_online_features(rdb, event, categories, concepts)
        mastery = rdb.hashes["user:u-1001:mastery"]
        self.assertEqual(mastery["data-modeling"], "0.85")
        self.assertEqual(mastery["distributed-systems"], "0.85")
        self.assertIn("c-105", rdb.sets["user:u-1001:completed"])


if __name__ == "__main__":
    unittest.main()
