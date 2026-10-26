# WDP-36 Preregistration & Ranked Hypotheses (2026-10-26, branch `arena/b8f55e32-gemsdoe36`)

Locked **before any WDP-36 holdout number was computed**. Machine-readable lock:
[`evidence/wdp36_preregistration_20261026.json`](../../evidence/wdp36_preregistration_20261026.json)
(the pipeline verifies its SHA-256 before running). Score labels: **HOLDOUT-DTI** = local
hide-and-recover (`gems-segment-pooled-v1`); **ORGANIZER-CONFIRMED** = copied from a DrivenData
submission-page receipt / owner brief of portal receipts. No projection is written as a score.

Official anchors (verified 2026-10-26): problem + metric
<https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/> (DTI, α=0.2, β=0.8,
R=300 m; test faults are expert-labelled faults **not in the USGS database**; Final Round rescores
the *same* single GeoTIFF against expanded labels); leaderboard
<https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/>; rules PDF
<https://docs.nlr.gov/docs/fy26osti/96647.pdf>; reference solution
<https://github.com/drivendataorg/gems-prize-reference-solution>; USGS GeoDAWN data release
DOI [10.5066/P93LGLVQ](https://doi.org/10.5066/P93LGLVQ) (CC0; Area 1 lines 200 m / Area 2 lines
400 m at azimuth 90°, ties at 180° — see USGS page fetched 2026-10-26);
EPSG:32611 <https://epsg.io/32611>; Tversky index <https://en.wikipedia.org/wiki/Tversky_index>.

**Sandbox obtainability check (2026-10-26, measured):** `curl` from this sandbox returns `000`
for drivendata.org, usgs.gov, asf.alaska.edu and gdr.openei.org, but `200` for github.com.
Competition rasters were therefore restored **only** via the GitHub mirror pinned in
`registry/data_manifest.json` (SHA-256 verified; integrity-pinned, **not** organizer-authenticated).
Any hypothesis needing a fresh non-GitHub download is **not viable in this sandbox** and is
deferred with its free official source named (H4/H5 below) — it is not silently assumed available.

## Five candidate hypotheses not previously implemented as a primary lane in this repo

### Rank 1 — H-WDP-A: Upward-continuation worm persistence (IMPLEMENTED as EXP-1 core)
- **Layers:** band 14 `tmi`, band 13 `iso_grav_anom` only.
- **Physical signature:** total-horizontal-derivative (THDR) “worms” recomputed after FFT upward
  continuation to h = 0/200/400/800 m; persistence = geometric mean of per-height footprint
  percentile ranks. Laplace physics: a source at depth z attenuates as exp(-|k|h); deep basement
  fault edges survive continuation, shallow sources (thin flows, cultural metal, flight-line
  stripes at 200–400 m spacing) decay.
- **Why off-catalogue:** basin-interior faults buried under Quaternary fill have no scarp for
  LiDAR/topo lanes (ATVR-36/H36-CTRB/H36-GPS) and were never surface-mapped into USGS/INGENIOUS,
  but their basement offset still offsets magnetic/gravity basement. This is exactly the
  “new fault not in the database” class the Initial Round scores.
- **Difference:** every prior GEMSDOE36 lane uses single-scale gradients/tilt or supervised HGB on
  raw bands; none ranks by *persistence across continuation heights*, and none is fully
  unsupervised (zero catalogue-trained parameters ⇒ the in-sample halo-collapse failure
  `IR-36-INSAMPLE-HALO-COLLAPSE` cannot occur).
- **Mimic:** deep non-fault lithologic contacts (pluton margins) persist identically.
- **Expected HOLDOUT-DTI effect / cost:** uncertain sign on catalogue-style holdout (see limitation
  in JSON lock); cost LOW (2 rFFTs + ranks, minutes on CPU, <1 GB RAM with memmap discipline).

### Rank 2 — H-WDP-B: Geodetic strain-rate discontinuity ridges (IMPLEMENTED as EXP-2 add-on)
- **Layers:** bands 04 `geod_2ndinv`, 07 `geod_shearrate`, 08 `geod_dilaterate`.
- **Signature:** gradient magnitude (after σ=1.5 px smoothing), percentile-ranked — i.e. *edges* of
  the strain-rate field, where an active creeping/locked fault partitions deformation.
- **Why off-catalogue:** an unmapped active fault still localises present-day strain even with no
  scarp and no basement magnetic contrast.
