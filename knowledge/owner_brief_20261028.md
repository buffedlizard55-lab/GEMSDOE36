# Owner brief — 28 October 2026 (read at the start of every session)

This is the operative summary of the owner's 28 October prompt. Key rules are quoted **verbatim**. The full 25 October wording stays byte-preserved in the [README](../README.md) under "Full standing owner brief". Where the two differ, this file governs. Historical scores in the brief are **owner- or user-reported** unless marked otherwise.

## Core values (quoted from the brief)

- **Maximize P(Win)** — "weigh tradeoffs, assess risk, and choose the path that maximizes the probability that Arena succeeds."
- **Own the Outcome** — "treat failure and success as signals and use them to improve."

## Session checklist

1. Read this file and the latest review: [`docs/research/review-20261028-session-b.md`](../docs/research/review-20261028-session-b.md).
2. Check the blockers in §Status before any experiment.
3. Restore data by SHA-pinned mirror and check pins: `scripts/restore_data.py --group core|scored|external`, then `scripts/prepare_data.py`.
4. Work on `arena/9c1525b7-gemsdoe36` only.
5. Label every number as **HOLDOUT-DTI** (evaluator version, withheld positives, 95% CI), **ORGANIZER-CONFIRMED** (from a submission-page receipt), or **OWNER/USER-REPORTED**. A projection is never written as a score.

## Operative requirements and current status

| # | Requirement (quoted or closely paraphrased) | Status, 28 Oct 2026 | Evidence |
|---|---|---|---|
| R1 | "an executive summary on every site that is clear and obvious which is the best submission" | **Partly met.** The nine-site page now names the highest reported file (GEMSDOE32 B2, 0.2778 OWNER-REPORTED) and its verdict. The verdict is DO NOT SUBMIT. | [executive guide](../docs/executive-summary.html) |
| R2 | "a table … what file to download, what the estimate score is, and whether it is a unique submission" | **Met as negative.** Estimate: *not estimable*. Unique vs the other eight: **NO** for all nine. | [nine-site table](../docs/executive-summary.html#focus9-decision) |
| R3 | "MUST GENERATE A UNIQUE TIF SUBMISSION … IT MUST BE OBVIOUS WHETHER IT IS OK TO DOWNLOAD AND SUBMIT" | **Not met — blocked.** No candidate. The lane paragraph is missing and the literal gate fails for any candidate above 22,163 dots. The page says plainly: **do not submit**. | [run card](../evidence/session_review_20261028b_run_card.json) |
| R4 | Parallel protocol: "Your lane is the single method paragraph below." | **Blocked.** No method paragraph is in the brief. | review §1A |
| R5 | Literal gate: rank-correlation ≤ 0.90 and ≤ 70% of dots within 3 px of any registry raster | **Fails by construction** above 22,163 dots (reg-052 covers 99.87% of the footprint). Decision needed. | review §1B and §5 |
| R6 | Holdout: "withhold whole fault segments with a buffer … pooled DTI (alpha 0.2, beta 0.8, 300 m triangular kernel)" | **Metric verified** against the official formula and worked example (recomputed 0.6027 → 0.60). **No holdout run** this session. | [metric](../src/gems/metric.py), [official page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) |
| R7 | Leakage canary: "AUC above 0.90 means leakage until proven otherwise" | **Not run** (no candidate feature). | — |
| R8 | Run card with validator output (no NaN inside footprint, values in [0,1], CRS/shape/transform match) | **Validator fixed** (filename bypass removed, regression test added). Run card written; no candidate, so no candidate hash. | [CLI test](../tests/test_validate_submission_cli.py) |
| R9 | Budget: "Stop after [3] experiments or [2] hours" | **0 of 3 experiments used.** Time was not recorded precisely, so no elapsed-time claim is made. | run card |
| R10 | "Do not pick submissions: promotion to a real slot is a separate selector step" | **Respected.** No slot used or approved. | run card `slot_used: false` |
| R11 | "Work line by line verifying from official verified trusted sources, provide links" | **Done for the claims listed in the review §9.** Items not fetched are labelled. | [review §9](../docs/research/review-20261028-session-b.md) |
| R12 | "Create a pull request and then merge … onto the main" | Done in this session (see the PR link in the final report). | GitHub |
| R13 | Put the prompt into the README and read it every session | **Met.** README links this file and the full 25 Oct text. | [README](../README.md) |

## Standing rules (quoted)

- "DO NOT COPY A PREVIOUS SUBMISSION UNLESS IT'S FOR LEARNING AND EDUCATION."
- "A lot of sites mention inspection only and a human inspector, but the inspection needs to be done through the project and needs to be validated for submission without human intervention." — validation is automated, and no human inspection is part of the gate.
- "Negative results are deliverables."
- "No hallucinations … Verify line by line."

## Official facts that bind the work (checked 28 Oct 2026)

- Metric: distance-weighted Tversky, α = 0.2 (FP), β = 0.8 (FN), 300 m triangular kernel. ([problem page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/))
- Format: single-band float32 GeoTIFF, EPSG:32611, 100 m, same bounds as training data, values in [0,1], outside the bounds null or NaN. ([problem page, submission format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/))
- Rules: a single raster layer at 100 m; "three submissions per week"; "Participants will submit a single entry"; generative-AI use must be disclosed in the narrative. ([official rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf))
- Public leaderboard top: 0.4544 on 28 Oct 2026. This is a public-split value, not a receipt for any file. ([leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/))

## Irregularities that a future session must not repeat

- A file whose name says "-zeros.tif" must not be validated more leniently than the same bytes under another name. (Fixed.)
- Identical rasters submitted under different sites are duplicates, even with different outside encodings. (GEMSDOE25 and GEMSDOE30.)
- Owner-reported scores must never be rendered as organizer-confirmed.
