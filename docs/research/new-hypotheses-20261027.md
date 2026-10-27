# GEMSDOE36 — New geological hypotheses register (2026-10-27)

**Status:** pre-holdout. None of N2–N5 has been validated on the spatially-blocked holdout yet.
**Rule applied:** validate the top candidate on holdout BEFORE any weekly submission slot is spent.
Negative results are deliverables (see N1 below, already tested negative).

## Method frame (shared with all candidates)

- Evaluator: Distance-Weighted Tversky Index, alpha=0.2 (FP), beta=0.8 (FN), triangular kernel R=300 m (3 px at 100 m), pooled over whole-segment withheld faults (buffer 30 px), 4 folds x 16 spatial cells, bootstrap 2000 over cells. Label every result HOLDOUT-DTI (evaluator `gems-segment-pooled-v1`, 60,988 withheld positives, 95% CI). A projection is never written as a score.
- Leakage canary: each feature alone on holdout; two-polarity AUC > 0.90 => leakage until proven otherwise.
- Uniqueness gate (lane rule): |Spearman rho| <= 0.90 vs every registry raster AND <= 70% of dots within 3 px of any one registry raster's dots, checked on surface before placement AND on final dots. Registry = locally restored scored rasters + SHA-256-verified pinned focus-site champions (see evidence/kpl36_registry_audit.json and evidence/pinned_focus_fetch.json).
- All candidates are emitted off-catalogue (dots > 2 px / 200 m from the USGS/INGENIOUS known-fault mask): dots on known faults earn zero TP credit yet consume budget — the organizer masks known faults pixel-exactly (DrivenData community thread 11516).
- Submission format fix verified locally: single-band float32 GeoTIFF on the exact organizer grid (EPSG:32611, 3730x3292, 100 m), values finite in [0,1] inside the footprint, zeros (never NaN) outside — this is what prevents the portal error "Predicted values must be in range [0, 1]". Verified for the promoted file `gemsdoe36-kpl36-exp3-20261026-fc869911e88c-zeros.tif` against `data/raw/sample_submission.tif` (PASS).

## Candidates, ranked by expected DTI improvement × implementation cost

### N2 (top candidate, validate next) — Hydrothermal alteration + blind-conduit halo

- **Layers:** DOE GDR 1391 / INGENIOUS 2 m temperature-probe regional measurements (`data/external/2m_temperature_probe_INGENIOUS_regional_data.zip`, already restored); GeoDAWN radiometric composite (`external/geodawn_rad_u8.tif`, band 4 K/Th proxy); competition band `02_rtp` (magnetite-destruction trough).
- **Physical signature:** Blind faults under alluvial cover often have no surface scarp but host hydrothermal alteration halos (radiometric K/Th contrast, RTP trough from magnetite destruction) above a shallow thermal anomaly. The conjunction (alteration AND thermal probe anomaly AND off-catalogue location) nominates concealed fluid conduits.
- **Why it catches off-catalogue faults:** Springs/vents already in catalogues are masked; this targets the *concealed* parts of the same hydrothermal systems — blind step-overs and intersections where temperature probes record anomalous shallow gradients but no mapped fault trace exists.
- **How it differs from the repo:** The GDR 2 m temperature-probe zip is restored but unused in any emission pipeline; radiometric enters ATVR-36 only as an undifferentiated composite context, never as a gated thermal×alteration conjunction. GDR 1391 well/spring geothermometers are used in H36-B as soft context, not as a blind-conduit prior.
- **Official/free source:** DOE Geothermal Data Repository submission 1391 — https://gdr.openei.org/submissions/1391 (CC BY 4.0); INGENIOUS geothermal data (GBCGE project — https://gbcge.org/current-projects/ingenious/).
- **Implementation cost:** medium — unzip probe CSV, rasterize/IDW to the 100 m grid, combine with band 02_rtp and the radiometric composite, threshold, emit dots off-catalogue.
- **Expected DTI improvement:** +0.008 to +0.018 HOLDOUT-DTI over a single-channel baseline (estimate only; must be measured on holdout).

### N4 — Strike-independent TMI analytic-signal envelope

- **Layers:** competition bands `03_tmi_hg` / `14_tmi` (total-field magnetics).
- **Physical signature:** 2D analytic-signal amplitude (Hilbert transform) of total-field magnetics highlights the *edges* of magnetic sources independent of magnetisation direction — deep crustal fault lineaments that have no surface expression.
- **Why it catches off-catalogue faults:** Deep-seated faults controlling geothermal upflow may never break the surface; directional gradients (VG/HG) are strike-sensitive and miss lineaments unfavourably oriented to the field. The envelope is strike-blind.
- **How it differs from the repo:** The repo uses directional derivatives only (`tmi_hg`, `tmi_vg` tilt/THDR in H36-A); no strike-independent analytic-signal envelope exists anywhere in the stack.
- **Implementation cost:** low — scipy 2D Hilbert transform, robust [0,1] normalisation, off-catalogue emission.
- **Expected DTI improvement:** +0.003 to +0.010 HOLDOUT-DTI.

### N5 — Drainage convergence / stream-power on detrended elevation

