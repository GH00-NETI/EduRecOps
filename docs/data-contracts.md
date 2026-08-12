# Data contracts

## `learning-events` v1

| Field | Type | Required | Description |
| --- | --- | ---: | --- |
| schema_version | string | Yes | Schema version |
| event_id | UUID | Yes | Idempotency key |
| event_type | enum | Yes | view/click/enroll/complete/rate/assessment |
| user_id | string | Yes | Learner identifier |
| course_id | string | Yes | Course identifier |
| session_id | UUID | Yes | User session |
| event_time | ISO-8601 UTC | Yes | Event time |
| device | enum | No | web/ios/android |
| position | integer | No | Display position |
| dwell_seconds | integer | No | Interaction duration |
| score | float [0,1] | For assessment | Normalized assessment score |

## `recommendation-impressions` v1

Every displayed item must produce an impression record, including items that receive no click.

| Field | Purpose |
| --- | --- |
| request_id, impression_id | Join request → slate → outcome |
| policy_id, model_version | Lineage and replay |
| course_id, rank, score | Ranking analysis |
| candidate_source | Coverage analysis by source |
| propensity | Counterfactual evaluation |
| feature_generated_at, served_at | Freshness and leakage checks |

## Compatibility

A producer must not remove fields or change their meaning within the same major version. Consumers must ignore unknown fields. Breaking changes require a new topic or version and a dual-read migration window.
