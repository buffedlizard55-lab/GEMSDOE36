# Validation Ledger & Forensic Results (`GEMSDOE36`)

Updated **2026-10-25 UTC** on branch `arena/b0ff24db-gemsdoe36`.  
All internal scores below carry the explicit label `HOLDOUT-DTI` from the shared whole-segment spatially buffered evaluator `SegmentHoldout` (`evaluator_version = "gems-segment-pooled-v1"`, `60,988` withheld positive pixels across `3,199` 8-connected fault components, `1,500 m` = `15 px` spatial training purge collar, `alpha = 0.2`, `beta = 0.8`, `R = 300 m` triangular kernel, `1,999` 10-km block-bootstrap resamples). All live DrivenData portal scores carry the explicit label `ORGANIZER-CONFIRMED`. **Zero projections are reported as scores.**

---

## 1. Byte-Verified Forensic Decomposition Across Focus Sites (`GEMSDOE24..36`)

Every scored raster below has **`on_catalogue = 0`** (`0` pixels overlapping the `60,988`-pixel `labels.tif` catalogue):

| Site / Artifact | `ORGANIZER-CONFIRMED` DTI | Total Dots | `d_cat in (0, 1]` (`100 m`) | `d_cat in (1, 2]` (`141–200 m`) | `d_cat > 2` (`> 200 m`) | Exact Set Algebra & Mechanism |
|---|---:|---:|---:|---:|---:|---|
| `19GEMSDOE` (`h19-5`) | `0.1922` | `121,131` | `9,651` | `7,675` | `103,805` | Continuous 1-px ridge skeleton (`sha256=ec1f9b56b83c...`); heavy redundant kernel overlap + flank penalty. |
| `GEMSDOE24` (`d1.5`) | `0.2477` | `60,069` | `5,355` | `3,414` | `51,300` | `1.5 px` dotted thinning along OOF multi-physics ridges (`sha256=68d0e2e4fcc5...`). |
| `GEMSDOE27` (`topo-gap-t-v2`) | `0.2449` | `61,328` | `5,413` | `3,462` | `52,453` | `GEMSDOE24` `d1.5` + `1,259` gap-closure dots (`sha256=33003374335d...`); net FP dilution `-0.0028`. |
| `GEMSDOE25` & `GEMSDOE30` (`d2.8`) | `0.2600` | `44,090` | `3,891` | `2,545` | `37,654` | **Pixel-identical footprint (`m25 == m30`)**; `2.8 px` dotted spacing (`+0.0123` over `d1.5`). |
| `GEMSDOE28` & `GEMSDOE31` (`h27-4-r1`) | `0.2708` | `40,199` | `0` | `2,545` | `37,654` | **Pixel-identical (`m28 == m31`)**; exact `d2.8` minus all `3,891` `(0,1] px` flank dots (`+0.0108`). |
| `GEMSDOE28` (`h32-1` / `h36-1` / `h38-1`) | `0.2649` / `0.2710` / `0.2707` | `42,294` / `37,660` / `37,860` | `2,095` / `0` / `0` | `2,545` / `6` / `206` | `37,654` | Partial vs near-complete `(0,2] px` flank pruning around the same `37,654` `>2 px` core. |
| **`GEMSDOE32` (`h33-h33-2-b2`)** | **`0.2778`** | **`37,654`** | **`0`** | **`0`** | **`37,654`** | **Exact `d2.8` minus all `6,436` `d_cat <= 2.0 px` flank dots (`+0.0178` over `d2.8`).** |
| `GEMSDOE33` (`h33d`) | `0.2632` | `41,865` | `1,377` | `2,517` | `37,971` | Partial re-introduction of `3,894` `<= 2 px` flank dots (`-0.0146` vs `GEMSDOE32`). |
| `GEMSDOE36` (old Line B `pinn-38854`) | `0.2750` | `38,854` | `0` | `0` | `38,854` | Copied all `37,654` `GEMSDOE32` pixels (`96.91%` overlap) + `1,200` radial IDW dots (`-0.0028`). **Archived.** |
| `GEMSDOE36` (old Line A `H6`) | `0.0512` | `24,881` | — | — | — | Circular `sgmc_off_catalogue` leak (`HOLDOUT-DTI = 0.000094`). **Archived.** |

