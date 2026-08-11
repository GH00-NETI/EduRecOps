# Evaluation protocol

| Lớp | Chỉ số | Gate |
| --- | --- | --- |
| Retrieval | Recall@50, coverage, long-tail recall | Không kém baseline theo cohort |
| Ranking | NDCG@10, MRR, calibration | NDCG tăng; cold-start không giảm quá ngưỡng |
| Học tập | completion@7/30d, assessment gain | Không đánh đổi learning outcome lấy click |
| Fairness | ΔNDCG, exposure parity, average popularity | Báo cáo slice và cảnh báo regression |
| Vận hành | p95/p99, error rate, feature age, fallback | Gate độc lập với quality gate |

## Chống leakage

- Label time luôn sau feature event time.
- Training row chỉ join feature có timestamp không vượt quá label timestamp.
- Split theo thời gian, không random split toàn cục.
- Mọi offline report ghi dataset snapshot, code commit, policy và model version.

## Online experiment

- Shadow trước khi nhận traffic.
- Sticky assignment theo user.
- Ramp 10% → 25% → 50% với sample floor.
- Tự động rollback nếu error delta > 2 điểm phần trăm, p95 > 1.5× control hoặc learning proxy suy giảm.
