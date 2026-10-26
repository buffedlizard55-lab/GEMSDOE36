# Preregistration — Lane `GVSC-36`: Geothermal Vent-Conduit Strike-Projected Up-Gradient & Multi-Scale Structural Fault Discovery

- **Date (UTC):** `2026-10-26`
- **Repository / Branch:** `buffedlizard55-lab/GEMSDOE36` (`arena/20b1a132-gemsdoe36`, branched after `6dae454`)
- **Evaluator (Frozen):** `gems.holdout.SegmentHoldout` (`gems-segment-pooled-v1`, `3,199` whole connected fault components, `60,988` total positives, `1,500 m` = `15 px` spatial buffer, pixel-exact visible-fault exclusion, pooled `DTI(alpha=0.2, beta=0.8, 300 m triangular kernel)`, `1,999` 10 km spatial-block bootstrap draws)
- **Experiment Budget:** Strictly `<= 3` candidate experiments (`EXP-1`, `EXP-2`, `EXP-3`) against frozen repo baseline `B0` (`0.13375`), `<= 2 hours` total walltime.

---

## 1. Candidate Untried Geological Hypotheses (Ranked Before Implementation)

All four candidate hypotheses below were checked against the repository's prior merged lanes (`PINN-38854` #4, retired `H6` #5, `Lane36` #12, `H36-GPS` #13, `H36-CTRB` #14, `ATVR-36` #15, `MOE36` #17, `MTO-36` #18, `WDP-36` #19) to ensure zero duplication.

| Rank | ID | Hypothesis & Targeted Physical Signature | Specific Data Layers (Official Free Sources) | Why Missing from USGS / INGENIOUS Catalogue | Named Non-Fault Mimic Process | Expected `HOLDOUT-DTI` Lift & Cost |
|---:|---|---|---|---|---|---|
| **1 (Selected)** | **`GVSC-36` (`H36-V1`)** | **Up-Hydraulic-Gradient Geothermal Plume Back-Projection & Strike-Corroborated Paleo-Vent Conduit Discovery** + LiDAR-Shadowing De-Biased Ensemble + Prentice–Pyke Calibrated 300 m Submodular Expected-DTI Allocation | Newly restored DOE OpenEI GDR `1391` (`doi:10.15121/1881483`, CC-BY-4.0) `paleo_geothermal_regional.zip` (`281` footprint sinter/travertine/tufa/silica-sand/explosion-crater/breccia vents), `2m_temperature_probe_INGENIOUS_regional_data.zip` (`2,782` footprint `F2mDAB` shallow probes across `34` basins), `gdr_volcanic_vents_in_footprint.csv` (`21` Quaternary vents, `dist_known_fault_px` stripped), `gdr_wellspring_in_footprint.csv` (`dist_known_fault_px` stripped), plus `training_features.tif`, `lidar_scarp_features_u8.tif`, and `geodawn_{rad,extensions}_u8.tif` | Over **75%** of Great Basin geothermal systems are blind (no mapped Quaternary range-front scarp; Faulds & Hinz, 2015). Buoyant fluids ascend blind fault conduits and flow `0.4–2.0 km` down-gradient (`-∇z`) in fan gravels before discharging as `F2mDAB` plumes, warm springs, or cementing sand, while siliceous sinter/explosion craters/breccias mark fossil vent throats eroded flat after Pleistocene Lake Lahontan desiccation | Perched lateral outflow plumes in permeable paleochannels; Pleistocene Lake Lahontan (`~1,250–1,360 m`) wave-cut shoreline tufa terraces; evaporite playa brines; unfaulted volcanic flow margins | **High (`+0.012` to `+0.025` vs `B0 = 0.13375`)**; Low cost (~15 min CPU, all archives SHA-verified locally) |
| **2** | `H36-V2` | **GeoDAWN Acquisition-Block Seam & Cultural Corridor Deconfounded Tilt-Ridge Detector** (within-block z-standardization of `01_mag_anom`/`02_rtp`/`06_tc` + road/rail magnetic embankment suppression) | `training_features.tif`, `geodawn_rad_u8.tif`, USGS GeoDAWN block polygons (`doi:10.5066/P93LGLVQ`), US Census TIGER/Line roads | Prevents flight-block tie seams and highway/railroad cut-and-fill scarps from consuming top-`37,654` dot budget in flat basins | Intra-block unfaulted lithologic contacts | Moderate (`+0.002` to `+0.006`); Low cost (deferred; sibling `H24-FUSE-HCW` C2ST variant was negative) |
| **3** | `H36-V3` | **Aseismic / Locked Brittle Strain-Localization Ratio** (`geod_2ndinv` strain-rate power vs `ieq_n100a15` historical seismicity modulated by relative `depth_to_base_surf` step gradient) | `training_features.tif` (`04_geod_2ndinv`, `07_geod_shearrate`, `08_geod_dilaterate`, `15_depth_to_base_surf`, `16_ieq_n100a15`) | Captures strain-accommodating Walker Lane / Central Nevada faults with long recurrence intervals (`>2 ka`) and subdued historical M>3 seismicity | Long-wavelength GPS interpolation lobes across unfaulted bedrock blocks | Low–Moderate (`+0.002` to `+0.005`); Low cost (core dimensionless interaction incorporated into `sa_strain_seis_ratio`) |
| **4** | `H36-V4` | **NASA/ASF OPERA Sentinel-1 `DISP-S1` InSAR Phase-Gradient Groundwater-Baffle Detector** (`<300 m` horizontal velocity step `|∇v_LOS|` across flat basin floors) | Official NASA/JPL `OPERA_L3_DISP-S1_V1` 30 m LOS velocity (`https://search.asf.alaska.edu/`) + `15_depth_to_base_surf` + `19_det_elev_slope` | Detects zero-relief intrabasin fault-gouge groundwater baffles via sharp aquifer-head compartmentalization across agricultural/playa floors | Stratigraphic clay-sand facies pinchouts and pumping-well cones of depression | High ceiling (`+0.010+`), **NOT VIABLE IN THIS SANDBOX** (`asf.alaska.edu` blocked by outbound allowlist; documented for CI runner ingest) |

