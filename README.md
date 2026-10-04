# GEMSDOE36 — DOE GEMS fault discovery

> **Recurring starting point:** reread this whole README before every substantive session. The full project brief, non-negotiable rules, current verified state, and next gates live here. Update the status/results sections after each work session; never replace a missing measurement with a claim.

**Research status (2026-10-04 UTC):** this checkout began with only this README. It now has a source register, five ranked hypotheses, an exact local DTI calculator, a differentiable stress-orientation training term, spatial-block CV mechanics, and a strict template-based GeoTIFF writer/validator. Current QA: **28 synthetic unit tests pass, Ruff passes, and the local site-link check passes.** The official competition rasters/template are not available in this environment; no model, real spatial holdout, contest score, or upload-ready prediction exists. The site offers a tiny synthetic QA TIFF for format testing only—**do not submit it**.

## Full project brief — reread before work

Build a scientifically grounded, auditable project for the DOE Geologic Enhanced Mapping System (GEMS) Prize Challenge, targeting strong generalization to **previously unmapped geological faults** in the GeoDAWN region. A leaderboard number is feedback, not evidence that this repository's method or file is correct. Do not promise a rank, score, or prize.

### Required outcome and guardrails

1. **Research before modeling.** Propose and rank 3–5 genuinely distinct geological hypotheses. For each, state the layers, target signature, why it might find off-catalogue faults, how it differs from this repository's method, qualitative expected DTI benefit, engineering/data cost, and verified availability. Do not invent a method already present in this initially empty repository.
2. **Validate before any weekly slot.** Test the leading hypothesis using spatially blocked holdouts before recommending or preparing a competition submission. Do not use random pixel splits as primary evidence. Keep all fold values, failure cases, calibration/emission choices, costs, and proxy-generalization limits.
3. **Stress is a loss constraint.** Treat regional stress/extension orientation as a differentiable, uncertainty-aware physics-informed term in the learning objective—not as a post-hoc compass filter. Do not infer orientation from scalar dilatation/shear/second-invariant bands alone; use a full tensor or an adequately justified mechanism inversion, spatially varying directions, and regime uncertainty.
4. **Generate only our own prediction.** Never copy a prior participant's output file/pixels. Prior work can be reviewed for educational context, but no historical prediction may be passed off as new. A submission TIFF must be produced by this project's method, have a unique filename and a short truthful submission note, and pass local checks against the official template.
5. **No guessed submission.** The competition asks for a single-band float32 GeoTIFF on the organizer grid (EPSG:32611, 100 m, same bounds, probabilities/confidence in [0,1], null/NaN outside bounds). Do not call a file submission-ready until shape, bounds, transform, CRS, mask, dtype, finite [0,1] values, and the final on-disk bytes are verified against the official sample. Local validity is not proof of platform acceptance.
6. **[0,1] rejection guard.** Reject non-finite or out-of-range in-bounds values before writing; use the sample-template mask (not a feature-band NoData mask); write safely, reread the bytes, and preserve a hash/manifest. Do not assert a historical rejection cause without the rejected file and template.
7. **Data sourcing.** When new data are proposed, identify a specific free/official source and verify what is actually available. A web landing page or download listing is not proof of local acquisition, AOI coverage, a compatible license, or added DTI value. Never bypass DrivenData enrollment/authentication or copy data from another participant's repository.
8. **User-facing site.** Put the download action/status near the top; include a linked executive-summary subpage with submission steps. Keep a date and source for any leaderboard observations; do not scrape, poll, or mirror DrivenData. The current site exposes a clearly marked synthetic QA file, not a fake competitive submission.
9. **Three review passes.** Review requirements/rules, scientific assumptions and validation, then code/edge cases/site/handoff. Log what was found and fixed.
10. **AI disclosure.** The September 2026 official rules allow generative AI but require a narrative describing the extent and how it was used. Keep the disclosure truthful and update it if AI later touches model design or results.
11. **Sources and limitations.** Link primary/official sources; record availability checks, uncertainties, failures, and next work. Flag score attribution, timing, and data inconsistencies.
12. **GitHub handoff.** The requested PR and merge must be attempted and reported honestly. Do not claim a PR, merge, or main-branch update until GitHub confirms it.

## Verified state now

