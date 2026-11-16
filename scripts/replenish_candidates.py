"""Build an inspectable catalog candidate proposal; never auto-merge into main."""
import argparse
import json
from pathlib import Path

from found_music.candidate_discovery import replenish, search_terms


def main() -> None:
    parser = argparse.ArgumentParser(description="Replenish Found Music catalog candidates")
    parser.add_argument("--queries", default="data/catalog_queries.txt")
    parser.add_argument("--candidates", default="data/candidates.csv")
    parser.add_argument("--library", default="data/library.csv")
    parser.add_argument("--feedback", default="data/feedback.csv")
    parser.add_argument("--seen", default="data/seen_recommendations.csv")
    parser.add_argument("--target", type=int, default=1000)
    parser.add_argument("--pause", type=float, default=0.5)
    parser.add_argument("--max-per-query", type=int, default=30)
    parser.add_argument("--seed-candidates", default=None, help="Optional prior approved pool used to rebuild deterministically")
    parser.add_argument("--apply", action="store_true", help="Write the staged candidate CSV; default is dry-run")
    parser.add_argument("--report", default="data/catalog_replenishment_report.json")
    args = parser.parse_args()
    terms = search_terms(Path(args.queries).read_text(encoding="utf-8"))
    if not terms:
        parser.error("No search terms found")
    result = replenish(
        args.candidates, args.library, args.feedback, args.seen,
        terms=terms, target=args.target, apply=args.apply, pause_seconds=args.pause,
        max_per_query=args.max_per_query, seed_candidates_path=args.seed_candidates,
    )
    report = Path(args.report)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    summary = {k: v for k, v in result.items() if k != "new_provenance"}
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
