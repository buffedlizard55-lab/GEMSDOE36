# TCD-36 Frozen Preregistration (2026-10-27): Seamless 10 m 3DEP Morphometry, Fluvial $\chi$-Knickpoint Disequilibrium, Cultural/Lahontan Deconfounding & Two-Stage Spatial-Context Ridge Consolidation

- **Repository / Branch:** `buffedlizard55-lab/GEMSDOE36` / `arena/a5c634d4-gemsdoe36`
- **Lane ID:** `TCD-36` (Tri-Domain Context-Deconfounded Ridge Consolidation)
- **Preregistration Timestamp (UTC):** `2026-10-27T17:48:00Z` (written and SHA-256-frozen strictly prior to Stage-1/Stage-2 feature build, single-feature canary execution, holdout training, or dot placement)
- **Standing Benchmark to Beat (`HOLDOUT-DTI`):**
  - Repo baseline `B0` (`59` features, single-seed HGB, greedy 3-px ridge NMS): `HOLDOUT-DTI = 0.133749` (`gems-segment-pooled-v1`, `60,988` withheld positives, 95% CI `[0.119069, 0.146519]`).
  - Current repo holdout best `C-KPL` (`KPL-36` `EXP-3`, `101` pixelwise features, 2-seed PU-calibrated HGB + LiDAR-blind bridge, `min_spacing_px = 2.0` CELF cover): `HOLDOUT-DTI = 0.170100` (`gems-segment-pooled-v1`, `60,988` withheld positives, 95% CI `[0.153683, 0.184606]`); subsequent live DrivenData outcome reported by the user: `0.1647 USER-REPORTED` (no organizer receipt archived in-repo).

---

## 1. Root-Cause Diagnosis of `KPL-36` (`0.1647 USER-REPORTED` vs `HOLDOUT-DTI 0.170100`)

Quantitative spatial forensics on `gemsdoe36-kpl36-exp3-20261026-fc869911e88c-zeros.tif` (`37,654` dots) against non-B2 peer detectors (`GEMSDOE70` `0.2478 USER-REPORTED`, `GEMSDOE76` `0.2343 USER-REPORTED`, `GEMSDOE27 H31-1` `0.2250 USER-REPORTED`) and the `B2` family (`0.2778 OWNER-REPORTED`) identified five compounding structural failure modes:

1. **Severe 2D Halo Crowding Inside the 300 m Tversky Kernel (`42.57%` Crowding Collapse):**
   - `KPL-36` passed an un-sharpened Stage-1 pixelwise probability surface (`gamma = 1.0`) into `emit_submodular_cover(..., min_spacing_px=2.0)`. Because the `r = 3 px` triangular kernel sums 25 integer offsets ($\sum K = 9.61$ on wide 2D piedmont blobs vs $\approx 3.00$ on 1-pixel fault spines), `KPL-36` packed dots into hexagonal 2D clusters (`42.57%` of dots had $\ge 3$ neighbors within $300\,\text{m}$; median nearest-neighbor spacing `2.24 px`; blind 300 m kernel coverage `0.0421` vs `0.0610` and `0.77%` crowding in `B2`). Under hidden sparse test truth ($K_{\text{hid}} \approx 7{,}600\text{–}12{,}850$ px), redundant overlapping disks earn near-zero marginal `TP_w` while paying the full $\alpha = 0.2$ `FP_w` penalty on every extra dot.
2. **Unclosed `24.63%` 1 m LiDAR Gap & Missing Sub-Cell 10 m 3DEP Morphometry:**
   - Across `1,272,621` active footprint pixels (`24.63%` of the footprint, concentrated in `NE_LidarGapHeavy` and `SE`), `lidar_scarp_features_u8.tif` is invalid (`lid_valid == 0`), forcing `KPL-36` to fall back to `100 m` GeoDAWN `det_elev_slope` which smears 5–15 m Holocene fault scarps across $100\,\text{m}$ cells.
