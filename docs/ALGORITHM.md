# Found Music v1 algorithm

The goal is not to find one narrow sound. It is to keep learning a broad personal taste profile while still surfacing unfamiliar music.

## Inputs

- **Library**: hard exclusion set. Owned tracks never appear as recommendations.
- **Feedback**: `star`, `added`, `rejected`, or `library`.
- **Candidate metadata**: artist, year, genres and lightweight tags.

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

## Next milestones

1. Convert the screenshots in `Music.zip` into a structured library CSV.
2. Backfill previous recommendation outcomes from the chat history.
3. Add a candidate metadata/enrichment pipeline.
4. Measure hit rate, star rate, duplicate rate, artist diversity and intra-batch similarity.
5. Tune weights from actual feedback instead of hand-picked constants.