---

## 2. Physical Formulation of `GVSC-36`

### 2.1 Up-Hydraulic-Gradient Plume Back-Projection Operator
Let $z_{\text{reg}} = G_{12}(\text{det\_elev})$ be the 1.2 km smoothed regional hydraulic-head proxy and
$$\mathbf{u}_{\text{up}}(r, c) = \frac{\nabla z_{\text{reg}}(r, c)}{\|\nabla z_{\text{reg}}(r, c)\|_2 + 2.0\text{ m/px}}$$
point upslope from basin floor to piedmont/range-front. Because shallow geothermal outflow plumes $Q$ (`F2mDAB > 0`, warm springs, carbonate/silica-cemented outflow aprons) migrate **down-slope (`-\mathbf{u}_{\text{up}}`)** away from their feeding fault conduit $\mathbf{x} = (r, c)$, the back-projected conduit potential evaluated at candidate fault pixel $\mathbf{x}$ integrates downslope plume mass across offsets $s \in \{4, 8, 14, 20\}\text{ px}$ (`400 m – 2,000 m`):
$$\mathcal{U}_{+\nabla z}(Q)(\mathbf{x}) = \sum_{s \in \{4, 8, 14, 20\}} w_s \, G_{\sigma_s}(Q)\!\left(\mathbf{x} - s\,\mathbf{u}_{\text{up}}(\mathbf{x})\right), \quad w = (0.35, 0.30, 0.20, 0.15).$$
To prevent tree coordinate memorization (`IR-36-INSAMPLE-HALO-COLLAPSE`), all point-derived fields are represented purely as local band-pass contrasts ($G_3 - \alpha G_{18}$) or multiplicative structural interactions with 1.5 km directional strike-anisotropy worms (`sa_worm_piedmont`, `sa_worm_mag`, `sa_worm_grav_base`), magnetic demagnetization troughs (`sa_rtp_trough_dog`), and MT/radiometric alteration edges (`sa_mt_cond_edge`, `sa_rad_k_th_anom`). Lake Lahontan shoreline tufa mimicry is explicitly down-weighted (`0.35x`) for `Tufa` records inside `1,250–1,360 m` elevation.

