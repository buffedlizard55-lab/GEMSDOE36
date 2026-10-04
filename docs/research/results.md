# Results ledger

## 2026-10-04 — initial research and repository foundation

- **Starting repository:** only `README.md` with `# GEMSDOE36`; no source, test suite, training code, data, site, candidate raster, model, or score receipt.
- **New code in this branch:** exact local DTI calculator, differentiable stress-orientation regularizer, spatial block-fold mechanics, fail-closed template-based GeoTIFF writer/validator, and a static-site link checker. Synthetic QA: 28 tests passed; Ruff passed; site-link check passed. `audit_inputs.py` returns its expected missing-data status (exit 2) because the official rasters are absent.
- **Research outcome:** five non-duplicate hypotheses ranked in `hypotheses.md`; H1 (multiphysics lineaments plus an objective-level, uncertainty-weighted stress orientation term) selected for future spatially blocked evaluation.
- **Input availability:** official competition data tab redirects to login. No training features, labels, official sample template or prediction grid were obtained. Public source pages were identified for NGL velocities, USGS/DOE GeoDAWN, USGS slip/dilation, INGENIOUS, and NBMG Monte Cristo data; binary/AOI checks remain pending as noted in `sources.md`.
- **Validation:** synthetic unit tests are not a spatial holdout. No real-data folds, DTI score, model, or comparative benefit have been measured.
- **TIF:** none is provided as upload-ready. This is intentional: exact template geometry, valid mask, candidate scores, real validation, and organizer acceptance are unverified. The format writer is ready to run when authorized data are placed locally.
- **Leaderboard:** `leaderboard.md` records the requested one-time 2026-10-04 public-page observation and attribution caveat; no ongoing access or feed is implemented.

## Required next result entry

Before any submission slot: record data hashes and template geometry; reproduce the organizer reference; run predeclared spatial folds and H1 ablations; show fold-by-fold DTI, costs, and test diagnostics; generate a unique candidate from the selected method; rerun local validator; write a truthful note and AI disclosure; retain platform response/score receipt if the competitor submits manually.
