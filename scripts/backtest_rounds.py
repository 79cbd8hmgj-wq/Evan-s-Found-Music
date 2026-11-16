from __future__ import annotations

import argparse
import json

from found_music.backtest import walk_forward_backtest, read_historical_rounds, result_dict
from found_music.io import read_feedback


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Backtest Found Music against historical recommendation rounds."
    )
    parser.add_argument("--rounds", default="data/historical_rounds.csv")
    parser.add_argument("--seed-feedback", default=None, help="Only use feedback verified to predate the FIRST historical round.")
    args = parser.parse_args()

    rounds = read_historical_rounds(args.rounds)
    history = read_feedback(args.seed_feedback) if args.seed_feedback else []
    result = walk_forward_backtest(rounds, history)
    print(json.dumps(result_dict(result), indent=2))


if __name__ == "__main__":
    main()
