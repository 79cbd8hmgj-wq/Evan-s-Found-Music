"""Historical evaluations must not learn from later listening rounds."""
from found_music.backtest import RoundTrack, walk_forward_backtest
from found_music.models import Feedback, RatedTrack, Track


def test_walk_forward_uses_only_earlier_rounds():
    first_good = Track("First good", "A", 2000, ("Hip-Hop/Rap",), ("soulful",))
    first_bad = Track("First bad", "B", 2000, ("Rock",), ("hard",))
    second_good = Track("Second good", "C", 2001, ("Hip-Hop/Rap",), ("soulful",))
    second_bad = Track("Second bad", "D", 2001, ("Rock",), ("hard",))
    rounds = [
        RoundTrack("r1", first_good, Feedback.STAR),
        RoundTrack("r1", first_bad, Feedback.SKIPPED),
        RoundTrack("r2", second_good, Feedback.STAR),
        RoundTrack("r2", second_bad, Feedback.SKIPPED),
    ]
    result = walk_forward_backtest(rounds, [])
    assert result.rounds == 2
    assert result.per_round[0].pairwise_accuracy == 0.5
    assert result.per_round[1].pairwise_accuracy > 0.5


def test_walk_forward_excludes_future_feedback_even_if_supplied_as_seed():
    future = Track("Future", "X", 2000, ("Hip-Hop/Rap",), ("soulful",))
    rows = [
        RoundTrack("r1", Track("Good", "A", 2000, ("Hip-Hop/Rap",), ("soulful",)), Feedback.ADDED),
        RoundTrack("r1", Track("Bad", "B", 2000, ("Rock",), ("hard",)), Feedback.SKIPPED),
    ]
    baseline = walk_forward_backtest(rows, [])
    contaminated = walk_forward_backtest(rows, [RatedTrack(future, Feedback.STAR)])
    assert baseline.per_round[0].pairwise_accuracy != contaminated.per_round[0].pairwise_accuracy


def test_walk_forward_rejects_noncontiguous_duplicate_round_ids():
    rows = [
        RoundTrack("r1", Track("A", "A"), Feedback.STAR),
        RoundTrack("r2", Track("B", "B"), Feedback.SKIPPED),
        RoundTrack("r1", Track("C", "C"), Feedback.STAR),
    ]
    import pytest
    with pytest.raises(ValueError, match="contiguous"):
        walk_forward_backtest(rows, [])
