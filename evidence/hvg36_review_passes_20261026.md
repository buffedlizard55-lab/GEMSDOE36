# Three-Pass Verification Ledger — Lane `HVG-36` & 9-Site Executive Summary (`2026-10-26`)

- **Repository**: `buffedlizard55-lab/GEMSDOE36`
- **Branch**: `arena/d98aabea-gemsdoe36`
- **Lane**: `HVG-36` (*Hydrothermal-Vent Structural-Conduit & Cross-Scale Potential-Field Dipole Ensemble*)
- **Verdict**: `negative` (`DOWNLOAD: YES (research)` · `DO NOT SUBMIT`)

---

## Pass 1 — Plan, Preregister, Implement, and Verify

1. **Preregistration & Hypothesis Ranking (`docs/research/preregistration-hvg36-20261026.md`, `evidence/hvg36_preregistration_20261026.json`)**:
   - Ranked 4 candidate geological hypotheses (`HVG-36-A`, `HVG-36-B`, `HVG-36-C`, `HVG-36-D`) before running any experiment, naming exact layers (`01_tmi`, `02_rtp`, `04_gravity_2025`, `05–07` radiometrics, `08_dem`, `10_earthquakes`, `12_bouguer_grav_anom`, `13_iso_grav_anom`, `14_geotherm_points`, `15_depth_to_base_surf`, `17_cond_surf`, `18_strain_2nd_inv`, `19_quaternary_vents`, plus USGS GeoDAWN `TMI_up150` / `tilt`), physical signatures, off-catalogue blind-fault mechanisms, named non-fault mimics, and implementation vs expected DTI rank.
2. **Feature Engineering & Leakage Canary (`src/gemsdoe36/hvg_features.py`, `evidence/hvg36_leakage_canary_20261026.json`)**:
   - Built 12 static + 2 fold-safe out-of-fold regressed residual features on the `5,167,373` valid pixels (`dist_known_fault_px` strictly banned and stripped on load).
   - Ran single-feature leakage canary via `gems.holdout.SegmentHoldout.canary()`: **all 14 features passed** (`max two-polarity ROC-AUC = 0.6440 <= 0.90` on `hvg_seismic_strain_corridor`).
3. **4-Fold `SegmentHoldout` Experiments & Unique GeoTIFF Emission (`scripts/run_hvg36_experiment.py`, `evidence/hvg36_holdout_experiments_20261026.json`, `evidence/hvg36_run_card_20261026.json`)**:
   - Evaluated `B0_base59` (`0.133169`, `[0.121427, 0.145472]`), `EXP-1` (`0.135759`, `[0.123271, 0.148461]`, winning `3/4` folds and setting a new `GEMSDOE36` holdout record), `EXP-2` (`0.133383`), and `EXP-3` (`0.133757`) on `gems-segment-pooled-v1` (`60,988` withheld positives, 1.5 km buffer).
   - Generated unique whole-array `[0, 1]` GeoTIFF `docs/downloads/gemsdoe36-hvg36-vent-dipole-20261026-b3ee97873192-zeros.tif` (`37,654` dots, scored content ID `b3ee97873192`, SHA-256 `85d56b03aff18f72d85de9c1e1ca02a2274263fffcd95aa0a6edac7bc9a08596`) and single-TIFF `.zip` (`2809617a47d4985311447ffa6c5b76dd7885fd6be887c197de8183d09a53ca61`).
4. **9-Site Executive Summary Table & Forensic Diagnostics (`evidence/focus_sites_9repo_summary_20261026.json`, `scripts/build_mto_site.py`)**:
   - Computed exact in-sample `SegmentHoldout` diagnostics for all 9 focus-site historical rasters (`GEMSDOE24..36`), proving why `GEMSDOE32 B2` (`0.006708` against `labels.tif` because of its `> 2 px` known-fault moat) achieved `0.2778` on the blind test set (`existing_faults.tif` masked).
   - Updated `docs/index.html`, `docs/executive-summary.html`, and `README.md` with clear, obvious executive summary banners and the full 9-site table listing downloadable files, estimated `HOLDOUT-DTI` scores vs `OWNER-REPORTED` live scores, and uniqueness across the 9 focus sites and 203-raster registry.

---

## Pass 2 — Code Review, Edge-Case Fixes, and Test Suite Verification

1. **Memory Footprint Fix (`src/gemsdoe36/hvg_features.py`)**:
   - Streaming 1–2 bands at a time and freeing intermediate `(3730, 3292)` float32 arrays avoided OOM pressure on the 3.9 GB sandbox and cached each feature column cleanly in `.cache/h36/`.
