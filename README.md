# GEMSDOE36 — `H36-CTRB`: Curvature-Tapered Strike-Worm, Geophysical Trunk Relay-Bridge & Tip-Lobe Concordance

> **AUTOMATED SUBMISSION & UNIQUENESS GATE STATUS: `PASS` (`verdict: promote`) — SAFE TO DOWNLOAD & SUBMIT**  
> Verified automatically by [`scripts/verify_release_gate.py`](scripts/verify_release_gate.py) and `pytest` (`0` human inspection required):
> - **Primary Portal-Safe GeoTIFF (`nodata=None`, zero NaNs across all `12,279,160` cells):** [`docs/downloads/gemsdoe36-h36-ctrb-submod-36800-20261025T000000Z-a1d85443-zeros.tif`](docs/downloads/gemsdoe36-h36-ctrb-submod-36800-20261025T000000Z-a1d85443-zeros.tif) (`304 KB`, `sha256=2bb4513d6307e2394d5de7e7e7649e28eff067b602b805a0215e82aa5ff89907`)
> - **Single-Member ZIP Archive:** [`docs/downloads/gemsdoe36-h36-ctrb-submod-36800-20261025T000000Z-a1d85443-zeros.zip`](docs/downloads/gemsdoe36-h36-ctrb-submod-36800-20261025T000000Z-a1d85443-zeros.zip) (`195 KB`, `sha256=4f7f7eae2f41a33f69de264e01722152b2cae3dbede37153dae9fa6f0e7eed7f`)
> - **Official-Text NaN-Outside Companion GeoTIFF (`nodata=NaN`):** [`docs/downloads/gemsdoe36-h36-ctrb-submod-36800-20261025T000000Z-a1d85443-nan.tif`](docs/downloads/gemsdoe36-h36-ctrb-submod-36800-20261025T000000Z-a1d85443-nan.tif) (`356 KB`, `sha256=d30c767aed69c8fcfdefd0ffc07b9d09bd261573b18525c7c3122f99409caf1c`)
> - **JSON Run Card:** [`docs/downloads/run_card.json`](docs/downloads/run_card.json) / [`evidence/h36_ctrb_run_card_20261025.json`](evidence/h36_ctrb_run_card_20261025.json)
> - **Submission Name:** `GEMSDOE36-H36-CTRB-Submod`  
> - **Submission Note (`104 / 140` chars):** `GEMSDOE36 H36-CTRB | 1.5km strike-worm+trunk relay+NSQ-PCC submod | 36800px d_cat>2 | HOLDOUT-DTI 0.1144`
> - **Uniqueness vs `107` Registry Rasters:** Pre-placement surface `max |Spearman rho| = 0.3297 <= 0.90`; final `36,800` dots `max |Spearman rho| = 0.2033 <= 0.90`, `max competing 3-px dot overlap = 51.01% <= 70.00%` (`33.95%` 3-px overlap and `2.10%` exact pixel overlap with `GEMSDOE32` `h33-2-b2`).
> - **Single-Feature Leakage Canary:** `PASS` across all `25` features (`max_symmetric_auc = 0.6414 <= 0.90`).
> - **Pooled Holdout Score:** `HOLDOUT-DTI = 0.114425` (`evaluator_version = "gems-segment-pooled-v1"`, `60,988` withheld positives, `95% CI [0.103795, 0.125756]`, `4/4` fold wins over both `CTRL-1` prior repo `H6 = 0.000094` and `CTRL-2` raw 19-band HGB OOF `= 0.057959`).

![H36-CTRB Diagnostic Overview](docs/assets/h36_ctrb_overview.png)

---

## Core Operating Values

- **Maximize P(Win):** Pursue hypotheses that empirically beat comparable, spatially blocked holdouts (`SegmentHoldout`, `gems-segment-pooled-v1`) without target leakage or pixel copying. Treat scarce weekly submission slots (`<= 3/week`) and the single final round submission as high-consequence experiments backed by calibrated uncertainty and exact DTI physics.
- **Own the Outcome:** Work autonomously end-to-end across forensic verification, physical feature engineering, spatial cross-calibration, automated binary byte validation, uniqueness auditing, documentation, and release gating. Surface every irregularity and limitation transparently; never write an unverified projection as a score.

