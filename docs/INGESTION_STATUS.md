# Library ingestion status

## Source corpus

The repository currently contains two ZIP source archives:

- `Music.zip`: 28 screenshots
- `Archive.zip`: 14 screenshots
- **42 screenshots total**

The GitHub Actions export job successfully extracted the full screenshot corpus.

## Phase 1 transcription: complete

All 42 screenshots have now been reviewed and merged into the structured library dataset.

Current canonical baseline:

- **370 unique known-library tracks** in `data/library.csv`
- **132 explicit feedback events** in `data/feedback.csv`
  - **112 favorite/star signals**
  - **11 added signals**
  - **9 rejected signals**

The screenshot corpus is intentionally treated as broad library evidence rather than one genre cluster. It spans rap, R&B, pop, dancehall, alternative/pop crossover and multiple eras. This breadth is the reason plain ownership is not weighted the same as a visible favorite star.

## Favorite evidence

Visible Apple Music favorite stars were preserved as `star` feedback. Existing historical feedback was retained, and an `added` record was upgraded to `star` when the later screenshot clearly showed the track favorited.

No favorite was inferred when the star icon was not visible.

## Deduplication improvements

Track-key normalization handles:

- `(feat. ...)` / `[feat. ...]`
- featured artist placed in the artist field
- `(Album Version)`
- punctuation/case normalization
- `AKA` versus dash title aliases
- collaboration artist variants and ordering

Examples include:

- `Can't Stop Me` ↔ `Can't Stop Me (feat. Ayanna Irish)`
- `Same N****s` ↔ `Same N****s (Album Version)`
- `Luchini AKA This Is It` ↔ `Luchini - This Is It`
- `Wonderful — Ashanti, Ja Rule & R. Kelly` ↔ a candidate credited to `Ja Rule feat. Ashanti`

## Discovery boundary

The recommender now enforces **1989–2016 inclusive** before scoring. Unknown-year candidates are excluded by default.

This is separate from the library itself: the library may contain newer tracks, and those can still provide taste evidence, but Found Music candidate output remains inside the requested discovery window.

## Next work

1. Build/enrich a large candidate pool with reliable title, artist and release year.
2. Run the first offline recommendation evaluation using the 370-track exclusion set.
3. Use the 132 feedback signals to compare scoring variants.
4. Add evaluation metrics for duplicate rate, hit rate, star rate, artist diversity and intra-batch similarity.
5. Tune exploration and diversity weights from measured results.
