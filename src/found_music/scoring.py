from __future__ import annotations

import math
import re
from collections import defaultdict
from dataclasses import dataclass

from .models import Feedback, RatedTrack, ScoredTrack, Track, artist_aliases, normalize


GENERIC_GENRES = {
    "music",
    "hip-hop/rap",
    "hip-hop",
    "rap",
    "r&b/soul",
    "pop",
    "rock",
}

SOURCE_TAGS = {"apple-music-catalog", "live-tuning-add"}


@dataclass(frozen=True)
class Weights:
    favorite: float = 3.6
    star: float = 2.4
    added: float = 1.4
    skipped: float = -0.75
    rejected: float = -1.2

    artist_similarity: float = 0.20
    genre_family_similarity: float = 0.85
    subgenre_similarity: float = 0.95
    tag_similarity: float = 1.20
    blend_similarity: float = 0.65
    era_similarity: float = 0.20
    collaboration_similarity: float = 0.15

    anchor_weight: float = 1.0
    profile_weight: float = 0.85
    novelty: float = 0.12


def _jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    if not a and not b:
        return 0.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _year_similarity(a: int | None, b: int | None) -> float:
    if a is None or b is None:
        return 0.0
    return math.exp(-abs(a - b) / 7.0)


def _genre_families(track: Track) -> frozenset[str]:
    families: set[str] = set()
    for raw in track.genres:
        genre = normalize(raw)
        if "hip-hop" in genre or genre == "rap" or genre.endswith(" rap"):
            families.add("hiphop")
        if "r&b" in genre or "soul" in genre:
            families.add("rnb")
        if "pop" in genre:
            families.add("pop")
        if "reggae" in genre or "dancehall" in genre:
            families.add("reggae")
        if "dance" in genre or "electronic" in genre or "house" in genre:
            families.add("dance")
        if "alternative" in genre and "rap" not in genre:
            families.add("alternative")
        if genre in {"rock", "hard rock"}:
            families.add("rock")
    return frozenset(families)


def _subgenres(track: Track) -> frozenset[str]:
    return frozenset(
        normalize(genre)
        for genre in track.genres
        if normalize(genre) not in GENERIC_GENRES
    )


def _meaningful_tags(track: Track) -> frozenset[str]:
    return frozenset(
        normalize(tag)
        for tag in track.tags
        if normalize(tag) and normalize(tag) not in SOURCE_TAGS
    )


def _featured_artists(track: Track) -> frozenset[str]:
    names = set(artist_aliases(track.artist))
    for match in re.findall(
        r"(?:feat\.|featuring)\s+([^\)\]]+)",
        track.title,
        flags=re.IGNORECASE,
    ):
        for part in re.split(r"\s*(?:,|&|\band\b|\bx\b)\s*", match):
            alias = normalize(part)
            if alias:
                names.add(alias)
    return frozenset(names)


def _is_collaboration(track: Track) -> bool:
    if re.search(r"(?:feat\.|featuring)", track.title, flags=re.IGNORECASE):
        return True
    return len(artist_aliases(track.artist)) > 1


def _blend_tokens(track: Track) -> frozenset[str]:
    families = sorted(_genre_families(track))
    blends = {
        f"{families[i]}+{families[j]}"
        for i in range(len(families))
        for j in range(i + 1, len(families))
    }
    return frozenset(blends)


def _preference_tokens(track: Track) -> frozenset[str]:
    tokens: set[str] = set()
    tokens.update(f"family:{x}" for x in _genre_families(track))
    tokens.update(f"subgenre:{x}" for x in _subgenres(track))
    tokens.update(f"tag:{x}" for x in _meaningful_tags(track))
    tokens.update(f"blend:{x}" for x in _blend_tokens(track))
    tokens.update(f"artist:{x}" for x in _featured_artists(track))
    tokens.add(f"collab:{'yes' if _is_collaboration(track) else 'no'}")
    if track.year is not None:
        tokens.add(f"era5:{track.year // 5 * 5}")
    return frozenset(tokens)


def _token_importance(token: str) -> float:
    if token.startswith("tag:"):
        return 1.25
    if token.startswith("blend:"):
        return 1.10
    if token.startswith("subgenre:"):
        return 1.00
    if token.startswith("family:"):
        return 0.80
    if token.startswith("artist:"):
        return 0.30
    if token.startswith("era5:"):
        return 0.35
    if token.startswith("collab:"):
        return 0.20
    return 0.50


def _feedback_weight(feedback: Feedback, weights: Weights) -> float:
    if feedback == Feedback.FAVORITE:
        return weights.favorite
    if feedback == Feedback.STAR:
        return weights.star
    if feedback == Feedback.ADDED:
        return weights.added
    if feedback == Feedback.SKIPPED:
        return weights.skipped
    if feedback == Feedback.REJECTED:
        return weights.rejected
    return 0.0