2. **Backwards-Compatible Signature Fix (`scripts/build_mto_site.py`, `tests/test_mto_release.py`)**:
   - Discovered during `pytest -q` that `tests/test_mto_release.py` calls `ensure_status(card, ledger)` with 2 positional arguments. Updated `ensure_status(card: dict, ledger: dict, hvg: dict | None = None)` so existing unit tests and the new `HVG-36` release check both pass.
3. **Linter & Import Cleanup (`scripts/run_hvg36_experiment.py`, `tests/test_hvg36.py`)**:
   - Fixed import sorting (`I001`) and unused imports (`F401`) caught by `ruff check src scripts tests`.
4. **Unit & Release Gate Suite**:
   - `pytest -q`: **110 passed, 1 skipped** (including `tests/test_hvg36.py` and `tests/test_mto_release.py`).
   - `ruff check src scripts tests`: **All checks passed!**
   - `scripts/check_site.py`, `scripts/audit_focus_sources.py`, `scripts/verify_mto_release.py`, `scripts/verify_release_gate.py`: **All passed with 0 errors.**

---

## Pass 3 — Prompt Compliance & Final Audit Against All User Requirements

| Prompt Requirement | Verification Status | Where Verified |
|---|---|---|
| Focus on highest-scoring submissions from `GEMSDOE24`, `25`, `27`, `28`, `30`, `31`, `32`, `33`, `36` | **PASS** — All 9 sites audited byte-for-byte with SHA-256, dot counts, XOR diffs, and `SegmentHoldout` diagnostics | `docs/index.html`, `docs/executive-summary.html`, `README.md`, `evidence/focus_sites_9repo_summary_20261026.json` |
| Executive summary on every site that is clear & obvious which submission is best, with table of downloadable file, estimated score (`HOLDOUT-DTI`), historical score (`OWNER-REPORTED`), and uniqueness across focus sites & registry | **PASS** — Prominent red/green banner + 9-site table + `GEMSDOE36` 7-lane table on `docs/index.html`, `docs/executive-summary.html`, and `README.md` | `docs/index.html`, `docs/executive-summary.html`, `README.md` |
| Unique `.tif` submission generated & obvious whether OK to download and submit without human intervention | **PASS** — `gemsdoe36-hvg36-vent-dipole-20261026-b3ee97873192-zeros.tif` (`b3ee97873192`), automatically validated, explicitly labeled `DOWNLOAD: YES (research) · DO NOT SUBMIT` (`verdict = "negative"`) | `docs/downloads/gemsdoe36-hvg36-vent-dipole-20261026-b3ee97873192-zeros.tif`, `evidence/hvg36_run_card_20261026.json` |
| Prevent `"Predicted values must be in range [0, 1]"` error on DrivenData & provide step-by-step submission instructions | **PASS** — Whole-array finite `[0.0, 1.0]` (`outside_zero_count = 7,111,787`, `nan_count = 0`); 5-step guide with copyable command & `<=140`-char notes on `docs/executive-summary.html` | `docs/executive-summary.html`, `tests/test_hvg36.py` |
| PhD-level analysis of why `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` (`GEMSDOE32`) got `0.2778` and how to beat `0.2778`, `0.3195`, `0.4413` | **PASS** — Algebraic inversion (`R^2 = 0.998523`, `TP_w = 5,151.3 px`, `K = 12,852.7 px`) + empirical proof (`0.006708` on `labels.tif` vs `0.2778` on blind test set) | `docs/index.html`, `docs/executive-summary.html`, `docs/research/hvg36-20261026.md` |
| 3–5 novel geological hypotheses ranked before implementing | **PASS** — 4 hypotheses (`HVG-36-A..D`) ranked by expected DTI gain & implementation cost prior to execution | `docs/research/preregistration-hvg36-20261026.md`, `evidence/hvg36_preregistration_20261026.json` |
| Parallel-Run Protocol (1. Lane & 0.90/70% uniqueness on surface & final dots; 2. Reuse shared holdout & writer; 3. Strict number labels; 4. 0.90 AUC leakage canary; 5. JSON run card; 6. Budget <=3 experiments / <=2 hours) | **PASS** — 3 experiments in `570.1 s`; canary max AUC `0.6440`; surface max `|rho| = 0.5713`; JSON run card emitted | `evidence/hvg36_run_card_20261026.json`, `docs/downloads/hvg36-run-card.json` |
| Preserve prompt in `README.md` | **PASS** — Full Owner Brief preserved in `README.md` and `knowledge/owner_brief_2026-10-25.md` | `README.md`, `knowledge/owner_brief_2026-10-25.md` |
