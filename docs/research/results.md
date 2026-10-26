> **Updated 2026-10-25 UTC (reconciled across `H36-CTRB`, `H36-GPS`, and `Lane36`). Earlier pre-2026-10-25 numbers used circular protocols (live-mirror projection; SGMC proxy) and are superseded. Every internal metric below is explicitly labeled `HOLDOUT-DTI` (`gems-segment-pooled-v1`, `60,988` withheld positive pixels, `95% CI`) and every portal score from owner score lists is labeled `ORGANIZER-CONFIRMED`. Zero projections are reported as scores.**

# Validation Ledger & Forensic Results (`GEMSDOE36`)

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

---

## 2. `H36-CTRB` Locked 3-Experiment Progression (`HOLDOUT-DTI`, `gems-segment-pooled-v1`, `60,988` Positives)

| Run ID | Description | Pooled `HOLDOUT-DTI` | `95% CI` | `NW` (`10,165` px) | `NE_LidarGap` (`12,511` px) | `SW` (`20,534` px) | `SE` (`17,778` px) |
|---|---|---:|---:|---:|---:|---:|---:|
| `CTRL-1` | Legacy `GEMSDOE36` `H6` static raster (control) | `0.000094` | `[0.000049, 0.000146]` | `0.00014` | `0.00004` | `0.00011` | `0.00009` |
| `CTRL-2` | Reconstructed 19-band raw `training_features` HGB (`d=3`) OOF + ridge NMS | `0.057959` | `[0.048011, 0.068518]` | `0.04707` | `0.08242` | `0.04079` | `0.06608` |
| `EXP-1` | Unsupervised 4-pillar physical concordance (`catalogue_features=[]`) + submodular ridge emission | `0.091617` | `[0.080409, 0.103325]` | `0.07163` | `0.10985` | `0.07348` | `0.11105` |
| `EXP-2` | 17-feature local physical `NSQ-PCC` OOF (no raw elev/slope) + submodular ridge emission | `0.110085` | `[0.100410, 0.119903]` | `0.09930` | `0.13132` | `0.09597` | `0.11695` |
| **`EXP-3`** | **Full 25-feature `H36-CTRB` (`NSQ-PCC` + 1.5 km strike worms + trunk relay/tip + submodular ridge)** | **`0.114425`** | **`[0.103795, 0.125756]`** | **`0.10488`** | **`0.13141`** | **`0.11022`** | **`0.11227`** |
| *Parallel `H36-GPS`* | *`C1` (59 base + 7 graben-pair features, `evidence/h36_run_card.json`)* | *`0.132026`* | *`[0.120531, 0.144335]`* | *`0.1416`* | *`0.1740`* | *`0.0829`* | *`0.1509`* |
| *Parallel `B0`* | *59-feature multi-scale topographic/geophysical OOF HGB (`evidence/h36_run_card.json`)* | *`0.133749`* | *`[0.122241, 0.146035]`* | *`0.1474`* | *`0.1729`* | *`0.0880`* | *`0.1484`* |
| *Recorded Group Best* | *`GEMSDOE24` `H24-GVC1` (recorded on `gems-segment-pooled-v1`, not re-run)* | *`0.148760`* | *`[0.134130, 0.163700]`* | — | — | — | — |

### Key Scientific Takeaway Across Lanes
- **`SW` (Walker Lane) Orthogonal Breakthrough:** `H36-CTRB` (`EXP-3`) achieves **`SW = 0.11022`**, outperforming `H36-GPS` (`0.0829`, **`+0.0273`**), `B0` (`0.0880`, **`+0.0222`**), and `GEMSDOE24 RSHG1` (`0.0799`, **`+0.0303`**) in the transtensional Walker Lane quadrant, while maintaining **zero `> 70%` overlaps against all `191` normal-coverage (`< 40%`) rasters** (`51.01%` max across all `107` owner-scored rasters; `33.95%` vs `GEMSDOE32`).
- **Fail-Closed Weekly Slot Verdict (`verdict: "negative"`):** Because `H36-CTRB` (`0.114425`) omits multi-scale elevation/slope features and therefore trails `B0` (`0.13375`) and the recorded group best `GEMSDOE24 H24-GVC1` (`0.14876`) in `NW/NE/SE`, and because 4 unsubmitted `41.3%–55.4%`-coverage blanket sweeps in `uniqueness_registry.json` (`198` rasters) exceed the literal `70%` overlap ceiling (`max = 83.88%`), the automated release gate sets **`verdict: "negative"` (`DOWNLOAD: YES · SUBMIT: NO — HOLD WEEKLY LIVE SLOT`)**.
- See also [`forensic_audit_and_results_2026-10-25.md`](forensic_audit_and_results_2026-10-25.md), [`why-02778.md`](why-02778.md), and [`../../knowledge/h36_findings_2026-10-25.md`](../../knowledge/h36_findings_2026-10-25.md).
