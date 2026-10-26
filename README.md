# GEMSDOE36 — DOE GEMS Prize: Subsurface Fault Detection (`H36-CTRB`)

**Live GitHub Pages Site & One-Click Download Portal:** [`docs/index.html`](docs/index.html) · [`docs/executive-summary.html`](docs/executive-summary.html)  
**Working Branch:** `arena/b0ff24db-gemsdoe36`

<!-- STATUS:START -->
> ## Automated Repository Release Gate: `DO NOT SUBMIT — HOLD WEEKLY LIVE SLOT` (`DOWNLOAD: YES` for format-safe `[0, 1]` research & ensemble inspection)
>
> * **Primary Branch Artifact (`H36-CTRB`, `arena/b0ff24db-gemsdoe36`):** [`gemsdoe36-h36-ctrb-submod-36800-20261025T000000Z-a1d85443-zeros.tif`](docs/downloads/gemsdoe36-h36-ctrb-submod-36800-20261025T000000Z-a1d85443-zeros.tif) · [ZIP](docs/downloads/gemsdoe36-h36-ctrb-submod-36800-20261025T000000Z-a1d85443-zeros.zip) · [NaN twin](docs/downloads/gemsdoe36-h36-ctrb-submod-36800-20261025T000000Z-a1d85443-nan.tif) · [Run Card](evidence/h36_ctrb_run_card_20261025.json)
>   * Name: `GEMSDOE36-H36-CTRB-Submod` · SHA-256: `2bb4513d6307e2394d5de7e7e7649e28eff067b602b805a0215e82aa5ff89907`
>   * Note (106 <= 140 chars): `GEMSDOE36 H36-CTRB | 1.5km worm+trunk relay submod | HOLDOUT-DTI 0.1144 | NEGATIVE hold slot | id a1d85443`
>   * **HOLDOUT-DTI:** **`0.114425`** (`95% CI [0.103795, 0.125756]`, `gems-segment-pooled-v1`, `60,988` withheld positives; **`SW = 0.11022` Walker Lane lift** vs `0.0880` `B0` and `0.0829` `H36-GPS`; `+0.05647` vs `CTRL-2` `4/4` folds; recorded group best `0.14876`).
>   * **Uniqueness:** `107` owner-scored rasters **PASS** (`surface |rho| = 0.3297`, `dots |rho| = 0.2033`, `max overlap = 0.5101 <= 0.70`, `0` normal-coverage `<40%` rasters `> 0.70`); `198` expanded registry **FAIL** (`0.8388` on 4 unsubmitted `41–55%` area blankets; [`evidence/h36_ctrb_crosscheck_20261025.json`](evidence/h36_ctrb_crosscheck_20261025.json)).
>   * **Gates:** G1 PASS · G2 FAIL · G3 PASS · G4a PASS · G4b PASS · G4c FAIL · G5 PASS -> **`verdict: "negative"`** (`12,279,160 / 12,279,160` cells finite in `[0.0, 1.0]`).
> * **Parallel `H36-GPS` (`gemsdoe36-h36-gps-graben-pair-20261026-bb29ce2a4bb4-zeros.tif`):** **DO NOT SUBMIT** (`HOLDOUT-DTI = 0.13203` vs `B0 = 0.13375`; 198-raster max overlap `0.8985`; [`evidence/h36_run_card.json`](evidence/h36_run_card.json), SHA-256 `e3800971b44116bca8ef8f996c3b2796b4d316962f797975f17d643abfac379b`, note `GEMSDOE36 H36-GPS graben-pair | HOLDOUT-DTI 0.1320 [0.1205,0.1443] seg-pooled-v1 60988pos | NEGATIVE | id bb29ce2a4bb4`).
>
> * **Parallel Lane36 (`gemsdoe36-lane36-supgbm-68302-20261026T002651Z-f35cb3e4-zeros.tif`):** **DO NOT SUBMIT** (own custom holdout says `promote`, shared-template 198-raster cross-check `FAIL` at `0.9317` max overlap; [`evidence/lane36_crosscheck.json`](evidence/lane36_crosscheck.json)).
<!-- STATUS:END -->

