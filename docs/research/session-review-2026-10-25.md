> **Parallel-session historical record:** environment availability statements below apply to that session. See [the subsequent safety audit](review-20261025.md) for restored mirror-template validation, current tests and retired legacy gates. No submission is approved.

# GEMSDOE36 review — 2026-10-25 UTC

## Decision and scope

**No new competition submission was generated. Do not download or submit the historical TIFFs currently in `docs/downloads/`.** The authorized competition rasters and sample template are absent from this checkout (`data/` contains only two JSON receipts). A synthetic-format fixture also exists and is explicitly not a submission. Without the real feature stack, labels, and official sample grid, no new scientific prediction, spatial holdout, uniqueness comparison against registry rasters, or organizer-format validation can be performed honestly. Reusing one of the old candidate rasters would violate the user's unique-submission requirement.

The requested lane's method paragraph was not included in the prompt. Its numerical duplication thresholds are stated (Spearman |rho| > 0.90 or >70% of points within 3 px), but a registry-raster inventory for the requested sites is not present locally, so the duplicate gate cannot be evaluated. No surface or final-dot comparisons were claimed.

## Repo review findings

1. The README and landing pages report old 2026-10-04 experiments as current, label old TIFFs as ready to submit, and show projected/owner-reported scores alongside holdout values. Those are not current, organizer-confirmed results.
2. `data/` has receipts only; `data/raw/` and `data/processed/` are missing. Running `bash scripts/run_checks.sh` stops immediately because pytest is not installed in this environment. The earlier attempted `python scripts/run_checks.sh` was an invocation error (shell script passed to Python), not a project test result.
3. Existing stored H6 holdout results evaluate against off-catalogue SGMC as a proxy. They are **not** organizer DTI, and their extremely strong proxy scores are not evidence of live competition performance. The log's own caveat says SGMC includes mapped faults that may not be in hidden truth.
4. No current official submission-page receipt was found. The user-provided leaderboard/site values cannot be treated as organizer-confirmed data.
5. The code's current writer/validator provides useful local checks, but a pass requires the official template and is not platform acceptance. Existing old TIFs are not newly validated here.

## Hypotheses for a future, properly gated experiment

These are proposals, not validated results or claims of winning. They are distinct from the extant code's Anderson orientation, geophysical corroboration/SGMC prior, geothermal context, dip projection, and dot-emission approaches.

