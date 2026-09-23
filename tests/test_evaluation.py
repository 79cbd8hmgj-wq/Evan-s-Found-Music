import pytest

from found_music.evaluation import batch_metrics, feedback_discrimination
from found_music.models import Feedback, RatedTrack, ScoredTrack, Track


def test_batch_metrics_report_diversity():
    batch = [
        ScoredTrack(Track("A", "Artist 1", 1999, ("hip-hop",)), 1, 0.2, 1.2),
        ScoredTrack(Track("B", "Artist 2", 2005, ("r&b",)), 1, 0.4, 1.4),
    ]
    metrics = batch_metrics(batch)
    assert metrics.size == 2
    assert metrics.unique_artists == 2
    assert metrics.unique_decades == 2
    assert metrics.average_exploration == pytest.approx(0.3)


def test_feedback_discrimination_counts_classes():
    history = [
        RatedTrack(Track("Star", "A", 2000, ("hip-hop",)), Feedback.STAR),
        RatedTrack(Track("Add", "B", 2001, ("hip-hop",)), Feedback.ADDED),
        RatedTrack(Track("Skip", "C", 2002, ("rock",)), Feedback.SKIPPED),
        RatedTrack(Track("Reject", "D", 2003, ("rock",)), Feedback.REJECTED),
    ]
    metrics = feedback_discrimination(history)
    assert metrics.positives == 2
    assert metrics.negatives == 2
    assert 0.0 <= metrics.pairwise_accuracy <= 1.0
