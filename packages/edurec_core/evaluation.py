from __future__ import annotations

from math import log2
from typing import Iterable, Sequence


def recall_at_k(relevant: set[str], ranked: Sequence[str], k: int) -> float:
    if not relevant:
        return 0.0
    return len(relevant.intersection(ranked[:k])) / len(relevant)


def ndcg_at_k(relevance: dict[str, float], ranked: Sequence[str], k: int) -> float:
    gains = [relevance.get(item, 0.0) for item in ranked[:k]]
    dcg = sum((2**gain - 1) / log2(index + 2) for index, gain in enumerate(gains))
    ideal = sorted(relevance.values(), reverse=True)[:k]
    idcg = sum((2**gain - 1) / log2(index + 2) for index, gain in enumerate(ideal))
    return dcg / idcg if idcg else 0.0


def catalog_coverage(rankings: Iterable[Sequence[str]], catalog_size: int) -> float:
    if catalog_size <= 0:
        return 0.0
    exposed = {item for ranking in rankings for item in ranking}
    return len(exposed) / catalog_size