---

## Arena Core Values — Guiding Every Engineering & Gate Decision

1. **Maximize `P(Win)`:** Every design choice is subordinate to maximizing probability of winning on the unseen private and expert-revised hidden fault evaluation sets — never wasting one of the three weekly submission slots on circular target proxies (`sgmc_off_catalogue`), copied sibling rasters (`96.91%` overlap with `GEMSDOE32`), or candidates that have not cleared both the group holdout best (`0.14876`) and the full registry uniqueness ceiling.
2. **Own the Outcome:** Zero manual inspection bottlenecks, zero unverified projections disguised as scores, zero hidden failures, and automated fail-closed verification across GeoTIFF format/range (`[0, 1]`), two-polarity single-feature leakage canaries, dual-scope registry uniqueness (`107` owner-scored rasters and `198` expanded registry rasters), and all local/external documentation links.

---

## Original User Prompt & Research Directive (Recorded Verbatim as Project Starting Point)

> Review this repo and analyze our highest scoring submissions across GEMSDOE24 (0.2477), GEMSDOE25 (0.2600), GEMSDOE27 (0.2449), GEMSDOE28 (0.2708, 0.2649, 0.2710, 0.2707), GEMSDOE30 (0.2600), GEMSDOE31 (0.2708), GEMSDOE32 (`h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`: 0.2778), GEMSDOE33 (0.2632), and GEMSDOE36 (`anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros`: 0.2750). I want a PhD level explanation of why and how GEMSDOE32 got the highest score and how we can beat it (highest score on the leaderboard right now is 0.3195; DrivenData competition high score is 0.4413).
>
> Generate 3–5 genuinely novel candidate geological hypotheses not yet tried in this repo, naming the specific layers, physical signature/transform, why each catches off-catalogue faults missing from USGS/INGENIOUS rather than catalogued ones, difference from existing repo code, named non-fault mimic process, and free official sources if external data is required, ranked by expected DTI improvement vs implementation cost.
>
> Follow the Parallel-Run Protocol:
> - Reuse the shared cached feature stack, `evaluate_holdout.py` (`SegmentHoldout`, hide-and-recover whole fault segments with 1,500 m buffer, derive catalogue features only from visible faults, mask visible faults pixel-exactly, pooled DTI with $\alpha = 0.2, \beta = 0.8$, 300 m triangular kernel), and `submission_writer.py`.
> - Run a single-feature leakage canary (`AUC > 0.90` = leakage until proven otherwise).
> - Enforce registry uniqueness on **both** the continuous surface before placement and final dots (`|Spearman rho| <= 0.90` and `<= 70%` of dots within `3 px` of any competing registry raster).
> - Stop after at most `3` experiments or `2` hours; label every metric explicitly `HOLDOUT-DTI` (with evaluator version, withheld positives, and `95% CI`) or `ORGANIZER-CONFIRMED` (never write a projection as a score); keep the submission note `<= 140` characters; prevent `"Predicted values must be in range [0, 1]"` via automated validation without requiring a human inspector; make submission readiness obvious on the site; execute 3 full review passes; end with one JSON Run Card; and open and merge a pull request onto `main`.

---

## 1. PhD-Level Forensic Explanation: Why `GEMSDOE32` (`h33-h33-2-b2`) Scored `0.2778` (`ORGANIZER-CONFIRMED`) & How to Beat It

All `107` owner-scored rasters and `198` expanded registry rasters were audited byte-for-byte on the exact `5,167,373`-pixel active Basin & Range footprint (`3730 x 3292`, `EPSG:32611`, `100 m` grid). Full derivations: [`docs/research/forensic_audit_and_results_2026-10-25.md`](docs/research/forensic_audit_and_results_2026-10-25.md) and [`docs/research/why-02778.md`](docs/research/why-02778.md).