### 2.2 Prentice–Pyke Bayes Case-Control Calibration & Exact 300 m Submodular Allocation
Under fold-local case-control subsampling ($\pi_+ = P_s / P_{\text{tot}}$, $\pi_- = M_s / M_{\text{tot}}$ computed strictly on `fold["train"]`), raw classifier probability $q(\mathbf{x})$ is mapped to population fault probability via exact Bayes odds inversion (Prentice & Pyke, 1979):
$$p(\mathbf{x}) = \frac{q(\mathbf{x})}{q(\mathbf{x}) + (\pi_+ / \pi_-)(1 - q(\mathbf{x}))}.$$
By linearity of expectation, expected weighted true-positive mass under the 300 m triangular kernel $k(d) = \max(1 - d/3, 0)$ is the monotone submodular function $\Phi(S) = \sum_{\mathbf{y}} p(\mathbf{y}) \max_{\mathbf{x} \in S} k(\|\mathbf{y} - \mathbf{x}\|_2)$, maximized via exact 25-offset Euclidean CELF lazy-greedy cover (`min_spacing_px = 2.0`, `d_vis > 2.0 px`, matched total budget `37,654` dots with fold-area budgets `[8414, 10404, 10410, 8426]`).

---

## 3. Frozen Three-Experiment Design & Decision Gates

- **Control `B0`:** Exact 59-feature repo baseline (`h36_features.py` + single HGB + `emit_dots`, `37,654` dots).
- **`EXP-1` (`75` features — Structural Anisotropy + Bayes Submodular Ablation):** `59 BASE` + `16 sa_*` directional strike-anisotropy / Verduzco tilt / basement-step / MT-edge features + 2-seed regularized HGB + Prentice–Pyke calibration + CELF 300 m submodular cover (`gamma = 1.0`). Zero new geothermal-vent archives.
- **`EXP-2` (`89` features — Full `GVSC-36` Geothermal Vent-Conduit Discovery):** `75 EXP-1` features + `14 gvsc_*` INGENIOUS paleo-sinter/explosion/breccia, `2m` `F2mDAB` thermal-probe, Quaternary volcanic-vent, and geothermometer up-gradient back-projected conduit features. Identical estimator and emitter to `EXP-1`.
- **`EXP-3` (`89` full + `73` LiDAR-blind features — LiDAR-Shadowing De-Biased Bridge Ensemble):** Blends `EXP-2` (`M_full`) with a dedicated LiDAR-blind subsurface/geothermal/10m-piedmont expert (`M_blind`, trained strictly without the 16 LiDAR columns) using fixed physical regime weights (`w_blind = 0.55` when `lid_valid == 0`; `0.30` when `lid_valid == 1` and `det_elev_slope < 4°`; `0.15` when `lid_valid == 1` and `det_elev_slope >= 4°`).

### Promotion Gates (All Fail-Closed)
1. **G1 (Leakage Canary):** Single-feature symmetric `AUC = max(auc, 1 - auc) <= 0.90` across pooled and all 4 folds for every feature.
2. **G2 (Holdout Superiority):** Best arm beats both `repo B0 = 0.13375` and recorded 9-site comparable best `0.14876` on `gems-segment-pooled-v1`, with paired 95% block-bootstrap CI vs `B0` strictly above `0`.
3. **G3 (Format & `[0, 1]` Whole-Array Safety):** Single-band `float32` GeoTIFF (`EPSG:32611`, `3730 x 3292`, `(100, 0, 243350, 0, -100, 4508550)`), `outside="zero"` (`nodata=None`), zero `NaN`/`Inf` across all `12,279,160` cells, all values in `[0.0, 1.0]`, zero dots within `200 m` (`d_cat <= 2.0 px`) of `existing_faults.tif`.
4. **G4 (Registry Uniqueness — Parallel-Run Protocol §1):** Surface `|Spearman rho| <= 0.90` AND final-dot 3-px overlap `<= 0.70` across the comparator registry (reporting Focus-9, Scored-107, Competing-Method, and Literal All-Entry transparently; any literal or competing violation forces `verdict = "negative"` / `DO NOT SUBMIT` with zero post-hoc dot perturbation).
