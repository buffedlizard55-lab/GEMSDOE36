# Operative continuation brief — 29 October 2026

Read the user's full standing brief in [`README.md`](../README.md) and this handoff before work. This file records session state and does **not** replace the user-supplied protocol.

## Binding protocol

- Work only in the assigned single-method lane. The required lane-assignment paragraph is still absent; do not infer a lane or use the hypothesis screen as an assignment.
- Stop on surface-rank correlation >0.90 or final-dot overlap >70% within 3 px of any registry raster. Use the pinned prepared cache, shared `scripts/evaluate_holdout.py` and `submission_writer.py`; withhold whole buffered fault segments; compute catalogue-derived features only from visible faults; run feature-alone leakage canaries (AUC >0.90 is leakage until proven otherwise).
- Label measured scores as **HOLDOUT-DTI** with evaluator, withheld positives, and 95% CI, or **ORGANIZER-CONFIRMED** with the submission-page receipt. Historical results without receipts remain OWNER/USER-REPORTED. A projection is not a score.
- Maximum 3 experiments or 2 hours. Weekly-slot selection is separate. Never copy a prior submission except for learning.

## Current decision

**Negative. No new candidate TIFF, score estimate, holdout result, submission name/note, organizer receipt, or selected slot.** Historical TIFFs on Pages are research-only. There is no unique, validated file to download for submission.

No explicit lane was found. The literal `reg-052` lattice forces the >70%/3-px gate above threshold from 22,164 dots and forces 82.3418% overlap at the 37,654-dot historical budget. This is a non-discriminating gate, not proof that a genuinely different geology method is a duplicate; the threshold was not weakened.

## Data and evidence

- Restored and SHA-verified 30 owner-mirror files (591,020,452 bytes); prepared 19 bands; pinned-grid check passed (3,292 × 3,730, EPSG:32611). These owner mirrors are not organizer-authenticated.
- Rechecked pinned rasters: 9 requested historical-best files plus one GEMSDOE28 family comparator = 10 rasters and 8 distinct in-footprint contents. Duplicate groups: GEMSDOE25/GEMSDOE30; GEMSDOE28 h27-4 alternate/GEMSDOE31 h27-4. **The GEMSDOE28 duplicate is not its h36-1 historical-best.**
- No new holdout was run. The user-reported leaderboard 0.3195 is unverified; the old repository observation 0.4544 is not fresh and has no submission receipt.
- Three external-data hypotheses and explicit access/data limits are in [`docs/research/review-20261029.md`](../docs/research/review-20261029.md). They are proposals only; no lane was inferred.

## Continuation artifacts

- Current run card: [`evidence/session_review_20261029_run_card.json`](../evidence/session_review_20261029_run_card.json).
- Research report: [`docs/research/review-20261029.md`](../docs/research/review-20261029.md).
- Content audit: [`evidence/focus9_content_checks_20261028.json`](../evidence/focus9_content_checks_20261028.json).
- Data receipt and prepared manifest: [`data/restore_receipt.json`](../data/restore_receipt.json), [`data/prepared_manifest.json`](../data/prepared_manifest.json).
- Strict archive format regression: `scripts/audit_release.py`, `tests/test_archive_authorization.py`.

Do not run another experiment until an explicit lane is supplied and the registry rule is resolved through an authorized, predeclared process. After eligibility, preserve the shared holdout, leakage, novelty, budget, and selector gates.