### 1.1 Exact Euclidean Distance-to-Catalogue Decomposition (`labels.tif`, `60,988` Pixels)

Every scored raster below has **`on_catalogue = 0`**:

| Site & Submission Artifact | `ORGANIZER-CONFIRMED` DTI | Total Dots | `d_cat in (0, 1] px` | `d_cat in (1, 2] px` | `d_cat > 2 px` | Exact Set Algebra |
|---|---:|---:|---:|---:|---:|---|
| `19GEMSDOE` (`h19-5`) | `0.1922` | `121,131` | `9,651` | `7,675` | `103,805` | Continuous 1-px ridge skeleton; heavy kernel self-overlap + flank FP tax. |
| `GEMSDOE24` (`d1.5`) | `0.2477` | `60,069` | `5,355` | `3,414` | `51,300` | `1.5 px` (`150 m`) dotted ridge emission (`+0.0555` over continuous lines). |
| `GEMSDOE27` (`topo-gap-t-v2`) | `0.2449` | `61,328` | `5,413` | `3,462` | `52,453` | `GEMSDOE24` `d1.5` + `1,259` gap-closure dots (`-0.0028` net FP dilution). |
| `GEMSDOE25` & `GEMSDOE30` (`d2.8`) | `0.2600` | `44,090` | `3,891` | `2,545` | `37,654` | **Pixel-identical (`m25 == m30`)**; `2.8 px` (`280 m`) spacing (`+0.0123`). |
| `GEMSDOE28` & `GEMSDOE31` (`h27-4-r1`) | `0.2708` | `40,199` | `0` | `2,545` | `37,654` | **Pixel-identical (`m28 == m31`)**; `d2.8` minus `3,891` `(0, 1] px` flank dots (`+0.0108`). |
| `GEMSDOE28` (`h32-1` / `h36-1` / `h38-1`) | `0.2649` / `0.2710` / `0.2707` | `42,294` / `37,660` / `37,860` | `2,095` / `0` / `0` | `2,545` / `6` / `206` | `37,654` | Partial vs near-complete `(0, 2] px` flank removal around the `37,654` core. |
| **`GEMSDOE32` (`h33-h33-2-b2`)** | **`0.2778`** | **`37,654`** | **`0`** | **`0`** | **`37,654`** | **`d2.8` minus all `6,436` `d_cat <= 2.0 px` flank dots (`+0.0178` over `d2.8`).** |
| `GEMSDOE33` (`h33d`) | `0.2632` | `41,865` | `1,377` | `2,517` | `37,971` | Partial re-introduction of `3,894` `<= 2 px` flank dots (`-0.0146`). |
| `GEMSDOE36` (old `pinn-38854`) | `0.2750` | `38,854` | `0` | `0` | `38,854` | Copied all `37,654` `GEMSDOE32` dots (`96.91%` overlap) + `1,200` radial IDW dots (`-0.0028`). |

### 1.2 Three Exact Mathematical Discoveries

