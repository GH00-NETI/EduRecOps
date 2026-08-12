# Runbook

## High API error rate

1. Check `/health`, `/ready`, and Prometheus alerts.
2. Inspect the Redis fallback rate and Kafka consumer lag.
3. If a candidate model is receiving traffic, set its traffic weight to zero.
4. Verify the champion model and feature-schema version.

## Feature freshness exceeds the SLO

1. Check Redpanda health and consumer lag.
2. Inspect duplicate and late-event rates.
3. Scale the feature worker if the backlog continues to grow.
4. Replay only from a verified offset, and confirm that the deduplication marker still has a valid TTL.

## Model rollback

1. Disable candidate and shadow traffic.
2. Point the stable manifest to the previous champion digest.
3. Verify p95 latency, error rate, and the output contract.
4. Record the incident with model, feature, dataset, and commit lineage.
