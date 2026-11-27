from found_music.models import Feedback, RatedTrack, Track
from found_music.diversity import artist_credits, recommend_relevance_batch


def test_all_familiar_artists_allowed_when_best_fit():
    library = [Track(f"Owned {i}", f"Artist {i}", 2001, ("Hip-Hop/Rap",), ("melodic-hook",)) for i in range(8)]
    history = [RatedTrack(t, Feedback.FAVORITE) for t in library]
    candidates = [Track(f"Fresh {i}", t.artist, 2001, t.genres, t.tags) for i, t in enumerate(library)]
    candidates += [Track(f"Novel {i}", f"Unknown {i}", 2016, ("Jazz",)) for i in range(8)]
    batch, report = recommend_relevance_batch(candidates, history, library, [], [], batch_size=8)
    assert len(batch) == 8
    assert report["unfamiliar_credit_tracks"] == 0


def test_all_unfamiliar_allowed_when_best_fit():
    anchor = Track("Owned", "Anchor", 2001, ("Hip-Hop/Rap",), ("melodic-hook",))
    candidates = [Track("Weak", "Anchor", 2016, ("Jazz",))]
    candidates += [Track(f"Fresh {i}", f"Unknown {i}", 2001, anchor.genres, anchor.tags) for i in range(8)]
    batch, report = recommend_relevance_batch(candidates, [RatedTrack(anchor, Feedback.FAVORITE)], [anchor], [], [], batch_size=8)
    assert len(batch) == 8
    assert report["unfamiliar_credit_tracks"] == 8


def test_repeated_exposure_lowers_rank_of_otherwise_equal_tracks():
    a = Track("A", "Repeated", 2001, ("Hip-Hop/Rap",))
    b = Track("B", "Other", 2001, ("Hip-Hop/Rap",))
    seen = [Track(f"Served {i}", a.artist, 2001) for i in range(6)]
    batch, _ = recommend_relevance_batch([a, b], [], [], seen, seen[-2:], batch_size=1)
    assert batch[0].track == b


def test_recent_artist_can_still_win_with_stronger_musical_fit():
    anchor = Track("Owned", "Repeated", 2001, ("Hip-Hop/Rap",), ("melodic-hook",))
    seen = [Track("Served", anchor.artist, 2001)]
    strong = Track("Fresh", anchor.artist, 2001, anchor.genres, anchor.tags)
    weak = Track("Weak", "Unknown", 2016, ("Jazz",))
    batch, report = recommend_relevance_batch([weak, strong], [RatedTrack(anchor, Feedback.FAVORITE)], [anchor], seen, seen, batch_size=1)
    assert batch[0].track == strong
    assert report["recent_reuse_slots"] == 1


def test_feature_credit_cap_never_relaxes():
    candidates = [Track("One (feat. Guest)", "A", 2001), Track("Two", "Guest", 2002)]
    batch, report = recommend_relevance_batch(candidates, [], [], [], [], batch_size=2)
    assert len(batch) == 1
    assert report["shortfall"] == 1


def test_preserves_year_and_track_exclusions():
    owned = Track("Owned", "A", 2001)
    served = Track("Served", "B", 2001)
    valid = Track("Fresh", "C", 2016)
    batch, _ = recommend_relevance_batch([owned, served, valid, Track("Too new", "D", 2017)], [], [owned], [served], [served], batch_size=4)
    assert [x.track for x in batch] == [valid]
