# Library ingestion status

## Source corpus

The repository currently contains two ZIP source archives:

- `Music.zip`: 28 screenshots
- `Archive.zip`: 14 screenshots

The GitHub Actions export job successfully extracted **42 total screenshots** into the `library-images` workflow artifact.

## Phase 1 transcription

This pass establishes a canonical `data/library.csv` and `data/feedback.csv`.

Current structured baseline:

- **53 known library tracks** in `data/library.csv`
- **37 explicit feedback events** in `data/feedback.csv`
- transcription from `Music.zip` screenshots 001–004
- confirmed historical Found Music accepts/stars/rejections backfilled from project records

The first four screenshots include records spanning Ginuwine, Mase, Nas, Eve, Fat Joe, 50 Cent, Fabolous, Lloyd Banks, Mario, Amerie, Common-era discoveries and broader pop/R&B/rap material. They are intentionally treated as library evidence, not as a single style cluster.

## Deduplication improvement

Track-key normalization now handles common screenshot/catalog variations:

- `(feat. ...)` / `[feat. ...]`
- featured artist placed in the artist field
- `(Album Version)`
- `AKA` versus dash title aliases such as `Luchini AKA This Is It` / `Luchini - This Is It`

This matters because the exclusion database should reject a known song even when Apple Music or a recommendation source formats it differently.

## Remaining work

1. Transcribe screenshots 005–028 from `Music.zip`.
2. Transcribe screenshots 001–014 from `Archive.zip`.
3. Merge and deduplicate all tracks into `data/library.csv`.
4. Enrich structured tracks with catalog metadata without changing ownership evidence.
5. Backfill additional historic feedback where the source records make the outcome explicit.
6. Run the first recommendation evaluation against the expanded exclusion set.
