# Known Irregularities & Forensic Audit Flags

Updated **2026-10-26 UTC** on branch `arena/b8f55e32-gemsdoe36` (reconciled across `WDP-36`, `ATVR-36`, `H36-CTRB`, `H36-GPS`, and `Lane36`). Every irregularity encountered across repository history, sibling-lane forensics, raw competition rasters, and pass-by-pass QA is documented below without omission.

## `WDP-36` Audit Discoveries (`arena/b8f55e32-gemsdoe36`, `2026-10-26`)

| ID | Irregularity Discovered | Forensic Proof | Resolution Implemented |
|---|---|---|---|
| **IR-36-WDP-01** | **Generated submission note misdescribed the winner** (`+strain/seis` although EXP-1 is persistence-only) | Pass-2 line-by-line review of the run card vs preregistered arm definitions. | Fixed generator (per-arm descriptions) + patched run card & receipt with a logged `corrections` entry; TIF SHA-256 unchanged. Regression-guarded in `tests/test_wdp36.py` + site checker exact-note assertions. |
| **IR-36-WDP-02** | **Portal “[0, 1]” error path fully characterised** | Whole-array audit of all 10 downloads: `-zeros` strict-PASS; `-nan` strict-FAIL (7,111,787 outside NaNs); `FORMAT_TEST` 32×48. | WDP-36 ships **zeros-only**; site quarantines `*-nan.tif` as DO-NOT-UPLOAD, fixture as NEVER upload. |
| **IR-36-WDP-03** | **One blanket drives literal uniqueness failure** | Surface \|ρ\|max 0.264 PASS; focus-9 max 0.4909; champion 0.2360; only GEMSDOE67 `ovtr-ml-cover` (54.8% coverage) exceeds 0.70 at 0.7227. | Fail-closed negative; dots not perturbed to evade (forbidden). Scopes reported separately. |
| **IR-36-WDP-04** | **Strain gradients hurt; persistence ≈ single-scale** | EXP-2 0.091090 < EXP-1 0.093269; paired CI includes 0. | Reported negative; no post-hoc reweighting. |
| **IR-36-WDP-05** | **External-data hypotheses sandbox-unobtainable** | Measured `curl 000` (drivendata/usgs/asf/gdr) vs `200` (github.com). | H-INSAR/H-FLIGHTLINE deferred with official free sources named; zero numbers claimed. |
| **IR-36-WDP-06** | **Canary scope note** | 8 surfaces canaried; strain sub-bands only via composite (max 0.6145). | Disclosed; future lanes canary every atomic channel. |

---

## `ATVR-36` Audit Discoveries (`arena/62b9a92c-gemsdoe36`, `2026-10-26`)

| ID | Irregularity Discovered | Forensic Proof | Resolution Implemented |
|---|---|---|---|
| **IR-36-ATVR-01 (`IR-36-INSAMPLE-HALO-COLLAPSE`)** | **Full-Catalogue In-Sample Tree Refit Collapses Onto `220–500 m` Known-Fault Halo** | When a 44-feature `HistGradientBoostingClassifier` is refit in-sample on 100% of `existing_faults.tif`, smooth geophysical covariates (`13_iso_grav_anom`, `15_depth_to_base_surf`, `06_tc`) memorize training coordinates, dumping `70.0%` of emitted dots within `d_cat <= 5 px` (`median = 3.2 px`) and producing `80.87%` mutual overlap with `GEMSDOE30` `MSDB1` (explaining why `GEMSDOE24 GVC1` dropped from `0.1488` holdout to `0.0859` `ORGANIZER-CONFIRMED` and `GEMSDOE30 MSDB1` dropped to `0.1462` `ORGANIZER-CONFIRMED`). | Switched deployment in `scripts/evaluate_holdout.py` to **Chernozhukov Spatial Out-of-Fold Cross-Fitting** (`median d_cat = 10.6 px`, `p90 = 31.6 px`, `35.94%` overlap vs `GEMSDOE32` `B2`). |
| **IR-36-ATVR-02 (`IR-36-BAND06-TC`)** | **`06_tc` in `training_features.tif` Is Airborne Radiometric Total Count, NOT Terrain Correction** | Direct footprint correlation against `external/geodawn_rad_u8.tif` band 4 (`TC`) yields **`Spearman = 0.999886`**, whereas correlation with terrain slope `19_det_elev_slope` is only `0.2147`. | Treated strictly as radiometric Total Count in `src/gemsdoe36/atvr_features.py`; paired with explicit `K / Th` ratio (`h36b_geodawn_k_th_ratio`). |
| **IR-36-ATVR-03 (`IR-36-GRAV-SIGNED-DERIV`)** | **`18_iso_grav_anom_hg` and `11_iso_grav_anom_vg` Are Signed Directional Derivatives (`+dg/dx, +dg/dy`), Not Magnitude / Vertical Derivative** | Numerical differentiation of `13_iso_grav_anom` gives `Spearman(dg/dx, band18) = +0.944740`, `Spearman(dg/dy, band11) = +0.937805`, and `Spearman(hypot(band18, band11), 05_iso_grav_anom_slope) = +0.940656`. | Documented in `src/gemsdoe36/atvr_features.py` so horizontal gradient magnitude uses `05_iso_grav_anom_slope` / `hypot`. |
| **IR-36-ATVR-04 (`IR-36-LIDAR-GAP`)** | **USGS 3DEP 1 m LiDAR Coverage Gap (`24.63%` of Footprint = `1,272,913` Pixels, Heavily Concentrated in `NE`)** | Zero-imputing missing LiDAR scarps creates false survey-boundary edges and suppresses recall in `NE_LidarGapHeavy` (`ATVR-36` `NE = 0.05312` vs `NW = 0.15048`, `SE = 0.15438`). | Encoded explicit `NaN` + binary indicator `h36a_lidar_valid_mask`, and documented `ATVR-36` (`NW/SE` leader) + `H36-CTRB` (`NE = 0.13141` leader) complementarity. |
| **IR-36-ATVR-05 (`IR-36-SUBCELL-BORDER-CLIP`)** | **`gemsdoe36.metric.distance_weighted_tversky(..., valid_mask=cell)` Clips Cross-Border 300 m Kernel Credit** | Zeroing `pred` outside `valid_mask` before convolving the 300 m kernel slightly under-counts border dots (`16`-cell `0.114542` vs unsplit `0.115835`). | Reported both `protocol.pooled_holdout` 16-cell DTI (`0.114542`), unsplit DTI (`0.115835`), and shared `gems.holdout.SegmentHoldout` DTI (`0.117925`). |

