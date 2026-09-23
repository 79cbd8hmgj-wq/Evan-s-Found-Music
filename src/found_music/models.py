from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Feedback(str, Enum):
    STAR = "star"
    ADDED = "added"
    REJECTED = "rejected"
    LIBRARY = "library"


@dataclass(frozen=True)
class Track:
    title: str
    artist: str
    year: int | None = None
    genres: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()

    @property
    def key(self) -> str:
        return normalize_key(self.artist, self.title)

    @property
    def feature_tokens(self) -> frozenset[str]:
        tokens = {f"artist:{normalize(self.artist)}"}
        tokens.update(f"genre:{normalize(x)}" for x in self.genres)
        tokens.update(f"tag:{normalize(x)}" for x in self.tags)
        if self.year:
            tokens.add(f"decade:{self.year // 10 * 10}")
        return frozenset(tokens)


@dataclass(frozen=True)
class RatedTrack:
    track: Track
    feedback: Feedback


@dataclass(frozen=True)
class ScoredTrack:
    track: Track
    relevance: float
    exploration: float
    final_score: float
    reasons: tuple[str, ...] = field(default_factory=tuple)


def normalize(value: str) -> str:
    return " ".join(value.lower().replace("’", "'").split())


def normalize_key(artist: str, title: str) -> str:
    return f"{normalize(artist)}::{normalize(title)}"
