from __future__ import annotations

from .domain import Course, LearnerProfile


def eligibility(course: Course, learner: LearnerProfile) -> tuple[bool, tuple[str, ...]]:
    """Apply hard academic constraints before any relevance score is considered."""
    failures: list[str] = []
    if course.course_id in learner.completed_courses:
        failures.append("already_completed")
    if course.language != learner.language:
        failures.append("language_mismatch")
    for concept, threshold in course.prerequisites:
        if learner.mastery.get(concept, 0.0) < threshold:
            failures.append(f"prerequisite:{concept}")
    return not failures, tuple(failures)