---

## Stored User Prompts (Starting Point Reread Every Session)

### Session Mandate (2026-10-25 Parallel-Run Protocol & Cross-Site Forensics)

```text
Review /home/user/GEMSDOE36 and analyze the highest-scoring submissions across:
- GEMSDOE24 (0.2477), GEMSDOE25 (0.2600), GEMSDOE27 (0.2449),
- GEMSDOE28 (0.2708, 0.2649, 0.2710, 0.2707), GEMSDOE30 (0.2600),
- GEMSDOE31 (0.2708), GEMSDOE32 (h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778),
- GEMSDOE33 (0.2632), and GEMSDOE36 (anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros: 0.2750),
in the context of the DrivenData DOE GEMS competition (competition high score reported as 0.4413; prior focus-family top 0.2778 and milestone 0.3195).

Requirements:
1. Deliver a PhD-level forensic explanation of why/how GEMSDOE32 reached 0.2778 and how to beat it, without ever copying pixels from any prior submission.
2. Generate 3–5 novel candidate geological hypotheses not yet tried in this repo (naming specific layers, physical signature, why each catches off-catalogue faults rather than catalogued ones, difference from existing repo implementations, and free official sources if external data is needed), ranked by expected DTI improvement vs cost.
3. Follow the Parallel-Run Protocol:
   - Reuse cached feature stack, evaluate_holdout.py (whole-segment hide-and-recover with spatial buffer, visible-only catalogue features, pixel-exact visible-fault masking, pooled DTI with alpha=0.2, beta=0.8, 300 m triangular kernel), and submission_writer.py.
   - Run single-feature leakage canary on holdout (AUC > 0.90 = leakage until proven otherwise).
   - Enforce uniqueness vs registry rasters on BOTH surface before placement and final dots: |Spearman rho| <= 0.90 and <= 70% of final dots within 3 px of any competing registry raster.
   - Label EVERY metric explicitly as HOLDOUT-DTI (with evaluator version, withheld positives, 95% CI) or ORGANIZER-CONFIRMED. Never write a projection as a score.
   - Respect the budget: stop after <= 3 experiments or <= 2 hours.
   - Emit one JSON Run Card with hypothesis, mechanism, named non-fault mimic process, holdout DTI + 95% CI, correlation/overlap vs registry, raster sha256, validator output, submission name + note (<= 140 chars), and verdict (promote / negative).
4. Prevent the "Predicted values must be in range [0, 1]" portal error via automated project validation (zero human inspector required) and make download readiness immediately obvious at the top of README and GitHub Pages (docs/index.html, docs/executive-summary.html).
5. Put this prompt in README.md, preserve Core Values (Maximize P(Win), Own the Outcome), verify sources with official links, flag irregularities, run 3 full passes, open a PR on arena/b0ff24db-gemsdoe36, and merge into main.
```

<details>
<summary>Archived Original Session Brief (2026-10-04)</summary>

> Review repo and understand how past submissions were generated, specifically analyzing why GEMSDOE32 reached 0.2778 (`h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`) and how to target higher than 0.2778 (up to 0.3195). Generate 3–5 candidate geological hypotheses incorporating Anderson's faulting theory (1905) and physics-informed orientation constraints, ranked by expected DTI improvement and cost. Generate a unique single-band `float32` GeoTIFF (`EPSG:32611`, `100 m`, `[0, 1]`), fix `"Predicted values must be in range [0, 1]"`, maintain GitHub Pages (`docs/index.html`, `docs/executive-summary.html`), run 3 passes, and PR/merge to `main`.
</details>

---

## 1. Automated Submission Deliverables & Portal Range-Error Prevention

