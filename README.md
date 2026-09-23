# Evan's Found Music

A personal music-discovery system built around one rule: **learn the whole taste profile without over-filtering around the latest favorite.**

The repository currently contains the source screenshot archive (`Music.zip`) plus the first implementation of a diversity-aware recommendation engine.

## What v1 does

- excludes known library tracks;
- learns from starred, added and rejected recommendations;
- scores candidates against multiple individual taste anchors instead of one narrow centroid;
- reserves room for exploration;
- diversifies each batch so one sound, artist or lane does not take over.

## Quick start

```bash
python -m pip install -e '.[dev]'
pytest

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
