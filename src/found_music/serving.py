"""Recorded recommendation batches with explicit source provenance."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from .io import read_feedback, read_tracks
from .diversity import recommend_diverse_batch

MODEL_VERSION = "v3"


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _atomic_write(path: Path, contents: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".found-music-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(contents)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def serve_batch(
    candidates_path: str | Path,
    feedback_path: str | Path,
    library_path: str | Path,
    seen_path: str | Path,
    batch_id: str,
    size: int,
    manifest_path: str | Path,
) -> dict:
    """Record a new batch. Do not show any generated batch before recording.

    Writes an immutable manifest containing input hashes and ranked scores, then
    updates the exposure ledger. A manifest left after an interrupted ledger
    write intentionally blocks accidental repeat issuance and can be reconciled.
    """
    if not batch_id or not batch_id.strip() or any(c in batch_id for c in "/\\"):
        raise ValueError("Provide a nonempty, path-safe batch_id")
    if size < 1:
        raise ValueError("Batch size must be positive")
    candidates_path, feedback_path, library_path, seen_path, manifest_path = map(
        Path, (candidates_path, feedback_path, library_path, seen_path, manifest_path)
    )
    if manifest_path.exists():
        raise ValueError("Batch manifest already exists; use a new batch_id")
    with seen_path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        fieldnames = reader.fieldnames
        previously_seen = list(reader)
    if not fieldnames or not {"title", "artist", "year", "genres", "tags", "batch_id"} <= set(fieldnames):
        raise ValueError("Invalid served-song ledger schema")
    if any(row["batch_id"] == batch_id for row in previously_seen):
        raise ValueError("Batch ID already exists in exposure ledger")

    candidates = read_tracks(candidates_path)
    feedback = read_feedback(feedback_path)
    library = read_tracks(library_path)
    seen = read_tracks(seen_path)
    # Ledger order is issuance order; group by batch rather than track count.
    recent_ids = list(dict.fromkeys(row["batch_id"] for row in previously_seen))[-3:]
    recent = [track for track, row in zip(seen, previously_seen) if row["batch_id"] in recent_ids]
    batch, diversity = recommend_diverse_batch(
        candidates, feedback, library, seen, recent, batch_size=size
    )
    if not batch:
        raise ValueError("No eligible candidate songs; replenish candidate pool")
    timestamp = datetime.now(timezone.utc).isoformat()
    manifest = {
        "batch_id": batch_id,
        "generated_at_utc": timestamp,
        "model_version": MODEL_VERSION,
        "requested_size": size,
        "source_sha256": {
            "candidates": _digest(candidates_path),
            "feedback": _digest(feedback_path),
            "library": _digest(library_path),
            "seen": _digest(seen_path),
        },
        "parameters": {
            "min_year": 1989,
            "max_year": 2016,
            "established_fraction": 0.30,
            "new_artist_fraction": 0.40,
            "exploration_fraction": 0.30,
            "recent_batch_window": 3,
            "diversity_lambda": 0.55,
            "max_per_artist": 1,
        },
        "diversity": diversity,
        "tracks": [
            {"rank": rank, "title": item.track.title, "artist": item.track.artist,
             "year": item.track.year, "score": round(item.final_score, 6),
             "exploration": round(item.exploration, 6)}
            for rank, item in enumerate(batch, 1)
        ],
    }
    # Persist manifest before the ledger so a partial failure is auditable.
    _atomic_write(manifest_path, json.dumps(manifest, indent=2) + "\n")
    for item in batch:
        track = item.track
        row = {field: "" for field in fieldnames}
        row.update({
            "title": track.title, "artist": track.artist,
            "year": str(track.year) if track.year is not None else "",
            "genres": "|".join(track.genres),
            "tags": "|".join(track.tags),
            "batch_id": batch_id,
        })
        previously_seen.append(row)
    from io import StringIO
    out = StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(previously_seen)
    _atomic_write(seen_path, out.getvalue())
    return manifest
