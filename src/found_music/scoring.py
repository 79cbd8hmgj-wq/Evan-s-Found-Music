from __future__ import annotations

import math
from dataclasses import dataclass

from .models import Feedback, RatedTrack, ScoredTrack, Track


@dataclass(frozen=True)
class Weights:
    star: float = 2.4
    added: float = 1.4
    skipped: float = -0.35
    rejected: float = -1.0
    year_similarity: float = 0.18
    novelty: float = 0.28


def _jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _year_similarity(a: int | None, b: int | None) -> float:
    if a is None or b is None:
        return 0.0
    return math.exp(-abs(a - b) / 8.0)


def similarity(a: Track, b: Track, weights: Weights = Weights()) -> float:
    token_sim = _jaccard(a.feature_tokens, b.feature_tokens)
    return token_sim + weights.year_similarity * _year_similarity(a.year, b.year)


def score_candidate(candidate: Track, history: list[RatedTrack], weights: Weights = Weights()) -> ScoredTrack:
    contributions: list[tuple[float, RatedTrack]] = []
    positive_similarities: list[float] = []

    for rated in history:
        sim = similarity(candidate, rated.track, weights)
        if rated.feedback == Feedback.STAR:
            weight = weights.star
            positive_similarities.append(sim)
        elif rated.feedback == Feedback.ADDED:
            weight = weights.added
            positive_similarities.append(sim)
        elif rated.feedback == Feedback.SKIPPED:
            weight = weights.skipped
        elif rated.feedback == Feedback.REJECTED:
            weight = weights.rejected
        else:
            continue
        contributions.append((weight * sim, rated))

    # Use several strongest anchors rather than collapsing taste into one centroid.
    positives = sorted((c for c in contributions if c[0] > 0), key=lambda x: x[0], reverse=True)[:4]
    negatives = sorted((c for c in contributions if c[0] < 0), key=lambda x: x[0])[:3]
    relevance = sum(c for c, _ in positives) + sum(c for c, _ in negatives)

    nearest_positive = max(positive_similarities, default=0.0)
    exploration = max(0.0, 1.0 - nearest_positive)
    final = relevance + weights.novelty * exploration

    reasons: list[str] = []
    for contribution, rated in positives[:2]:
        reasons.append(f"positive anchor: {rated.track.artist} — {rated.track.title} ({contribution:.2f})")
    if negatives:
        contribution, rated = negatives[0]
        reasons.append(f"negative anchor: {rated.track.artist} — {rated.track.title} ({contribution:.2f})")
    reasons.append(f"exploration={exploration:.2f}")

    return ScoredTrack(candidate, relevance, exploration, final, tuple(reasons))
