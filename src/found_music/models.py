from __future__ import annotations

import re
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
        tokens = {f"artist:{normalize_artist(self.artist)}"}
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


def _slug(value: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", normalize(value)).split())


def normalize_artist(artist: str) -> str:
    # Apple Music/screenshots sometimes put a featured artist in the artist
    # field and sometimes in the title. Use the lead artist for deduping.
    artist = re.split(r"\s+(?:feat\.|featuring)\s+", normalize(artist), maxsplit=1)[0]
    return _slug(artist)


def normalize_title(title: str) -> str:
    value = normalize(title)
    value = re.sub(
        r"\s*[\(\[]\s*(?:feat\.|featuring)\s+.*?[\)\]]",
        "",
        value,
    )
    value = re.sub(r"\s*\(album version\)", "", value)
    value = value.replace(" aka ", " ")
    return _slug(value)


def normalize_key(artist: str, title: str) -> str:
    return f"{normalize_artist(artist)}::{normalize_title(title)}"
