from __future__ import annotations

from .models import RatedTrack, ScoredTrack, Track, history_key_set
from .scoring import Weights, score_candidate, similarity


def recommend_batch(
    candidates: list[Track],
    history: list[RatedTrack],
    library_keys: set[str],
    batch_size: int = 15,
    exploration_fraction: float = 0.20,
    diversity_lambda: float = 0.55,
    weights: Weights = Weights(),
    min_year: int = 1989,
    max_year: int = 2016,
    allow_unknown_year: bool = False,
) -> list[ScoredTrack]:
    """Select a mixed, deduplicated batch inside the configured year boundary."""
    seen_keys = history_key_set(history)

    def eligible(candidate: Track) -> bool:
        if candidate.alias_keys & library_keys:
            return False
        if candidate.alias_keys & seen_keys:
            return False
        if candidate.year is None:
            return allow_unknown_year
        return min_year <= candidate.year <= max_year

    eligible_candidates = [candidate for candidate in candidates if eligible(candidate)]
    scored = [score_candidate(candidate, history, weights) for candidate in eligible_candidates]
    if not scored:
        return []

    explore_slots = round(batch_size * exploration_fraction)
    exploit_slots = max(0, batch_size - explore_slots)

    exploit_pool = sorted(scored, key=lambda x: x.final_score, reverse=True)
    explore_pool = sorted(scored, key=lambda x: (x.exploration, x.final_score), reverse=True)

    selected: list[ScoredTrack] = []
    used: set[str] = set()

    def pick(pool: list[ScoredTrack], count: int) -> None:
        for _ in range(count):
            best: ScoredTrack | None = None
            best_mmr = float("-inf")
            for item in pool:
                if item.track.key in used:
                    continue
                redundancy = max(
                    (similarity(item.track, chosen.track, weights) for chosen in selected),
                    default=0.0,
                )
                mmr = item.final_score - diversity_lambda * redundancy
                if mmr > best_mmr:
                    best_mmr = mmr
                    best = item
            if best is None:
                return
            selected.append(best)
            used.add(best.track.key)

    pick(exploit_pool, exploit_slots)
    pick(explore_pool, min(explore_slots, batch_size - len(selected)))
    if len(selected) < batch_size:
        pick(exploit_pool, batch_size - len(selected))
    return selected
