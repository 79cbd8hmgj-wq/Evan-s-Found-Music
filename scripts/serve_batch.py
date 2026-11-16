"""Create a reproducible recorded batch without displaying unrecorded results."""
import argparse
import json
from pathlib import Path

from found_music.serving import serve_batch


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate, record, and report a Found Music batch")
    parser.add_argument("--batch-id", required=True, help="Unique stable ID, e.g. 2026-11-round-3")
    parser.add_argument("--size", type=int, default=20)
    parser.add_argument("--candidates", default="data/candidates.csv")
    parser.add_argument("--feedback", default="data/feedback.csv")
    parser.add_argument("--library", default="data/library.csv")
    parser.add_argument("--seen", default="data/seen_recommendations.csv")
    parser.add_argument("--manifest", default=None, help="Output JSON path; defaults to data/batches/<batch-id>.json")
    args = parser.parse_args()
    path = args.manifest or str(Path("data/batches") / (args.batch_id + ".json"))
    result = serve_batch(
        args.candidates, args.feedback, args.library, args.seen,
        args.batch_id, args.size, path,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
