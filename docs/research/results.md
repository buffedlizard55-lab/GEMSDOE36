# GEMSDOE36 Experimental Results & Validation Ledger

**Ledger Updated:** 2026-10-04 UTC (build re-issued 2026-10-25 with corrected metadata)  
**Labeling convention:** every number is HOLDOUT-DTI (local spatial holdout) or ORGANIZER-CONFIRMED-as-cited (copied from GEMSDOE site histories; no local organizer receipt exists — see docs/research/known_irregularities.md IR-04/IR-05). No projection is written as a score. Session run card: `evidence/run_card.json`.  
**Evaluation Protocol:** 4-Quadrant Spatially Blocked Holdout Mirror (`gemsdoe36.live_mirror`) for the Anderson-PINN line; 5-fold spatially-blocked off-catalogue holdout for the H6 line (see §4).  
**Candidate lines (both unique, both preserved):** Anderson-PINN primary `gemsdoe36-anderson-geothermal-pinn-38854-20261025T235127Z-9b9ea4e6-zeros.tif` (sections 1–3) and the off-catalogue H6 gate-passed candidate `GEMS36_h6_offcatalog_network_prior_20261004T193432.021282Z_3276c04090_3c064db2.tif` (section 4). The owner selects the single final file to upload. The two lines used different holdout protocols and are not compared head-to-head.

---

## 1. Executive Summary of Results

In this cycle, we formulated, implemented, and empirically validated candidate geological hypotheses targeting the gap between the `GEMSDOE32` baseline score (ORGANIZER-CONFIRMED-as-cited 0.2778) and the public leaderboard top (ORGANIZER-CONFIRMED-as-cited 0.3195; stale/unverified per IR-05).

We completed the autonomous data pipeline, processing 23 competition rasters and external tables (including 418 MB of GeoDAWN potential fields and 465 GDR 1391 geothermal well records), sanitizing 58,171 sentinel values, and implementing Andersonian physics-informed neural network (PINN) orientation loss.

### Benchmark Evaluation on 4-Quadrant Spatial Holdout:
All models were tested on identical spatial folds using the published DTI metric ($\alpha=0.2, \beta=0.8, R=300\text{ m}$):

| Model / Variant | Emitted Dots | Catalogue Flank (B=2) | Fold 0 (NW) | Fold 1 (NE) | Fold 2 (SW) | Fold 3 (SE) | LM Mean DTI (HOLDOUT-DTI) | Margin vs Base (HOLDOUT-DTI) |
|---|---|---|---|---|---|---|---|---|
| **BASE-0.2778** (`h33-h33-2-b2`) | 37,654 | 0 on-cat (B=2) | 0.178454 | 0.422879 | 0.213825 | 0.256524 | **0.267921** | +0.000000 |
| **H36-1-StepOver** | 38,554 | 0 on-cat (B=2) | 0.178454 | 0.422879 | 0.213969 | 0.256524 | **0.267956** | +0.000036 |
| **H36-2-BasementStep** | 38,554 | 0 on-cat (B=2) | 0.182487 | 0.422256 | 0.216210 | 0.255586 | **0.269135** | +0.001214 |
| **H36-3-GeothermalConduit** | 38,854 | 0 on-cat (B=2) | 0.176956 | 0.422366 | 0.226154 | 0.253638 | **0.269778** | +0.001858 |
| **GEMSDOE36-LEAD-PINN** | **38,854** | **0 on-cat (B=2)** | **0.177000** | **0.422342** | **0.224972** | **0.255320** | **0.269908** | **+0.001987** |

**Statistical Significance (HOLDOUT-DTI):** `GEMSDOE36-LEAD-PINN` has a positive pooled margin (+0.001987) but wins only **1 of 4 quadrants** (SW); the paired block bootstrap 95% CI on the margin, [-0.001330, +0.008059], **spans zero**, so the gain is within noise on this 4-block holdout and is not statistically significant. No live-score projection is stated (a projection is never a score). The lead is **not slot-eligible**; verdict: negative (see `evidence/run_card.json`). No weekly submission slot was spent.

---

## 2. Generated Competition Submission Deliverables

The production pipeline generated the following verified competition submission bundle under `docs/downloads/`:

### 2.1 Primary Submission GeoTIFF (Portal-Safe Fail-Closed)
- **File Name:** `gemsdoe36-anderson-geothermal-pinn-38854-20261025T235127Z-9b9ea4e6-zeros.tif`
- **File Size:** 318,120 bytes (311 KB)
- **SHA-256 Digest:** `686f6773ab0d678942103830c96ddb9dcec6c2c12f503395b5a9752ca6c59fe7`
- **Grid Dimensions:** 3,730 rows $\times$ 3,292 columns = 12,279,160 cells
- **Coordinate Reference System:** EPSG:32611 (WGS 84 / UTM zone 11N)
- **Spatial Resolution:** 100 m $\times$ 100 m
- **Data Type:** `float32` (single band)
- **Range & Finite Contract:** Min = 0.0, Max = 1.0; Exactly 12,279,160 finite cells (0 NaN, 0 Inf).
- **NoData Header:** `nodata=None` (prevents portal range validation crash: `"Predicted values must be in range [0, 1]"`).
- **Positive Pixel Count:** 38,854 dots ($> 0.5$)
- **Catalogue Contamination:** 0 pixels within 200 m of known USGS/INGENIOUS faults.

### 2.2 Companion NaN Outside GeoTIFF
- **File Name:** `gemsdoe36-anderson-geothermal-pinn-38854-20261025T235127Z-9b9ea4e6-nan.tif`
- **File Size:** 371,056 bytes (363 KB)
- **SHA-256 Digest:** `17d396f0b5c97c160d500212b987f3a1092ba3ac32e85d6f7b1e0a0e08a38b5a`
- **Valid Footprint Cells:** 5,167,373 finite cells in $[0, 1]$; Outside: 7,111,787 NaN cells (`nodata=nan`).

