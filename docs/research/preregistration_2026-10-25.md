# GEMSDOE36 Preregistration — 2026-10-25 Session (`H36-CTRB`)

**Date Frozen:** 2026-10-25 UTC  
**Branch:** `arena/b0ff24db-gemsdoe36`  
**Shared Evaluator:** `src/gems/holdout.py` (`SegmentHoldout`, `evaluator_version = "gems-segment-pooled-v1"`, 4 quadrant folds, `buffer_px = 15` / `1,500 m`, whole 8-connected components hidden everywhere, pixel-exact `visible` fault masking, pooled DTI $\alpha = 0.2, \beta = 0.8, R = 300\text{ m}$ triangular kernel, 1,999 spatial-block bootstrap draws on $10\text{ km} \times 10\text{ km}$ tiles).  
**Shared Writer & Novelty Tool:** `scripts/submission_writer.py`, `src/gems/submission.py`, `src/gems/novelty.py`, `scripts/validate_submission.py`.  
**Maximum Budget (Protocol Rule 6):** $\le 3$ experiments (`EXP-1`, `EXP-2`, `EXP-3`) and $\le 2.0$ hours wall time. Zero weekly submission slots are spent automatically; promotion to a live DrivenData weekly slot is a separate owner/selector step within the platform's 3/week cap.

---

## 1. Candidate Geological Hypotheses (Preregistered & Ranked Before Execution)

### Rank #1 (Lead): `H36-A` — Curvature-Tapered Geophysical Strike-Worm, Trunk Relay-Bridge & Tip-Lobe Concordance with Nested Purged OOF Submodular DTI Emission (`H36-CTRB`)
- **Specific Layers Involved:**
  - Official 19-band `training_features.tif`: `rtp` (b2), `tmi_hg` (b3), `geod_2ndinv` (b4), `iso_grav_anom_slope` (b5), `tc` (b6), `geod_shearrate` (b7), `geod_dilaterate` (b8), `tmi_vg` (b9), `iso_grav_anom_vg` (b11), `det_elev` (b12, local breakline residual only), `iso_grav_anom` (b13), `tmi` (b14), `depth_to_base_surf` (b15), `cond_surf` (b17), `iso_grav_anom_hg` (b18), `det_elev_slope` (b19, macro-relief denominator only).
  - USGS GeoDAWN CC0 radiometric & extension grids: `rad_k`, `rad_th`, `rad_u` (`geodawn_rad_u8.tif`), `ext_thk`, `ext_uk`, `ext_tmi_up150` (`geodawn_extensions_u8.tif`).
  - USGS 3DEP 1 m LiDAR scarp derivatives: `step_max`, `lapneg_max`, `downface_max`, `upface_max`, `coh100`, `valid` (`lidar_scarp_features_u8.tif`), with native `NaN` routing in the ~31.8% non-LiDAR footprint.
  - DOE GDR 1391 (`gdr_wellspring_in_footprint.csv`, CC BY 4.0): `temp_c`, `geothermquartz_c`, `geothermchalc_c` (`dist_known_fault_px` strictly blocked).
