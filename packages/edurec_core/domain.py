from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Course:
    course_id: str
    title: str
    category: str
    difficulty: int
    concepts: tuple[str, ...]
    prerequisites: tuple[tuple[str, float], ...] = ()
    quality_score: float = 0.75
    popularity_score: float = 0.50
    language: str = "vi"


@dataclass(frozen=True)
class LearnerProfile:
    user_id: str
    interests: frozenset[str] = frozenset()
    completed_courses: frozenset[str] = frozenset()
    mastery: dict[str, float] = field(default_factory=dict)
    recent_categories: tuple[str, ...] = ()
    language: str = "vi"


@dataclass(frozen=True)
class RecommendationContext:
    device: str = "web"
    hour: int = 12
    exploration_bucket: int = 0


@dataclass(frozen=True)
class RankedCourse:
    course: Course
    score: float
    candidate_source: str
    score_breakdown: dict[str, float]
    reasons: tuple[str, ...]
