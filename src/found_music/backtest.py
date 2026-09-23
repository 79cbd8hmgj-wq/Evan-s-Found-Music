from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path

from .models import Feedback, RatedTrack, Track
from .scoring import Weights, score_candidate


POSITIVE = {Feedback.STAR, Feedback.ADDED}
NEGATIVE = {Feedback.SKIPPED, Feedback.REJECTED}


@dataclass(frozen=True)
class RoundTrack:
    round_id: str
    track: Track
    outcome: Feedback


@dataclass(frozen=True)
class RoundResult:
    round_id: str
    tracks: int
    positives: int
    negatives: int
    pairwise_accuracy: float
    precision_at_k: float


@dataclass(frozen=True)
class BacktestResult:
    rounds: int
    tracks: int
    positives: int
    negatives: int
    pairwise_accuracy: float
    precision_at_k: float
    per_round: tuple[RoundResult, ...]


def read_historical_rounds(path: str | Path) -> list[RoundTrack]:
    with open(path, newline="", encoding="utf-8") as fh:
        rows = csv.DictReader(fh)
        return [
            RoundTrack(
                round_id=row["round_id"].strip(),
                track=Track(
                    title=row["title"].strip(),
                    artist=row["artist"].strip(),
                    year=int(row["year"]) if row.get("year", "").strip() else None,
                    genres=tuple(
                        x.strip()
                        for x in row.get("genres", "").split("|")
                        if x.strip()
                    ),
                ),
                outcome=Feedback(row["outcome"].strip()),
            )
            for row in rows
        ]


def _score_round(
    round_id: str,
    rows: list[RoundTrack],
    history: list[RatedTrack],
    weights: Weights,
) -> RoundResult:
    round_aliases = {
        alias
        for row in rows
        for alias in row.track.alias_keys
    }
    training = [
        rated
        for rated in history
        if not (rated.track.alias_keys & round_aliases)
    ]

    scored = [
        (row, score_candidate(row.track, training, weights).final_score)
        for row in rows
    ]
    positives = [score for row, score in scored if row.outcome in POSITIVE]
    negatives = [score for row, score in scored if row.outcome in NEGATIVE]

    comparisons = 0
    wins = 0.0
    for positive in positives:
        for negative in negatives:
            comparisons += 1
            if positive > negative:
                wins += 1
            elif positive == negative:
                wins += 0.5

    k = len(positives)
    ranked = sorted(scored, key=lambda x: x[1], reverse=True)
    top_k = ranked[:k]
    top_hits = sum(1 for row, _ in top_k if row.outcome in POSITIVE)

    return RoundResult(
        round_id=round_id,
        tracks=len(rows),
        positives=len(positives),
        negatives=len(negatives),
        pairwise_accuracy=(wins / comparisons if comparisons else 0.0),
        precision_at_k=(top_hits / k if k else 0.0),
    )


def backtest_rounds(
    rounds: list[RoundTrack],
    history: list[RatedTrack],
    weights: Weights = Weights(),
) -> BacktestResult:
    grouped: dict[str, list[RoundTrack]] = {}
    for row in rounds:
        grouped.setdefault(row.round_id, []).append(row)

    per_round = tuple(
        _score_round(round_id, rows, history, weights)
        for round_id, rows in grouped.items()
    )

    pairwise_weight = sum(
        result.positives * result.negatives for result in per_round
    )
    weighted_pairwise = sum(
        result.pairwise_accuracy * result.positives * result.negatives
        for result in per_round
    )
    total_positives = sum(result.positives for result in per_round)
    weighted_precision = sum(
        result.precision_at_k * result.positives for result in per_round
    )

    return BacktestResult(
        rounds=len(per_round),
        tracks=sum(result.tracks for result in per_round),
        positives=total_positives,
        negatives=sum(result.negatives for result in per_round),
        pairwise_accuracy=(
            weighted_pairwise / pairwise_weight if pairwise_weight else 0.0
        ),
        precision_at_k=(
            weighted_precision / total_positives if total_positives else 0.0
        ),
        per_round=per_round,
    )


def result_dict(result: BacktestResult) -> dict:
    payload = asdict(result)
    payload["per_round"] = [asdict(item) for item in result.per_round]
    return payload