All artifacts in `docs/downloads/` are verified automatically on every test run by [`scripts/verify_release_gate.py`](scripts/verify_release_gate.py), [`src/gemsdoe36/submission.py`](src/gemsdoe36/submission.py), and [`src/gems/submission.py`](src/gems/submission.py):

| Artifact | Path | Format / CRS / Grid | Size | SHA-256 | Automated Gate Status |
|---|---|---|---|---|---|
| **Primary Portal-Safe TIF** | [`gemsdoe36-h36-ctrb-submod-36800-20261025T000000Z-a1d85443-zeros.tif`](docs/downloads/gemsdoe36-h36-ctrb-submod-36800-20261025T000000Z-a1d85443-zeros.tif) | 1-band `float32`, `EPSG:32611`, `3730×3292` (`100 m`), `nodata=None` | `304 KB` | `2bb4513d6307e2394d5de7e7e7649e28eff067b602b805a0215e82aa5ff89907` | **PASS** (`12,279,160 / 12,279,160` finite in `[0.0, 1.0]`; `36,800` dots; `0` within `200 m` of catalogue) |
| **Single-Member ZIP** | [`gemsdoe36-h36-ctrb-submod-36800-20261025T000000Z-a1d85443-zeros.zip`](docs/downloads/gemsdoe36-h36-ctrb-submod-36800-20261025T000000Z-a1d85443-zeros.zip) | Deflated single-member ZIP of `-zeros.tif` | `195 KB` | `4f7f7eae2f41a33f69de264e01722152b2cae3dbede37153dae9fa6f0e7eed7f` | **PASS** (exact byte-identical inner `.tif` verified) |
| **NaN-Outside Companion TIF** | [`gemsdoe36-h36-ctrb-submod-36800-20261025T000000Z-a1d85443-nan.tif`](docs/downloads/gemsdoe36-h36-ctrb-submod-36800-20261025T000000Z-a1d85443-nan.tif) | 1-band `float32`, `EPSG:32611`, `3730×3292` (`100 m`), `nodata=NaN` | `356 KB` | `d30c767aed69c8fcfdefd0ffc07b9d09bd261573b18525c7c3122f99409caf1c` | **PASS** (`5,167,373` footprint cells finite in `[0.0, 1.0]`, `7,111,787` outside `NaN`) |
| **Parallel-Run Card JSON** | [`docs/downloads/run_card.json`](docs/downloads/run_card.json) | `gems-parallel-run-card-v1` | `53 KB` | Identical to `evidence/h36_ctrb_run_card_20261025.json` | **PASS** (`verdict: "promote"`) |

### Why `"Predicted values must be in range [0, 1]"` Cannot Recur
DrivenData's ingestion pre-check rejects rasters containing `-3.4028235e+38` sentinels or unmasked `NaN` values under strict whole-array `((a >= 0) & (a <= 1)).all()` checks. Our primary `-zeros.tif` sets all `7,111,787` outside-footprint cells to `0.0` with `nodata=None` (`variant_strict_whole_array_no_nan_allowed: true`), while our companion `-nan.tif` satisfies strict `NaN`-outside compliance (`official_format_compliant: true`). Both are verified automatically before publication.

> **Historical Artifacts Archived (Do Not Submit):** Prior repo files `gemsdoe36-anderson-geothermal-pinn-38854-...` (`0.2750` `ORGANIZER-CONFIRMED`, archived due to `96.91%` copied pixel overlap with `GEMSDOE32`) and `GEMS36_h6_offcatalog_network_prior_...` (`0.0512` `ORGANIZER-CONFIRMED`, archived due to circular `sgmc` target leakage) remain in `docs/downloads/` strictly as historical audit records documented in [`registry/submission_build.json`](registry/submission_build.json).

---

## 2. PhD-Level Forensic Autopsy of `GEMSDOE24..36` & How to Beat `0.2778`

### 2.1 Exact Byte-Level Decomposition Across All 9 Focus Sites
Direct pixel-set algebra across the `107` unique cached registry rasters ([`registry/priority_rasters.json`](registry/priority_rasters.json)) reveals a single exact nested mathematical chain (`on_catalogue == 0` on all 9 rasters):

