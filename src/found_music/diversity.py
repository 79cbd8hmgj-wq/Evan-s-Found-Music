"""Cross-round artist diversity policy for prospective discovery."""
from __future__ import annotations

import re
from collections import Counter

from .models import RatedTrack, ScoredTrack, Track, artist_aliases, library_key_set, history_key_set, normalize
from .scoring import Weights, score_candidate, similarity


def artist_credits(track: Track) -> frozenset[str]:
    """Conservative text-based identities, including explicitly credited guests."""
    aliases = set(artist_aliases(track.artist))
    for match in re.findall(r"(?:feat\.|featuring)\s+([^\)\]]+)", track.title, re.I):
        aliases.update(artist_aliases(match))
    return frozenset(aliases)


def recommend_diverse_batch(
    candidates: list[Track],
    history: list[RatedTrack],
    library: list[Track],
    seen: list[Track],
    recent: list[Track],
    *,
    batch_size: int = 20,
    weights: Weights = Weights(),
) -> tuple[list[ScoredTrack], dict]:
    """Allocate 30/40/30 slots and avoid shared credits and recent artists.

    Use exploration as the primary objective in its own allocation. Prefer
    previously unseen credits; only relax the recent window if necessary.
    Never relax the within-batch credit cap or the track/year exclusions.
    """
    excluded = library_key_set(library) | history_key_set(history) | library_key_set(seen)
    known_credits = set().union(*(artist_credits(t) for t in [*library, *(x.track for x in history), *seen]))
    recent_credits = set().union(*(artist_credits(t) for t in recent))
    exposure = Counter(a for t in seen for a in artist_credits(t))
    scored = [
        score_candidate(t, history, weights) for t in candidates
        if t.year is not None and 1989 <= t.year <= 2016 and not t.alias_keys & excluded
    ]
    credits = {id(x): artist_credits(x.track) for x in scored}
    established = round(batch_size * .30)
    novel = round(batch_size * .40)
    targets = {"established": established, "new_artist": novel, "exploration": batch_size - established - novel}
    counts = dict.fromkeys(targets, 0)
    selected: list[ScoredTrack] = []
    used_credits: set[str] = set()
    used_tracks: set[str] = set()
    fallback = 0
    recent_reuse = 0

    def pick(lane: str, *, allow_recent: bool = False, any_lane: bool = False) -> bool:
        def eligible(item: ScoredTrack) -> bool:
            names = credits[id(item)]
            if item.track.alias_keys & used_tracks or names & used_credits:
                return False
            if not allow_recent and names & recent_credits:
                return False
            if not any_lane:
                if lane == "established" and not names & known_credits:
                    return False
                if lane == "new_artist" and names & known_credits:
                    return False
            return True

        def objective(item: ScoredTrack) -> tuple[float, float]:
            names = credits[id(item)]
            redundancy = max((similarity(item.track, x.track, weights) for x in selected), default=0.0)
            penalty = .08 * max((exposure[a] for a in names), default=0)
            relevance = item.final_score - .55 * redundancy - penalty
            if lane == "exploration":
                return (item.exploration - .55 * redundancy - penalty, relevance)
            return (relevance, item.exploration)

        pool = [x for x in scored if eligible(x)]
        if not pool:
            return False
        # Exploration favors unfamiliar artists when such a candidate exists.
        if lane == "exploration":
            unfamiliar = [x for x in pool if not credits[id(x)] & known_credits]
            if unfamiliar:
                pool = unfamiliar
        best = max(pool, key=objective)
        selected.append(best)
        used_credits.update(credits[id(best)])
        used_tracks.update(best.track.alias_keys)
        counts[lane] += 1
        return True

    # Reserve each lane's allocation before filling deficits.
    for lane, count in targets.items():
        for _ in range(count):
            if not pick(lane):
                break

    # Prioritize avoiding recent artists over forcing the exact quota.
    while len(selected) < batch_size and pick("exploration", any_lane=True):
        fallback += 1
    while len(selected) < batch_size and pick("exploration", allow_recent=True, any_lane=True):
        fallback += 1
        recent_reuse += 1

    return selected, {
        "targets": targets,
        "selected": counts,
        "fallback_slots": fallback,
        "recent_reuse_slots": recent_reuse,
        "shortfall": max(0, batch_size - len(selected)),
        "distinct_credited_names": len(used_credits),
        "unfamiliar_credit_tracks": sum(not (credits[id(x)] & known_credits) for x in selected),
    }


# Initial tuning defaults; these are score penalties, never allocation quotas.
EXPOSURE_PENALTY = 0.12
RECENT_EXPOSURE_PENALTY = 0.14
DIVERSITY_PENALTY = 0.55


def recommend_relevance_batch(
    candidates: list[Track],
    history: list[RatedTrack],
    library: list[Track],
    seen: list[Track],
    recent: list[Track],
    *,
    batch_size: int = 20,
    weights: Weights = Weights(),
) -> tuple[list[ScoredTrack], dict]:
    """Rank all eligible songs together; familiarity is descriptive, not a quota.

    Exposure counts use previously recommended tracks, not library ownership.
    A frequent collaborator incurs the same exposure penalty as a lead credit.
    Logarithmic penalties remain finite so a sufficiently strong fit can win.
    """
    import math

    excluded = library_key_set(library) | history_key_set(history) | library_key_set(seen)
    known = set().union(*(artist_credits(t) for t in [*library, *(r.track for r in history), *seen]))
    exposure = Counter(a for t in seen for a in artist_credits(t))
    recent_exposure = Counter(a for t in recent for a in artist_credits(t))
    scored = [
        score_candidate(t, history, weights) for t in candidates
        if t.year is not None and 1989 <= t.year <= 2016 and not t.alias_keys & excluded
    ]
    credits = {id(item): artist_credits(item.track) for item in scored}
    selected: list[ScoredTrack] = []
    used_credits: set[str] = set()
    used_tracks: set[str] = set()
    trace = []
    while len(selected) < batch_size:
        best = None
        best_value = float("-inf")
        best_trace = None
        for item in scored:
            names = credits[id(item)]
            if item.track.alias_keys & used_tracks or names & used_credits:
                continue
            total = max((exposure[a] for a in names), default=0)
            recent_count = max((recent_exposure[a] for a in names), default=0)
            penalty = EXPOSURE_PENALTY * math.log1p(total) + RECENT_EXPOSURE_PENALTY * math.log1p(recent_count)
            redundancy = max((similarity(item.track, other.track, weights) for other in selected), default=0.0)
            value = item.final_score - penalty - DIVERSITY_PENALTY * redundancy
            if value > best_value:
                best, best_value = item, value
                best_trace = {"title": item.track.title, "artist": item.track.artist,
                              "base_score": round(item.final_score, 6),
                              "artist_exposure": total, "recent_exposure": recent_count,
                              "exposure_penalty": round(penalty, 6),
                              "redundancy_penalty": round(DIVERSITY_PENALTY * redundancy, 6),
                              "selection_score": round(value, 6)}
        if best is None:
            break
        selected.append(best)
        used_credits.update(credits[id(best)])
        used_tracks.update(best.track.alias_keys)
        trace.append(best_trace)
    return selected, {
        "policy": "relevance-first-soft-exposure",
        "shortfall": max(0, batch_size - len(selected)),
        "distinct_credited_names": len(used_credits),
        "unfamiliar_credit_tracks": sum(not (credits[id(x)] & known) for x in selected),
        "recent_reuse_slots": sum(any(recent_exposure[a] for a in credits[id(x)]) for x in selected),
        "selection_trace": trace,
    }
