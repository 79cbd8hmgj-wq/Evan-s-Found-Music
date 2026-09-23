# Evan's Found Music

A personal music-discovery system built around one rule: **learn the whole taste profile without over-filtering around the latest favorite.**

The repository contains multiple screenshot archives of the music library (`Music.zip`, `Archive.zip`, and future ZIP additions) plus the first implementation of a diversity-aware recommendation engine. All source archives are treated as one library corpus and deduplicated after transcription.

## What v1 does

- excludes known library tracks;
- learns from starred, added and rejected recommendations;
- scores candidates against multiple individual taste anchors instead of one narrow centroid;
- reserves room for exploration;
- diversifies each batch so one sound, artist or lane does not take over;
- indexes any number of ZIP-based library sources.

## Quick start

```bash
python -m pip install -e '.[dev]'
pytest

# Index every ZIP archive in the repository root.
python scripts/index_music_zip.py

found-music \
  --candidates data/candidates.csv \
  --feedback data/feedback_seed.csv \
  --library data/library.csv \
  --size 15
```

`data/candidates.csv` and `data/library.csv` use the columns:

```text
title,artist,year,genres,tags
```

Pipe-delimit multiple genres or tags inside one field.

See `docs/ALGORITHM.md` for the recommendation design and next milestones.
