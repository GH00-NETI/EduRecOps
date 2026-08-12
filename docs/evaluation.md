# Evaluation protocol

| Layer | Metrics | Gate |
| --- | --- | --- |
| Retrieval | Recall@50, coverage, long-tail recall | No regression against the baseline in any cohort |
| Ranking | NDCG@10, MRR, calibration | Higher NDCG without excessive cold-start regression |
| Learning | completion@7/30d, assessment gain | Never trade learning outcomes for clicks |
| Fairness | NDCG gap, exposure parity, average popularity | Report slices and alert on regressions |
| Operations | p95/p99, error rate, feature age, fallback | Evaluate independently from model-quality gates |

## Leakage prevention

- Label time must always follow feature event time.
- A training row may only join features whose timestamps do not exceed the label timestamp.
- Use temporal splits rather than a global random split.
- Every offline report records the dataset snapshot, code commit, policy, and model version.

## Online experiment

- Run in shadow mode before serving user traffic.
- Use sticky assignment by learner.
- Ramp from 10% → 25% → 50% with a minimum sample-size requirement.
- Roll back automatically if the error-rate delta exceeds 2 percentage points, p95 exceeds 1.5× control, or the learning proxy declines.
