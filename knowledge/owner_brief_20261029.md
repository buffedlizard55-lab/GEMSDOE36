# Pre-run continuation brief — 29 October 2026 (historical snapshot)

Read the user's full standing brief in [`README.md`](../README.md) and this handoff before work. This file records session state and does **not** replace the user-supplied protocol.

> **Historical pre-GSEWC36 snapshot — do not use its “no experiment” statements as the latest outcome.** This brief was written before the later preregistered GSEWC36-EXP1 test. The current research outcome is in [`docs/research/hypothesis-screen-20261029.md`](../docs/research/hypothesis-screen-20261029.md) and [`evidence/gsewc36_run_card_20261029.json`](../evidence/gsewc36_run_card_20261029.json): negative HOLDOUT-DTI result, no TIFF, and no slot. The missing method-lane assignment and literal novelty gates remain unresolved. This file is retained as a time-stamped handoff, not an active run card.

## Binding protocol

- Work only in the assigned single-method lane. The required lane-assignment paragraph is still absent; do not infer a lane or use the hypothesis screen as an assignment.
- Stop on surface-rank correlation >0.90 or final-dot overlap >70% within 3 px of any registry raster. Use the pinned prepared cache, shared `scripts/evaluate_holdout.py` and `submission_writer.py`; withhold whole buffered fault segments; compute catalogue-derived features only from visible faults; run feature-alone leakage canaries (AUC >0.90 is leakage until proven otherwise).
- Label measured scores as **HOLDOUT-DTI** with evaluator, withheld positives, and 95% CI, or **ORGANIZER-CONFIRMED** with the submission-page receipt. Historical results without receipts remain OWNER/USER-REPORTED. A projection is not a score.
- Maximum 3 experiments or 2 hours. Weekly-slot selection is separate. Never copy a prior submission except for learning.

## Decision at the pre-run checkpoint (historical)

**Negative at this pre-run checkpoint. No new candidate TIFF, score estimate, holdout result, submission name/note, organizer receipt, or selected slot had yet been recorded.** Historical TIFFs on Pages are research-only. There is no unique, validated file to download for submission.

No explicit lane was found. The literal `reg-052` lattice forces the >70%/3-px gate above threshold from 22,164 dots and forces 82.3418% overlap at the 37,654-dot historical budget. This is a non-discriminating gate, not proof that a genuinely different geology method is a duplicate; the threshold was not weakened.

## Data and evidence

- Restored and SHA-verified 30 owner-mirror files (591,020,452 bytes); prepared 19 bands; the ignored numeric cache `.cache/gems_work/bands` contains 21 arrays (19 features plus footprint/labels; 957,781,264 bytes). The pinned-grid check passed (3,292 × 3,730, EPSG:32611). These owner mirrors are not organizer-authenticated.
- Rechecked pinned rasters: 9 requested historical-best files plus one GEMSDOE28 family comparator = 10 rasters and 8 distinct in-footprint contents. Duplicate groups: GEMSDOE25/GEMSDOE30; GEMSDOE28 h27-4 alternate/GEMSDOE31 h27-4. **The GEMSDOE28 duplicate is not its h36-1 historical-best.**
- At this pre-run checkpoint, no new holdout had yet run. The later GSEWC36-EXP1 is documented in the current report/run card linked above. The user-reported leaderboard 0.3195 is unverified; the old repository observation 0.4544 is not fresh and has no submission receipt.
- Three distinct proposals were ranked in the pre-run snapshot [`docs/research/review-20261029.md`](../docs/research/review-20261029.md): hydrochemical mixing front, seasonal Landsat vegetation/moisture persistence, and paired lateral channel deflection. The leading GDR working CSV has no major-ion/trace-element columns; no lane was inferred at that checkpoint. The later GSEWC test did not assign a lane.

## Continuation artifacts

- Earlier pre-run status card: [`evidence/session_review_20261029_run_card.json`](../evidence/session_review_20261029_run_card.json).
- Current research run card: [`evidence/gsewc36_run_card_20261029.json`](../evidence/gsewc36_run_card_20261029.json).
- Research report: [`docs/research/review-20261029.md`](../docs/research/review-20261029.md).
- Content audit: [`evidence/focus9_content_checks_20261028.json`](../evidence/focus9_content_checks_20261028.json).
- Data receipt and prepared manifest: [`data/restore_receipt.json`](../data/restore_receipt.json), [`data/prepared_manifest.json`](../data/prepared_manifest.json).
- Strict archive format regression: `scripts/audit_release.py`, `tests/test_archive_authorization.py`.

The single GSEWC36 research experiment does not authorize another experiment or assign a lane. Do not run further experiments until the lane is explicit and the registry rule is resolved through an authorized, predeclared process. After eligibility, preserve the shared holdout, leakage, novelty, budget, and selector gates.
