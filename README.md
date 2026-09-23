# Evan's Found Music

A personal music-discovery system built around one rule: **learn the whole taste profile without over-filtering around the latest favorite.**

The repository contains multiple screenshot archives of the music library (`Music.zip`, `Archive.zip`, and future ZIP additions) plus a diversity-aware recommendation engine. All source archives are treated as one library corpus and deduplicated into a canonical exclusion set.

## Current data

- **42 library screenshots** indexed and transcribed
- **370 unique known-library tracks** in `data/library.csv`
- **132 explicit feedback signals** in `data/feedback.csv`
  - 112 favorites/stars
  - 11 additions
  - 9 rejections

Visible Apple Music favorite stars are treated as strong positive taste evidence. Ordinary library membership is used primarily for deduplication and does not automatically receive the same weight.

## What v1 does

- excludes known library tracks, including common catalog-format variants;
- learns separately from starred, added and rejected songs;
- scores candidates against multiple individual taste anchors instead of one narrow centroid;
- reserves room for exploration;
- diversifies each batch so one sound, artist or lane does not take over;
- enforces the Found Music **1989–2016** discovery boundary by default;
- indexes any number of ZIP-based library sources.

## Quick start

```bash
python -m pip install -e '.[dev]'
pytest

# Index every ZIP archive in the repository root.
python scripts/index_music_zip.py

found-music \
  --candidates data/candidates.csv \
  --feedback data/feedback.csv \
  --library data/library.csv \
  --size 15
```

`data/candidates.csv` and `data/library.csv` use:

```text
title,artist,year,genres,tags
```

Candidate tracks without a known year are excluded by default so the 1989–2016 boundary cannot be bypassed accidentally. Use `--allow-unknown-year` only for deliberate testing.

See `docs/ALGORITHM.md` and `docs/INGESTION_STATUS.md` for design and data status.
