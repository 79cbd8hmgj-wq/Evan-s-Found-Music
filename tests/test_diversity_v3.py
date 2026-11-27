from found_music.models import Feedback, RatedTrack, Track
from found_music.diversity import artist_credits, recommend_diverse_batch


def test_featured_artist_counts_as_shared_credit():
    a = Track("First (feat. Jadakiss)", "Mase", 2004)
    b = Track("Second", "Jadakiss", 2005)
    assert artist_credits(a) & artist_credits(b)


def test_round_balances_familiar_novel_and_exploration():
    known = [Track(f"Owned {i}", f"Known {i}", 2004, ("Hip-Hop/Rap",)) for i in range(10)]
    feedback = [RatedTrack(t, Feedback.STAR) for t in known]
    candidates = [
        *[Track(f"New known {i}", t.artist, 2005, t.genres) for i, t in enumerate(known)],
        *[Track(f"Novel {i}", f"Novel {i}", 2005, ("Hip-Hop/Rap",)) for i in range(20)],
        *[Track(f"Adjacent {i}", f"Adjacent {i}", 2005, ("Reggae",)) for i in range(10)],
    ]
    batch, report = recommend_diverse_batch(candidates, feedback, known, [], [], batch_size=20)
    assert len(batch) == 20
    assert report["selected"] == {"established": 6, "new_artist": 8, "exploration": 6}
    assert sum(not (artist_credits(x.track) & set().union(*(artist_credits(t) for t in known))) for x in batch) >= 14
    assert sum("Reggae" in x.track.genres for x in batch) >= 6


def test_recent_credits_avoided_and_no_shared_features():
    recent = Track("Served (feat. Repeat)", "Old lead", 2000, ("Hip-Hop/Rap",))
    known = Track("Owned", "Anchor", 2000, ("Hip-Hop/Rap",))
    feedback = [RatedTrack(known, Feedback.STAR)]
    candidates = [
        Track("A (feat. Repeat)", "Anchor", 2001, ("Hip-Hop/Rap",)),
        Track("B", "Repeat", 2001, ("Hip-Hop/Rap",)),
        Track("C (feat. Guest)", "New one", 2001, ("Hip-Hop/Rap",)),
        Track("D (feat. Guest)", "New two", 2001, ("Hip-Hop/Rap",)),
        Track("E", "New three", 2001, ("Hip-Hop/Rap",)),
        Track("F", "New four", 2001, ("Reggae",)),
    ]
    batch, report = recommend_diverse_batch(candidates, feedback, [known], [recent], [recent], batch_size=3)
    credits = [artist_credits(x.track) for x in batch]
    assert len(batch) == 3
    assert all(not (c & artist_credits(recent)) for c in credits)
    assert all(not (a & b) for i, a in enumerate(credits) for b in credits[i+1:])
    assert report["fallback_slots"] == 1


def test_does_not_relax_credit_cap_to_fill_small_pool():
    candidates = [Track(f"Song {i}", "One artist", 2001) for i in range(10)]
    batch, report = recommend_diverse_batch(candidates, [], [], [], [], batch_size=5)
    assert len(batch) == 1
    assert report["shortfall"] == 4
