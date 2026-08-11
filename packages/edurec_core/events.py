from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

ALLOWED_EVENTS = {"view", "click", "enroll", "complete", "rate", "assessment"}


@dataclass(frozen=True)
class LearningEvent:
    event_id: str
    event_type: str
    user_id: str
    course_id: str
    session_id: str
    event_time: str
    schema_version: str = "1.0"

    def validate(self) -> None:
        UUID(self.event_id)
        UUID(self.session_id)
        if self.event_type not in ALLOWED_EVENTS:
            raise ValueError(f"unsupported event_type: {self.event_type}")
        if not self.user_id or not self.course_id:
            raise ValueError("user_id and course_id are required")
        parsed = datetime.fromisoformat(self.event_time.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("event_time must include a timezone")