1. **Optimal `2.8–3.0 px` (`280–300 m`) Point-Kernel Packing (`0.1922 -> 0.2477 -> 0.2600`):** Under $K(d)=\max(0, 1-d/3)$ and $\text{DTI}=\text{TP}_w/(\text{TP}_w + 0.2\,\text{FP}_w + 0.8\,\text{FN}_w)$, adjacent 1-px skeleton pixels cover overlapping 300 m disks (`67%` redundant kernel overlap) while paying full $0.2$ FP cost per pixel. Spacing dots `~280–300 m` cuts FP penalty ~3x while preserving >88% along-strike truth coverage.
2. **Unmasked `<= 200 m` Catalogue-Flank Hallucination Removal (`0.2600 -> 0.2708 -> 0.2778`):** DrivenData masks `labels == 1` (`d_cat = 0`), **not** `100–200 m` parallel flanks! Gaussian derivatives ($\sigma = 100\text{–}300\text{ m}$) blur mapped range-front scarps outward by `1–2 px`. Removing `(0,1] px` (`3,891` dots) gave `+0.0108`, and removing `(1,2] px` (`2,545` dots) gave another `+0.0070` (`+0.0178` total, zero model change).
3. **Nested Subset Inversion & Dinkelbach Optimality:** From `37,654 ⊂ 38,854` (`+1,200` dots = `+240` FP denominator units, `0.2778 -> 0.2750`), $D_{37654} \approx 23,572$, $\text{TP}_w \approx 6,548$, and hidden ground-truth trace count is **$|G| \approx 16,000\text{–}21,000\text{ px}$**. Under Dinkelbach's fractional transform, adding pixel $j$ increases DTI iff $\Delta\mathbb{E}[\text{TP}_w(j\mid S)] > \frac{0.2\,D^*}{1-0.2\,D^*}(1-\bar{p}_j)$. To genuinely surpass `0.2778` (`0.4413` public #1), a detector must raise **new off-catalogue basin/relay/Walker Lane recall** rather than re-thinning `H19-5`.

---

## 2. Five Novel Geological Hypotheses (`H36-A` .. `H36-E`, Ranked by Expected DTI Lift vs Cost)

Full preregistration: [`docs/research/preregistration_2026-10-25.md`](docs/research/preregistration_2026-10-25.md).

