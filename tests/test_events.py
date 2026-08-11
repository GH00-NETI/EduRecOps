import sys
import unittest
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "packages"))
from edurec_core.events import LearningEvent


class EventContractTests(unittest.TestCase):
    def make_event(self, event_type="view"):
        return LearningEvent(
            event_id=str(uuid.uuid4()), event_type=event_type, user_id="u-1", course_id="c-101",
            session_id=str(uuid.uuid4()), event_time=datetime.now(timezone.utc).isoformat(),
        )

    def test_valid_event(self):
        self.make_event().validate()

    def test_unknown_event_rejected(self):
        with self.assertRaises(ValueError):
            self.make_event("unknown").validate()


if __name__ == "__main__":
    unittest.main()
