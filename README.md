# Evan's Found Music

A personal music-discovery system built around one rule: **learn the whole taste profile without over-filtering around the latest favorite.**

The repository contains multiple screenshot archives of the music library (`Music.zip`, `Archive.zip`, and future ZIP additions) plus a diversity-aware recommendation engine. All source archives are treated as one library corpus and deduplicated into a canonical exclusion set.

## Current data

- **42 original library screenshots** indexed and transcribed, plus the November 2026 listening screenshots and round outcomes reconciled into CSV data
- **426 library rows** in `data/library.csv`
- **228 feedback rows** in `data/feedback.csv`
  - stars/favorites and additions as positive evidence
  - explicit rejections as stronger negatives
  - skipped recommendations as mild negatives
- **1,000 catalog-year-eligible candidate records** in `data/candidates.csv`

Visible Apple Music favorite stars are treated as strong positive taste evidence. Ordinary library membership is used primarily for deduplication and does not automatically receive the same weight.

## What v1 does

- excludes known library tracks, including common catalog-format variants;
- learns separately from starred, added, skipped and rejected songs;
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
  --seen data/seen_recommendations.csv \
  --size 15
```

`data/candidates.csv` and `data/library.csv` use:

```text
title,artist,year,genres,tags
```

Candidate tracks without a known year are excluded by default so the 1989–2016 boundary cannot be bypassed accidentally. Use `--allow-unknown-year` only for deliberate testing.

See `docs/ALGORITHM.md`, `docs/INGESTION_STATUS.md`, and `docs/CANDIDATE_PIPELINE.md` for design and data status.

## November 2026 P1 reconciliation

The current dataset includes 44 user-confirmed latest library additions (19 starred), plus two 20-song discovery rounds. Round 1 recorded 6 adds including 2 stars and 4 confirmed already-owned recommendations; its other 10 outcomes are not assumed to be explicit skips. Round 2 recorded 8 adds including 3 stars and 12 explicit skips. Where an item already existed, its evidence was retained and stronger explicit feedback promoted rather than duplicated by exact local song key.

The formerly ineligible entries in the candidate pool were moved to `data/candidate_quarantine.csv` with `already-known-or-served` reasons. These historical records remain inspectable and are not deleted. The candidate pool has been expanded to 1,000 records using catalog search with per-query caps. Catalog dates and version identities still require careful interpretation.

The `found-music` CLI now reads `data/seen_recommendations.csv` automatically; an explicit `--seen` path overrides it. The CLI errors if that ledger is unavailable rather than silently serving repeats. Tracks generated manually outside the CLI are **not** evidence of measured performance of this engine. New recommendation batches must record exposure when issued and collect outcomes afterward.

A number of November screenshot-derived entries lack verified release year and/or genre metadata. Their ownership and feedback status are explicit, but music similarity scores should not be interpreted as fully calibrated until metadata is enriched.

## Issue a reproducible discovery round

For future recommendations that will actually be presented to the listener, use:

```bash
python scripts/validate_data.py
python scripts/backtest_rounds.py
python scripts/compare_scoring.py
python scripts/serve_batch.py --batch-id 2026-11-round-3 --size 20
```

The serving command **records** the issued tracks in `data/seen_recommendations.csv` and produces a scored, timestamped manifest at `data/batches/<batch-id>.json`. Commit both files as one change before sharing the batch outside the current working tree. Do not rerun the same batch ID. The CLI's older `found-music` command can inspect rankings but does **not** record them; do not use it to issue live recommendations.

This project distinguishes an *offline ranking comparison* from a *prospective acceptance rate*. Older rounds are backtested in their file order with no presumed pre-existing seed, because the accumulated feedback CSV contains future information. The system cannot claim improving prospective performance until multiple recorded, outcome-complete engine-generated rounds have been evaluated.

Current `data/historical_rounds.csv` includes the fully classified November Round 2. The other recent round contains confirmed additions and ownership duplicates but no explicit ratings for the remaining non-additions, so it is not treated as a fully labelled comparison.

The initial 1,000-candidate inventory is in place. Continue replenishing and improving recording-identity and release-year verification before treating this as a fully comprehensive discovery catalog.

## Catalog candidate replenishment

The candidate-replenishment pipeline reads the queries in `data/catalog_queries.txt`, searches Apple's public iTunes catalog (US storefront), filters for catalog years 1989–2016, excludes known library/feedback/served songs, and caps accepted candidates per query to protect breadth.

```bash
# Preview the next 300 candidates without changing the inventory
python scripts/replenish_candidates.py --target 1300

# Generate and validate an actual proposal
python scripts/replenish_candidates.py --target 1300 --apply
python scripts/validate_data.py
pytest -q
```

The initial diversified build preserved the 73 baseline eligible records, imported 927 new entries from 31 search queries, and now contains 1,000 records representing 338 distinct credited artist names. See `data/catalog_replenishment_report.json` and `docs/CANDIDATE_PIPELINE.md` for provenance and caveats. Catalog release year is not necessarily the recording's original release year.

`.github/workflows/catalog-candidates.yml` creates live catalog proposals in CI and weekly once deployed on the default branch. These are artifacts for review, not auto-merged library mutations.
