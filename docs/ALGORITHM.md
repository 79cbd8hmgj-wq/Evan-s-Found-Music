# Found Music v1 algorithm

The goal is not to find one narrow sound. It is to keep learning a broad personal taste profile while still surfacing unfamiliar music.

## Inputs

- **Library**: hard exclusion set. Owned tracks never appear as recommendations.
- **Feedback**: `star`, `added`, `rejected`, or `library`.
- **Candidate metadata**: artist, year, genres and lightweight tags.
- **Source archives**: any number of ZIP archives containing library screenshots. They are combined into one deduplicated library corpus after transcription.

## Scoring

1. A candidate is compared with individual feedback anchors rather than one global taste centroid.
2. Stars carry more positive weight than ordinary adds.
3. Rejections subtract score from similar candidates.
4. Only a few strongest positive and negative anchors are used for each candidate so one giant cluster cannot dominate everything.
5. Novel candidates receive a small exploration bonus.

## Batch selection

The scorer is followed by MMR-style diversification. Once a track is selected, very similar candidates become less attractive for the rest of that batch.

Default batch target:

- 80% exploit: strongest current matches.
- 20% explore: less-certain tracks that can teach us something new.

This split is intentionally configurable and should be tuned from real Found Music outcomes, not assumed permanently.

## Library ingestion

`scripts/index_music_zip.py` indexes all ZIP archives in the repository root by default. This means new screenshot batches can be added without replacing or renaming earlier source material.

The transcription stage should:

1. combine screenshots from every archive;
2. normalize artist/title spelling;
3. collapse duplicate tracks appearing in multiple screenshots or archives;
4. preserve star/favorite evidence when visible;
5. produce one canonical `data/library.csv` used as the hard exclusion set.

## Next milestones

1. Convert screenshots across all source ZIP archives into a structured, deduplicated library CSV.
2. Backfill previous recommendation outcomes from the chat history.
3. Add a candidate metadata/enrichment pipeline.
4. Measure hit rate, star rate, duplicate rate, artist diversity and intra-batch similarity.
5. Tune weights from actual feedback instead of hand-picked constants.
