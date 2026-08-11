from __future__ import annotations

import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any

import redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, make_asgi_app

from edurec_core import LearnerProfile, RecommendationContext, RecommendationPolicy

app = FastAPI(title="EduRecOps Recommendation API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:8080").split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.mount("/metrics", make_asgi_app())
rdb = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)
policy = RecommendationPolicy()
REQUESTS = Counter("edurec_recommendation_requests_total", "Recommendation requests", ["status", "policy"])
LATENCY = Histogram("edurec_recommendation_latency_seconds", "Recommendation latency")
FALLBACKS = Counter("edurec_feature_fallback_total", "Feature store fallbacks")


class RecommendationRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)
    top_k: int = Field(default=5, ge=1, le=50)
    context: dict[str, Any] = Field(default_factory=dict)


def load_profile(user_id: str) -> tuple[LearnerProfile, str]:
    try:
        profile = LearnerProfile(
            user_id=user_id,
            interests=frozenset(rdb.smembers(f"user:{user_id}:categories")),
            completed_courses=frozenset(rdb.smembers(f"user:{user_id}:completed")),
            mastery={key: float(value) for key, value in rdb.hgetall(f"user:{user_id}:mastery").items()},
            recent_categories=tuple(rdb.lrange(f"user:{user_id}:recent_categories", 0, 9)),
        )
        return profile, "redis"
    except redis.RedisError:
        FALLBACKS.inc()
        return LearnerProfile(user_id=user_id, interests=frozenset({"ai", "data"})), "fallback"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "recommendation-api", "version": "0.2.0"}


@app.get("/ready")
def ready() -> dict[str, Any]:
    try:
        connected = bool(rdb.ping())
    except redis.RedisError:
        connected = False
    return {"ready": connected, "redis": connected}


@app.post("/v1/recommendations")
def recommend(req: RecommendationRequest) -> dict[str, Any]:
    started = time.perf_counter()
    request_id = str(uuid.uuid4())
    try:
        learner, feature_source = load_profile(req.user_id)
        context = RecommendationContext(
            device=str(req.context.get("device", "web")),
            hour=int(req.context.get("hour", 12)),
            exploration_bucket=int(req.context.get("exploration_bucket", 0)),
        )
        ranked = policy.rank(learner, context, top_k=req.top_k)
        REQUESTS.labels("ok", policy.policy_id).inc()
        now = datetime.now(timezone.utc).isoformat()
        return {
            "request_id": request_id,
            "user_id": req.user_id,
            "policy_id": policy.policy_id,
            "model_version": os.getenv("MODEL_VERSION", "explainable-baseline-v2"),
            "feature_source": feature_source,
            "feature_generated_at": now,
            "served_at": now,
            "recommendations": [
                {
                    "course_id": item.course.course_id,
                    "title": item.course.title,
                    "category": item.course.category,
                    "score": round(item.score, 4),
                    "candidate_source": item.candidate_source,
                    "reasons": list(item.reasons),
                    "score_breakdown": {key: round(value, 4) for key, value in item.score_breakdown.items()},
                }
                for item in ranked
            ],
        }
    except Exception:
        REQUESTS.labels("error", policy.policy_id).inc()
        raise
    finally:
        LATENCY.observe(time.perf_counter() - started)
