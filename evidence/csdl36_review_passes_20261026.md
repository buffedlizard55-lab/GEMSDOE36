# Three-Pass Verification & Review Ledger — `CSDL-36` & 9-Focus-Site Refresh (2026-10-26)

## Pass 1 — Implementation & Verification

1. **Registry & Priority Raster Restoration**:
   - Restored and SHA-256 verified all `25/25` raw competition files (`python3 scripts/restore_data.py --group all`), `233/233` scored+peer registry rasters (`198/198` in `registry/uniqueness_registry.json` via `python3 scripts/fetch_registry_rasters.py`), `107/107` priority 9-site rasters (`python3 scripts/cache_priority_registry.py`), and `10/10` pinned 9-site forensic comparison rasters (`python3 scripts/cache_focus9_audit.py`).
2. **Preregistration (`CSDL-36`)**:
   - Locked `docs/research/preregistration-csdl36-20261026.md` and `evidence/csdl36_preregistration_20261026.json` (`sha256: 4f13538329ecea6b2878c6b42d74ca130bf3faa45906fc0cb68c0b4eb22fb0a2`) with 4 ranked geological hypotheses (`CSDL-36-A`..`D`) and explicit remediations for `IR-GVSC36-01`..`04`.
3. **Feature Engineering, Leakage Canary, Holdout, Uniqueness & GeoTIFF Emission**:
   - Built `src/gemsdoe36/csdl_features.py` (`BASE=59`, `CSDL_STRUCTURAL=16`, `CSDL_CONDUIT=12`, `EXP1=75`, `EXP2=87`, `LIDAR_REMOVED=14`, `EXP3_BLIND=73`) and executed `scripts/run_csdl36.py`.
   - Passed `G1` leakage canary across all `87` features (`max_symmetric_auc = 0.671595 <= 0.90`).
   - Evaluated `B0` (`0.133422`), `EXP-1` (`0.155206` `[0.140923, 0.169815]`), `EXP-2` (`0.155970` `[0.141880, 0.170267]`), and `EXP-3` (`0.152541` `[0.138223, 0.167204]`) on `gems-segment-pooled-v1` (`60,988` withheld positives, `1,500 m` buffer, `1,999` bootstrap draws).
   - Screened surface rank correlation (`0.439820 <= 0.90`) strictly before dot placement (`2026-10-26T23:13:09Z < 2026-10-26T23:17:43Z`), emitted `37,654` dots (`docs/downloads/gemsdoe36-csdl36-exp2-20261026-12962cc72ae1-zeros.tif`, SHA-256 `d840ce6aa03c8fc6c44d6ab761b7be1590859a00c711d623e4c9eb5479cfc778`), and verified 9-focus-site uniqueness (`0.686859 <= 0.70` across `108` rasters) and fail-closed `verdict = "negative"` due to `reg-052` (`0.994104`) and `reg-062` (`0.934615`).

## Pass 2 — Bug, Edge-Case & Audit Review

1. **Bug Found & Fixed during Feature Construction**:
   - `_read_clean` initially read raw `-3.4028235e+38` nodata pixels outside the valid footprint into `scipy.ndimage.convolve`, bleeding extreme negative values across the footprint edge; fixed by masking `(a < NODATA_CUT) | (~fp) = np.nan` prior to convolution and verified with `G1` canary (`max_symmetric_auc = 0.671595 <= 0.90`).
2. **Bug Found & Fixed in Site & Test Integration**:
   - `tests/test_mto_release.py` asserts `len(additional_archives()) == 6` for the legacy archive list; preserved the 6-item `additional_archives()` contract and placed `CSDL-36 EXP-2` in the primary `archive_section` cards (`4 + 6 = 10` total research artifacts in `docs/downloads/submissions_manifest.json`).
   - Fixed `ruff` `B905` (`strict=True` on `zip()`) in `scripts/run_csdl36.py`, `F841` in `scripts/verify_csdl36_release.py` (added explicit `holdout["lane_id"]` and `holdout["withheld_positives"]` check against `rc`), and `I001` import sorting in `tests/test_csdl36.py`.

## Pass 3 — Final End-to-End Requirement & Release Verification

Executed all automated verifiers and test suites from the repository root:
- `python3 scripts/build_site.py`: `PASSED` (rebuilt `docs/index.html`, `docs/executive-summary.html`, `docs/current-run.json`, `docs/downloads/submissions_manifest.json`, and `README.md` preserving the standing owner brief verbatim).
- `python3 scripts/check_site.py`: `PASSED` (verified all local links, anchors, SHA-256 digests, ZIP contents, score provenance labels, and fail-closed `DO NOT SUBMIT` banner).
- `python3 scripts/verify_csdl36_release.py`: `PASSED` (`CSDL-36 EXP-2`, `HOLDOUT-DTI = 0.155970`, `focus9_max_overlap_3px = 0.686859`, `verdict = "negative"`).
- `python3 scripts/verify_gvsc36_release.py`: `PASSED`.
- `python3 scripts/verify_mto_release.py`: `PASSED`.
- `python3 scripts/verify_release_gate.py`: `PASSED`.
- `pytest -q`: `151 passed, 1 skipped`.
- `ruff check src scripts tests`: `All checks passed!`.
