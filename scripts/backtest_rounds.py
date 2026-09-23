from __future__ import annotations

import argparse
import json

from found_music.backtest import backtest_rounds, read_historical_rounds, result_dict
from found_music.io import read_feedback


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Backtest Found Music against historical recommendation rounds."
    )
    parser.add_argument("--rounds", default="data/historical_rounds.csv")
    parser.add_argument("--feedback", default="data/feedback.csv")
    args = parser.parse_args()

    rounds = read_historical_rounds(args.rounds)
    history = read_feedback(args.feedback)
    result = backtest_rounds(rounds, history)
    print(json.dumps(result_dict(result), indent=2))


if __name__ == "__main__":
    main()
