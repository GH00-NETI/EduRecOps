# Roadmap 12 tuần

| Tuần | Kết quả |
|---|---|
| 1 | Đặc tả bài toán, KPI, event schema, synthetic generator |
| 2 | PostgreSQL, Kafka, Redis, API ingest |
| 3 | Streaming features, deduplication, late-event tests |
| 4 | Baseline popularity + content filter, dashboard latency |
| 5 | Training dataset point-in-time, offline evaluation |
| 6 | Two-Tower retrieval + ANN index |
| 7 | Ranker sequence-aware, hard negatives, calibration |
| 8 | MLflow tracking/registry, model/data lineage |
| 9 | Kubeflow pipeline và quality gates |
| 10 | KServe/Triton, canary và rollback |
| 11 | Drift monitoring, load test, chaos test |
| 12 | Báo cáo, demo, benchmark, security review |

## Definition of done

- Recall@50 ≥ 0.35; NDCG@10 ≥ 0.20 trên split theo thời gian.
- API p95 < 150 ms ở 100 RPS trong môi trường demo.
- Event consumer replay không làm tăng sai counter.
- Candidate model không nhận 100% traffic nếu gate offline/online thất bại.
- Có test, data contract, runbook rollback và dashboard.