def similarity(a: Track, b: Track, weights: Weights = Weights()) -> float:
    components = [
        (
            weights.artist_similarity,
            1.0 if (_featured_artists(a) & _featured_artists(b)) else 0.0,
        ),
        (
            weights.genre_family_similarity,
            _jaccard(_genre_families(a), _genre_families(b)),
        ),
        (
            weights.subgenre_similarity,
            _jaccard(_subgenres(a), _subgenres(b)),
        ),
        (
            weights.tag_similarity,
            _jaccard(_meaningful_tags(a), _meaningful_tags(b)),
        ),
        (
            weights.blend_similarity,
            _jaccard(_blend_tokens(a), _blend_tokens(b)),
        ),
        (
            weights.era_similarity,
            _year_similarity(a.year, b.year),
        ),
        (
            weights.collaboration_similarity,
            1.0 if _is_collaboration(a) == _is_collaboration(b) else 0.0,
        ),
    ]
    denominator = sum(weight for weight, _ in components)
    if denominator <= 0:
        return 0.0
    return sum(weight * value for weight, value in components) / denominator


def _preference_profile_score(
    candidate: Track,
    history: list[RatedTrack],
    weights: Weights,
) -> tuple[float, tuple[tuple[str, float], ...]]:
    positive_counts: dict[str, float] = defaultdict(float)
    negative_counts: dict[str, float] = defaultdict(float)
    positive_total = 0.0
    negative_total = 0.0

    for rated in history:
        feedback_weight = _feedback_weight(rated.feedback, weights)
        if feedback_weight == 0:
            continue
        tokens = _preference_tokens(rated.track)
        if feedback_weight > 0:
            positive_total += feedback_weight
            target = positive_counts
            magnitude = feedback_weight
        else:
            negative_total += abs(feedback_weight)
            target = negative_counts
            magnitude = abs(feedback_weight)
        for token in tokens:
            target[token] += magnitude

    if positive_total == 0 or negative_total == 0:
        return 0.0, ()

    token_scores: list[tuple[str, float]] = []
    alpha = 1.5
    for token in _preference_tokens(candidate):
        pos_rate = (positive_counts[token] + alpha) / (positive_total + 2 * alpha)
        neg_rate = (negative_counts[token] + alpha) / (negative_total + 2 * alpha)
        log_odds = math.log(pos_rate / neg_rate)
        token_scores.append((token, _token_importance(token) * log_odds))

    if not token_scores:
        return 0.0, ()

    # Average instead of summing so tracks with richer metadata are not
    # rewarded merely for having more catalog labels.
    total_importance = sum(_token_importance(token) for token, _ in token_scores)
    raw = sum(score for _, score in token_scores) / max(total_importance, 1e-9)
    score = max(-1.5, min(1.5, raw))
    strongest = tuple(
        sorted(token_scores, key=lambda item: abs(item[1]), reverse=True)[:3]
    )
    return score, strongest


def score_candidate(
    candidate: Track,
    history: list[RatedTrack],
    weights: Weights = Weights(),
) -> ScoredTrack:
    contributions: list[tuple[float, RatedTrack]] = []
    positive_similarities: list[float] = []

    for rated in history:
        sim = similarity(candidate, rated.track, weights)
        feedback_weight = _feedback_weight(rated.feedback, weights)
        if feedback_weight > 0:
            positive_similarities.append(sim)
        if feedback_weight != 0:
            contributions.append((feedback_weight * sim, rated))

    positives = sorted(
        (c for c in contributions if c[0] > 0),
        key=lambda x: x[0],
        reverse=True,
    )[:4]
    negatives = sorted(
        (c for c in contributions if c[0] < 0),
        key=lambda x: x[0],
    )[:4]

    positive_anchor = (
        sum(c for c, _ in positives) / len(positives) if positives else 0.0
    )
    negative_anchor = (
        sum(c for c, _ in negatives) / len(negatives) if negatives else 0.0
    )
    anchor_score = positive_anchor + negative_anchor

    profile_score, profile_reasons = _preference_profile_score(
        candidate, history, weights
    )

    nearest_positive = max(positive_similarities, default=0.0)
    exploration = max(0.0, 1.0 - nearest_positive)

    relevance = (
        weights.anchor_weight * anchor_score
        + weights.profile_weight * profile_score
    )
    final = relevance + weights.novelty * exploration

    reasons: list[str] = [
        f"anchor={anchor_score:.2f}",
        f"profile={profile_score:.2f}",
    ]
    for token, contribution in profile_reasons:
        reasons.append(f"{token}={contribution:+.2f}")
    reasons.append(f"exploration={exploration:.2f}")

    return ScoredTrack(candidate, relevance, exploration, final, tuple(reasons))