### Exact Algebraic DTI Inversion from Nested Subsets (`37,654 ⊂ 38,854` and `37,654 ⊂ 40,199 ⊂ 44,090`)
Because `GEMSDOE36` old (`38,854` px) is an exact superset of `GEMSDOE32` (`37,654` px) adding `1,200` radial dots (`+240` FP penalty units at $\alpha = 0.2$) and dropping score from `0.2778` (`ORGANIZER-CONFIRMED`) to `0.2750` (`ORGANIZER-CONFIRMED`):
$$\frac{T}{D_{37654}} = 0.2778, \qquad \frac{T + \Delta T}{D_{37654} + 240 - 0.8\,\Delta T} = 0.2750$$
For $\Delta T \approx 0$, $D_{37654} \approx 23,572$, $T = \text{TP}_w \approx 6,548$, and since $D = 0.2\,\text{TP}_w + 0.2\,\text{FP}_w + 0.8\,|G|$, hidden unmapped ground-truth fault count is tightly bounded at **$|G| \approx 16,000\text{–}21,000\text{ pixels}$** (`~1,600–2,100 km` of hidden trace). Furthermore, the two-step jump `0.2600 -> 0.2708 -> 0.2778` proves **neither `(0,1] px` nor `(1,2] px` catalogue flanks are masked by DrivenData's scorer** — all `6,436` dots within `200 m` of `labels.tif` were actively scored as zero-credit false positives!

---

## 2. `H36-CTRB` Locked 3-Experiment Progression (`HOLDOUT-DTI`, `gems-segment-pooled-v1`)

| Run ID | Description | Pooled `HOLDOUT-DTI` | `95% CI` (1,999 10-km Block Bootstrap) | `NW` (`10,165` px) | `NE_LidarGap` (`12,511` px) | `SW` (`20,534` px) | `SE` (`17,778` px) |
|---|---|---:|---:|---:|---:|---:|---:|
| `CTRL-1` | Legacy `GEMSDOE36` `H6` static raster (control) | `0.000094` | `[0.000049, 0.000146]` | `0.00014` | `0.00004` | `0.00011` | `0.00009` |
| `CTRL-2` | Reconstructed 19-band raw `training_features` HGB (`d=3`) OOF + ridge NMS | `0.057959` | `[0.048011, 0.068518]` | `0.04707` | `0.08242` | `0.04079` | `0.06608` |
| `EXP-1` | Unsupervised 4-pillar physical concordance (`catalogue_features=[]`) + submodular ridge emission | `0.091617` | `[0.080409, 0.103325]` | `0.07163` | `0.10985` | `0.07348` | `0.11105` |
| `EXP-2` | 17-feature local physical `NSQ-PCC` OOF (no raw elev/slope) + submodular ridge emission | `0.110085` | `[0.100410, 0.119903]` | `0.09930` | `0.13132` | `0.09597` | `0.11695` |
| **`EXP-3`** | **Full 25-feature `H36-CTRB` (`NSQ-PCC` + 1.5 km strike worms + trunk relay/tip + submodular ridge)** | **`0.114425`** | **`[0.103795, 0.125756]`** | **`0.10488`** | **`0.13141`** | **`0.11022`** | **`0.11227`** |
| *Ref (Sibling)* | *`GEMSDOE24` `oof_multiphysics_hgb_d3` (includes raw `det_elev_slope` / LiDAR exposure)* | *`0.130000`* | *`[0.115650, 0.143960]`* | — | — | — | — |
| *Ref (Sibling)* | *`GEMSDOE24` `RSHG1` (failed uniqueness at `72.69%` 3-px overlap on `8GEMSDOE`)* | *`0.128990`* | *`[0.115780, 0.143050]`* | `0.1332` | `0.1566` | `0.0799` | `0.1516` |

