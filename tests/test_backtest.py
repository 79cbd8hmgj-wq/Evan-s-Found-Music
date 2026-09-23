from found_music.backtest import RoundTrack, backtest_rounds
from found_music.models import Feedback, RatedTrack, Track


def test_backtest_scores_round_without_leaking_round_outcomes():
    star = Track("Star", "A", 2000, ("hip-hop",))
    skip = Track("Skip", "B", 2000, ("rock",))
    history = [
        RatedTrack(star, Feedback.STAR),
        RatedTrack(skip, Feedback.SKIPPED),
        RatedTrack(Track("Anchor", "C", 2000, ("hip-hop",)), Feedback.STAR),
    ]
    rounds = [
        RoundTrack("r1", star, Feedback.STAR),
        RoundTrack("r1", skip, Feedback.SKIPPED),
    ]
    result = backtest_rounds(rounds, history)
    assert result.rounds == 1
    assert result.tracks == 2
    assert result.positives == 1
    assert result.negatives == 1
    assert result.pairwise_accuracy == 1.0
    assert result.precision_at_k == 1.0