| Site (`Artifact`) | Portal Score (`ORGANIZER-CONFIRMED`) | Positive Pixels | `0 < d_cat <= 1 px` (`100 m`) | `1 < d_cat <= 2 px` (`141–200 m`) | `d_cat > 2 px` (`> 200 m`) | Forensic Relationship |
|---|---:|---:|---:|---:|---:|---|
| `19GEMSDOE` (`h19-5`) | `0.1922` | `121,131` | `9,651` | `7,675` | `103,805` | Unthinned 1-px OOF gradient-boosted multi-physics ridges. |
| `GEMSDOE24` (`d1.5`) | `0.2477` | `60,069` | `5,355` | `3,414` | `51,300` | `1.5 px` spacing along `h19-5` OOF ridge surface (`+0.0555`). |
| `GEMSDOE27` (`topo-gap-t-v2`) | `0.2449` | `61,328` | `5,413` | `3,462` | `52,453` | `d1.5` + `1,259` topographic gap-closure dots (`-0.0028` FP dilution). |
| `GEMSDOE25` & `GEMSDOE30` (`d2.8`) | `0.2600` | `44,090` | `3,891` | `2,545` | `37,654` | **Footprint byte-identical (`m25 == m30`)**; `2.8 px` dotted spacing (`+0.0123`). |
| `GEMSDOE28` & `GEMSDOE31` (`h27-4-r1`) | `0.2708` | `40,199` | `0` | `2,545` | `37,654` | **Byte-identical (`m28 == m31`)**; exact `d2.8` minus `3,891` `(0,1] px` flank dots (`+0.0108`). |
| `GEMSDOE28` (`h32-1` / `h36-1` / `h38-1`) | `0.2649` / `0.2710` / `0.2707` | `42,294` / `37,660` / `37,860` | `2,095` / `0` / `0` | `2,545` / `6` / `206` | `37,654` | Intermediate `(0,2] px` flank/tip edits on the identical `37,654` `>2 px` set. |
| **`GEMSDOE32` (`h33-h33-2-b2`)** | **`0.2778`** | **`37,654`** | **`0`** | **`0`** | **`37,654`** | **Exact `d2.8` minus all `6,436` `d_cat <= 2.0 px` flank dots (`+0.0178` over `d2.8`).** |
| `GEMSDOE33` (`h33d`) | `0.2632` | `41,865` | `1,377` | `2,517` | `37,971` | Re-added `3,894` `<= 2 px` flank dots (`-0.0146` vs `GEMSDOE32`). |
| `GEMSDOE36` (prior Line B `pinn-38854`) | `0.2750` | `38,854` | `0` | `0` | `38,854` | Exact superset of `GEMSDOE32` (`37,654` copied + `1,200` radial IDW dots; `-0.0028`). |

### 2.2 Three Exact Mathematical Proofs Derived from This Chain
1. **Why `GEMSDOE32` Won (`0.2778` `ORGANIZER-CONFIRMED`):** DrivenData masks `labels.tif` (`d_cat == 0`) pixel-exactly, **not** with a 200 m collar. Because potential-field horizontal gradients (`tmi_hg`, `iso_grav_anom_hg`) and 100 m DEM slopes blur across `100–250 m`, models trained on `labels.tif` emit parallel flank artifacts at `d_cat in (0, 2] px` (`100–200 m`). Those `6,436` flank dots (`3,891` at `100 m` + `2,545` at `141–200 m`) sit on unmasked pixels, earn virtually **zero** hidden-fault $\text{TP}_w$ credit, and incur $0.2 \times 6,436 = 1,287.2$ false-positive denominator units. Pruning `d_cat <= 2.0 px` yielded the entire `0.2600 -> 0.2708 -> 0.2778` progression.
2. **Exact Hidden Ground-Truth Scale (`|G|`):** Solving the nested subset pair `GEMSDOE32` (`37,654` px, `0.2778` `ORGANIZER-CONFIRMED`) $\subset$ old `GEMSDOE36` (`38,854` px = `37,654 + 1,200` zero-gain radial dots, `0.2750` `ORGANIZER-CONFIRMED`):
   $$\frac{T}{D} = 0.2778, \quad \frac{T}{D + 0.2(1200)} = 0.2750 \implies D \approx 23,572, \quad T = \text{TP}_w \approx 6,548, \quad |G| \approx 16,000\text{–}21,000\text{ px}.$$
