from found_music.models import Feedback, RatedTrack, Track, library_key_set
from found_music.recommend import recommend_batch
from found_music.scoring import Weights, score_candidate


def test_library_tracks_are_excluded():
    owned = Track("Owned Song", "Artist", 2001, ("hip-hop",), ("smooth",))
    other = Track("Fresh Song", "Other", 2002, ("hip-hop",), ("smooth",))
    history = [RatedTrack(Track("Anchor", "A", 2001, ("hip-hop",), ("smooth",)), Feedback.STAR)]
    result = recommend_batch([owned, other], history, library_key_set([owned]), batch_size=2)
    assert [x.track.title for x in result] == ["Fresh Song"]


def test_previously_rated_tracks_are_never_recommended_again():
    seen = RatedTrack(Track("Seen Song", "Artist", 2005), Feedback.SKIPPED)
    fresh = Track("Fresh Song", "Artist", 2006)
    result = recommend_batch([seen.track, fresh], [seen], set(), batch_size=5)
    assert [x.track.title for x in result] == ["Fresh Song"]


def test_feature_and_album_version_variants_dedupe():
    library = [
        Track("Can't Stop Me (feat. Ayanna Irish)", "Jadakiss"),
        Track("Same N****s (Album Version)", "Mase"),
    ]
    candidates = [
        Track("Can't Stop Me", "Jadakiss feat. Ayanna Irish", 2009),
        Track("Same N****s", "Mase", 1999),
        Track("Fresh Song", "Other", 2000),
    ]
    result = recommend_batch(candidates, [], library_key_set(library), batch_size=5)
    assert [x.track.title for x in result] == ["Fresh Song"]


def test_collaboration_artist_order_dedupes():
    library = [Track("Wonderful", "Ashanti, Ja Rule & R. Kelly")]
    candidate = Track("Wonderful", "Ja Rule feat. Ashanti", 2004)
    assert recommend_batch([candidate], [], library_key_set(library)) == []


def test_luchini_title_alias_dedupes():
    assert Track("Luchini AKA This Is It", "Camp Lo").key == Track("Luchini - This Is It", "Camp Lo").key


def test_hard_year_boundary_is_enforced():
    candidates = [
        Track("Too Old", "A", 1988),
        Track("Inside", "B", 1999),
        Track("Too New", "C", 2017),
        Track("Unknown", "D", None),
    ]
    result = recommend_batch(candidates, [], set(), batch_size=10)
    assert [x.track.title for x in result] == ["Inside"]


def test_unknown_year_can_be_explicitly_allowed():
    candidate = Track("Unknown", "D", None)
    result = recommend_batch([candidate], [], set(), allow_unknown_year=True)
    assert [x.track.title for x in result] == ["Unknown"]


def test_skipped_is_a_milder_negative_than_rejected():
    candidate = Track("Candidate", "C", 2005, ("hip-hop",), ("club",))
    skipped = RatedTrack(Track("Skip", "A", 2005, ("hip-hop",), ("club",)), Feedback.SKIPPED)
    rejected = RatedTrack(Track("Reject", "B", 2005, ("hip-hop",), ("club",)), Feedback.REJECTED)
    skip_score = score_candidate(candidate, [skipped], Weights()).final_score
    reject_score = score_candidate(candidate, [rejected], Weights()).final_score
    assert skip_score > reject_score


def test_diversity_avoids_near_duplicates():
    anchor = RatedTrack(Track("Anchor", "A", 2004, ("hip-hop",), ("melodic",)), Feedback.STAR)
    a = Track("A1", "Same", 2004, ("hip-hop",), ("melodic", "rnb-hook"))
    b = Track("A2", "Same", 2004, ("hip-hop",), ("melodic", "rnb-hook"))
    c = Track("Different", "Else", 2005, ("southern rap",), ("soulful",))
    result = recommend_batch([a, b, c], [anchor], set(), batch_size=2, exploration_fraction=0.5, diversity_lambda=1.0)
    assert len(result) == 2
    assert len({x.track.key for x in result}) == 2


def test_rejected_track_reduces_similar_candidate_score():
    positive = RatedTrack(Track("Good", "A", 2005, ("hip-hop",), ("soulful",)), Feedback.ADDED)
    rejected = RatedTrack(Track("Bad", "B", 2005, ("crunk",), ("club",)), Feedback.REJECTED)
    soulful = Track("Soulful", "C", 2006, ("hip-hop",), ("soulful",))
    club = Track("Club", "D", 2006, ("crunk",), ("club",))
    result = recommend_batch([soulful, club], [positive, rejected], set(), batch_size=2, exploration_fraction=0)
    assert result[0].track.title == "Soulful"
