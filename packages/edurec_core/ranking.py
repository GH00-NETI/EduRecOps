from __future__ import annotations

import hashlib
from statistics import fmean
from typing import Iterable

from .catalog import CATALOG
from .domain import Course, LearnerProfile, RankedCourse, RecommendationContext
from .eligibility import eligibility


class RecommendationPolicy:
    """Explainable policy that optimizes readiness and learning value, not clicks alone."""

    policy_id = "learning-value-v1"
    weights = {
        "affinity": 0.20,
        "readiness": 0.24,
        "learning_value": 0.22,
        "quality": 0.16,
        "novelty": 0.10,
        "popularity": 0.06,
        "exploration": 0.02,
    }

    @staticmethod
    def _stable_exploration(user_id: str, course_id: str, bucket: int) -> float:
        raw = f"{user_id}:{course_id}:{bucket}".encode()
        return int(hashlib.sha256(raw).hexdigest()[:8], 16) / 0xFFFFFFFF

    @staticmethod
    def _readiness(course: Course, learner: LearnerProfile) -> float:
        if not course.prerequisites:
            return 1.0
        ratios = [min(1.0, learner.mastery.get(c, 0.0) / threshold) for c, threshold in course.prerequisites]
        return fmean(ratios)

    @staticmethod
    def _learning_value(course: Course, learner: LearnerProfile) -> float:
        return fmean([1.0 - learner.mastery.get(c, 0.0) for c in course.concepts])

    def rank(
        self,
        learner: LearnerProfile,
        context: RecommendationContext,
        courses: Iterable[Course] = CATALOG,
        top_k: int = 5,
    ) -> list[RankedCourse]:
        rows: list[RankedCourse] = []
        recent = set(learner.recent_categories[-3:])
        for course in courses:
            allowed, _ = eligibility(course, learner)
            if not allowed:
                continue
            affinity = 1.0 if course.category in learner.interests else 0.25
            readiness = self._readiness(course, learner)
            learning_value = self._learning_value(course, learner)
            novelty = 1.0 if course.category not in recent else 0.25
            exploration = self._stable_exploration(learner.user_id, course.course_id, context.exploration_bucket)
            parts = {
                "affinity": affinity,
                "readiness": readiness,
                "learning_value": learning_value,
                "quality": course.quality_score,
                "novelty": novelty,
                "popularity": course.popularity_score,
                "exploration": exploration,
            }
            score = sum(self.weights[key] * value for key, value in parts.items())
            reasons = []
            if affinity == 1.0:
                reasons.append("phù hợp sở thích")
            if readiness >= 0.9:
                reasons.append("đủ kiến thức nền")
            if learning_value >= 0.6:
                reasons.append("có giá trị học tập cao")
            if novelty == 1.0:
                reasons.append("mở rộng chủ đề")
            source = "learning_path" if course.prerequisites else "discovery"
            rows.append(RankedCourse(course, score, source, parts, tuple(reasons[:3])))
        rows.sort(key=lambda item: (-item.score, item.course.course_id))
        return rows[: max(1, min(top_k, 50))]
