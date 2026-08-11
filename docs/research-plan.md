# Kế hoạch nghiên cứu

## Câu hỏi

1. Multi-source candidate generation có tăng Recall@50 so với popularity baseline không?
2. Prerequisite guard có giảm tỷ lệ gợi ý quá khó mà không làm giảm coverage quá mức không?
3. Knowledge-state features có cải thiện completion@30d và NDCG@10 không?
4. Learning-value ranker có giữ engagement trong khi tăng learning gain proxy không?

## Giả thuyết

- H1: Two-Tower + learning-path union tăng Recall@50 tối thiểu 10% tương đối.
- H2: Prerequisite guard giảm unsuitable recommendation rate xuống dưới 2%.
- H3: Thêm mastery và sequence features cải thiện NDCG@10 trên nhóm active learners.
- H4: Multi-objective policy không làm completion@30d giảm trên bất kỳ cohort chính nào.

## Thiết kế thí nghiệm

- Chia dữ liệu theo thời gian; giữ thứ tự trong từng learner.
- Baseline: popularity, category affinity và quality.
- Candidate: Two-Tower, learning path và cold-start cohort popularity.
- Báo cáo theo cohort: new, active, lapsed; beginner/intermediate/advanced; web/mobile.
- Chỉ dùng IPS/SNIPS/DR khi propensity và support overlap hợp lệ.

## Dataset

- Synthetic event stream: kiểm tra replay, duplicate, out-of-order và feature freshness.
- MOOCCubeX: retrieval, concept graph và prerequisite-aware experiments.
- EdNet/OULAD: knowledge state và completion proxy.
- Không phân phối lại dataset có giấy phép hạn chế trong repo.
