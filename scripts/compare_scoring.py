from __future__ import annotations

import json
import math

from found_music.backtest import NEGATIVE, POSITIVE, read_historical_rounds
from found_music.io import read_feedback
from found_music.models import Feedback, RatedTrack, Track
from found_music.scoring import score_candidate


def jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def legacy_similarity(a: Track, b: Track) -> float:
    token_sim = jaccard(a.feature_tokens, b.feature_tokens)
    year_sim = 0.0
    if a.year is not None and b.year is not None:
        year_sim = 0.18 * math.exp(-abs(a.year - b.year) / 8.0)
    return token_sim + year_sim


def legacy_weight(feedback: Feedback) -> float:
    if feedback == Feedback.FAVORITE:
        return 3.4
    if feedback == Feedback.STAR:
        return 2.4
    if feedback == Feedback.ADDED:
        return 1.4
    if feedback == Feedback.SKIPPED:
        return -0.35
    if feedback == Feedback.REJECTED:
        return -1.0
    return 0.0


def legacy_score(candidate: Track, history: list[RatedTrack]) -> float:
    contributions = []
    positive_sims = []
    for rated in history:
        sim = legacy_similarity(candidate, rated.track)
        weight = legacy_weight(rated.feedback)
        if weight > 0:
            positive_sims.append(sim)
        if weight:
            contributions.append((weight * sim, rated))

    positives = sorted((c for c in contributions if c[0] > 0), key=lambda x: x[0], reverse=True)[:4]
    negatives = sorted((c for c in contributions if c[0] < 0), key=lambda x: x[0])[:3]
    relevance = sum(c for c, _ in positives) + sum(c for c, _ in negatives)
    exploration = max(0.0, 1.0 - max(positive_sims, default=0.0))
    return relevance + 0.28 * exploration


def evaluate(scorer):
    rounds = read_historical_rounds("data/historical_rounds.csv")
    history = read_feedback("data/feedback.csv")
    grouped = {}
    for row in rounds:
        grouped.setdefault(row.round_id, []).append(row)

    total_pairs = 0
    total_pair_wins = 0.0
    total_pos = 0
    top_hits = 0
    per_round = []

    for round_id, rows in grouped.items():
        aliases = {alias for row in rows for alias in row.track.alias_keys}
        training = [rated for rated in history if not (rated.track.alias_keys & aliases)]
        scored = [(row, scorer(row.track, training)) for row in rows]
        pos = [score for row, score in scored if row.outcome in POSITIVE]
        neg = [score for row, score in scored if row.outcome in NEGATIVE]

        pair_wins = 0.0
        for p in pos:
            for n in neg:
                total_pairs += 1
                if p > n:
                    total_pair_wins += 1
                    pair_wins += 1
                elif p == n:
                    total_pair_wins += 0.5
                    pair_wins += 0.5

        ranked = sorted(scored, key=lambda x: x[1], reverse=True)
        k = len(pos)
        hits = sum(1 for row, _ in ranked[:k] if row.outcome in POSITIVE)
        total_pos += k
        top_hits += hits
        per_round.append({
            "round_id": round_id,
            "pairwise_accuracy": pair_wins / (len(pos) * len(neg)) if pos and neg else 0.0,
            "precision_at_k": hits / k if k else 0.0,
        })

    return {
        "pairwise_accuracy": total_pair_wins / total_pairs if total_pairs else 0.0,
        "precision_at_k": top_hits / total_pos if total_pos else 0.0,
        "per_round": per_round,
    }


def main():
    payload = {
        "v1": evaluate(legacy_score),
        "v2": evaluate(lambda track, history: score_candidate(track, history).final_score),
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
