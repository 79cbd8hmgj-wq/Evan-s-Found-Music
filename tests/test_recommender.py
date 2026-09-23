from found_music.models import Feedback, RatedTrack, Track
from found_music.recommend import recommend_batch


def test_library_tracks_are_excluded():
    owned = Track("Owned Song", "Artist", 2001, ("hip-hop",), ("smooth",))
    other = Track("Fresh Song", "Other", 2002, ("hip-hop",), ("smooth",))
    history = [RatedTrack(Track("Anchor", "A", 2001, ("hip-hop",), ("smooth",)), Feedback.STAR)]
    result = recommend_batch([owned, other], history, {owned.key}, batch_size=2)
    assert [x.track.title for x in result] == ["Fresh Song"]


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
