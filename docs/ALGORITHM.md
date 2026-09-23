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
