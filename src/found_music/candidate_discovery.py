"""Replenish the eligible song pool using public catalog metadata.

Catalog releaseDate is an album/storefront release date, not proof of an
original recording's first release. Never silently infer missing years.
"""
from __future__ import annotations

import csv
import io
import json
import os
import re
import tempfile
import time
from dataclasses import dataclass
from collections import Counter
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .io import read_tracks
from .models import Track, library_key_set, normalize_artist

FIELDS = ["title", "artist", "year", "genres", "tags"]
BASE = "https://itunes.apple.com/search"


@dataclass(frozen=True)
class CatalogSong:
    title: str
    artist: str
    year: int
    genre: str
    catalog_id: int


def search_terms(contents: str) -> list[str]:
    terms = []
    seen = set()
    for raw in contents.splitlines():
        term = raw.strip()
        if not term or term.startswith("#") or term.casefold() in seen:
            continue
        seen.add(term.casefold())
        terms.append(term)
    return terms


def extract_songs(payload: dict) -> tuple[list[CatalogSong], list[dict]]:
    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        raise ValueError("Catalog response missing results array")
    accepted = []
    rejected = []
    for item in payload["results"]:
        if not isinstance(item, dict):
            rejected.append({"reason": "invalid-result", "item": item})
            continue
        try:
            name = item.get("trackName")
            artist = item.get("artistName")
            date = item.get("releaseDate")
            catalog_id = item.get("trackId")
            if (item.get("kind") != "song" or item.get("wrapperType") != "track"
                    or not isinstance(name, str) or not name.strip()
                    or not isinstance(artist, str) or not artist.strip()
                    or isinstance(catalog_id, bool) or not isinstance(catalog_id, int)
                    or not isinstance(date, str) or not re.match(r"^\d{4}-\d{2}-\d{2}", date)):
                raise ValueError("invalid-song-metadata")
            year = int(date[:4])
            if year < 1989 or year > 2016:
                raise ValueError("outside-release-boundary")
            if not 30000 <= item.get("trackTimeMillis", 0) <= 1200000:
                raise ValueError("invalid-duration")
            accepted.append(CatalogSong(
                title=name.strip(), artist=artist.strip(), year=year,
                genre=str(item.get("primaryGenreName") or "").strip(), catalog_id=catalog_id))
        except (ValueError, TypeError) as error:
            rejected.append({"reason": str(error), "item": item})
    return accepted, rejected


def search_itunes(term: str, limit: int = 200, attempts: int = 3) -> dict:
    if limit < 1 or limit > 200:
        raise ValueError("Search limit must be 1..200")
    url = BASE + "?" + urlencode({
        "term": term, "country": "us", "media": "music",
        "entity": "song", "attribute": "artistTerm", "limit": limit,
    })
    for attempt in range(attempts):
        try:
            request = Request(url, headers={"User-Agent": "FoundMusicResearch/1.0", "Accept": "application/json"})
            with urlopen(request, timeout=25) as response:
                return json.load(response)
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
            if attempt + 1 == attempts:
                raise
            time.sleep(min(8, 2 ** attempt))
    raise RuntimeError("Catalog fetch exhausted retries")


def _exclusion_keys(exclusions: list[tuple[str, str]]) -> set[str]:
    return library_key_set([Track(title, artist) for title, artist in exclusions])


def merge_candidates(
    results: list[dict],
    exclusions: list[tuple[str, str]],
    existing: list[tuple[str, str]] | None = None,
) -> list[CatalogSong]:
    """Dedupe candidates by conservative preexisting alias logic and track IDs."""
    keys = _exclusion_keys(exclusions + (existing or []))
    used_ids = set()
    output = []
    for raw in results:
        if raw.get("kind") != "song":
            continue
        songs, _ = extract_songs({"results": [raw]})
        for song in songs:
            candidate = Track(song.title, song.artist, song.year)
            if song.catalog_id in used_ids or candidate.alias_keys & keys:
                continue
            output.append(song)
            used_ids.add(song.catalog_id)
            keys.update(candidate.alias_keys)
    return output


def _csv_rows(items: list[Track]) -> str:
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=FIELDS)
    writer.writeheader()
    for track in items:
        writer.writerow({
            "title": track.title, "artist": track.artist,
            "year": track.year or "", "genres": "|".join(track.genres),
            "tags": "|".join(track.tags),
        })
    return out.getvalue()


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(dir=path.parent, prefix=".found-music-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def replenish(
    candidates_path: str | Path,
    library_path: str | Path,
    feedback_path: str | Path,
    seen_path: str | Path,
    *,
    terms: list[str],
    fetch=search_itunes,
    target: int = 1000,
    apply: bool = True,
    pause_seconds: float = 0.0,
    max_per_query: int = 30,
    max_per_artist: int = 8,
    seed_candidates_path: str | Path | None = None,
) -> dict:
    """Stage all searches before writing; a failed request leaves inputs intact."""
    if target < 1:
        raise ValueError("target must be positive")
    if max_per_query < 1:
        raise ValueError("max_per_query must be positive")
    if max_per_artist < 1:
        raise ValueError("max_per_artist must be positive")
    if not terms:
        raise ValueError("At least one catalog search term required")
    candidates_path = Path(candidates_path)
    previous = read_tracks(seed_candidates_path or candidates_path)
    library = read_tracks(library_path)
    feedback = read_tracks(feedback_path)
    seen = read_tracks(seen_path)
    existing = [(t.title, t.artist) for t in previous]
    exclusions = [(t.title, t.artist) for t in [*library, *feedback, *seen]]
    keys = _exclusion_keys(exclusions + existing)
    tracks = list(previous)
    artist_counts = Counter(normalize_artist(t.artist) for t in tracks)
    # Existing overrepresented artists remain in the pool, but cannot grow.
    terms = sorted(terms, key=lambda term: artist_counts[normalize_artist(term)])
    provenance = []
    retrieved = 0
    dropped = 0
    queries = 0
    used_sources: set[str] = set()
    for term in terms:
        if len(tracks) >= target:
            break
        accepted_this_query = 0
        payload = fetch(term)
        songs, rejected = extract_songs(payload)
        retrieved += len(payload["results"])
        dropped += len(rejected)
        queries += 1
        for song in songs:
            t = Track(song.title, song.artist, song.year, (song.genre,) if song.genre else (), ("itunes-catalog",))
            artist = normalize_artist(t.artist)
            if t.alias_keys & keys or artist_counts[artist] >= max_per_artist:
                dropped += 1
                continue
            artist_counts[artist] += 1
            keys.update(t.alias_keys)
            tracks.append(t)
            provenance.append({"artist": song.artist, "title": song.title, "catalog_id": song.catalog_id,
                               "catalog_year": song.year, "query": term})
            accepted_this_query += 1
            used_sources.add(term)
            if len(tracks) >= target or accepted_this_query >= max_per_query:
                break
        if pause_seconds and len(tracks) < target:
            time.sleep(pause_seconds)
    if apply and len(tracks) != len(previous):
        _atomic_write(candidates_path, _csv_rows(tracks))
    return {
        "existing_candidates": len(previous),
        "new_candidates": len(tracks) - len(previous),
        "total_candidates": len(tracks),
        "target": target,
        "query_count": queries,
        "unique_query_sources": len(used_sources),
        "max_per_query": max_per_query,
        "max_per_artist": max_per_artist,
        "catalog_results": retrieved,
        "filtered_results": dropped,
        "source": "Apple iTunes Search API, US storefront, catalog release year",
        "applied": apply,
        "new_provenance": provenance,
    }
