# AI Disclosure — GEMSDOE36

_Required by the official rules (§3.2): generative AI use is allowed, but the
submission narrative must state the **extent** and **how** it was used. This
document is that statement, kept current as the project evolves._

**Last updated:** 2026-10-04 (after the H6 candidate passed the 5-fold holdout
gate and the upload-ready TIFF was generated).

## Extent and how generative AI was used

Generative AI — specifically **Claude, operated through Arena.ai's Agent Mode**
as an autonomous coding agent — was used to:

1. **Implement the entire prediction pipeline.** The agent wrote the data
   preparation (`scripts/prepare_data.py`), the belief-field construction
   (`src/gemsdoe36/field.py`), the Anderson extension/orientation utilities
   (`src/gemsdoe36/anderson.py`, `src/gemsdoe36/orientation.py`), the
   exact-marginal-gain dot emitter (`src/gemsdoe36/emitter.py`), the published
   DTI reference implementation (`src/gemsdoe36/metric.py`), the spatial
   block-fold utility (`src/gemsdoe36/spatial_cv.py`), the fail-closed GeoTIFF
   writer/validator (`src/gemsdoe36/submission.py`), and the physics-informed
   U-Net (`src/gemsdoe36/model.py`).
2. **Run and interpret the 5-fold spatially-blocked holdout**
   (`scripts/run_holdout.py`), including the ablations that retired the
   concentrated top-K emission and the dip projection in favor of the
   broad-coverage off-catalogue SGMC prior (H6).
3. **Build the submission** (`scripts/build_h6_submission.py`) and the
   documentation/research site.

## What was and was not given to the AI

- **Given (authorized training data):** the competition feature raster, label
  raster, and sample template, supplied to the pipeline as SHA-256-pinned
  mirrors of the official files (provenance in `docs/research/sources.md`).
  These are the same bytes a human would load for modeling; using them as
  features is the competition's intent ("you may use the provided set of faults
  for training").
- **Not given:** any private-test labels, any private/leaderboard score, or any
  other participant's submission pixels. The incumbent study TIFs in
  `data/study/` are **learning references only** — used to understand the
  metric regime and as holdout baselines, never copied into the submission.
- **Selection rule:** the candidate was chosen **on the spatially-blocked
  holdout alone**, before any submission slot was used, per the rules'
  anti-overfit requirement that the final file be chosen without private
  scores.

## Reproducibility

Every result cited on the site and in the README is reproducible from this
repository: pinned data, fixed seeds (fold seed 36), and the scripts named
above. The candidate TIFF's provenance (config, dot count, self-score, and
validation manifest) is in `outputs/h6_diagnostics.json` and the `.json`
manifest next to the TIFF.

## Honest limitation

The holdout is a *relative* comparison on an off-catalogue SGMC proxy, which
over-counts old faults the organizers' hidden set excludes. The proxy→live
transfer is therefore only partially calibrated; this is stated on the site
and does not change the fact that the candidate beat the incumbent on every
fold before the slot was spent.
