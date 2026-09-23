from __future__ import annotations

import argparse

from .io import read_feedback, read_tracks
from .recommend import recommend_batch


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a diversity-aware Found Music recommendation batch.")
    parser.add_argument("--candidates", required=True)
    parser.add_argument("--feedback", required=True)
    parser.add_argument("--library", required=True)
    parser.add_argument("--size", type=int, default=15)
    args = parser.parse_args()

    candidates = read_tracks(args.candidates)
    history = read_feedback(args.feedback)
    library = read_tracks(args.library)
    batch = recommend_batch(candidates, history, {t.key for t in library}, batch_size=args.size)

    for i, item in enumerate(batch, 1):
        print(f"{i:>2}. {item.track.artist} — {item.track.title}  score={item.final_score:.3f}")
        for reason in item.reasons:
            print(f"    {reason}")


if __name__ == "__main__":
    main()
