from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum


class Feedback(str, Enum):
    STAR = "star"
    ADDED = "added"
    SKIPPED = "skipped"
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
    def alias_keys(self) -> frozenset[str]:
        title = normalize_title(self.title)
        aliases = {f"{artist}::{title}" for artist in artist_aliases(self.artist)}
        aliases.add(self.key)
        return frozenset(aliases)

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


def artist_aliases(artist: str) -> frozenset[str]:
    value = normalize(artist)
    value = re.sub(r"\s+(?:feat\.|featuring)\s+", " & ", value)
    parts = re.split(r"\s*(?:,|&|\bx\b|\band\b)\s*", value)
    aliases = {_slug(part) for part in parts if _slug(part)}
    aliases.add(_slug(value))
    return frozenset(aliases)


def normalize_artist(artist: str) -> str:
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


def library_key_set(tracks: list[Track]) -> set[str]:
    return {alias for track in tracks for alias in track.alias_keys}


def history_key_set(history: list[RatedTrack]) -> set[str]:
    return {alias for rated in history for alias in rated.track.alias_keys}