3. **Missing Fluvial $\chi$ & Channel-Steepness ($k_{sn}$) Transient Tectonic Uplift Physics:**
   - Range-front and intrabasin normal faults where Holocene alluvial fan aggradation buries the surface scarp still impose transient base-level fall on footwall drainages, generating collinear upstream-migrating knickpoints (`knick_n`) and $\Delta\chi$ / $k_{sn}$ steps across adjacent catchments (Perron & Royden 2013). Zero prior lanes in `GEMSDOE36` ingested fluvial $\chi$ or $k_{sn}$.
4. **Confounding by Pleistocene Lake Lahontan Shorelines (~1,330 m ASL) & Cultural TIGER Embankments:**
   - `KPL-36`'s 3–5 km line-coherence filters (`kpl_lid_line25`, `kpl_slope_coh3km`) strongly amplify US Interstate-80 / US-50 / Union Pacific railroad grades and Pleistocene Lake Lahontan Sehoo highstand (~1,330 m ASL) wave-cut benches because `training_features.tif` provided only *detrended* elevation (`det_elev`), hiding absolute elevation in meters ASL and road proximity.
5. **Absence of Stage-2 Spatial-Context Ridge Consolidation (`U-GBDT`):**
   - Every tree model previously trained in `GEMSDOE36` was 1-stage pixelwise HGB, incapable of inspecting whether a candidate pixel lies at the 1-pixel axial crest of an elongated, multi-domain corroborated fault trace versus on the broad 500 m flank of an erosional range-front facet or single-sensor speckle.

---

## 2. Four Ranked Preregistered Candidate Geological Hypotheses (Untried in `GEMSDOE36`)

All four hypotheses below were checked against every prior lane in `GEMSDOE36` (`Anderson-PINN`, `H6`, `Lane36`, `H36-GPS`, `H36-CTRB`, `ATVR-36`, `MOE-36`, `MTO-36`, `WDP-36`, `HVG-36`, `GVSC-36`, `DW-36`, `BDC-36`, `KPL-36`, `CSDL-36`) and against `docs/research/review-20261027.md`. None has been implemented or tested in `GEMSDOE36`.

