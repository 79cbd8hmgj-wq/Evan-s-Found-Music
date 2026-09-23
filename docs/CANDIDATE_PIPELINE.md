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