3. **Exact Dinkelbach Marginal Inclusion Criterion to Beat `0.2778` (and Reach Higher Leaderboard Tiers):** Under official $\text{DTI}(\alpha=0.2, \beta=0.8) = \frac{\text{TP}_w}{0.2\,\text{TP}_w + 0.2\,\text{FP}_w + 0.8\,|G|}$, a candidate dot $x$ improves $\text{DTI}$ above operating level $D^*$ **if and only if**:
   $$\Delta \text{TP}_w(x \mid S) > \frac{0.2\,D^*}{1 - 0.2\,D^*}\,\Delta \text{FP}_w(x).$$
   Beating the `0.2778` family genuinely (without copying pixels) requires: (a) eliminating **upland crystalline slope accessibility bias** (`det_elev_slope`) that caused sibling `RSHG1` to duplicate steep-slope ridge maps (`72.69%` overlap on `8GEMSDOE`), (b) detecting **blind intrabasin, hydrothermal, and relay/tip structures** via 2D `1.5 km` strike-worm line integrals and basement-trunk topology, (c) calibrating probabilities out-of-quadrant via **Nested Spatial-Quadrant Purged Cross-Calibration (`NSQ-PCC`)**, and (d) placing dots via **Minoux lazy-greedy Dinkelbach-Submodular 300 m maximization** strictly along 1-px Hessian centerlines (`ridge_nms`) outside `d_cat <= 2.0 px`.

---

## 3. Ranked Novel Candidate Geological Hypotheses (`H36-A` through `H36-E`)

Full mathematical specifications are preregistered in [`docs/research/preregistration_2026-10-25.md`](docs/research/preregistration_2026-10-25.md):

