# Research plan

## Research questions

1. Does multi-source candidate generation improve Recall@50 over a popularity baseline?
2. Can the prerequisite guard reduce overly difficult recommendations without an unacceptable coverage loss?
3. Do knowledge-state features improve completion@30d and NDCG@10?
4. Can the learning-value ranker preserve engagement while improving a learning-gain proxy?

## Hypotheses

- H1: Two-Tower retrieval plus a learning-path union improves Recall@50 by at least 10% relative.
- H2: The prerequisite guard reduces the unsuitable recommendation rate below 2%.
- H3: Mastery and sequence features improve NDCG@10 for active learners.
- H4: The multi-objective policy does not reduce completion@30d in any primary cohort.

## Experimental design

- Split data by time while preserving event order within each learner.
- Baselines: popularity, category affinity, and course quality.
- Candidates: Two-Tower retrieval, learning paths, and cohort popularity for cold start.
- Report cohorts: new, active, and lapsed learners; beginner, intermediate, and advanced levels; web and mobile.
- Use IPS, SNIPS, or DR only when propensities are valid and support overlap is sufficient.

## Datasets

- Synthetic event stream: replay, duplicate, out-of-order, and feature-freshness tests.
- MOOCCubeX: retrieval, concept-graph, and prerequisite-aware experiments.
- EdNet or OULAD: knowledge-state and completion-proxy experiments.
- Do not redistribute datasets with restrictive licenses in this repository.