- **Layers:** competition band `12_det_elev` (detrended DEM).
- **Physical signature:** D8 flow accumulation × slope (stream power). Concealed Quaternary scarps deflect and converge alluvial-fan drainage; high stream-power convergence on fans marks young, unmapped scarps.
- **Why it catches off-catalogue faults:** Young scarps on fans are often unmapped in regional catalogues (mapped at coarser scale or omitted as "geomorphic"), but they are exactly the blind/young faults the leaderboard credits.
- **How it differs from the repo:** Repo topography channels use Hessian scarp/toe curvature and relief ratios (`h36a_elev_hessian_*`, `h36a_slope_rel_relief25`) — local line metrics, not integrated drainage convergence. No flow-accumulation channel exists in the stack.
- **Implementation cost:** medium — D8 flow direction/accumulation on the 5.16 M-pixel footprint (chunked), combine with slope.
- **Expected DTI improvement:** +0.004 to +0.012 HOLDOUT-DTI.

### N3 — Instrumental seismicity cluster-edge density (conditional on data)

- **Layers:** USGS ComCat instrumental seismicity (M>=2.5, 2000-present) rasterised to cluster-edge density.
- **Physical signature:** Active blind faults mark the boundaries of seismicity clusters; cluster edges (high gradient of event density) are off-catalogue fault traces.
- **Why it catches off-catalogue faults:** Seismicity illuminates currently active structures regardless of catalogue status.
- **How it differs from the repo:** No seismicity layer exists in the repo's feature stack or emission pipelines.
- **Official/free source:** USGS ComCat — https://earthquake.usgs.gov/fdsnws/event/1/ (count + CSV query; footprint bbox -120.1,37.3,-116.1,40.8). The repo's CI workflow (`.github/workflows/verify-external-sources.yml`) queries ComCat and TNM 3DEP endpoints — verify those endpoints are reachable from this sandbox before adopting; if not, mark N3 non-viable without a manual download step.
- **Implementation cost:** medium/high (external download required).
- **Expected DTI improvement:** +0.005 to +0.015 HOLDOUT-DTI (unmeasured).

### N1 — Shear/dilation structure-tensor coherence — TESTED NEGATIVE

- **Layers:** `07_geod_shearrate` x `08_geod_dilaterate` structure-tensor coherence.
- **Result:** HOLDOUT-DTI 0.0170 [0.0145, 0.0200] vs baseline `det_elev_slope` 0.0217 [0.0190, 0.0242]; delta -0.0047. Leakage canary passed (AUC 0.49). Card: `evidence/n1_holdout_run_card.json`.
- **Verdict:** negative. Do not promote, do not spend a slot. Kept as a deliverable (a ruled-out idea).

## Ranking summary

| Rank | Candidate | Expected ΔDTI | Cost | Holdout-validated? | Next step |
|------|-----------|---------------|------|--------------------|-----------|
| 1 | N2 hydrothermal alteration + blind-conduit halo | +0.008…0.018 | medium | No | Build thermal×radiometric conjunction surface; run segment holdout + canary; if it beats the current best (KPL-36 EXP-3 HOLDOUT-DTI 0.1701 [0.1551, 0.1861]) with CI separation, emit TIF, run registry audit, then selector decides on a slot |
| 2 | N4 TMI analytic-signal envelope | +0.003…0.010 | low | No | Same protocol as N2 |
| 3 | N5 drainage convergence / stream-power | +0.004…0.012 | medium | No | Same protocol as N2 |
| 4 | N3 seismicity cluster edges | +0.005…0.015 | medium/high | No | First confirm ComCat obtainability from this sandbox; if blocked, drop |
| 5 | N1 shear/dilation coherence | -0.0047 measured | low | Yes (negative) | Filed; do not revisit |

## Baseline to beat

KPL-36 EXP-3 is the current promoted arm: HOLDOUT-DTI 0.170100 [0.155089, 0.186137], 60,988 withheld positives, evaluator `gems-segment-pooled-v1`, leakage canary max AUC 0.6344, registry gate passed (max |rho| 0.0567, max 3-px overlap 0.6674 vs 20 rasters), format-valid vs the organizer template. Any new submission must beat 0.1701 on the *same* holdout design before a slot is considered.

## Sources to verify (free, official, named)

- Anderson, E.M. (1905) The Dynamics of Faulting, DOI 10.1144/transed.8.3.387
- Raissi et al. (2019) PINNs, JCP 378, DOI 10.1016/j.jcp.2018.10.045
- USGS GeoDAWN airborne geophysics — https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and ; ScienceBase item 657e1d85d34e23d3533209f7
- DOE GDR 1391 — https://gdr.openei.org/submissions/1391
- USGS ComCat — https://earthquake.usgs.gov/fdsnws/event/1/
- USGS TNM 3DEP — https://tnmaccess.nationalmap.gov/api/v1/products
- GBCGE INGENIOUS — https://gbcge.org/current-projects/ingenious/
- EPSG:32611 — https://epsg.io/32611
- Tversky index — https://en.wikipedia.org/wiki/Tversky_index
- Official competition: https://www.drivendata.org/competitions/306/competition-doe-gems/ (spec page 967, about 968, data tab requires DrivenData login)
- Scoring clarification (known faults masked pixel-exactly): https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4

All links above are named in repo sources or the user brief; none were independently re-fetched in this session except via the repo's own CI workflow (ComCat/TNM/GDR endpoint checks in `.github/workflows/verify-external-sources.yml`). Treat every link as "verify before relying on".