### 2.3 Single-Member Zip Archive
- **File Name:** `gemsdoe36-anderson-geothermal-pinn-38854-20261025T235127Z-9b9ea4e6-zeros.zip`
- **File Size:** 212,160 bytes (208 KB)
- **SHA-256 Digest:** `24e9929a938fe1c606e381f058156b482ac2053580d26d20d5b3774e724a6082`
- **Archive Contents:** Exactly 1 member: `gemsdoe36-anderson-geothermal-pinn-38854-20261025T235127Z-9b9ea4e6-zeros.tif`.

### 2.4 Competition Submission Metadata
- **Submission Name:** `GEMSDOE36-Anderson-PINN-20261025`
- **Submission Note:** `GEMSDOE36 Anderson-PINN | B=2 catalogue-flank prune + Anderson/geothermal dots; 38,854 dots; 0 on-cat; HOLDOUT-DTI 0.2699` (121 characters; within 200 character platform limit and within the run-card 140 cap).

---

## 3. Detailed Verification Gates Passed

1. **CRS and Resolution:** EPSG:32611 verified; transform pixel size = 100.0 m.
2. **Dimension and Shape:** $(3730, 3292)$ exactly matches the official sample submission template.
3. **Band Count:** Single band (count = 1), `float32`.
4. **Finite Range:** In-bounds values strictly in $[0.0, 1.0]$.
5. **Portal Range Fix:** Primary submission contains 0 NaNs and `nodata=None`, ensuring strict adherence to $[0, 1]$ across all 12,279,160 array elements.
6. **Integrity and Audit:** SHA-256 verified against `docs/downloads/submissions_manifest.json` and `gemsdoe36-anderson-geothermal-pinn-38854-20261025T235127Z-9b9ea4e6-audit.json`.

---

## 4. Off-catalogue candidate line (H6) — 5-fold spatial holdout gate

*Session `arena/01a10834-gemsdoe36`, 2026-10-04. This is a second, independent candidate
line (off-catalogue fault-network prior) with its own holdout protocol. It is not compared
head-to-head against the Anderson-PINN line above; both candidate TIFs are preserved.*

- **Data:** the owner-supplied SHA-256-pinned mirrors of the official rasters (features,
  labels, sample template) plus external layers (USGS 3DEP LiDAR scarp, GeoDAWN
  radiometric/extension grids, USGS SGMC proxy, GDR-1391 geothermal manifests) are present
  under `data/`. Provenance and the single point of trust (owner mirrors, not
  organizer-authenticated bytes) are in `sources.md`.
- **Pipeline:** `prepare_data_h6.py` (49 channels) → `field.py` (multi-family corroboration
  belief field + off-catalogue SGMC prior) → `anderson_dip.py` (spatially varying extension
  field, dip projection, soft strike weight) → `emitter.py` (exact-marginal-gain dots,
  support confinement, 200 m catalogue-flank exclusion, 300 m scatter) → `submission.py`
  (fail-closed writer).
- **Holdout gate — run 5 (concentrated top-K, H1 dip primary): FAIL.** `full_topk` beat the
  incumbent in 2/5 folds (0.0916 / 0.0241 / 0.1191 / 0.0491 / 0.1353 vs
  0.1319 / 0.0811 / 0.0838 / 0.0968 / 0.0902); high variance, failure mode = **under-coverage**
  (concentrated dots vs the incumbent's broad 37.6k). Dip ablation: `nodip` ≥ `full` in 4/5
  (dip is a small negative on a surface-trace target). `model_only` 0.004–0.029 (geophysics
  alone is near-zero off-catalogue). ⇒ the lever is coverage + an off-catalogue prior, not dip.
- **Hypothesis H6 (off-catalogue SGMC network prior + broad-coverage emission) promoted to lead.**
  Emission target changed from the concentrated top-K to the full off-catalogue SGMC line
  network; the emitter stops at the break-even bar at ~23–25k dots.
- **Holdout gate — run 6 (H6 broad coverage): PASS 5/5.** `full_cover` (23.2–23.7k dots) beat
  `incumbent_h33` on **every fold**: 0.4162 / 0.3414 / 0.4816 / 0.3826 / 0.5191 vs
  0.1319 / 0.0811 / 0.0838 / 0.0968 / 0.0902 (mean 0.428 vs 0.097, ~4.4×). Ablations:
  `full_topk`→`full_cover` ≈10× (coverage); `model_only`→`full_cover` (the SGMC prior carries
  the off-catalogue signal); `full_cover`→`nodip_cover` a consistent small negative
  (−0.01…−0.045, so dip is off in the candidate). Full table in `holdout_results.json`.
  **Current local holdout best on this line = H6 `nodip_cover` (mean 0.452).** Caveat: the SGMC
  proxy over-counts old faults the hidden set excludes, so proxy→live transfer is partial.
- **Upload-ready candidate generated and validated.** Config = dip off, SGMC prior on, broad
  coverage, scatter 3 px, flank exclusion → **24,881 dots**, binary dot map, EPSG:32611 100 m,
  single float32 band, [0,1] in-bounds, NaN outside, template match, SHA-256 manifest. File:
  `GEMS36_h6_offcatalog_network_prior_20261004T193432.021282Z_3276c04090_3c064db2.tif`
  (mirrored to `docs/downloads/` for the site). Diagnostics in `holdout_results.json`. The
  upload itself is the owner's manual step; no slot has been spent and no organizer score
  exists yet.
- **Not done yet:** the H5 CNN ensemble has not been trained/gated, so it is not in this file.
  It may use a later slot only if it beats the H6 holdout best on the same folds.
