from __future__ import annotations

import argparse

from .io import read_feedback, read_tracks
from .models import library_key_set
from .recommend import recommend_batch


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a diversity-aware Found Music recommendation batch.")
    parser.add_argument("--candidates", required=True)
    parser.add_argument("--feedback", required=True)
    parser.add_argument("--library", required=True)
    parser.add_argument("--seen", default=None, help="Optional CSV of previously served recommendations.")
    parser.add_argument("--size", type=int, default=15)
    parser.add_argument("--min-year", type=int, default=1989)
    parser.add_argument("--max-year", type=int, default=2016)
    parser.add_argument("--allow-unknown-year", action="store_true")
    args = parser.parse_args()

    candidates = read_tracks(args.candidates)
    history = read_feedback(args.feedback)
    library = read_tracks(args.library)
    seen = read_tracks(args.seen) if args.seen else []
    batch = recommend_batch(
        candidates,
        history,
        library_key_set(library),
        seen_recommendation_keys=library_key_set(seen),
        batch_size=args.size,
        min_year=args.min_year,
        max_year=args.max_year,
        allow_unknown_year=args.allow_unknown_year,
    )

    for i, item in enumerate(batch, 1):
        print(f"{i:>2}. {item.track.artist} — {item.track.title}  score={item.final_score:.3f}")
        for reason in item.reasons:
            print(f"    {reason}")


if __name__ == "__main__":
    main()