| Rank | Candidate | Inputs and targeted physical signature | Why potentially finds uncatalogued faults | Difference from repo | Expected DTI direction / cost | Availability and gate |
|---|---|---|---|---|---|---|
| 1 | Flight-line crossover residual coherence | Official USGS GeoDAWN raw magnetic/radiometric flight-line profiles; direction-conditioned crossover misfit and repeatable residual edges | A buried structure may persist across intersecting flight directions while acquisition striping tends to align with a single flight direction; tests signal absent from gridded products | Profile-level nuisance correction and cross-line reproducibility, rather than another transform of the prepared grids | Unknown; medium/high compute and preprocessing | USGS GeoDAWN [ScienceBase](https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7) and [DOI data release](https://doi.org/10.5066/P93LGLVQ). Catalog presence is not verified local AOI coverage. Obtain, inspect license/data overlap, then test each feature alone for leakage and spatial holdout. |
| 2 | Multi-date InSAR deformation discontinuity | Sentinel-1 repeat-pass interferometric coherence and line-of-sight velocity gradients, with look-direction consistency | Independent surface deformation can expose active blind fault zones that are not visible as topographic scarps or mapped magnetic edges | Time-series radar deformation data are not in the local stack and are not simply another static raster transform | Unknown, potentially useful only for active structures; high compute / access burden | NASA [Sentinel-1](https://www.earthdata.nasa.gov/data/platforms/space-based-platforms/sentinel-1); ASF DAAC access requires Earthdata account. Must first establish acquisition coverage, geometry, temporal coherence, license, and sufficient fault-scale resolution. Not yet viable. |
| 3 | Fault-related geomorphic drainage-network disruption | USGS 3DEP elevation data; channel-network angular deflections, aligned knickpoints, and across-fault channel-profile offsets from multi-scale DEMs | Subtle young faults can deflect channels or offset drainage where geophysics is ambiguous; spatially localized geomorphic evidence may target unmapped traces | Repo has no drainage-network extraction / channel topology feature (existing scarp and topographic transformations are not this) | Unknown; medium, dependent on DEM coverage and channel extraction quality | USGS [3DEP](https://www.usgs.gov/3d-elevation-program). Coverage can be checked from the official service, but this checkout has no AOI query or tiles. Must quantify coverage and compare to matched non-fault controls before use. |
| 4 | Well-log stratigraphic offset / basement-depth discontinuity | Public borehole lithology, temperature and depth-to-basement records; spatially cross-validated change points in basement elevation or stratigraphic thickness | Fault offsets may be recorded in subsurface logs even where surface expressions and potential-field grids are weak | Existing GDR points are used as geothermal context; this tests subsurface stratigraphic discontinuities, not vent proximity or a smooth temperature field | Potentially high specificity but likely sparse; high data curation | DOE [Geothermal Data Repository](https://gdr.openei.org/) and [GDR 1391](https://gdr.openei.org/submissions/1391). Need to verify downloadable machine-readable well logs, spatial density and use rights first; not viable until confirmed. |

No feature has been evaluated alone; no AUC/leakage-canary result exists for these proposals. Do not promote any without the user's prescribed isolated-feature leakage test, whole-segment buffered holdout, paired DTI with CI, and registry duplication screen.

## Why the supplied 0.2778 cannot be explained as fact

The user's listed score for `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` is **user-reported only** in this checkout. It has no linked organizer receipt here. Its mechanism (thinning predictions near already-known faults reducing false-positive penalty under an asymmetric distance-weighted metric) is a plausible hypothesis, but repo history contains conflicting claims about the artifact's status and score. Therefore this review cannot assert that the pruning caused an organizer-observed increase to 0.2778. Nor can the repo establish that a new method will beat it.

## Reproduction checks performed

- `python scripts/run_checks.sh` — incorrect command; shell syntax error, not a test result.
- Created an ignored local virtual environment and installed declared project/dev dependencies. `.venv/bin/python -m pytest -q` — **56 passed, 1 skipped** (optional Torch-dependent test skipped because Torch is absent).
- `.venv/bin/ruff check src scripts tests` — **failed with 32 findings** across existing project files (e.g. executable-bit/shebang mismatch, unused noqa, and style findings). No automatic mass-fix was applied.
- `.venv/bin/python scripts/check_site.py` — run separately below; the site checker validates existing links/artifacts, not suitability for new submission.
- File inventory — no competition raster under `data/raw/` or prepared feature stack under `data/processed/`.
- No network source content was fetched during this review; linked sources are official source routes from existing repo documentation and need fresh verification before acquisition/use.

## Required next steps before any genuine submission

1. Place the authorized official files in `data/raw/` using the repository's download/restore process; verify hashes against official-origin documentation, not an unverified mirror.
2. Install declared dev dependencies, run tests/lint/site checks, and reconcile old unsupported claims in README and pages with provenance.
3. Inventory all registry rasters and implement rank-correlation / 3-pixel overlap checks on the surface and final points.
4. Implement/repair the evaluator protocol: segment-level buffered withholding, derive catalogue features only from visible faults, pixel-exact visible-fault mask, pooled DTI (alpha .2, beta .8, triangular 300 m), and bootstrap/block CI. Confirm evaluator version and positive count in every report.
5. Run each feature alone as a leakage canary (AUC > .90 triggers investigation), then at most three preregistered experiments; promote only a candidate that beats the local holdout best. No weekly slot should be used before that gate.
6. Build a fresh TIFF from the candidate and official template, validate footprint NaNs / in-footprint [0,1] / CRS / shape / transform, hash it, then label it plainly as “OK TO DOWNLOAD AND SUBMIT” only after the full gate passes. Any organizer score must be labeled ORGANIZER-CONFIRMED only with the submission-page receipt.

## Run card

```json
{
  "hypothesis": "No experiment run; proposals above are preregistration candidates only.",
  "mechanism": "Not tested.",
  "named_non_fault_mimic": "Flight-line acquisition striping can mimic linear magnetic/radiometric edges.",
  "holdout_dti_ci": "Not available: missing official rasters/template and no run; no score projection.",
  "correlation_overlap_vs_registry": "Not evaluated: registry raster inventory unavailable.",
  "raster_sha256": null,
  "validator_output": "NOT RUN: no fresh candidate and no official sample template; NaN/range/CRS/shape/transform unverified.",
  "submission_name": null,
  "note": "No new TIFF generated; do not submit historical or synthetic files.",
  "verdict": "negative"
}
```