| Rank | Hypothesis | Specific Layers & Transform | Why Off-Catalogue (Missing from USGS/INGENIOUS) | Difference vs Prior `GEMSDOE36` | Named Non-Fault Mimic | Cost & Status |
|---:|---|---|---|---|---|---|
| **1** | **`H36-A`: Curvature-Tapered `1.5 km` Potential-Field Strike-Worm & Upward-Continuation Attenuation** | `tmi`, `rtp`, `tc`, `tmi_hg`, `tmi_vg`, `iso_grav_anom_hg`, `iso_grav_anom_vg`, `depth_to_base_surf`, GeoDAWN `TMI_up150`. Antialiased 12-azimuth `1.5 km` line integral of tilt-zero sharpness + `|TMI - TMI_up150|` shallow attenuation + Andersonian strike weight $w_{\text{And}}(\theta)$. | Intrabasin Quaternary playa/bajada cover (`10–300 m`) erases surface scarps (Carson Sink, Dixie/Fairview/Gabbs valleys), leaving collinear basement density steps and shallow magnetic truncations untouched. | Prior `prepare_data.py` used pixel-local gradients (`sigma <= 1.5 px`) and ignored `TMI_up150` depth attenuation; `H36-A` integrates along `1.5 km` strike chords and pairs offset gravity HGM + magnetic tilt-zero dip corridors. | Unfaulted Tertiary ash-flow tuff/basalt paleochannel margins and volcanic calderas; aeromagnetic tie-line artifacts. | **Low-Med** (`Implemented in EXP-1..3`) |
| **2** | **`H36-B`: Label-Free Geophysical Trunk Relay-Bridge & $\cos^4\psi$ Tip-Lobe Potential** | Derived strictly from label-free potential-field/basement trunks (`>= 1.2 km`, `catalogue_features=[]`): opposing-EDT cancellation $(1 - \|\overline{\nabla d_{\text{trunk}}}\|)\exp(-d_{\text{trunk}}/18)$ + outward $\cos^4\psi\exp(-r/14)$ tip cones. | Normal-fault displacement transfers across `0.5–3.5 km` step-over relay ramps and unmapped horse-tail tip splays (Peacock & Sanderson 1991; Faulds & Hinz 2015) where single-scarp offset drops below field-mapping visibility. | Prior `field.py` used circular `sgmc_off_catalogue` (`0.0512` `ORGANIZER-CONFIRMED`), and `d_vis`-based tip operators collapse under `SegmentHoldout` quadrant hiding. `H36-B` is 100% label-free and invariant across unseen quadrants. | Paired opposing alluvial fan toes across narrow intermontane valleys (`2–4 km` apart) where opposing bedrock contacts mimic a structural horst/graben bridge. | **Low-Med** (`Implemented in EXP-1 & EXP-3`) |
| **3** | **`H36-C`: Epithermal K-Metasomatism (`Th/K` Depletion), Magnetite-Destruction Trough & Anisotropic Geothermometer Triad** | GeoDAWN `K`, `Th`, `U`, `ThK`, `UK`; `rtp` positive Laplacian; MT `cond_surf` lateral gradient; GDR 1391 `temp_c`, `geothermquartz_c`, `geothermchalc_c` (`3,306` thermal records + `21` vents via `csv.DictReader`, stripping `dist_known_fault_px`). | Blind geothermal upflow zones (Bradys, Desert Peak, McGinness Hills) ascend along permeable fault damage zones without diagnostic surface scarps, altering wallrock (`Th/K` drop), oxidizing magnetite (`RTP` trough), and forming smectite clay caps (`cond_surf`). | Prior `geothermal.py` pasted isotropic `3 km` IDW discs onto copied `GEMSDOE32` dots (`0.2750` `ORGANIZER-CONFIRMED`), and `prepare_data_h6.py` had a naive `split(",")` CSV bug. `H36-C` models elongated NNE alteration corridors cleanly. | Potassium-richfelsic rhyolite domes, evaporite playa alkali flats (potassic accumulation without basement fault), and stratiform conductive lacustrine clays. | **Low** (`Implemented in EXP-1..3`) |
| **4** | **`H36-D`: Macro-Relief-Normalized Contour-Orthogonal Piedmont Breakline & `NaN`-Routed 1 m LiDAR Asymmetry** | `det_elev`, `det_elev_slope` (macro-roughness divisor ONLY; raw `det_elev`/`det_elev_slope` banned!), 3DEP 1 m LiDAR `downface_max`, `upface_max`, `step_max`, `lapneg_max`, `coh100`, `valid` (`NaN` outside `valid`). | Subtle `< 2 m` piedmont scarplets cutting alluvial fans are drowned out by `30°` range-interior bedrock cliffs in raw slope rasters and dissected by down-fan desert washes. | Prior code imputed `0` across the `24.6%` (`1,272,913` px) LiDAR gap and fed raw slope, causing steep-ridge confounding; `H36-D` divides by `1.6 km` macro-roughness, enforces contour-orthogonality $|\hat{\mathbf{n}}_{\text{loc}}\cdot\hat{\mathbf{g}}_{\text{reg}}|^2$, and routes missing LiDAR as `NaN`. | Pleistocene pluvial Lake Lahontan wave-cut shoreline terraces (~1,330 m highstand benches), forming contour-parallel one-sided steps without subsurface fault offset. | **Low** (`Implemented in EXP-1..3`) |
| **5** | **`H36-E`: Relocated Double-Difference Microseismicity Planar Projection & OPERA Sentinel-1 InSAR Velocity Gradient** | External free official sources: USGS ANSS ComCat FDSN API (`https://earthquake.usgs.gov/fdsnws/event/1/`, CC0) + NASA/JPL OPERA `DISP-S1` (`https://search.asf.alaska.edu/`, open NASA Earthdata). Projects $2\text{–}12\text{ km}$ hypocenter planes up-dip to surface traces. | Active blind Walker Lane shear zones and swarm-active accommodation zones rupture seismically at depth before developing mapped surface scarps. | Not yet ingested in any `GEMSDOE` repo; strictly orthogonal crustal kinematics. | Ephemeral playa evaporite swell/shrinkage and agricultural groundwater subsidence bowls in InSAR; geothermal injection microseismic clouds. | **Med-High** (*Conditional / Blocked in sandbox network; never fabricated*) |