- **Difference:** prior lanes fed raw strain *magnitudes* to trees; none ridge-detected strain
  *gradients* as the ranking signal.
- **Mimic:** smooth regional gradients, volcanic inflation, GPS interpolation artefacts.
- **Cost:** LOW. **Risk:** geodetic grids are smooth/low-resolution ⇒ weak 100 m localisation.

### Rank 3 — H-WDP-C: Seismicity proximity/intensity lineaments (IMPLEMENTED as EXP-3 add-on)
- **Layers:** band 16 `ieq_n100a15` (+), band 10 `deq_n100a15` (sign-flipped; band tags describe
  10 as a distance parameter and 16 as intensity/density — tags re-verified line-by-line
  2026-10-26 from `training_features.tif`).
- **Signature:** σ=2 px smoothed composite percentile — diffuse microseismic alignments over blind
  active structures.
- **Why off-catalogue:** blind faults with no surface/geopotential expression can still be seismogenic.
- **Difference:** never used as a primary ranking surface in this repo (only as HGB covariates).
- **Mimic:** aftershock clouds, induced seismicity near geothermal plants.
- **Cost:** LOW. **Risk:** catalogue seismicity is spatially clustered near known structures ⇒
  holdout may reward halo dots; the d>2 px exclusion + canary + paired ablation guard this.

### Rank 4 — H-INSAR: Sentinel-1 LOS velocity steps (DEFERRED — not obtainable in sandbox)
- **Free official source needed:** NASA ASF OPERA L3 DISP-S1 (`OPERA_L3_DISP-S1_V1`) via ASF DAAC
  <https://asf.alaska.edu/> / NASA Earthdata. **Measured 2026-10-26: unreachable from sandbox
  (`curl 000`) and no GitHub mirror is pinned in `registry/`** ⇒ violates the “check obtainable
  before proposing as viable” rule for *this* session. Viable only from an unrestricted machine or
  a future GitHub-mirrored cache with SHA-256 pins. Not implemented; no numbers claimed.

### Rank 5 — H-FLIGHTLINE: GeoDAWN 1-D flight-line profile worms (DEFERRED — not obtainable in sandbox)
- **Free official source needed:** USGS GeoDAWN line-data CSVs inside DOI
  [10.5066/P93LGLVQ](https://doi.org/10.5066/P93LGLVQ) (CC0). The USGS landing page is readable via
  the fetch tool but bulk download hosts are unreachable from sandbox bash (`curl 000` to usgs.gov)
  and no pinned GitHub mirror exists in `registry/data_manifest.json`. Gridded 100 m bands smooth
  across 200–400 m lines; raw profiles could sharpen worms — but proposing it as runnable today
  would be a hallucination. Deferred; EXP-1 is its gridded-data approximation.

## Experiments (≤3) and frozen control
- **A0 (control):** single-scale (h=0) THDR worms, mag+grav mean rank.
- **EXP-1:** PERS alone. **EXP-2:** 0.70·PERS + 0.30·STRAIN. **EXP-3:** 0.60·PERS + 0.25·STRAIN + 0.15·SEIS (rank space).
- Emission, budgets, holdout, canary, uniqueness and fail-closed gates G1–G4: exactly as locked in
  the JSON. Winner = highest pooled HOLDOUT-DTI; **promote only if > 0.14876** (recorded group best)
  with canary + uniqueness + format all passing. Otherwise the GeoTIFF is a research download with
  an automatic **DO NOT SUBMIT** verdict. Negative results are deliverables.

## Why 0.2778 happened, in one paragraph (full proof: `why-02778.md`)
`GEMSDOE32 h33-h33-2-b2` (0.2778 ORGANIZER-CONFIRMED) added **zero** new coordinates over the
0.2600 `d2.8` field: it only deleted the 6,436 dots within 2 px (200 m) of the catalogue
(0 XOR vs `d2.8 & d_cat>2px`, measured). Dots hugging known faults earn ≈0.002–0.006 credit each
vs 0.130 average — the scorer masks/ignores known-fault vicinities and test faults are new — so
deleting them removed pure 0.2·FP denominator tax. Beating 0.2778 therefore needs **more credit per
dot from genuinely new-fault locations** (≈+8% TPw for 0.30 at equal budget; ≈+59% for the public
0.4413), not more collar tricks. WDP-36 tests whether deep/buried-fault geography supplies that
credit from terrain the scarp lanes cannot see; the holdout decides, fail-closed.
