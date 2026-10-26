# KPL-36 preregistration — long-range line-coherence lane (2026-10-26)

Written BEFORE any KPL feature was computed or scored. Machine-readable twin:
`evidence/kpl36_preregistration_20261026.json` (hash-locked in the runner).

## Why 0.2778 happened (one paragraph, sources in `why-02778.md`)

The GEMSDOE32 champion is the H19-5 corroborated field thinned to 44,090 dots
(0.2600 OWNER-REPORTED) and then *purely deleted* down to 37,654 dots by removing
every dot ≤2 px from the known-fault catalogue. No new coordinate was added after
0.2600. Under the official identity `DTI = T / (0.2(T+S−M) + 0.8N)` a dot pays for
itself iff its realised 300 m-kernel credit exceeds `0.2·DTI` (0.0556 at 0.2778);
the deleted near-catalogue dots carried only 0.002–0.006 credit each (hidden truth
is *new* faults, known faults are scorer-masked), so deleting them raised DTI by
denominator thrift. Beating 0.2778 therefore requires a detector whose *average*
dot earns >0.130 credit at the same budget — i.e. +8% true-positive credit for
0.30 — not another emission trick on the same field.

## Ranked hypotheses (3–5 required; top one is implemented)

### H-KPL-A (rank 1, IMPLEMENTED as EXP-1/EXP-2) — Expert-traceability: 3–5 km oriented line coherence
- **Layers:** LiDAR `step_max`/`ex_max` (USGS 3DEP 1 m-derived u8 product), organizer
  `det_elev_slope`, `tmi_hg`, `iso_grav_anom_hg` (training_features bands 19/3/18).
- **Physical signature:** structure-tensor coherence `(λ1−λ2)/(λ1+λ2)` with a 3 km
  integration scale (σ=15 px), directional line-integral anisotropy at half-lengths
  15 px (3.1 km) and 25 px (5.1 km), cross-channel orientation agreement
  `cos(2Δθ)` between topographic and magnetic tensors, and a long/short persistence
  ratio. Existing repo worms integrate only 1.5 km (half=7 px); nothing in the repo
  integrates 3–5 km or measures cross-channel tensor-orientation agreement.
- **Why off-catalogue:** hidden truth was drawn by human experts tracing *continuous
  kilometre-scale lines*. Unmapped faults are disproportionately long-but-faint:
  locally below a pixelwise GBM's threshold, but coherent over 3–5 km so along-strike
  integration raises SNR ~√N while suppressing short (<1 km) erosional/cultural
  segments that pixelwise models waste dots on.
- **Named non-fault mimic:** long straight roads/railways/pipelines and Lahontan
  shoreline benches; also range-front erosional facets.
- **Expected Δ / cost:** +0.005…+0.020 HOLDOUT-DTI over GVSC-89 if the expert-trace
  model is right; cost low (label-free convolutions, ~minutes).

### H-KPL-B (rank 2, IMPLEMENTED as EXP-3) — PU-spy decontaminated training
- **Layers:** all EXP-2 features; change is statistical, not a new layer.
- **Signature/mechanism:** random "negatives" are contaminated by ~12.5 k hidden
  fault pixels and their halos. Spy-PU: hide 15% of positives inside the unlabelled
  pool, train, set the reliable-negative threshold at the 10th percentile of spy
  scores, retrain positives vs reliable negatives only. No prior repo lane does PU
  correction (all use random far negatives).
- **Why off-catalogue:** stops the classifier from being *penalised for firing on
  unmapped-fault habitat* during training — exactly the habitat the leaderboard credits.
- **Named non-fault mimic / risk:** reliable negatives skew to flat basins → model
  may over-fire on any range front (erosional mimic).
- **Expected Δ / cost:** −0.005…+0.015; cost low-medium (+3 fits/fold).

### H-KPL-C (rank 3, NOT implemented — emission sensitivity only)
DTI-exact budget×collar selection {(37,654,B2),(44,090,B2),(37,654,B3)} on OOF
surfaces. Reported as sensitivity for all arms; NOT used to select the deploy
budget (37,654/B2 stays frozen) because holdout-optimal budget is biased upward
(holdout truth is dense known faults; hidden truth is sparse).

### H-KPL-D (rank 4, NOT viable in this sandbox — external route named)
Drainage-deflection / knickpoint-alignment features need a *raw* DEM for D8 flow
routing; the organizer stack has only detrended elevation (band 12), which distorts
regional flow. Free official source: USGS 3DEP 1/3 arc-second DEM via The National
Map downloader (https://apps.nationalmap.gov/downloader/). Sandbox egress is
GitHub/PyPI only, so it is **not obtainable here**; route is an owner-CI mirror
into a GitHub repo (same pattern as the existing LiDAR u8 product). Deferred.

### H-KPL-E (rank 5, NOT implemented)
Least-cost-path completion between collinear catalogue tips through a feature-cost
surface. Tip/relay terms already exist (`gts_relay_bridge`, `gts_tip_lobe`) and tip
lanes historically land inside the champion family (0.2632); routing (vs straight
lobes) is the only new element. Lower priority than A/B.

## Frozen protocol
- Evaluator: `gems.holdout.SegmentHoldout`, `gems-segment-pooled-v1`, buffer 15 px
  (1,500 m), 60,988 withheld positives, pooled DTI α=0.2 β=0.8, 300 m kernel.
  Every KPL feature is label-free (no catalogue read), hence fold-safe by construction.
- Controls in-run: B0 (base-59, GVSC recipe) and C-GVSC (89-feature LiDAR-blind
  bridge, replication of the recorded repo best 0.158855).
- Emission (all arms): CELF submodular cover (`emit_submodular_cover`, γ=1.0,
  min-spacing 2 px, pool 240 k), budget 37,654 total allocated per fold by valid
  area, eligible = valid ∧ d_visible > 2 px. B0 uses `emit_dots` (its recorded recipe).
- Canary: every KPL feature alone via `SegmentHoldout.canary`; abort arm if any
  two-polarity AUC > 0.90.
- Deploy surface: assembled out-of-fold surface of the winning arm (each footprint
  pixel predicted by the model that never saw its quadrant), global B2 collar vs the
  full catalogue, CELF 37,654 dots, zeros outside footprint (whole-array [0,1]).

## Promotion gates (all required for `promote`)
G1 canary pass · G2 best arm pooled HOLDOUT-DTI > 0.158855 (recorded GVSC EXP-3)
AND paired Δ vs in-run B0 95% CI strictly > 0 · G3 uniqueness vs the nine focus
sites: surface max |Spearman| ≤ 0.90 vs all fetched focus-9 rasters AND final dots
≤ 70% within 3 px of **each site champion** (9 dotted highest-scoring files);
overlap vs every other fetched raster reported with 3-px footprint-coverage
(pigeonhole) annotation · G4 strict format validator pass (whole-array [0,1] finite,
CRS/shape/transform = sample_submission, 37,654 dots, min catalogue distance > 2 px).
If any gate fails the verdict is `negative` and the site must say DO NOT SUBMIT.
Budget: ≤3 experiments (EXP-1/2/3) + 2 controls; ≤2 h compute.
