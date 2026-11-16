# Candidate pipeline

## Purpose

The candidate pool is deliberately broader than a nearest-neighbor playlist. Found Music works best when a batch contains multiple plausible directions rather than fifteen variants of the most recent favorite.

## Current pool

- **151 verified candidates**
- **370 known-library exclusions**
- **139 feedback events**
- questionable Apple Music matches are retained separately in `data/candidate_quarantine.csv`

Candidate records use canonical Apple Music title/artist metadata, release year and catalog genres. The recommender still treats the local library/feedback datasets as the authority for ownership and prior exposure.

## Admission rules

A candidate must:

1. resolve to a song rather than a music video;
2. have a reliable release year inside **1989–2016**;
3. not overlap a known library alias;
4. not overlap any previously rated/seen track;
5. pass catalog title/artist validation.

An Apple Music result reporting `inLibrary=true` is conservatively quarantined as duplicate-risk. It is **not** automatically written into `data/library.csv`, because that field has not been reliable enough to act as ownership truth by itself.

## Feedback semantics

- `star`: strongest positive evidence
- `added`: positive evidence
- `skipped`: mild negative evidence; tried but did not make the cut
- `rejected`: stronger negative evidence
- plain library membership: exclusion evidence, not automatically a strong preference score

Previously rated tracks are always excluded from future batches regardless of feedback class.

## Diversity controls

The default 15-song batch now uses:

- 80% exploit / 20% explore target
- MMR-style similarity penalty
- a default maximum of one track per artist
- the hard 1989–2016 boundary

The artist cap can relax only when the eligible pool is too small to fill the requested batch.

## Baseline evaluation

On the current corpus:

- feedback discrimination pairwise accuracy: **0.608**
- generated batch: **15/15 unique artists**
- decades represented: **3**
- average pairwise similarity: **0.360**

The discrimination metric is diagnostic rather than a claim of recommendation accuracy. It measures whether known positive feedback generally scores above skipped/rejected feedback when each item is held out from its own history.

The first baseline is intentionally conservative. Weight tuning should follow live Found Music outcomes rather than optimizing aggressively against this small historical sample.


## November 2026 catalog replenishment (draft PR #8)

`data/candidates.csv` now contains **1,000 catalog-year-eligible, deduplicated candidate records**. The diversified build began from the preserved 73-record baseline `data/candidates_seed.csv` and added 927 candidates from 31 distinct search queries (6,094 catalog results examined). The resulting 1,000 tracks have 338 distinct catalog artist-credit strings, and the largest single credit has 31 tracks. These are catalog records, **not** 1,000 guaranteed discoveries: unmatched recording aliases or prior ownership not present in the local datasets can still cause duplicates.

Source: [Apple iTunes Search API](https://performance-partners.apple.com/search-api), US storefront, `media=music`, `entity=song`, `attribute=artistTerm`, with a maximum 30 accepted tracks per query to encourage artist breadth. All items must have `kind=song`, valid track identity, a catalog release date within **1989–2016**, and a plausible duration. The release date supplied by iTunes can refer to an album/reissue rather than the first-ever release of a recording; this limitation should be addressed before claiming strict original-release compliance.

The new candidate inventory was validated against the currently checked-in ownership, feedback, and exposure sets. Search provenance is preserved in `data/catalog_replenishment_report.json` (query string, catalog song ID, title, artist credit, and catalog year). All existing feedback and exposure records remain intact.

### Replenishment commands

Preview (default: does not modify the candidate CSV):

```bash
python scripts/replenish_candidates.py --target 1300 --report data/catalog_replenishment_report.json
```

Stage a larger inventory locally, validate it, and review before committing:

```bash
python scripts/replenish_candidates.py --target 1300 --apply
python scripts/validate_data.py
pytest -q
```

The seed queries in `data/catalog_queries.txt` span multiple artists, genres, and eras. The script retries transient catalog failures and makes no candidate-file change if a query raises an exception before completion. It does not silently replace the feedback or ownership files.

A GitHub Actions workflow provides a pull-request live-source smoke test and a weekly/manual replenishment **proposal**. Weekly runs stage up to 300 additional candidates and upload the CSV and provenance report as artifacts. They do **not** merge automatically or update `main`; new candidates must be reviewed and committed to become part of future recommendation rounds. The workflow only becomes scheduled on the default branch after the relevant PRs are merged. Actual growth can be lower than the target if the searched catalog has too few eligible tracks.

### Known gaps

- Candidate metadata currently contains catalog genre and year, not consistent audio features.
- iTunes catalog release dates are not confirmed original track-release dates.
- A song may appear under alternate remixes, artist credits, or catalog editions not covered by local aliases.
- The seeded artist query strategy is catalog-backed but not a statistically exhaustive music-discovery method.
- Automated integration of scheduled proposal artifacts into new reviewed pull requests is a separate workflow improvement.