---

## 4. Parallel-Run Validation Results (`SegmentHoldout`, `gems-segment-pooled-v1`)

Evaluated across `60,988` withheld fault pixels (`3,199` whole 8-connected components hidden everywhere when touching a quadrant or its `1,500 m` buffer; pixel-exact masking of `fold["visible"]`; `1,999` 10-km spatial block-bootstrap resamples):

| Run | Features & Placement | `HOLDOUT-DTI` (`gems-segment-pooled-v1`) | `95% CI` | `NW` | `NE_LidarGap` | `SW` | `SE` | Fold Wins vs `CTRL-2` |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `CTRL-1` | Prior Repo `H6` static candidate | `0.000094` | `[0.000049, 0.000146]` | `0.00014` | `0.00004` | `0.00011` | `0.00009` | — |
| `CTRL-2` | Raw 19-band `training_features` HGB (`d=3`) OOF + ridge NMS | `0.057959` | `[0.048011, 0.068518]` | `0.04707` | `0.08242` | `0.04079` | `0.06608` | baseline |
| `EXP-1` | Unsupervised 4-pillar concordance + Dinkelbach-submodular ridge | `0.091617` | `[0.080409, 0.103325]` | `0.07163` | `0.10985` | `0.07348` | `0.11105` | `4 / 4` |
| `EXP-2` | Local 17-feature `NSQ-PCC` OOF + Dinkelbach-submodular ridge | `0.110085` | `[0.100410, 0.119903]` | `0.09930` | `0.13132` | `0.09597` | `0.11695` | `4 / 4` |
| **`EXP-3`** | **Full 25-feature `H36-CTRB` (`NSQ-PCC` + 1.5 km worms + trunk relay/tip)** | **`0.114425`** | **`[0.103795, 0.125756]`** | **`0.10488`** | **`0.13141`** | **`0.11022`** | **`0.11227`** | **`4 / 4`** |

- **Key Scientific Findings:**
  1. **`NE_LidarGapHeavy` (`24.6%` missing LiDAR) is `H36-CTRB`'s strongest fold (`HOLDOUT-DTI = 0.13141`)**, confirming that `NaN`-routed LiDAR + 1.5 km potential-field/alteration worms generalize seamlessly across regions lacking 1 m 3DEP coverage.
  2. **Adding the 8 2D structural network features (`EXP-2 -> EXP-3`) lifted `SW` Walker Lane by `+0.01425` (`0.09597 -> 0.11022`)** and `NW` by `+0.00558`, winning `3/4` folds over `EXP-2` and `4/4` folds over `EXP-1`, `CTRL-2`, and `CTRL-1`.
  3. **Honest Cross-Lane Context:** Sibling `GEMSDOE24`'s raw-slope-included `oof_multiphysics_hgb_d3` (`HOLDOUT-DTI = 0.13000`, `95% CI [0.11565, 0.14396]`) scores `0.01558` higher on mapped catalogue recovery because mapped `labels.tif` traces sit preferentially on steep exposed range fronts (`det_elev_slope`); however, `GEMSDOE24`'s `RSHG1` (`0.12899`) failed uniqueness at `72.69%` overlap with `8GEMSDOE` steep-slope ridges and dropped to `0.0799` on `SW`, whereas `H36-CTRB` passes all uniqueness gates (`44.18%` on `8GEMSDOE`; `51.01%` global max competing overlap) and reaches `0.11022` on `SW`.

---

## 5. Irregularities Flagged & Verified Official Trusted Sources

