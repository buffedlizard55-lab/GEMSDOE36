# GVSC-36 three-pass review — 2026-10-26 UTC

Branch: `arena/20b1a132-gemsdoe36`. This is an auditable record of the completed three-arm research run, not a submission authorization. Preregistration window: `2026-10-26T16:26:08Z` to `2026-10-26T18:23:13Z` (7,024.26 seconds; under the 7,200-second cap). Three candidate arms were run; no portal slot was spent.

## Pass 1 — inspect the project and preregister

- Read the repository decision, current run cards, nine-site byte audit, shared template pins, input manifest, historical H24-GVC1 record, novelty registry and test commands.
- Proposed four ranked hypotheses in `docs/research/preregistration-gvsc36-20261026.md`; selected a geothermal vent/conduit back-projection lane using pinned owner-mirrored GDR 1391 archives plus the existing 59-feature baseline.
- The preregistration records its own implementation plan, limits and official source leads. However, a retrospective comparison identifies meaningful conceptual overlap with prior GEMSDOE24 H24-GVC1 (geothermal vents, 2 m temperature probes, geothermometers, upflow and lineaments). This prevents a clean claim that the scientific lane itself was entirely untried; see IR-GVSC36-01. Historical H24-GVC1 `0.148763` is **HOLDOUT-DTI**, not an organizer score.
- No direct DrivenData, USGS or DOE GDR download was performed in this environment. The pinned owner mirror hashes were verified; this does not authenticate upstream provenance.

## Pass 2 — implement and run the frozen experiments

- Implemented `src/gemsdoe36/gvsc_features.py` and `scripts/run_gvsc36.py`, using the shared `SegmentHoldout`, `gems.submission` writer/validator, and `gems.novelty.compare_registry` rather than forking the metric/writer.
- Built 89 feature columns, testing individual features with the holdout canary. Result: 89 checked; maximum symmetric AUC 0.668429 (`sa_worm_piedmont`), below 0.90.
- Completed exactly EXP-1, EXP-2 and EXP-3; B0 was the matched control. Candidate arm results are reported only as **HOLDOUT-DTI**, `gems-segment-pooled-v1`, 60,988 withheld positives, 1,500 m buffer, pooled alpha 0.2 / beta 0.8 / 300 m triangular kernel, with 95% block-bootstrap intervals. Best EXP-3: 0.158855 [0.145456, 0.173084]; paired difference to same-run B0 +0.030740 [ +0.022172, +0.039694 ].
- The recorded end-to-end preregistration-to-run-card wall interval is 7,024.26 seconds of the 7,200-second cap; no further experiment is allowed this session. See `evidence/gvsc36_walltime_accounting_20261026.json`.
- Frozen preregistration/code feature-count discrepancy: the plan says 73 LiDAR-blind features; executable code contains 74 (IR-GVSC36-04). No feature/hyperparameter changes were made after reading holdout results.

## Pass 3 — artifact, gate and user-facing checks

- Emitted `docs/downloads/gemsdoe36-gvsc36-exp3-20261026-5fb822bdfb60-zeros.tif`, SHA-256 `ad809c2b0919d4b71afee80f0b4827aa9ad4ecd8c66507109a3d3f7292cac1a1`, and one-TIFF ZIP. Independent local validators pass exact grid, single-band float32, all-grid finite `[0,1]`, and template alignment.
- Pre-placement surface rank screen passes (maximum absolute rho 0.496905 across 206 registry/local comparators). Final-dot uniqueness fails: 94.60% overlap with GEMSDOE22 H23-B, 94.11% with GEMSDOE67 OVTR, and 99.62% maximum literal all-entry overlap. Focus-nine maximum is 69.02%; focus-only evidence is not sufficient to pass the all-registry rule.
- **IR-GVSC36-03:** The completed runner placed dots and wrote the TIFF before running the surface novelty comparison. The surface was not tuned in response, but required screening order was violated; the run remains negative. The code has since been reordered for a future run, but that does not retroactively cure this execution.
- Both Pages subpages now show the GVSC download, holdout evidence, local validation and explicit `DO NOT SUBMIT`. This update does not replace the MTO-36 current-run status or override its separate audit.
- Artifact-only verifier: `python scripts/verify_gvsc36_release.py` PASS (verdict negative, research download allowed, submit false). Full suite: **115 passed, 1 skipped** (PyTorch unavailable for the orientation test). Ruff: PASS. `python scripts/check_site.py`: PASS. `git diff --check`: PASS. These checks cannot test organizer acceptance.

## Outcome / gates

| Gate | Result |
|---|---|
| Leakage canary | PASS (89 features; max symmetric AUC 0.668429) |
| Matched holdout improvement | PASS (+0.030740 HOLDOUT-DTI; paired 95% CI entirely above zero) |
| Archived group reference | PASS numerically (EXP-3 HOLDOUT-DTI 0.158855 vs recorded 0.148763 HOLDOUT-DTI; reference is recorded, not recomputed) |
| Format, strict range, CRS/shape/transform | PASS locally |
| Surface uniqueness screen | PASS (max absolute rank correlation 0.496905) |
| Focus-nine overlap | PASS (69.02% maximum) |
| Expanded competing-method overlap | **FAIL** (94.60% max) |
| Literal all-entry overlap | **FAIL** (99.62% max) |
| Scientific hypothesis distinctness | **UNRESOLVED / concern** (H24-GVC1 overlap) |
| Surface-before-placement chronology | **FAIL** (logged; no post-hoc changes) |
| Organizer score/portal acceptance | **NONE / NOT TESTED** |

Final verdict `negative`, research download only, no slot selected or used. This outcome neither forecasts nor estimates the competition score. The current run card preserves the full row-level evidence, including the failing registry rows and provenance caveats.