- **Physical Signature Targeted:**
  1. *Multi-Azimuth 1.5 km Strike-Worm Persistence:* 12-azimuth ($0^\circ, 15^\circ, \dots, 165^\circ$) 15-px (`1.5 km`) Gaussian-tapered line integrals over shallow magnetic tilt zero-crossing sharpness + gravity horizontal gradient + hydrothermal alteration edges, isolating collinear brittle fault planes from point/circular anomalies.
  2. *Label-Free Geophysical Trunk Relay-Bridges & Tip Lobes:* Extracts major NNE/NW Anderson-consistent basement-step trunks purely from potential-field + basement-depth gradients (`catalogue_features = []`), then computes the opposing-EDT harmonic bridge potential $(1 - \|\overline{\nabla d_{\text{trunk}}}\|) \exp(-d_{\text{trunk}}/18)$ (peaking strictly midway between sub-parallel geophysical trunks in relay ramps and graben step-overs) and directional $\cos^4\psi$ propagation lobes ahead of geophysical trunk terminations.
  3. *Cross-Horizon Double-Angle Tensor Coherence ($S_{\text{xmod}}$):* Resultant vector length of double-angle strike vectors $(\cos 2\theta_h, \sin 2\theta_h)$ across deep gravity/basement, shallow magnetic/radiometric, and macro-relief-normalized contour-orthogonal surface breaklines.
  4. *Nested Spatial-Quadrant Purged Cross-Calibration (`NSQ-PCC`) + Exact Lazy-Greedy 300 m Submodular DTI Kernel Emission:* Leaves out each training quadrant inside `fold["train"]` to fit out-of-domain isotonic probability calibration, then maximizes expected 300 m triangular-kernel coverage $\Delta\mathbb{E}[\text{TP}_w(x\mid S)] - \lambda_{\text{fp}}\mathbb{E}[\text{FP}_w(x)]$ with $B = 2.0\text{ px}$ (`200 m`) visible-flank exclusion.
- **Why It Catches Missing / Off-Catalogue Faults:** USGS/INGENIOUS compilations predominantly mapped steep bedrock range-front scarps (`det_elev_slope`), missing inter-segment relay-ramp transfer faults, along-strike blind fault-tip extensions, and intrabasin alluvial-covered graben steps where surface slope is muted yet shallow potential-field decay, basement steps, and hydrothermal alteration remain coherent.
- **How It Differs from Everything in `GEMSDOE36`:** Zero prior submission rasters read (fixing Line B's `96.91%` pixel copy of `d28`), zero `SGMC` polylines read (fixing Line A / `H6`'s circular target leakage), excludes raw `det_elev` and raw `det_elev_slope` upland ridge confounds, and introduces label-free geophysical trunk opposing-EDT relay bridges + 12-azimuth 1.5 km strike worms + `NSQ-PCC` submodular 300 m kernel optimization.
- **Named Non-Fault Mimic:** Buried Neogene basaltic feeder dikes or welded ash-flow tuff paleochannel margins between two mountain ranges (mitigated by requiring gravity/basement step concordance and cross-horizon strike coherence).
- **Expected Impact & Cost:** Highest expected `HOLDOUT-DTI` gain (`+0.02` to `+0.06` over unsupervised and raw-band baselines); **Medium** cost (~90 s compute, `< 1.0 GiB` RAM).

### Rank #2: `H36-B` — Hydrothermal Potassic-Argillic Alteration Triad & Chemical Geothermometer Upflow Detector (`HAPB`)
- **Specific Layers Involved:** `ext_thk` (Th/K), `ext_uk` (U/K), `rad_k/th/u`, `cond_surf` (b17), `rtp` (b2), `tmi_hg/vg` (b3, b9), and GDR 1391 silica/chalcedony geothermometers (`geothermquartz_c`, `geothermchalc_c`, `temp_c`).
- **Physical Signature Targeted:** Co-located Th/K depletion troughs (potassic adularia/illite metasomatism enriching K relative to immobile Th), magnetite-destruction susceptibility troughs ($\nabla^2 \text{rtp} > 0$), MT smectite clay-cap lateral conductivity gradients ($|\nabla \text{cond\_surf}|$), and NNE-anisotropic chemical geothermometer plumes.
- **Why It Catches Off-Catalogue Faults:** Blind geothermal step-overs (Desert Peak / Bradys style) lack Quaternary surface scarps because strain is partitioned across distributed fracture meshes, yet paleo/modern fluid upflow permanently alters host-rock K/Th ratios, magnetization, and electrical conductivity.
- **How It Differs from `GEMSDOE36`:** Replaces `geothermal.py`'s isotropic 3 km radial `temp_c >= 130 C` blobs with parsed silica geothermometry + the 3-way mineralogical alteration triad (Th/K trough + magnetite destruction + MT conductivity edge).
- **Named Non-Fault Mimic:** Closed-basin evaporitic playa potassium concentration or unaltered high-silica rhyolite domes.
- **Expected Impact & Cost:** Moderate standalone, strong synergistic contributor inside `H36-A` / `EXP-2` / `EXP-3`; **Low** cost.

