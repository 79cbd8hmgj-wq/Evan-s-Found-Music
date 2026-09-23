from __future__ import annotations

from found_music.io import read_feedback, read_tracks
from found_music.models import library_key_set


def main() -> None:
    candidates = read_tracks("data/candidates.csv")
    history = read_feedback("data/feedback.csv")
    library = read_tracks("data/library.csv")

    library_keys = library_key_set(library)
    history_keys = {
        alias for rated in history for alias in rated.track.alias_keys
    }

    errors: list[str] = []
    seen_candidate_aliases: set[str] = set()

    for track in candidates:
        if track.year is None:
            errors.append(f"candidate missing year: {track.artist} — {track.title}")
        elif not 1989 <= track.year <= 2016:
            errors.append(
                f"candidate outside 1989-2016: {track.artist} — {track.title} ({track.year})"
            )

        if track.alias_keys & library_keys:
            errors.append(f"candidate already in library: {track.artist} — {track.title}")
        if track.alias_keys & history_keys:
            errors.append(f"candidate already in feedback history: {track.artist} — {track.title}")
        if track.alias_keys & seen_candidate_aliases:
            errors.append(f"duplicate candidate alias: {track.artist} — {track.title}")
        seen_candidate_aliases.update(track.alias_keys)

    if errors:
        raise SystemExit("\n".join(errors))

    print(
        f"validated {len(candidates)} candidates against "
        f"{len(library)} library tracks and {len(history)} feedback events"
    )


if __name__ == "__main__":
    main()
