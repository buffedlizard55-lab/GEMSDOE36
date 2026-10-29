# Repository review — 29 October 2026

## Verdict

**Negative: no new TIFF is authorized or produced.** The current-run manifest remains `ok_to_download_and_submit: false`; no holdout result, candidate hash, or organizer receipt supports promotion. The supplied parallel-run rule requires stopping when either literal novelty condition fails. The 28 October review documents a missing method paragraph and a registry-coverage bound that forces >70% within-3-pixel overlap for candidates at or above 22,164 dots. The repository's own pairwise audit says all 72 directed pairs among the nine focus rasters exceed 70% overlap. Therefore changing a filename or thinning a previous raster would not meet the stated lane protocol and would not be a defensible submission.

## Executive readout on requested focus sites

The highest submission score in the supplied records is GEMSDOE32 B2, **0.2778 OWNER-REPORTED** (not organizer-confirmed; no submission receipt is linked). Repository forensics reproduced its raster lineage: 37,654 dots, a strict subset of the GEMSDOE25 44,090-dot raster, with 6,436 dots removed and none added; removed dots are catalogue-adjacent. This gives a plausible metric-based explanation for the reported lift: reducing predictions on already catalogued faults can reduce false-positive weight under a task targeting uncatalogued faults. It is not evidence that the score is reproducible or that a further lift is achievable. The next-highest cited GEMSDOE36 Anderson result is 0.2750 OWNER-REPORTED. GEMSDOE25 and GEMSDOE30 are content-identical in the footprint despite different outside encodings; they are not distinct strategies. Other nine-site files have overlap and/or correlation that violates the literal protocol. Consult `docs/executive-summary.html` for the per-site table and its explicit DO NOT SUBMIT statuses.

## Hypothesis queue already in the repo

The three ranked leads and their layers, physical signatures, alternative mimics, implementation differences, and cost are in `docs/research/review-20261028-session-b.md` §3: (1) catalogue-flank exclusion using the cached catalogue (lowest implementation cost); (2) multi-contact displacement consensus using cached DEM/geologic contacts; (3) persistent groundwater-head discontinuity using official well observations. The groundwater coverage was not established; Landsat thermal persistence was likewise not fetched or verified. No new external-data hypothesis is represented as ready to test. No holdout experiment ran in this review because the literal novelty gate is a stop condition, not because a projection or leaderboard estimate was substituted for a holdout result.

## Code review finding fixed

`scripts/audit_release.py` previously relaxed the outside-footprint rule based on `-zeros.tif` or `atvr36` in a filename. This repeated the exact class of validator bypass already removed from the submission CLI. Archive format auditing now applies the strict outside-footprint rule uniformly, via `validate_archive_raster`; a regression test proves the same strict option is used for both historical filename patterns. This is only a format-audit fix and grants no candidate or slot authorization.

Also corrected the owner brief's stale branch name. It now refers to this checkout's active branch, `arena/7be5e97f-gemsdoe36`.

## Three review passes

1. **Requirements/repo pass:** read the full README, owner brief, current run manifest, latest run card, nine-site evidence, and latest research review. Existing negative release status and evidence take precedence over historical score claims.
2. **Bug/edge-case pass:** found archive auditing still had filename-based zeros exceptions even though the submission validator's bypass was fixed. Removed the exception and added focused coverage; no candidate files were modified.
3. **Final validation pass:** `pytest`: **191 passed, 8 skipped**; skipped because Torch or restored/pinned project data were absent in this checkout. Ruff passed, `scripts/check_site.py` passed, `compileall` passed, and `git diff --check` passed. The data-dependent focus re-fetch and full raster/holdout checks were not rerun because the raw template/labels and registry rasters were not restored here.

## Remaining blockers / next work

- The missing single-method lane paragraph and infeasible literal 70%/3-px rule require an explicit protocol resolution before a candidate can be evaluated for promotion. Do not silently alter thresholds after seeing a candidate.
- Restore SHA-pinned competition inputs and registry rasters before data-dependent audits. Mirrors are owner-provided, not organizer-authenticated; original DrivenData data page requires login.
- Run the feature-alone leakage canary and buffered whole-segment holdout only after the protocol is resolved, within the stated 3-experiment / 2-hour budget.
- Verify official submission portal behavior for outside-footprint NaNs and [0,1] range with a rejected-file trace or organizer documentation; current error cause is unknown.
- Continue to label all historical listed scores OWNER-REPORTED unless a submission-page receipt establishes ORGANIZER-CONFIRMED status.
- No leaderboard score is projected from holdout. No slot was used or selected.

## Trusted references for manual review

- Official competition problem, metric, and format: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
- Official competition rules PDF: https://docs.nlr.gov/docs/fy26osti/96647.pdf
- Official public leaderboard (time-sensitive): https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/
- Reference implementation: https://github.com/drivendataorg/gems-prize-reference-solution
- USGS GeoDAWN survey information: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and

These sources do not independently verify owner-hosted raster scores or hashes.