---

## `H36-CTRB` & Parallel-Session Irregularities (`IR-36-NEW-01..06` & `IR-01..26`)

| ID | Irregularity Discovered | Resolution Implemented |
|---|---|---|
| **IR-36-NEW-01** | Legacy docs fabricated a `4/4` fold win table & unverified projection string on old Line B (`0.2750` `ORGANIZER-CONFIRMED` live vs `0.2778` `GEMSDOE32`). | Hard-banned all projections-as-scores via `scripts/verify_release_gate.py` & `scripts/check_site.py`. |
| **IR-36-NEW-02** | Old `anderson-geothermal-pinn-38854` copied `100%` of `GEMSDOE32`'s `37,654` pixels (`96.91%` overlap). | Zero prior or registry rasters read in `atvr_features.py`, `ctrb.py`, or `h36_features.py`. |
| **IR-36-NEW-03** | Old Line A (`prepare_data_h6.py`) had circular `sgmc_off_catalogue` target leakage (`0.0512` live, `0.000094` honest holdout) and naive CSV `split(",")` risking `dist_known_fault_px` reads. | Banned `derived_sgmc_faults_100m_u8.tif` and `dist_known_fault_px`; parsed GDR CSVs strictly via `csv.DictReader`. |
| **IR-36-NEW-04** | Exact cross-lane identities (`GEMSDOE25 == GEMSDOE30` at `0.2600`; `GEMSDOE28 == GEMSDOE31` at `0.2708`; `GEMSDOE32` `0.2778` == `d2.8 & d_cat > 2 px`); `0.4413` is external public #1 (`xiaofanhu`). | Recorded exact provenance of every benchmark without conflating external milestones with internal `HOLDOUT-DTI`. |
| **IR-36-NEW-05** | Isotonic 2D plateau lattice tiling & per-fold stitch imbalance in early submodular runs. | Prevented via 2.2 px minimum spacing + CELF submodular expected-credit cover (`submodular_emit.py`) and 1-px `ridge_nms` (`ctrb.py`). |
| **IR-36-NEW-06** | Dense-Blanket Registry Coverage Trap in `uniqueness_registry.json`: while `ATVR-36` passes **100% of all 9 focus repositories (`GEMSDOE24..36`)** (`max overlap = 63.28% <= 70%`) and `H36-CTRB` passes all `107` owner-scored rasters in `priority_rasters.json`, `4–8` non-focus `80k–517k`-dot area blankets (`41%–55%` Nevada 3-px coverage, e.g., `GEMSDOE67`, `GEMSDOE22`, `GEMSDOE77`) exceed `70%` literal directional containment. | Fail-closed protocol enforced: recorded in `evidence/atvr36_crosscheck_20261026.json` and `evidence/h36_ctrb_crosscheck_20261025.json` with `verdict: "negative"` (`DO NOT SUBMIT` standalone to weekly live slot). |
| **IR-01..IR-26** | Unauthenticated portal data redirect (restored via `restore_data.py`), rules PDF cutoff precedence, `AI_DISCLOSURE.md` requirement, `d_cat <= 2 px` unmasked flank discovery, `-zeros.tif` `[0, 1]` portal fix, sandbox network host allowlist, byte-pinned `GEMSDOE24@fc2bc6f` shared template (`tests/test_template_pins.py`), and `Lane36` `93.17%` overlap reconciliation. | Preserved and enforced automatically by `pytest`, `scripts/verify_release_gate.py`, and `scripts/check_site.py`. |
