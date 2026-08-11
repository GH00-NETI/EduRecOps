import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "packages"))
from edurec_core import LearnerProfile, RecommendationContext, RecommendationPolicy


class RecommendationPolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = RecommendationPolicy()
        self.context = RecommendationContext(exploration_bucket=7)

    def test_completed_course_is_filtered(self):
        learner = LearnerProfile("u-1", completed_courses=frozenset({"c-101"}))
        ids = {item.course.course_id for item in self.policy.rank(learner, self.context, top_k=50)}
        self.assertNotIn("c-101", ids)

    def test_prerequisites_are_hard_constraints(self):
        learner = LearnerProfile("u-1", mastery={"ml": 0.2, "docker": 0.2})
        ids = {item.course.course_id for item in self.policy.rank(learner, self.context, top_k=50)}
        self.assertNotIn("c-106", ids)

    def test_course_becomes_eligible_after_mastery(self):
        learner = LearnerProfile("u-1", interests=frozenset({"ai"}), mastery={"ml": 0.8, "docker": 0.8})
        ids = {item.course.course_id for item in self.policy.rank(learner, self.context, top_k=50)}
        self.assertIn("c-106", ids)

    def test_policy_is_deterministic(self):
        learner = LearnerProfile("u-1", interests=frozenset({"data"}), mastery={"python": 0.8, "sql": 0.8})
        first = self.policy.rank(learner, self.context, top_k=8)
        second = self.policy.rank(learner, self.context, top_k=8)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