### Rank #3: `H36-C` — Alluvial-Piedmont Buried Basement-Bench Curvature & Gravity-Magnetic Tilt Zero-Crossing Sharpness (`PBB-Div`)
- **Specific Layers Involved:** `depth_to_base_surf` (b15), `iso_grav_anom_hg` (b18), `iso_grav_anom_vg` (b11), `tc` (b6), `tmi` (b14), `ext_tmi_up150`, stratified by low macro-relief piedmont fans.
- **Physical Signature Targeted:** Reciprocal-depth Blakely-Simpson tilt zero-crossing sharpness $|\nabla \text{tc}|\exp(-|\text{tc}|/\sigma)$ paired with gravity tilt zero-crossing sharpness and minimum-curvature Hessian ridges of `depth_to_base_surf` beneath Quaternary valley fill.
- **Why It Catches Off-Catalogue Faults:** Intrabasin synthetic/antithetic normal faults buried under `100–800 m` of unconsolidated alluvium have zero optical or 10 m DEM expression.
- **How It Differs from `GEMSDOE36`:** Replaces `anderson_dip.py`'s fixed-depth spatial pixel shift (proven negative `-0.01` to `-0.045` in H6 Run 6) with in-place zero-crossing curvature and upward-continuation attenuation (`TMI - TMI_up150`).
- **Named Non-Fault Mimic:** Unfaulted pre-Cenozoic granitic batholith roofs or buried erosional paleovalley walls beneath Tertiary basin fill.
- **Expected Impact & Cost:** Moderate-High in basin interiors; **Low-Medium** cost (integrated into `EXP-1..3`).

### Rank #4: `H36-D` — Macro-Relief-Normalized Contour-Orthogonal Tectonic vs. Fluvial/Shoreline Scarp Asymmetry (`TFGA`)
- **Specific Layers Involved:** `det_elev` (b12), `det_elev_slope` (b19), 1 m 3DEP LiDAR `downface_max`, `upface_max`, `step_max`, `coh100`, `valid`.
- **Physical Signature Targeted:** Divides local LRM elevation breaklines by $1.6\text{ km}$ regional ruggedness $G_{\sigma=16}(\text{det\_elev\_slope}) + \tau_0$ and multiplies by $|\hat{\mathbf{n}}_{\text{local}} \cdot \hat{\mathbf{g}}_{\text{reg}}|^2$ (keeping contour-parallel range-front/piedmont scarps while rejecting cross-contour incised fluvial washes), paired with 1 m LiDAR one-sided step polarity `|downface - upface| * coh100`.
- **Why It Catches Off-Catalogue Faults:** Subtle `< 2 m` piedmont scarplets on alluvial fans are masked by ephemeral desert washes in raw slope maps and suppressed by mountain-range dynamic range unless normalized by local macro-relief.
- **How It Differs from `GEMSDOE36`:** `prepare_data_h6.py` took unnormalized `max(step, curvature)` and imputed `0` in the 31.8% LiDAR gap; `H36-D` separates one-sided tectonic steps from two-sided gullies, suppresses down-fan washes, and routes missing LiDAR as `NaN`.
- **Named Non-Fault Mimic:** Pleistocene pluvial Lake Lahontan wave-cut shoreline terraces (~1,330 m highstand benches), which form contour-parallel one-sided steps without subsurface fault offset.
- **Expected Impact & Cost:** Moderate; **Low** cost (integrated into `EXP-1..3`).

