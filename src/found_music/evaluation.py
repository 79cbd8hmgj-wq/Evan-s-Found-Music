from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import combinations

from .models import Feedback, RatedTrack, ScoredTrack, Track, normalize_artist
from .scoring import Weights, score_candidate, similarity


@dataclass(frozen=True)
class BatchMetrics:
    size: int
    unique_artists: int
    unique_decades: int
    average_pairwise_similarity: float
    average_exploration: float


@dataclass(frozen=True)
class FeedbackMetrics:
    positives: int
    negatives: int
    pairwise_accuracy: float
    positive_mean_score: float
    negative_mean_score: float


def batch_metrics(batch: list[ScoredTrack], weights: Weights = Weights()) -> BatchMetrics:
    tracks = [item.track for item in batch]
    pairs = list(combinations(tracks, 2))
    avg_similarity = (
        sum(similarity(a, b, weights) for a, b in pairs) / len(pairs)
        if pairs else 0.0
    )
    decades = {track.year // 10 * 10 for track in tracks if track.year is not None}
    return BatchMetrics(
        size=len(batch),
        unique_artists=len({normalize_artist(track.artist) for track in tracks}),
        unique_decades=len(decades),
        average_pairwise_similarity=avg_similarity,
        average_exploration=(
            sum(item.exploration for item in batch) / len(batch) if batch else 0.0
        ),
    )


def feedback_discrimination(
    history: list[RatedTrack], weights: Weights = Weights()
) -> FeedbackMetrics:
    scored: list[tuple[Feedback, float]] = []
    for i, rated in enumerate(history):
        if rated.feedback not in {
            Feedback.FAVORITE,
            Feedback.STAR,
            Feedback.ADDED,
            Feedback.SKIPPED,
            Feedback.REJECTED,
        }:
            continue
        other_history = history[:i] + history[i + 1 :]
        score = score_candidate(rated.track, other_history, weights).final_score
        scored.append((rated.feedback, score))

    positive_scores = [
        score for feedback, score in scored
        if feedback in {Feedback.FAVORITE, Feedback.STAR, Feedback.ADDED}
    ]
    negative_scores = [
        score for feedback, score in scored
        if feedback in {Feedback.SKIPPED, Feedback.REJECTED}
    ]

    comparisons = 0
    wins = 0.0
    for positive in positive_scores:
        for negative in negative_scores:
            comparisons += 1
            if positive > negative:
                wins += 1.0
            elif positive == negative:
                wins += 0.5

    return FeedbackMetrics(
        positives=len(positive_scores),
        negatives=len(negative_scores),
        pairwise_accuracy=(wins / comparisons if comparisons else 0.0),
        positive_mean_score=(
            sum(positive_scores) / len(positive_scores) if positive_scores else 0.0
        ),
        negative_mean_score=(
            sum(negative_scores) / len(negative_scores) if negative_scores else 0.0
        ),
    )


def metrics_dict(metrics: BatchMetrics | FeedbackMetrics) -> dict:
    return asdict(metrics)
