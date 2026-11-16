"""Catalog replenishment: schema, year, overlap, provenance and failure isolation."""
import csv
from found_music.candidate_discovery import extract_songs, merge_candidates, search_terms, replenish


def song(name, artist, year="2005-01-01T00:00:00Z", track_id=1, kind="song"):
    return dict(wrapperType="track", kind=kind, trackId=track_id,
                trackName=name, artistName=artist, releaseDate=year,
                primaryGenreName="Hip-Hop/Rap", trackTimeMillis=220000)


def test_extract_requires_verified_catalog_fields_and_date():
    songs, rejected = extract_songs({"results": [
        song("Valid", "Artist", track_id=12),
        song("Outside", "Artist", year="2019-01-01T00:00:00Z", track_id=13),
        song("Video", "Artist", track_id=14, kind="music-video"),
        song("No ID", "Artist", track_id=None),
        song("No date", "Artist", year=""),
    ]})
    assert [(x.title, x.year) for x in songs] == [("Valid", 2005)]
    assert len(rejected) == 4


def test_merge_excludes_ownership_feedback_seen_and_duplicate_versions():
    result = merge_candidates(
        [song("New", "Artist", track_id=3), song("New", "Artist", track_id=4),
         song("Owned", "Singer", track_id=5), song("Skipped", "Other", track_id=6),
         song("Served", "Last", track_id=7)],
        exclusions=[("Owned", "Singer"), ("Skipped", "Other"), ("Served", "Last")],
        existing=[("Old Candidate", "Artist")],
    )
    assert [(x.title, x.artist) for x in result] == [("New", "Artist")]


def test_replenish_can_run_again_without_repeating_candidates(tmp_path):
    for name, header, rows in [
        ("library.csv", ["title", "artist", "year", "genres", "tags"], [["Owned", "Singer", "2000", "", ""]]),
        ("feedback.csv", ["title", "artist", "year", "genres", "tags", "feedback"], []),
        ("seen.csv", ["title", "artist", "year", "genres", "tags", "batch_id"], []),
        ("candidates.csv", ["title", "artist", "year", "genres", "tags"], []),
    ]:
        with (tmp_path / name).open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(header); w.writerows(rows)

    def fetch(term):
        return {"results": [song("Owned", "Singer", track_id=10),
                            song("Fresh", "Artist", track_id=11)]}

    paths = [tmp_path / n for n in ("candidates.csv", "library.csv", "feedback.csv", "seen.csv")]
    first = replenish(*paths, terms=["Artist"], fetch=fetch, target=10)
    assert first["new_candidates"] == 1
    assert first["total_candidates"] == 1
    second = replenish(*paths, terms=["Artist"], fetch=fetch, target=10)
    assert second["new_candidates"] == 0
    assert second["total_candidates"] == 1


def test_replenish_does_not_modify_candidates_when_source_fails(tmp_path):
    paths = []
    for name, header in [
        ("candidates.csv", "title,artist,year,genres,tags\n"),
        ("library.csv", "title,artist,year,genres,tags\n"),
        ("feedback.csv", "title,artist,year,genres,tags,feedback\n"),
        ("seen.csv", "title,artist,year,genres,tags,batch_id\n"),
    ]:
        p = tmp_path / name; p.write_text(header); paths.append(p)
    original = paths[0].read_bytes()
    def broken(term):
        raise RuntimeError("catalog down")
    import pytest
    with pytest.raises(RuntimeError, match="catalog down"):
        replenish(*paths, terms=["Artist"], fetch=broken, target=10)
    assert paths[0].read_bytes() == original


def test_query_seed_loader_deduplicates_and_ignores_comments():
    assert search_terms("Mase\n# note\nMase\nNas\n") == ["Mase", "Nas"]
