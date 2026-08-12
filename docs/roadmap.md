# 12-week roadmap

| Week | Deliverable |
| --- | --- |
| 1 | Problem definition, KPIs, event schema, and synthetic generator |
| 2 | PostgreSQL, Kafka, Redis, and API ingestion |
| 3 | Streaming features, deduplication, and late-event tests |
| 4 | Popularity and content-filtering baseline with a latency dashboard |
| 5 | Point-in-time training dataset and offline evaluation |
| 6 | Two-Tower retrieval and ANN index |
| 7 | Sequence-aware ranker, hard negatives, and calibration |
| 8 | MLflow tracking, registry, and model/data lineage |
| 9 | Kubeflow pipeline and quality gates |
| 10 | KServe/Triton, canary rollout, and rollback |
| 11 | Drift monitoring, load testing, and chaos testing |
| 12 | Report, demo, benchmark, and security review |

## Definition of done

- Recall@50 ≥ 0.35 and NDCG@10 ≥ 0.20 on a temporal split.
- API p95 < 150 ms at 100 RPS in the demo environment.
- Consumer replay does not incorrectly increment counters.
- A candidate model never receives 100% traffic when an offline or online gate fails.
- Tests, data contracts, a rollback runbook, dashboards, and an end-to-end demo are available.
