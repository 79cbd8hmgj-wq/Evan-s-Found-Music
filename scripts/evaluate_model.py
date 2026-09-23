from __future__ import annotations

import argparse
import json

from found_music.evaluation import batch_metrics, feedback_discrimination, metrics_dict
from found_music.io import read_feedback, read_tracks
from found_music.models import library_key_set
from found_music.recommend import recommend_batch


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the Found Music recommender.")
    parser.add_argument("--candidates", default="data/candidates.csv")
    parser.add_argument("--feedback", default="data/feedback.csv")
    parser.add_argument("--library", default="data/library.csv")
    parser.add_argument("--size", type=int, default=15)
    args = parser.parse_args()

    candidates = read_tracks(args.candidates)
    history = read_feedback(args.feedback)
    library = read_tracks(args.library)
    batch = recommend_batch(
        candidates,
        history,
        library_key_set(library),
        batch_size=args.size,
    )

    payload = {
        "source_counts": {
            "candidates": len(candidates),
            "feedback": len(history),
            "library": len(library),
        },
        "feedback_discrimination": metrics_dict(feedback_discrimination(history)),
        "batch_metrics": metrics_dict(batch_metrics(batch)),
        "batch": [
            {
                "title": item.track.title,
                "artist": item.track.artist,
                "year": item.track.year,
                "score": round(item.final_score, 6),
                "exploration": round(item.exploration, 6),
            }
            for item in batch
        ],
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