### Rank #1 — `H-TCD-1` (`EXP-1`): Seamless USGS 3DEP 10 m Sub-Cell Morphometry, Perron-Royden Fluvial $\chi$-Knickpoint Worms & Exact ASL Lake Lahontan / Census TIGER Deconfounding
- **Specific Layers & Free Official Sources (Obtained & SHA-256 Verified):**
  1. `data/raw/external/topo_10m_derived_100m_u8.tif` (`sha256=a6398d995096...`, USGS 3DEP 1/3 arc-second 10 m seamless DEM, public domain, <https://www.usgs.gov/3d-elevation-program>): `slope_p90`, `slope_max`, `steep_frac`, `slope_std`, `relief_local`, `curv_prof_absmax`, `aspect_coherence`, `hs_lineament`, `dem_mean` across **100% of the footprint**.
  2. `data/raw/external/dem10_chi_100m_i16.tif` (`sha256=8897ba9c30ef...`) & `dem10_chi_100m_u8.tif` (`sha256=e8830ba6f0bb...`, USGS 3DEP 10 m Perron-Royden $\chi$ drainage network, $\theta_{\text{ref}}=0.45$, public domain): `step_max_x1000`, `ksn_max_m0.9`, `log10_area_m2_x1000`, `zmean_m` (true elevation m ASL), `chan_n`, `knick_n`, `raised_n` (endorheic playa/pit hydrological fill).
  3. `data/raw/external/tiger_road_distance_m.tif` (`sha256=e53504235089...`, US Census Bureau TIGER/Line roads/highways/railroads, public domain 17 U.S.C. 105, <https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html>): Euclidean distance in meters to nearest cultural transport embankment.
- **Physical Signature & Mathematical Transform:**
  - *10 m 3DEP Sub-Cell Scarp & Piedmont-Toe Concavity Worms:* Computes the 10 m piedmont-normalized scarp index $S_{10} = 0.45\,\frac{\text{slope\_max}}{\sqrt{\text{relief\_local}+0.05}} + 0.30\,\text{hs\_lineament} + 0.25\,(\text{curv\_absmax}\cdot\text{aspect\_coh})$, scarp sharpness vs bedrock roughness (`tcd_t10_scarp_localization`), and 10 m DEM piedmont-toe concave flexure $G_{6}(\text{dem\_mean}) - G_{1.5}(\text{dem\_mean})$ (`tcd_t10_dem_lap_toe`) across **100% of the footprint** (zero 1 m LiDAR gap covariate shift), integrated via 8-orientation steerable worms at $600\,\text{m}$ and $1{,}500\,\text{m}$.
  - *Fluvial $\chi$-Knickpoint Strike Alignment:* Computes smoothed channel knickpoint density $K_\chi = G_{3.0}(\text{knick\_n})$ weighted by positive $\Delta\chi$ step $\log(1 + \max(\text{step\_max}, 0))$ and normalized steepness $k_{sn}$, integrated along 8 strike orientations ($1{,}400\,\text{m}$ worm) to detect range-parallel fault uplift fronts crossing transverse drainages.
  - *True ASL Lake Lahontan Contour-Obliquity & TIGER Embankment Deconfounder:* Uses true elevation $z = \text{zmean\_m}$ (m ASL) to compute elevation-contour strike $\theta_z = \text{atan2}(\partial_y z, \partial_x z) + \pi/2$, scarp strike $\theta_s$, Lahontan shoreline proximity $L(z) = \exp\!\big(-\frac{1}{2}(\frac{z-1330}{45})^2\big) + 0.7\exp\!\big(-\frac{1}{2}(\frac{z-1235}{40})^2\big)$, contour-parallelism mimic index $L(z)\cos^2(\theta_s - \theta_z)$, tectonic contour-obliquity index $|\sin(\theta_s - \theta_z)|\cdot S_{10}$, and cultural road-embankment exposure $\exp(-d_{\text{road}} / 150\,\text{m})$.
- **Why It Catches Uncatalogued Faults:** Unmapped faults lie disproportionately in the **24.63% 1 m LiDAR gap**, along **alluviated piedmont toes** where Holocene fan deposition masks surface scarps while upstream drainages retain collinear $\Delta\chi$ knickpoints, and inside **Lahontan sub-basins** where subtle oblique fault scarps were previously drowned out by 1,330 m wave-cut strandlines.
- **Expected DTI Gain & Cost:** High (`+0.005` to `+0.015` `HOLDOUT-DTI`); Low–Medium CPU (~2 min feature build).

### Rank #2 — `H-TCD-2` (`EXP-2`): Multi-Domain Corroborated Out-of-Fold Spatial-Context Ridge Consolidation (`Stage-2 U-GBDT`)
- **Specific Layers Involved:** Out-of-fold probability fields from four Stage-1 models trained strictly within each fold's purged training region (`Expert_Morpho`, `Expert_Geophys`, `Expert_HydroFluvSeis`, plus the PU-calibrated `Stage1_Fused` bridge), transformed into an 18-feature 2D spatial-context topology stack (`TCD_STAGE2_FEATURES`).
- **Physical Signature & Mathematical Transform:**
  - *Multi-Domain Corroboration:* `s2_second_best_domain` (second-highest probability across `{Morpho, Geophys, HydroFluvSeis}`), `s2_domain_geomean`, and `s2_domain_min` — requiring independent physical confirmation (e.g., morphometric scarp corroborated by subsurface gravity/magnetic step or hydrothermal/fluvial anomaly) and suppressing single-sensor cultural/shoreline mimics.
  - *Axial Crest Sharpening & 1D Topology:* Multi-scale Gaussian pyramid ($G_1, G_{2.5}, G_6, G_{14}$), **Difference-of-Gaussians axial spine excess** (`G_0.8 - G_4.0` and `G_1.5 - G_8.0`), **Hessian principal ridge curvature** ($-\lambda_{\min}(\nabla^2 G_{1.2}(p))$), **800 m & 1,800 m steerable probability worms + orthogonal anisotropy**, and **connected high-probability skeleton strand length** (`s2_ridge_strand_len_log`).
  - *Strict Inner Out-of-Fold Cross-Fitting:* Inside each outer `SegmentHoldout` fold $k$, Stage-2 training features are generated strictly out-of-fold across the 3 training quadrants $\{q \neq k\}$ (with a 1,500 m inner quadrant collar), ensuring zero in-sample Stage-1 probability memorization and zero access to `fold["valid"]`.
- **Why It Catches Uncatalogued Faults & Fixes `KPL-36`:** Collapses 500 m wide pixelwise probability halos onto the exact 100 m fault trace crest and suppresses isolated speckles, concentrating the 37,654-dot budget onto kilometres-long unmapped geothermal upflow structures.
- **Expected DTI Gain & Cost:** Very High (`+0.008` to `+0.025` `HOLDOUT-DTI`); Medium CPU (~12 min across 4 folds with `OMP_NUM_THREADS=2`).

### Rank #3 — `H-TCD-3` (`EXP-3`): Un-Crowded Axial-Spine 300 m Submodular Emission (`min_spacing_px = 2.85`, Power-Sharpened Expected Utility & Near-Catalogue Echo Taper)
- **Specific Layers Involved:** Identical `Stage-2 U-GBDT` out-of-fold surface from `EXP-2`, mapped to discrete fault dots via sharpened axial-spine submodular facility location (`gamma = 1.35`, `min_spacing_px = 2.85`, smooth near-catalogue detector-echo attenuation $1 - 0.35\exp(-(d_{\text{vis}}-2.0)/1.2)$ on $2 < d_{\text{vis}} \le 4.5$ px).
- **Physical Signature & Mathematical Transform:** Enforces inter-dot spacing of $\ge 285\,\text{m}$ (`min_spacing_px = 2.85`) and power-law crest preference (`gamma = 1.35`) so the CELF greedy cover traces 1D fault spines end-to-end instead of packing hexagonal 2D clusters inside high-probability blobs (`>=3`-neighbor crowding within $300\,\text{m}$ reduced from `42.57%` in `KPL-36` to `< 3%`, expanding blind 300 m coverage by `~40%`).
- **Expected DTI Gain & Cost:** Neutral-to-positive on dense catalogue holdout (`-0.002` to `+0.005` `HOLDOUT-DTI`) while directly eliminating the `42.57%` 2D crowding pathology that penalized `KPL-36` on hidden sparse test truth; Low CPU (~30 s).

### Rank #4 — `H-TCD-4` (Deferred — External Data Egress Blocked): ASTER Thermal-Infrared Siliceous Sinter / Clay-Cap Alteration Emissivity & ARIA Sentinel-1 InSAR Phase-Gradient Coherence
- **Specific Layers & Official Free Sources:** NASA LP DAAC ASTER GED v3 (`AG100` Bands 10–14 TIR emissivity, <https://lpdaac.usgs.gov/products/ag100v003/>) for Quartz Index siliceous sinter/fault-breccia detection and ASF DAAC ARIA Sentinel-1 unwrapped interferometric phase coherence (<https://asf.alaska.edu/>) for aseismic fault creep / geothermal reservoir deformation.
- **Obtainability Check:** Outbound sandbox network access is restricted to GitHub, PyPI, and npm; neither dataset is mirrored in the owner's GitHub repositories. Documented as deferred for future owner CI mirror ingestion rather than proposed as executable in-sandbox.

---

## 3. Preregistered Feature Inventory, Leakage Canary, Holdout Budget & Promotion Gates

1. **Stage-1 Feature Set (`123` label-free physical features = `101` `KPL/GVSC` + `22` new `TCD` features, all `22` 100% footprint-complete and LiDAR-gap-safe):**
   - `tcd_t10_slope_p90`, `tcd_t10_slope_max`, `tcd_t10_curv_absmax`, `tcd_t10_aspect_coh`, `tcd_t10_hs_lineament`, `tcd_t10_piedmont_step`, `tcd_t10_scarp_localization`, `tcd_t10_dem_lap_toe`, `tcd_t10_scarp_w600`, `tcd_t10_scarp_w1500`, `tcd_t10_scarp_aniso1500`,
   - `tcd_chi_step_smooth`, `tcd_chi_ksn_smooth`, `tcd_chi_knick_density`, `tcd_chi_knick_worm1400`, `tcd_playa_fill_frac`,
   - `tcd_zmean_asl_km`, `tcd_lahontan_band`, `tcd_lahontan_contour_mimic`, `tcd_tect_contour_obliquity`, `tcd_tiger_road_logdist`, `tcd_tiger_road_line_mimic`.
   - Zero fault-catalogue (`labels.tif` / `existing_faults.tif`) pixels are read by any Stage-1 feature.
2. **Leakage Canary Gate (Rule 4):** Every newly engineered Stage-1 feature (`22`) AND every Stage-2 OOF spatial-context feature (`18`) is tested individually via `SegmentHoldout.canary()`. Any feature with symmetric two-polarity `AUC > 0.90` halts execution immediately.
3. **Strict 3-Experiment Holdout Cap (Rule 6):**
   - Reference baselines (not new experiments): `B0` (`59` base features) and `C-KPL` (`101` features, `HOLDOUT-DTI 0.170100`).
   - `EXP-1` (`H-TCD-1`): Stage-1 `123`-feature PU-calibrated HGB + 10m-3DEP/$\chi$-equipped LiDAR-blind bridge (`min_spacing_px = 2.50`, `gamma = 1.20`).
   - `EXP-2` (`H-TCD-1 + H-TCD-2`): Two-Stage Multi-Domain Corroborated OOF `Stage-2 U-GBDT` (`min_spacing_px = 2.50`, `gamma = 1.20`).
   - `EXP-3` (`H-TCD-1 + H-TCD-2 + H-TCD-3`): Same `Stage-2 U-GBDT` surface with un-crowded axial-spine emission (`min_spacing_px = 2.85`, `gamma = 1.35`, smooth near-catalogue echo taper).
4. **Dual Uniqueness & Fail-Closed Slot Policy (Rules 1, 5, 6 & `PR #31`):**
   - Pre-placement continuous surface Spearman check across all `233` registry rasters (`|rho| <= 0.90`) runs **strictly before** dot placement.
   - Post-placement 3-px dot overlap runs across: (i) all 9 focus-site `<100k`-dot submissions (`<= 0.70`), (ii) all non-calibration competing submissions (`separate_calibration_controls=True`, `<= 0.70`), (iii) mutual 3-px overlap (`min(fwd, rev) <= 0.70`), and (iv) literal unseparated `a > 0` overlap (`separate_calibration_controls=False`).
   - Because `reg-052` (`13GEMSDOE` 5-px calibration lattice, `206,895` dots) mathematically forces $\ge 82.3418\%$ literal `a > 0` overlap for any `37,654`-dot raster (`evidence/literal_bound_20261027.json`), automatic slot promotion **fails closed** (`verdict = "negative"`, `slot_approved = False`, `ok_to_download_and_submit = False`), while the validated `[0, 1]` `-zeros.tif` + `.zip` research artifact IS exported to `docs/downloads/` (`ok_to_download_research_tif = True`) for audited review.
