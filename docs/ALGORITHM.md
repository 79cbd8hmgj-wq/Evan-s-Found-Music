# Found Music v1 algorithm

The goal is not to find one narrow sound. It is to keep learning a broad personal taste profile while still surfacing unfamiliar music.

## Inputs

- **Library**: hard exclusion set. Owned tracks never appear as recommendations.
- **Feedback**: `star`, `added`, `rejected`, or `library`.
- **Candidate metadata**: artist, year, genres and lightweight tags.
- **Source archives**: any number of ZIP archives containing library screenshots.

The current corpus contains 42 screenshots across `Music.zip` and `Archive.zip`, transcribed into 370 unique known-library tracks.

## Scoring

1. A candidate is compared with individual feedback anchors rather than one global taste centroid.
2. Stars carry more positive weight than ordinary adds.
3. Rejections subtract score from similar candidates.
4. Only a few strongest positive and negative anchors are used for each candidate so one giant cluster cannot dominate everything.
5. Novel candidates receive a small exploration bonus.
6. Plain library membership is primarily exclusion evidence; it does not automatically become a high-weight positive signal.

This distinction matters because the library is broad. A visible favorite star is a much stronger preference signal than simply owning a track.

## Hard discovery boundary

Found Music currently uses **1989 through 2016 inclusive**.

The recommender enforces that boundary before scoring. Candidates with unknown years are excluded by default. This prevents a missing metadata field from silently allowing post-2016 recommendations.

## Deduplication

Track matching normalizes common catalog differences:

- `(feat. ...)` / `[feat. ...]`
- featured artists placed in the artist field instead of the title
- `(Album Version)`
- punctuation/case differences
- `AKA` versus dash aliases such as `Luchini AKA This Is It` / `Luchini - This Is It`
- collaboration artist ordering where at least one named artist matches

Library entries generate multiple artist aliases, so a candidate such as `Ja Rule feat. Ashanti — Wonderful` can be excluded by a library entry whose catalog artist is `Ashanti, Ja Rule & R. Kelly`.

## Batch selection

The scorer is followed by MMR-style diversification. Once a track is selected, very similar candidates become less attractive for the rest of that batch.

Default batch target:

- 80% exploit: strongest current matches.
- 20% explore: less-certain tracks that can teach us something new.

This split is intentionally configurable and should be tuned from real Found Music outcomes.

## Library ingestion

`scripts/index_music_zip.py` indexes all ZIP archives in the repository root by default. New screenshot batches can therefore be added without replacing earlier source material.

The current ingestion pass has:

1. combined both source archives;
2. transcribed all 42 screenshots;
3. normalized and deduplicated the visible library into `data/library.csv`;
4. preserved visible favorite/star evidence in `data/feedback.csv`;
5. backfilled explicit historical accept/reject outcomes from Found Music project records.

## Next milestones

1. Add candidate catalog metadata/enrichment, especially release year.
2. Build a candidate pool large enough for meaningful exploration.
3. Run offline evaluation against historical recommendation outcomes.
4. Measure hit rate, star rate, duplicate rate, artist diversity and intra-batch similarity.
5. Tune scoring weights from actual Found Music feedback instead of hand-picked constants.

## Reproducible prospective rounds (November 2026)

A batch intended for listening must be generated through the recorded serving workflow, not merely printed from the scoring CLI:

```bash
python scripts/serve_batch.py --batch-id 2026-11-round-3 --size 20
```

The command scores the currently eligible candidate pool, writes a per-batch JSON manifest under `data/batches/`, and appends every selected song to `data/seen_recommendations.csv` before printing the results. Commit **both** manifest and ledger together. The manifest records exact input SHA-256 hashes, model version, ranking, scores, timestamp, and selection parameters. Do not display an unrecorded batch as an actual issued recommendation.

The serving operation is not a remote GitHub transaction: interruption after manifest creation but before ledger update leaves a manifest that deliberately blocks accidental reissuance. Reconcile such cases before retrying with a new ID. Only a committed ledger provides protection across computers/chat sessions. The input hashes help verify which snapshot was used.

### Chronological evaluation

`scripts/backtest_rounds.py` now uses `walk_forward_backtest()`: it scores all songs in a round using only prior rounds, then reveals that round's outcomes for subsequent rounds. Its default seed is empty because `data/feedback.csv` includes future observations. The optional `--seed-feedback` argument should only be used with feedback independently confirmed to predate the earliest evaluated round.

`scripts/compare_scoring.py` compares legacy scoring and v2 under chronological updates rather than using all future feedback. Historical rows are assumed to appear in chronological round order. This ordering remains a provenance assumption for older batches without reliable dates; benchmarks are diagnostic and do not establish a randomized or controlled comparison.

The fully classified `2026-11-discovery-2` round is included. The earlier November discovery round has partially unclassified non-additions and is excluded from positive-vs-negative ranking evaluation. Incomplete genre/year metadata on recent events can weaken historical discrimination measurements.