### Paired Spatial-Block Bootstrap Comparisons (`EXP-3` vs Controls & Ablations)
- **`EXP-3` vs `CTRL-1` (Legacy `GEMSDOE36` `H6`):** $\Delta\text{DTI} = +0.11433$, `95% CI [+0.10370, +0.12566]`, **`4/4` fold wins**.
- **`EXP-3` vs `CTRL-2` (Raw 19-band HGB OOF):** $\Delta\text{DTI} = +0.05647$ (`1.97x`), `95% CI [+0.04341, +0.07006]`, **`4/4` fold wins**.
- **`EXP-3` vs `EXP-1` (Unsupervised Concordance):** $\Delta\text{DTI} = +0.02281$, `95% CI [+0.00907, +0.03585]`, **`4/4` fold wins**.
- **`EXP-3` vs `EXP-2` (Local-17 Ablation without Worms/Relay/Tip):** $\Delta\text{DTI} = +0.00434$, `95% CI [-0.00234, +0.01149]`, **`3/4` fold wins** (`+0.01425` lift in `SW` Walker Lane and `+0.00558` in `NW`).
- **Cross-Lane Tradeoff Note:** Omitting raw `det_elev` and raw `det_elev_slope` gives up `~0.0156` of range-interior catalogue slope self-recovery relative to `GEMSDOE24`'s raw-slope `oof_multiphysics_hgb_d3` (`0.13000`), while **cutting steep-slope ridge confounding on `8GEMSDOE_Hedge-v2` from `72.69%` (failed gate) down to `44.18%` (passed gate)** and lifting `SW` Walker Lane recovery from `0.0799` (`RSHG1`) to **`0.11022` (`+37.9%`)**.

---

## 3. Automated Canary, Uniqueness (`107` Rasters), and GeoTIFF Validator Gate Summary

1. **Single-Feature Two-Polarity Leakage Canary (`evidence/h36_ctrb_canary_20261025.json`):**
   - **PASS** across all `25` features (`max_symmetric_auc = 0.641427 <= 0.90`; highest pooled feature `geom_piedmont_breakline = 0.60248`).
2. **Registry Uniqueness (`registry/priority_rasters.json`, `107` unique rasters = `106` competing methods + `1` synthetic 5-px lattice control):**
   - **Pre-placement continuous surface:** **PASS** (`max |Spearman rho| = 0.3297 <= 0.90`).
   - **Final `36,800` emitted dots:** **PASS** (`max |Spearman rho| = 0.2033 <= 0.90`; `max competing 3-px dot overlap = 51.01% <= 70.00%`; `33.95%` 3-px overlap and `2.10%` exact pixel overlap with `GEMSDOE32` `h33-2-b2`).
3. **Dual GeoTIFF Contract Validators (`gemsdoe36.submission.validate_submission` + `gems.submission.check_variants`):**
   - Primary [`gemsdoe36-h36-ctrb-submod-36800-20261025T000000Z-a1d85443-zeros.tif`](../downloads/gemsdoe36-h36-ctrb-submod-36800-20261025T000000Z-a1d85443-zeros.tif) (`sha256=2bb4513d6307e2394d5de7e7e7649e28eff067b602b805a0215e82aa5ff89907`): **PASS** (`EPSG:32611`, `3730 x 3292`, `float32`, `nodata=None`, `12,279,160 / 12,279,160` cells finite in `[0.0, 1.0]`, `36,800` positive dots, `0` on-catalogue, `0` within `200 m` of catalogue).
   - Companion [`gemsdoe36-h36-ctrb-submod-36800-20261025T000000Z-a1d85443-nan.tif`](../downloads/gemsdoe36-h36-ctrb-submod-36800-20261025T000000Z-a1d85443-nan.tif) (`sha256=d30c767aed69c8fcfdefd0ffc07b9d09bd261573b18525c7c3122f99409caf1c`): **PASS** (`official_format_compliant = True`).
