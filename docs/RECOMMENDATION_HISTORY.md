# Recommendation history

Found Music keeps **ownership**, **feedback**, and **exposure** as separate concepts.

## Why exposure needs its own ledger

A song can be:

- recommended and added;
- recommended and starred;
- recommended and skipped;
- recommended but not explicitly rated;
- already owned before Found Music ever suggested it.

Only storing feedback is not enough to prevent repeats. A previously served track should not reappear simply because no explicit feedback row was created for it.

`data/seen_recommendations.csv` therefore records tracks that have already been surfaced by Found Music. It is a hard exclusion set, independent of the library and feedback tables.

The initial ledger backfills the recommendation batches that are recoverable from the project records and the current conversation, including targeted, broad-discovery, duplicate-error, corrected, and recent broad rounds.

## Recommendation eligibility

A new candidate is rejected when any alias overlaps:

1. `data/library.csv` — known ownership;
2. `data/feedback.csv` — already rated/observed outcome;
3. `data/seen_recommendations.csv` — already surfaced;
4. another candidate in the same canonical pool.

This is in addition to the 1989–2016 year boundary.

## Future batches

When a live batch is shown to the user, every served track should be appended to the recommendation ledger immediately. Feedback can then be recorded separately after the user reports what was added or starred.

This prevents deduplication from depending on whether feedback has arrived yet.