### Rank #5 (Conditional / External Data Blocked in Sandbox): `H36-E` — Relocated Double-Difference Microseismicity Planar Projection & OPERA Sentinel-1 InSAR Velocity Gradient
- **Specific Free Official Sources Required:** USGS ANSS ComCat FDSN API (`https://earthquake.usgs.gov/fdsnws/event/1/`, CC0 public domain) + NASA/JPL OPERA `DISP-S1` (`https://search.asf.alaska.edu/`, open data requiring NASA Earthdata login).
- **Obtainability Check:** Outbound sandbox access is restricted to `github.com`, `pypi.org`, and `npmjs.org`; therefore `H36-E` cannot be fetched autonomously in this environment and is recorded strictly as a future external-data upgrade, never fabricated.

---

## 2. Locked 3-Experiment Progression & Promotion Criteria

All 3 experiments use the exact same `SegmentHoldout` (`gems-segment-pooled-v1`, 60,988 withheld positives, `buffer_px = 15`), exact $B = 2.0\text{ px}$ (`200 m`) visible-flank exclusion, and target full-footprint emission rate `37,654 / 5,167,373 = 0.00728687`.

1. **`EXP-1` (`H36-Unsup-Concordance-Submod`):** Label-free rank-corroborated fusion of Pillars 1–3 (`H36-A..D` physical surfaces) + exact 300 m submodular DTI kernel emission.
2. **`EXP-2` (`H36-LocalPhys-NSQPCC-Submod`):** Nested Spatial-Quadrant Purged Cross-Calibrated (`NSQ-PCC`) OOF `HistGradientBoostingClassifier` over the 17 pixel-local physical/alteration/contour-orthogonal features (no 1.5 km strike worms, no geophysical trunk relay bridges or tip lobes, no cross-horizon tensor coherence) + exact 300 m submodular DTI kernel emission.
3. **`EXP-3` (`H36-CTRB-NSQPCC-Submod` — Primary Candidate):** Full 25-feature `H36-CTRB` stack (`EXP-2` + 12-azimuth 1.5 km potential-field & alteration strike worms + label-free geophysical trunk opposing-EDT relay bridges & tip propagation lobes + cross-horizon double-angle tensor coherence) with `NSQ-PCC` OOF probability calibration and adaptive train-calibrated submodular 300 m DTI kernel emission.

### Automated Gate Rules (Zero Human Intervention):
1. **Leakage Canary Gate:** Every single one of the 25 features tested alone on `SegmentHoldout.canary()` must satisfy $\max(\text{AUC}, 1 - \text{AUC}) \le 0.90$ pooled and in every fold.
2. **Pre-Placement Surface & Final-Dot Uniqueness Gate:** Checked via `src/gems/novelty.py` against all 107 unique rasters across `GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, 36` + local historic calibration rasters:
   - Pre-placement surface `max |Spearman rho| <= 0.90` across all 107 rasters;
   - Final binary dots `max |Spearman rho| <= 0.90` across all 107 rasters AND `max 3-px directional dot overlap <= 0.70` across all 106 competing method rasters (`competing_method_passed == True`).
3. **Holdout Promotion Gate:** Primary candidate (`EXP-3`) must strictly beat:
   - In-repo `CTRL-G36-H6-NoSGMC` (leak-free `field.py` with `enable_sgmc_prior=False`),
   - Unsupervised `EXP-1`, and
   - Standard raw-band OOF ridge baseline `CTRL-Raw19-OOF`,
   with a strictly positive 95% paired spatial-block bootstrap CI (`ci95_low > 0`) against the strongest control, AND win $\ge 3/4$ spatial folds.
4. **Format & Portal Safety Gate:** Primary `-zeros.tif` (`nodata=None`, 100% of 12,279,160 cells finite in `[0.0, 1.0]`) and companion `-nan.tif` (`nodata=NaN`, 5,167,373 footprint cells finite in `[0.0, 1.0]`) must pass all hard checks in both `src/gems/submission.py:check_variants` and `scripts/validate_submission.py`, with `0` pixels within `200 m` of `existing_faults.tif`, a unique submission name, and a note $\le 140$ characters.
