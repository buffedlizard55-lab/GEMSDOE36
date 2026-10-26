# GEMSDOE36 — preregistration, 2026-10-25 (written before any H36-GPS holdout number existed)

Lane declaration: the owner brief's "single method paragraph below" is **missing** (IR-36-16).
This session therefore declares one lane before experimenting and stays in it:

> **H36-GPS — LiDAR scarp-polarity / graben-pair corroboration inside a fold-safe multi-sensor
> field.** New physics features (conjugate synthetic + antithetic scarp pairing along the regional
> slope; strike-coherent 1.5 km scarp line integrals; scarp polarity) are added to a label-free
> 59-feature stack; a supervised out-of-fold model is trained per hide-and-recover fold; dots are
> emitted on ridge centre-lines at ≥ 3 px spacing.

## Ranked hypotheses (none appears in the 118 owner-scored rasters or earlier GEMSDOE36 work)

| rank | id | layers / transform | why it can catch off-catalogue faults | non-fault mimic | cost | expected effect (not a score) |
|---|---|---|---|---|---|---|
| 1 | **H36-GPS** | 1 m 3DEP LiDAR scarp product (`downface_max`, `upface_max`, `step_max`, `coh100`) + organizer `det_elev` regional slope; graben-pair search 200 m–2 km along the slope; 1.5 km contour-parallel line integrals | small grabens and antithetic scarps on piedmonts are below the 1:250k compilation scale of the Quaternary fault database but are what NLR/USGS experts see on 1 m LiDAR (rules PDF: test labels = new faults by NLR + USGS experts; features include GeoDAWN LiDAR) | Lake Lahontan beach ridges / barrier bars (paired facing slopes), fan-head trenches, road and canal embankments, landslide head/toe pairs | low (cached data) | small–moderate holdout gain over the matched baseline |
| 2 | H36-ANNULUS | emission rule: exclude ≤ 3 px (300 m) of the full catalogue in the live map | live evidence only: B=0→1→2 ladder rose 0.2600→0.2708→0.2778, and 8 owner-scored rasters with median catalogue distance ≤ 3 px scored 0.0005–0.0461 | — | zero | cannot be tested on the quadrant holdout (visible faults are ≥ 1.5 km from every validation pixel); applied as a declared rule, never claimed as holdout evidence |
| 3 | H36-SEIS | relocated seismicity lineaments (USGS ComCat FDSN, https://earthquake.usgs.gov/fdsnws/event/1/) | active faults without surface mapping | aftershock clouds off-fault; depth→surface projection error | medium–high: host blocked in this sandbox; needs a GitHub Actions fetch | not run this session |
| 4 | H36-SHORE | Lahontan shoreline suppression from absolute elevation bands (USGS 3DEP, https://www.usgs.gov/3d-elevation-program) | removes the strongest scarp mimic in the region | — | medium: needs absolute DEM (organizer band is detrended) | not run this session |
| 5 | H36-STRAIN | regional budget proportional to geodetic shear-rate quantile (organizer bands) | fault density scales with strain rate | GPS-network interpolation artefacts | low | not run (a related owner-scored strain lane scored 0.0000) |

## Experiments (budget: ≤ 3 experiments or 2 hours)

* **E1 (primary, paired):** B0 = out-of-fold HistGradientBoosting on the 59 base features;
  C1 = identical model + the 7 `gps_*` lane features. Same folds, seeds, sample sizes and emission
  (37,654-dot total budget split by fold area; ridge-NMS candidates; ≥ 3 px greedy spacing).
* **E2 (conditional, physics-only):** label-free rank-average of `gps_graben_pair`,
  `gps_conjugate_line`, `gps_coherent_scarp_line`, same emission — tests the physics without
  supervision.
* **E3:** reserved; not to be used for tuning after seeing E1/E2.

Evaluator: shared template `gems.holdout.SegmentHoldout` (GEMSDOE24@fc2bc6f, byte-identical,
`gems-segment-pooled-v1`, whole 8-connected components hidden with a 1.5 km collar, visible faults
masked pixel-exactly, pooled TPw/FPw/FNw, α = 0.2, β = 0.8, 300 m kernel, 10 km block bootstrap).

## Decision rule (all must pass for PROMOTE; otherwise NEGATIVE = download for research only)

1. C1 beats B0: paired 95% CI lower bound > 0 and ≥ 3/4 folds won.
2. C1 HOLDOUT-DTI exceeds both B0 and the best comparable recorded group number on the same
   evaluator (GEMSDOE24 `H24-GVC1` 0.14876, recorded there, not re-run here).
3. Leakage canary: no feature with single-feature AUC > 0.90 in either polarity.
4. Uniqueness (surface before placement and final dots): every |Spearman ρ| ≤ 0.90; 3-px dot
   overlap ≤ 0.70 against every competing-method registry raster (space-filling controls are
   classified by the template's pigeonhole rule and reported, never deleted).
5. Format: template `check_variants` format-valid and strict whole-array [0, 1] (zeros outside).

No organizer score is predicted. A pass authorises nothing by itself: slot selection is a separate
selector step within the weekly cap (three per week per the official rules PDF, §3.2/§3.4).

---

### Addendum (written after E1/E2; does not change any rule above)

External-source obtainability for H36-SEIS / H36-SHORE was verified through GitHub Actions
(`.github/workflows/verify-external-sources.yml`, run
https://github.com/buffedlizard55-lab/GEMSDOE36/actions/runs/40249277516): USGS ComCat FDSN
returned HTTP 200 with 6,264 M ≥ 2.5 events (2000-01-01 → 2026-10-25) in the footprint bbox, and the
USGS TNM API listed 1,985 3DEP 1 m DEM products and 106 1/3 arc-second products intersecting it
(`evidence/external_source_verification.json`). None of these data were used in today's candidate.
