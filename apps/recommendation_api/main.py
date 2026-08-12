from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any

import psycopg
import redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, make_asgi_app

from edurec_core import LearnerProfile, RecommendationContext, RecommendationPolicy

APP_VERSION = "0.2.0"
DEFAULT_MODEL_VERSION = "baseline-v1"

app = FastAPI(title="EduRecOps Recommendation API", version=APP_VERSION)
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
IMPRESSION_FAILURES = Counter("edurec_impression_log_failures_total", "Impression log failures")


class RecommendationRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)
    top_k: int = Field(default=5, ge=1, le=50)
    context: dict[str, Any] = Field(default_factory=dict)


def model_version() -> str:
    return os.getenv("MODEL_VERSION", DEFAULT_MODEL_VERSION)


def load_profile(user_id: str) -> tuple[LearnerProfile, str, str | None]:
    """Return learner profile, feature source, and feature timestamp when available."""
    try:
        profile = LearnerProfile(
            user_id=user_id,
            interests=frozenset(rdb.smembers(f"user:{user_id}:categories")),
            completed_courses=frozenset(rdb.smembers(f"user:{user_id}:completed")),
            mastery={key: float(value) for key, value in rdb.hgetall(f"user:{user_id}:mastery").items()},
            recent_categories=tuple(rdb.lrange(f"user:{user_id}:recent_categories", 0, 9)),
        )
        feature_generated_at = rdb.get(f"user:{user_id}:features_updated_at")
        return profile, "redis", feature_generated_at
    except redis.RedisError:
        FALLBACKS.inc()
        return LearnerProfile(user_id=user_id, interests=frozenset({"ai", "data"})), "fallback", None


def log_impressions(
    *,
    request_id: str,
    user_id: str,
    ranked: list[Any],
    served_at: str,
    context: dict[str, Any],
    policy_id: str,
    version: str,
) -> None:
    """Persist one impression row per displayed recommendation when DATABASE_URL is set."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url or not ranked:
        return
    rows = []
    context_json = json.dumps(context)
    for rank, item in enumerate(ranked, start=1):
        # Uniform propensity over the returned slate for offline estimators.
        propensity = 1.0 / len(ranked)
        rows.append(
            (
                str(uuid.uuid4()),
                request_id,
                user_id,
                item.course.course_id,
                rank,
                float(item.score),
                item.candidate_source,
                policy_id,
                version,
                propensity,
                served_at,
                context_json,
            )
        )
    try:
        with psycopg.connect(database_url) as conn, conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO recommendation_impressions
                    (impression_id, request_id, user_id, course_id, rank, score,
                     candidate_source, policy_id, model_version, propensity, served_at, context)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                """,
                rows,
            )
            conn.commit()
    except Exception:
        IMPRESSION_FAILURES.inc()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "recommendation-api", "version": APP_VERSION}


@app.get("/ready")
def ready() -> dict[str, Any]:
    redis_ok = False
    postgres_ok = False
    try:
        redis_ok = bool(rdb.ping())
    except redis.RedisError:
        redis_ok = False

    database_url = os.getenv("DATABASE_URL")
    if database_url:
        try:
            with psycopg.connect(database_url, connect_timeout=2) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    postgres_ok = cur.fetchone() is not None
        except Exception:
            postgres_ok = False
    else:
        # Local unit/demo mode without Postgres still allows serving rankings.
        postgres_ok = True

    return {
        "ready": redis_ok and postgres_ok,
        "redis": redis_ok,
        "postgres": postgres_ok,
    }


@app.post("/v1/recommendations")
def recommend(req: RecommendationRequest) -> dict[str, Any]:
    started = time.perf_counter()
    request_id = str(uuid.uuid4())
    try:
        learner, feature_source, feature_generated_at = load_profile(req.user_id)
        context = RecommendationContext(
            device=str(req.context.get("device", "web")),
            hour=int(req.context.get("hour", 12)),
            exploration_bucket=int(req.context.get("exploration_bucket", 0)),
        )
        ranked = policy.rank(learner, context, top_k=req.top_k)
        REQUESTS.labels("ok", policy.policy_id).inc()
        served_at = datetime.now(timezone.utc).isoformat()
        version = model_version()
        response_context = {
            "device": context.device,
            "hour": context.hour,
            "exploration_bucket": context.exploration_bucket,
            **{key: value for key, value in req.context.items() if key not in {"device", "hour", "exploration_bucket"}},
        }
        log_impressions(
            request_id=request_id,
            user_id=req.user_id,
            ranked=ranked,
            served_at=served_at,
            context=response_context,
            policy_id=policy.policy_id,
            version=version,
        )
        return {
            "request_id": request_id,
            "user_id": req.user_id,
            "policy_id": policy.policy_id,
            "model_version": version,
            "feature_source": feature_source,
            "feature_generated_at": feature_generated_at or served_at,
            "served_at": served_at,
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