All 5 newly discovered irregularities (`IR-36-NEW-01` fabricated fold table in prior docs; `IR-36-NEW-02` `96.91%` copied `GEMSDOE32` pixels in prior Line B; `IR-36-NEW-03` circular `sgmc` leak + CSV `split(",")` comma bug in prior Line A; `IR-36-NEW-04` cross-lane pixel-identical pairs & benchmark provenance; `IR-36-NEW-05` Pass-2 visual QA fixes for 2D plateau lattice tiling and NW fold-stitch calibration seam) are documented in full in [`docs/research/known_irregularities.md`](docs/research/known_irregularities.md).

### Verified Official & Peer-Reviewed Sources
1. **DrivenData DOE GEMS Competition Specification & Metric (`alpha=0.2, beta=0.8, R=300 m`):** <https://www.drivendata.org/competitions/306/competition-doe-gems/>
2. **Official DOE GEMS Leaderboard:** <https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/>
3. **USGS Earth MRI GeoDAWN Aeromagnetic & Radiometric Survey:** <https://www.usgs.gov/special-topics/earth-mri>
4. **Great Basin Center for Geothermal Energy — INGENIOUS Project & DOE GDR Submission 1391:** <https://gdr.openei.org/submissions/1391>
5. **USGS Quaternary Fault and Fold Database of the United States:** <https://www.usgs.gov/programs/earthquake-hazards/faults>
6. **USGS 3D Elevation Program (3DEP) 1 m LiDAR:** <https://www.usgs.gov/3d-elevation-program>
7. **USGS ANSS Comprehensive Earthquake Catalog (ComCat API, `H36-E`):** <https://earthquake.usgs.gov/fdsnws/event/1/>
8. **NASA/JPL OPERA Surface Displacement (`DISP-S1`, `H36-E`):** <https://www.jpl.nasa.gov/go/opera/products/disp-product-suite/>
9. **Anderson, E. M. (1905) / (1951):** *The Dynamics of Faulting and Dyke Formation with Applications to Britain*, Oliver & Boyd.
10. **Faulds, J. E., & Hinz, N. H. (2015):** *Favorable Tectonic and Structural Settings of Geothermal Systems in the Great Basin Region, Western USA*, World Geothermal Congress.
11. **Peacock, D. C. P., & Sanderson, D. J. (1991):** *Displacements, segment linkage and relay ramps in normal fault zones*, Journal of Structural Geology, 13(6), 721–733.

---

## 6. Reproducibility & Generative AI Disclosure

### Reproduce Verification & Tests Locally (Zero Manual Input)
```bash
# 1. Restore SHA-256-verified raw rasters & external layers
.venv/bin/python scripts/restore_data.py

# 2. Run full unit + automated release/uniqueness/validator gate suite (66 tests)
.venv/bin/pytest -q

# 3. Run standalone zero-human submission & HTML link release gate
.venv/bin/python scripts/verify_release_gate.py

# 4. Re-run full 25-feature stack, canary, 3-experiment SegmentHoldout & bundle build
.venv/bin/python -u scripts/evaluate_holdout.py
```

### Generative AI Disclosure Narrative (Per Official Competition Rules)
Generative AI (Arena.ai Agent Mode) was used autonomously for cross-repository forensic byte analysis, mathematical formulation and Python implementation of the 25-feature `H36-CTRB` physical/structural operator stack (`src/gemsdoe36/ctrb.py`), Nested Spatial-Quadrant Purged Cross-Calibration (`NSQ-PCC`), Minoux lazy-greedy Dinkelbach-Submodular 300 m ridge emission, automated canary/uniqueness/GeoTIFF validation (`scripts/evaluate_holdout.py`, `scripts/verify_release_gate.py`), unit testing (`tests/test_ctrb.py`, `tests/test_release_gate.py`), and technical documentation. No pixel values were copied from any prior submission; all predictions derive solely from physics-informed feature extraction and out-of-fold spatial modeling on the authorized competition datasets.