1. **`H36-A` (Rank 1 — Implemented in `src/gemsdoe36/ctrb.py`):** *1.5 km Antialiased Strike-Worm Potential-Field & Hydrothermal Line Integrals + Double-Angle Structure-Tensor Concordance* (`grav_hgm_worm_max/coh`, `mag_tdr_worm_max/coh`, `hydro_worm_max`, `struct_concordance_3p`, `anderson_worm_concordance`) across `training_features.tif` (`gb_ba_up500`, `mag_padded`, `tg`, `qfaults_strain`), `derived_geodawn_100m_f32.tif`, and `gdr_wellspring_in_footprint.csv` (`csv.DictReader`, `dist_known_fault_px` stripped). Targets basin-interior concealed step-faults; suppresses circular volcanic plugs & flight-line ties.
2. **`H36-B` (Rank 2 — Implemented in `src/gemsdoe36/ctrb.py`):** *Label-Free Geophysical Trunk Relay-Ramp Bridges & $\cos^4\psi$ Tip-Propagation Lobes* (`trunk_relay_bridge`, `trunk_tip_lobe`, `trunk_t_junction`) from opposing signed-EDT distances between top-5% geophysical basement trunks (`0` catalogue pixels used). Targets unmapped synthetic relay ramps (`0.5–3.2 km`) and horse-tail splays; suppresses across-valley pairings (`> 3.2 km`).
3. **`H36-C` (Rank 3 — Implemented in `src/gemsdoe36/ctrb.py`):** *Contour-Orthogonal Piedmont Micro-Scarp Breaklines & Explicit NaN-Safe LiDAR Routing* (`geom_contour_scarp`, `geom_piedmont_breakline`, `lidar_scarp_breakline`, `lidar_valid_flag`, excluding raw `det_elev` and `det_elev_slope`). Targets `0.3–1.5 m` degraded alluvial-fan scarps while eliminating upland cliff accessibility confounding and zero-imputation bias across the `31.8%` LiDAR gap (`NE` quadrant `48.2%` missing).
4. **`H36-D` (Rank 4 — Implemented in `src/gemsdoe36/ctrb.py`):** *Nested Spatial-Quadrant Purged Cross-Calibration (`NSQ-PCC`) + Minoux Lazy-Greedy Dinkelbach-Submodular 300 m Ridge Emission* (`fit_predict_nsq_pcc_fold`, `submodular_dti_emit`). Eliminates tree leaf overfitting and 2D plateau lattice tiling while maximizing marginal 300 m kernel coverage outside `d_cat <= 2.0 px`.
5. **`H36-E` (Rank 5 — Conditional External Data Route):** *Relocated Microseismic Lineament Trends ([USGS ANSS ComCat](https://earthquake.usgs.gov/fdsnws/event/1/)) & [ASF OPERA CSLC-S1](https://www.asf.alaska.edu/data-sets/derived-data-sets/opera/) Cross-Line Phase-Gradient Steps.* Blocked inside the sandbox (`earthquake.usgs.gov` / `asf.alaska.edu` unreachable; external reachability verified in CI via `.github/workflows/verify-external-sources.yml`).

---

## 3. `H36-CTRB` Parallel-Run Protocol Results (`HOLDOUT-DTI` & Dual-Registry Audit)

Evaluator: byte-pinned `gems.holdout.SegmentHoldout` (`evaluator_version = "gems-segment-pooled-v1"`, `60,988` withheld positive pixels, `3,199` components, `1,500 m` purge collar, `1,999` 10-km block bootstrap draws). Budget: **`3 / 3` experiments** (`1,352.1 s < 7,200 s`).

| Run ID | Description | Pooled `HOLDOUT-DTI` | `95% CI` | `NW` | `NE_LidarGap` | `SW` (Walker Lane) | `SE` |
|---|---|---:|---:|---:|---:|---:|---:|
| `CTRL-1` | Prior repo `GEMSDOE36` `H6` static raster | `0.000094` | `[0.000049, 0.000146]` | `0.00014` | `0.00004` | `0.00011` | `0.00009` |
| `CTRL-2` | Reconstructed 19-band raw `training_features` HGB (`d=3`) OOF + ridge NMS | `0.057959` | `[0.048011, 0.068518]` | `0.04707` | `0.08242` | `0.04079` | `0.06608` |
| `EXP-1` | Unsupervised 4-pillar concordance + submodular ridge emission | `0.091617` | `[0.080409, 0.103325]` | `0.07163` | `0.10985` | `0.07348` | `0.11105` |
| `EXP-2` | 17-feature local physical `NSQ-PCC` OOF + submodular ridge emission | `0.110085` | `[0.100410, 0.119903]` | `0.09930` | `0.13132` | `0.09597` | `0.11695` |
| **`EXP-3`** | **Full 25-feature `H36-CTRB` (`NSQ-PCC` + 1.5 km strike worms + trunk relay + submod)** | **`0.114425`** | **`[0.103795, 0.125756]`** | **`0.10488`** | **`0.13141`** | **`0.11022`** | **`0.11227`** |
| *Parallel `H36-GPS`* | *59 base + 7 graben-pair features (`evidence/h36_run_card.json`)* | *`0.132026`* | *`[0.120531, 0.144335]`* | *`0.1416`* | *`0.1740`* | *`0.0829`* | *`0.1509`* |
| *Parallel `B0`* | *59-feature multi-scale topographic/geophysical OOF HGB* | *`0.133749`* | *`[0.122241, 0.146035]`* | *`0.1474`* | *`0.1729`* | *`0.0880`* | *`0.1484`* |
| *Group Best* | *`GEMSDOE24` `H24-GVC1` (recorded on `gems-segment-pooled-v1`)* | *`0.148760`* | *`[0.134130, 0.163700]`* | — | — | — | — |

### Gate Summary for `gemsdoe36-h36-ctrb-submod-36800-20261025T000000Z-a1d85443-zeros.tif`
- **`G1` Matched Local Controls:** **PASS** (`+0.05647` vs `CTRL-2`, `95% CI [+0.04341, +0.07006]`, `4/4` folds; `+0.00434` vs `EXP-2`, `3/4` folds; **`SW = 0.11022` beats `B0` `0.0880` and `H36-GPS` `0.0829` in Walker Lane**).
- **`G2` Group Holdout Best (`0.14876`):** **FAIL** (`0.114425 < 0.13375` `B0` and `< 0.14876` `GEMSDOE24 H24-GVC1` due to omitting raw multi-scale elevation/slope features in `NW/NE/SE`).
- **`G3` Single-Feature Leakage Canary (`evidence/h36_ctrb_canary_20261025.json`):** **PASS** (`max_symmetric_auc = 0.641427 <= 0.90`).
- **`G4a` Pre-Placement Surface Uniqueness:** **PASS** (`max |Spearman rho| = 0.3297 <= 0.90`).
- **`G4b` Owner-Scored 107-Raster Final-Dot Uniqueness (`registry/priority_rasters.json`):** **PASS** (`max |rho| = 0.2033 <= 0.90`, `max competing 3-px overlap = 51.01% <= 70.00%`, `33.95%` vs `GEMSDOE32`, `0` normal-coverage `< 40%` rasters `> 70%`).
- **`G4c` Expanded 198-Raster Final-Dot Check (`registry/uniqueness_registry.json`, `evidence/h36_ctrb_crosscheck_20261025.json`):** **FAIL** (`max overlap = 83.88%` on 4 unsubmitted `41.3%–55.4%`-footprint-coverage blanket sweeps, `IR-36-NEW-06`).
- **`G5` Format & Strict `[0, 1]` Range (`sha256 = 2bb4513d6307e2394d5de7e7e7649e28eff067b602b805a0215e82aa5ff89907`):** **PASS** (`EPSG:32611`, `3730 x 3292`, `float32`, `nodata=None`, all `12,279,160` cells finite in `[0.0, 1.0]`, `36,800` dots, `0` `d_cat <= 2 px`).
- **Automated Gate Verdict:** **`verdict: "negative"` — `DOWNLOAD: YES (Research / Walker-Lane Orthogonal Signal) · SUBMIT: NO (Hold Weekly Slot)`**.

---

## 4. Zero-Human Automated Verification Commands

```bash
.venv/bin/python scripts/verify_release_gate.py   # Verifies H36-CTRB Run Card, SHA-256s, dual [0,1] validators, canary, uniqueness, and links
.venv/bin/python scripts/check_site.py            # Verifies GitHub Pages banners, hashes, notes, and cross-checks across all 3 lanes
.venv/bin/pytest -q                               # Runs all unit, template-pin, protocol, submission, CTRB, and release-gate tests
.venv/bin/ruff check src/gemsdoe36/ctrb.py scripts/evaluate_holdout.py scripts/verify_release_gate.py tests/test_ctrb.py tests/test_release_gate.py
```

---

## 5. Verified Official Sources & Links for Manual Review

- **DrivenData GEMS Competition Home:** <https://www.drivendata.org/competitions/306/competition-doe-gems/>
- **DrivenData Problem Description & Metric (`page/967`):** <https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/>
- **DrivenData Public Leaderboard:** <https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/>
- **Official DOE / NLR Competition Rules PDF (`NLR 96647`):** <https://docs.nlr.gov/docs/fy26osti/96647.pdf>
- **Official Organizer Reference Solution:** <https://github.com/drivendataorg/gems-prize-reference-solution>
- **DOE GDR Submission 1391 (INGENIOUS Great Basin Dataset):** <https://gdr.openei.org/submissions/1391>
- **USGS GeoDAWN Geophysical & Radiometric Grids (`doi:10.5066/P93LGLVQ`):** <https://doi.org/10.5066/P93LGLVQ>
- **USGS 3D Elevation Program (3DEP 1 m LiDAR):** <https://www.usgs.gov/3d-elevation-program>
- **USGS Quaternary Fault and Fold Database:** <https://www.usgs.gov/programs/earthquake-hazards/faults>
- **USGS ANSS ComCat API (`H36-E`):** <https://earthquake.usgs.gov/fdsnws/event/1/>
- **NASA / ASF OPERA Surface Displacement (`H36-E`):** <https://www.asf.alaska.edu/data-sets/derived-data-sets/opera/>
