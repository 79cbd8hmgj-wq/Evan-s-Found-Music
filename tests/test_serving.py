"""Exposure recording must be reproducible, no duplicate batch issuance."""
import csv
import json

import pytest

from found_music.serving import serve_batch


def write_csv(path, header, rows):
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        writer.writerows(rows)


def test_recorded_batch_updates_exposure_and_writes_manifest(tmp_path):
    candidates = tmp_path / "candidates.csv"
    library = tmp_path / "library.csv"
    feedback = tmp_path / "feedback.csv"
    seen = tmp_path / "seen.csv"
    manifest = tmp_path / "batch.json"
    write_csv(candidates, ["title", "artist", "year", "genres", "tags"], [
        ["Fresh", "Artist A", "2001", "Hip-Hop/Rap", ""],
        ["Other", "Artist B", "2002", "R&B/Soul", ""],
    ])
    write_csv(library, ["title", "artist", "year", "genres", "tags"], [])
    write_csv(feedback, ["title", "artist", "year", "genres", "tags", "feedback"], [])
    write_csv(seen, ["title", "artist", "year", "genres", "tags", "batch_id"], [])

    first = serve_batch(candidates, feedback, library, seen, "batch-001", 1, manifest)
    assert len(first["tracks"]) == 1
    assert first["model_version"] == "v4"
    assert "new_artist_fraction" not in first["parameters"]
    assert "exploration_fraction" not in first["parameters"]
    assert first["diversity"]["shortfall"] == 0
    assert first["source_sha256"]["candidates"]
    assert json.loads(manifest.read_text(encoding="utf-8"))["batch_id"] == "batch-001"
    with seen.open(newline="", encoding="utf-8") as fh:
        recorded = list(csv.DictReader(fh))
    assert len(recorded) == 1
    assert recorded[0]["batch_id"] == "batch-001"

    with pytest.raises(ValueError, match="already exists"):
        serve_batch(candidates, feedback, library, seen, "batch-001", 1, manifest)
    second = serve_batch(candidates, feedback, library, seen, "batch-002", 1, tmp_path / "second.json")
    assert second["tracks"][0]["title"] != first["tracks"][0]["title"]


def test_serving_requires_nonempty_candidate_pool(tmp_path):
    candidates = tmp_path / "candidates.csv"
    library = tmp_path / "library.csv"
    feedback = tmp_path / "feedback.csv"
    seen = tmp_path / "seen.csv"
    write_csv(candidates, ["title", "artist", "year", "genres", "tags"], [])
    write_csv(library, ["title", "artist", "year", "genres", "tags"], [])
    write_csv(feedback, ["title", "artist", "year", "genres", "tags", "feedback"], [])
    write_csv(seen, ["title", "artist", "year", "genres", "tags", "batch_id"], [])
    with pytest.raises(ValueError, match="No eligible"):
        serve_batch(candidates, feedback, library, seen, "empty", 10, tmp_path / "batch.json")
