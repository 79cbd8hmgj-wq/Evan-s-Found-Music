from __future__ import annotations

import csv
from pathlib import Path

from .models import Feedback, RatedTrack, Track


def read_tracks(path: str | Path) -> list[Track]:
    with open(path, newline="", encoding="utf-8") as fh:
        rows = csv.DictReader(fh)
        return [
            Track(
                title=row["title"].strip(),
                artist=row["artist"].strip(),
                year=int(row["year"]) if row.get("year", "").strip() else None,
                genres=tuple(x.strip() for x in row.get("genres", "").split("|") if x.strip()),
                tags=tuple(x.strip() for x in row.get("tags", "").split("|") if x.strip()),
            )
            for row in rows
        ]


def read_feedback(path: str | Path) -> list[RatedTrack]:
    tracks = read_tracks(path)
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    return [RatedTrack(track, Feedback(row["feedback"].strip())) for track, row in zip(tracks, rows)]