- **Official goal:** predict fault-confidence values on the GeoDAWN grid; the official metric is distance-weighted Tversky with \(\alpha=0.2\), \(\beta=0.8\), triangular support \(R=300\) m. The official problem page specifies one float32 band, EPSG:32611, 100 m, same bounds, and null/NaN outside.
- **Data access:** the official data tab redirected this unauthenticated workspace to login. No training raster, label raster, or official sample submission was acquired. We did not request or store credentials and did not bypass access controls.
- **Model/validation:** no trained model and no real-data spatial holdout. The DTI, orientation and fold utilities are only tested with synthetic arrays. No numeric expected gain is claimed.
- **TIFF:** no competition-grid candidate exists. `docs/downloads/GEMS36_FORMAT_TEST_NOT_SUBMISSION.tif` is a small synthetic test fixture with deliberately wrong competition dimensions/bounds. It verifies basic GeoTIFF handling, not a model, official grid, or upload acceptance.
- **Score report:** the user-reported 0.2778 is not tied to GEMSDOE32, this checkout, or a local file by any organizer receipt available here. See the [leaderboard note](docs/research/leaderboard.md) and [official board](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/). No leaderboard values are mirrored or automated because the published Terms of Use require prior written consent for monitoring/copying.
- **Original repository state:** initial tracked content was only `README.md` containing `# GEMSDOE36`; there was no existing model implementation. Compare proposals with the [organizer reference solution](https://github.com/drivendataorg/gems-prize-reference-solution), not with nonexistent local code.

## Ranked research and validation decision

The five non-duplicative hypotheses are documented in [`docs/research/hypotheses.md`](docs/research/hypotheses.md). H1 is the lead: multiscale geophysical lineament evidence plus an uncertainty-weighted stress-orientation penalty *in the differentiable objective*. The rank is a prior, not a measured score. H1 cannot be promoted until the authorized rasters arrive and the matched spatial-fold/ablation plan passes.

Read [`docs/research/validation-plan.md`](docs/research/validation-plan.md) before any model experiment. It predeclares 512-pixel spatial tiles, 30-pixel training collars, the 3-pixel metric support buffer, matched baseline/prediction budgets, stress ablations, and a release gate. This plan has **not** been run on competition data.

## Project map

- `docs/index.html` — landing page; submission status and synthetic QA download are visible near the top.
- `docs/executive-summary.html` — executive summary and step-by-step submission guide.
- `docs/downloads/GEMS36_FORMAT_TEST_NOT_SUBMISSION.tif` — synthetic QA fixture, **never upload**; small and intentionally not on the organizer grid.
- `docs/research/hypotheses.md` — ranked, sourced geological hypotheses.
- `docs/research/sources.md` — source register and actual availability/coverage caveats.
- `docs/research/validation-plan.md` — preregistered spatial holdout and promotion gates.
- `docs/research/results.md` — date-stamped results ledger; no contest score is claimed.
- `docs/research/known_irregularities.md` — data, score-attribution, deadline and rules caveats.
- `docs/AI_DISCLOSURE.md` — required disclosure draft for a future narrative.
- `src/gemsdoe36/metric.py` — exact published DTI calculator (local evaluator, not training loss).
- `src/gemsdoe36/orientation.py` — differentiable local strain-axis and trace-orientation penalty; optional PyTorch.
- `src/gemsdoe36/spatial_cv.py` — deterministic spatial tile folds and train/evaluation collars.
- `src/gemsdoe36/submission.py` — fail-closed, template-based writer/validator with read-back and manifest.
- `scripts/audit_inputs.py`, `scripts/build_submission.py`, `scripts/validate_submission.py`, `scripts/check_site.py` — local data/TIFF workflow and static-site link checks; no authentication or downloads.
- `tests/` — analytic/synthetic checks only; not evidence of real-data DTI.

## Setup and checks

Python 3.10+ is required. Data and generated candidates are ignored by Git.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
# Optional for training-time differentiable orientation loss:
# install a CPU/CUDA-compatible PyTorch build using the current PyTorch instructions
python -m pip install '.[train]'
python -m pytest -q
python -m ruff check src scripts tests
```

The optional `train` extra may install a large PyTorch build; choose the right CPU/GPU wheel for your machine. No GPU is needed for metric, spatial fold, writer, and site tests.

After obtaining the files through the official enrolled data page, place them under ignored `data/raw/`. Replace the labels argument below with the exact raster filename provided by the organizers:

```bash
python scripts/audit_inputs.py \
  --features data/raw/training_features.tif \
  --labels data/raw/labels.tif \
  --template data/raw/sample_submission.tif
```

The audit fails on missing files or grid mismatch. Inspect band-level NoData and valid masks before training. Do not place competition rasters or model checkpoints in Git.

### Local candidate path (only after a model and real holdout exist)

```bash
# `scores.npy` must be this project's selected full-grid 2-D probability map.
python scripts/build_submission.py outputs/prediction.npy \
  --template data/raw/sample_submission.tif \
  --note docs/submission_note.txt

python scripts/validate_submission.py outputs/submissions/GEMS36_candidate_<UTC>_<hash>.tif \
  --template data/raw/sample_submission.tif --json
```

The writer requires exact sample geometry, finite [0,1] scores inside the sample's valid area, writes NaN outside, disables TIFF predictors, rereads its own bytes, and creates a SHA-256 manifest. If any gate fails, no successful candidate is published. This code path has synthetic tests only; **it has not produced a contest candidate in this repository.**

## Stress orientation in the objective

`orientation.py` derives a principal horizontal extension axis from full \((\epsilon_{EE},\epsilon_{EN},\epsilon_{NN})\) strain components and a confidence measure, computes a differentiable structure-tensor alignment penalty on predicted probability gradients, and provides `physics_informed_objective(base_loss, ...)` that adds this term during training. Trace orientation is axial (modulo 180°); for normal faulting, a map-view trace normal is expected to be compatible with the extension direction. The current implementation's angle convention is east-toward-south in raster coordinates; geographic EN angles are converted explicitly. Mixed regimes and uncertainty must be modeled. No training experiment has used this loss yet.

## Competition rules, AI, and leaderboard hygiene

The [September 2026 official rules](https://www.nlr.gov/docs/fy26osti/96647.pdf) require a narrative disclosure of generative-AI use (§3.2), permit up to three feedback submissions per week (§3.4), and require choosing one final submission for both prize rounds. The [AI disclosure draft](docs/AI_DISCLOSURE.md) describes only the work done so far and must be updated for any future model.

The official DrivenData [Terms of Use](https://www.drivendata.org/termsofuse/) prohibit automated leaderboard monitoring/copying and manual monitoring/copying without prior written consent. The current site links to the official board and ships no poller or live mirror. A dated one-time note is in [`docs/research/leaderboard.md`](docs/research/leaderboard.md); do not refresh or publish a score feed without permission or an authorized API.

## Sources and current limitations

Start with [`docs/research/sources.md`](docs/research/sources.md): official DrivenData metric/rules/data links; USGS GeoDAWN DOI `10.5066/P93LGLVQ`; NGL Great Basin strain and MAGNET velocities; USGS slip/dilation DOI `10.5066/P9YL58W6`; NBMG Monte Cristo mapped rupture; GDR INGENIOUS; and USGS heat-flow/ComCat references. Some official/public download listings were verified, but no competition data or new binary layer was acquired locally and exact grid overlap remains unmeasured.

Important scientific limitations:

- The official features include scalar strain summaries, not a unique stress-axis raster.
- GNSS-derived strain is kinematic evidence, not a direct stress measurement at every cell; a local tensor, temporal window, interpolation uncertainty, and regime model are needed.
- Regional extensional/transtensional structures vary; a single fixed NNE strike prior is not defensible.
- Geophysical edges can be lithologic contacts or survey artifacts; geothermal context is not fault truth.
- A spatial holdout on known catalogue traces is still only a proxy for privately labeled off-catalogue faults.
- The platform's previous `[0, 1]` rejection cannot be diagnosed from this checkout; the rejected file and official sample are absent.
- The official homepage lists Dec 3, 2026 23:59 UTC, while rules Appendix A.1 says 5:00 p.m. ET on the deadline date (22:00 UTC in December). Treat the earlier time as safe and seek organizer clarification.

See [`docs/research/known_irregularities.md`](docs/research/known_irregularities.md) for the full register.

## Three-pass review and next actions

Three review passes are logged in [`docs/research/review-log.md`](docs/research/review-log.md): requirements/rules; geology and validation; code/site/handoff. Latest recorded QA is 26 synthetic tests, Ruff, and the local site check all passing; re-run `scripts/run_checks.sh` plus the input audit after any changes.

**Next gates, in order:**

1. Obtain the official rasters/template through an authorized competition session; record hashes and metadata.
2. Run preflight and reproduce the organizer baseline.
3. Build H1 features and full-tensor orientation prior; run spatial-block holdout and ablations. Publish all folds and failure cases.
4. Only if the preregistered gate passes, generate a unique candidate, a verified local GeoTIFF, a source/method note, and an AI disclosure.
5. Have the participant upload manually if desired; retain the organizer's receipt. Respect submission limits and select only one final file.
6. Create the requested branch PR and merge only after CI/review and GitHub confirmation; report the PR/merge result honestly.
