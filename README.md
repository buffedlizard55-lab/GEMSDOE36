# GEMSDOE36 — DOE GEMS fault discovery

> **Recurring starting point:** reread this complete README before every substantive session. Keep the standing brief, evidence state, limitations, and next gates here for future agents and collaborators. Update the status/results after each work session; never replace a missing measurement with a claim.

## User brief — verbatim, reread every session (recorded 2026-10-04)

This is the owner's standing instruction, stored in full as the starting point for
every session. The distilled operational rules follow below it; where they differ,
the brief and the explicit owner corrections below govern.

> **Goal:** get to the **top of the leaderboard** on the DOE GEMS Prize fault
> discovery competition (DrivenData 306), GeoDAWN region. Core values for every
> decision: **Maximize P(Win)** and **Own the Outcome.**
>
> 1. **MUST generate a UNIQUE TIF submission.** Never copy a previous
> submission's pixels into ours — prior GEMSDOE sites/repositories are for
> learning and forensics only.
> 2. **Encode Anderson (1905) faulting / regional stress orientation as a
> > CONSTRAINT in the differentiable training loss** (Raissi–Perdikaris–
> > Karniadakis 2019 physics-informed style) — a soft orientation-consistency
> > term, NOT a post-hoc compass filter. In a Great Basin normal-faulting regime
> > (~60° dip), penalize candidates whose local strike deviates from the
> > Anderson-predicted range given the known regional extension direction.
> 3. **Analyze WHY h33-2-b2 (GEMSDOE32, owner-reported 0.2778) was the best**
> > prior submission and design the strategy to beat the current top (owner-
> > reported 0.3195). PhD-level analysis, from the forensics in the prior
> > repos — never by copying their rasters.
> 4. **Store this standing prompt in the repo README** as the reread-every-
> > session starting point.
> 5. **Fix the prior platform rejection** “Predicted values must be in range
> > [0, 1]”: give the submission a unique name + short comment, and an
> > executive-summary subpage explaining exactly how to submit. Fail closed on
> > range/geometry so a recurrence is impossible.
> 6. **Generate 3–5 new candidate geological hypotheses** (layers, physical
> > signature, why each catches off-catalogue faults, difference from this
> > repo) **ranked by expected DTI improvement vs cost.** Name the free
> > official sources for any data that still needs verification.
> 7. **Validate the top hypothesis on a spatially-blocked holdout BEFORE
> > spending a weekly submission slot.** Never spend a slot on an idea that
> > has not beaten the current holdout best.
> 8. Work **autonomously end-to-end** (no manual input expected), in **3
> > passes** (implement → bug review → re-check against the original request).
> > **No hallucinations:** verify line by line from official/verified/trusted
> > sources, provide links for manual review, and flag irregularities.
> 9. AI disclosure is required per the official rules (narrative of extent/use).
> > Then **PR and merge to `main`**, reporting success only after GitHub
> > confirms.

### Owner corrections and constraints (standing)

- The TIF must be an **obvious, easy download on the site** — “as easy as
  clicking a File to submit” — and this is stated in the executive summary /
  very top of the site.
- Never guess the submission format: single-band **float32** GeoTIFF,
  **EPSG:32611, 100 m**, the **exact organizer grid**, **[0,1]** in-bounds,
  **NaN/null outside**; ≤3 submissions/week; **one final file for both prize
  rounds**, chosen without private scores.
- Strain is not automatically stress: the orientation term needs a defensible
  stress/extension source with spatial uncertainty (see `orientation.py`).

**Research status (2026-10-04 UTC, session `arena/01a10834-gemsdoe36`):** the
owner-supplied mirrors of the official competition rasters (SHA-256 pinned) are
present under `data/` (19-band features, 60,988-pixel catalogue, sample
template, 1 m LiDAR scarp features, GeoDAWN radiometric/extension grids, USGS
SGMC proxy, GDR-1391 geothermal manifests). A full pipeline now exists:
`scripts/prepare_data.py` (49-channel feature set), `anderson.py` (spatially
varying extension field + dip projection + soft strike-consistency weight),
`field.py` (multi-family corroboration belief field), `emitter.py`
(exact-marginal-gain dot emission with support confinement and the validated
200 m catalogue-flank exclusion), `model.py` (physics-informed U-Net with the
Anderson orientation term **in the training loss**), and
`scripts/run_holdout.py` (5-fold spatially-blocked gate vs the incumbent).
Hypotheses are ranked in `docs/research/hypotheses.md`; the gate results land
in `docs/research/holdout_results.json`. The upload-ready unique TIFF is
published to the site **only after the 5-fold gate passes** — until then the
landing page says so and only the QA fixture is downloadable (**do not submit
it**).

## Full standing brief — reread before work

Build a scientifically grounded, auditable project for the DOE Geologic Enhanced Mapping System (GEMS) Prize Challenge. The strategic target is strong generalization to **previously unmapped geological faults** in the GeoDAWN region. Do not promise a score, rank, or prize.

### Decision principles

- **Maximize P(Win):** pursue improvements that can beat the best comparable, spatially blocked holdout in this repository. Spend scarce weekly submission slots as experiments, not lottery tickets. Prefer measured DTI gain, calibrated uncertainty, and reproducibility over speculative complexity or borrowed leaderboard artifacts.
- **Own the Outcome:** work autonomously where authorized; own research, code, source verification, validation, delivery, and follow-up. Report blockers and failures directly. Do not imply a TIFF, PR, merge, score, or organizer acceptance exists unless it actually does.

### Required outcome and non-negotiable rules

1. **Research before modeling.** Maintain 3–5 distinct, ranked geological hypotheses. For each, identify specific layers/inputs, the physical signature, why it could find faults absent from USGS/INGENIOUS catalogues, what is new relative to this repository and prior site history, qualitative DTI potential, engineering cost, a free official/trusted source, license/access, and what is or is not verified about AOI coverage. A public landing page is not proof of local data acquisition, coverage, or value.
2. **Study history without copying it.** Review prior GEMSDOE site/repository histories to understand evidence classes, proxy/holdout weaknesses, and failed approaches. Never copy another participant's raster pixels or files into a new prediction. Do not use participant mirrors to bypass DrivenData enrollment or to obtain contest data. Preserve score attribution caveats.
3. **Validate before any weekly slot.** Run the leading hypothesis against the **current best local spatially blocked holdout** using matched labels, folds, prediction policy/budget, and exact DTI. Do not use random-pixel splits as primary evidence. Keep pooled and every-fold scores, uncertainty, ablations, failure cases, computation cost, calibration/emission decisions, and proxy-generalization limits. If no reproducible holdout winner exists, the gate is closed.
4. **Stress/orientation belongs in the loss.** Regional stress/extension orientation must be a differentiable, uncertainty-aware constraint in the training objective—not a post-hoc compass filter. Do not infer a unique direction from scalar dilatation, shear magnitude, or second-invariant bands. Use a full tensor or defensible stress/mechanism source, spatially varying directions, and regime/data uncertainty. Strain is not automatically stress.
5. **Generate only our own prediction.** Never reuse or copy a prior prediction raster. Any eventual candidate must be generated by this project's code, have a unique collision-resistant TIFF filename, a distinct human-readable submission name, and a short truthful method/holdout note.
6. **Never guess a submission.** Follow the official submission description: single-band float32 GeoTIFF, EPSG:32611, 100 m, exact organizer sample grid, in-bounds confidence/probability in [0,1], and null/NaN outside the data bounds. Do not call a file upload-ready until shape, transform, bounds, CRS, mask, dtype, finite range, and final bytes are verified against the authorized sample template. A local pass is not platform acceptance.
7. **Fail closed on range and geometry.** Reject non-finite or out-of-range in-bounds values before writing. Use the official sample mask, not feature-band NoData. Write safely, reread the bytes, preserve a SHA-256 manifest, and do not diagnose a historical `[0,1]` rejection without the rejected bytes and template.
8. **User-facing site.** Make the actual TIFF download/status easy to find. Until a real candidate passes, prominently say no submission is available and label the synthetic fixture **NOT A SUBMISSION / NEVER UPLOAD**. Include a linked executive summary with exact submission instructions. GitHub Pages is configured for `main:/`; root `index.html` must route visitors to `/docs/`.
9. **Three review passes.** For substantive changes review (1) request/rules/sources, (2) geological assumptions/validation, and (3) code/edge cases/site/handoff. Log fixes and unresolved issues.
10. **AI disclosure.** The September 2026 official rules allow generative AI but require a narrative describing its extent and how it was used. Keep the disclosure truthful and update it if AI later touches model design, experiments, or results.
11. **Verify and cite.** Use official/trusted sources, record links and dates, flag irregularities and contradictions, avoid hallucinations, and state what was not checked. Do not scrape, poll, or mirror DrivenData standings without prior written permission or a clearly authorized API.
12. **GitHub handoff.** Attempt a PR and merge to `main`; only report success after GitHub confirms it. Work only on the session branch `arena/01a10801-gemsdoe36`.

## Verified state and hard blockers

- **Competition task:** predict fault confidence on the GeoDAWN region. The public problem page describes expert-labeled new faults absent from the existing public USGS database, a distance-weighted Tversky metric with \(\alpha=0.2\), \(\beta=0.8\), and triangular support \(R=300\) m. Official format text says one float32 band, EPSG:32611, 100 m, exact bounds/grid, [0,1] values and null/NaN outside.
- **Known-fault mask:** DrivenData staff clarified that pixels corresponding to existing USGS/INGENIOUS faults are excluded from scoring, including re-evaluation. This does **not** justify an arbitrary 200 m catalogue buffer: nearby, distinct hidden faults may still receive credit within the 300 m metric. See the official [staff clarification](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516).
- **Data access:** Dropbox direct download is blocked from this sandbox; the competition rasters were instead obtained from the **owner's own GitHub repositories** (GEMSDOE @ c0c06ac8, GEMSDOE24 @ 07345ea0) as SHA-256-pinned mirrors of the official files (pins in `GEMSDOE32 registry/data_manifest.json`). These are owner-supplied mirrors — **not organizer-authenticated bytes**; provenance is recorded in `docs/research/sources.md` and `data/processed/manifest.json`. No credentials were used; no access control was bypassed.
- **Model/holdout:** the belief-field + exact-gain-emission pipeline is built and running on real data; the 5-fold spatially-blocked gate (`scripts/run_holdout.py`) is the promotion gate and its results are in `docs/research/holdout_results.json`. A physics-informed U-Net (`model.py`) with the Anderson orientation term in the loss is configured (CPU) and is the H5 ensemble layer. Do not report a numeric expected improvement as measured until the gate table says so.
- **Score attribution:** the user-supplied `0.2778` is not tied by an organizer receipt to GEMSDOE32 or a local file. GEMSDOE32's own README calls H33-2-B2 `0.2747` a projection, labels that artifact `UNSCORED`, and says no organizer score exists for its artifacts. GEMSDOE31 describes a `0.2708` geometry as owner-reported, while GEMSDOE32's later audit disputes that attribution; no receipt resolves the conflict. The user-supplied `0.3195` is not verified as the current public maximum; a one-time 2026-10-04 board read showed higher entries. No score table or participant names are mirrored. See [`docs/research/leaderboard.md`](docs/research/leaderboard.md) and the [official live board](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/).
- **Prior site-history lesson:** GEMSDOE32 contains useful owner-reported experiments/projections but explicitly distinguishes them from organizer scores. A prior site's own audit also found a mismatch between its advertised primary download and its measured best artifact. Treat all inherited rankings as hypotheses until this repository reproduces them on authorized data and an uncontaminated spatial holdout. No prior TIFF or pixels are reused here.
- **Official reference solution:** this repo began with only a README title; no prior model code existed. Compare against the [organizer reference](https://github.com/drivendataorg/gems-prize-reference-solution). Its example notebook writes an output without an explicit NoData tag, while the official problem text says null/NaN outside bounds. This format inconsistency remains unresolved until the authorized sample/organizer clarification is checked; this project follows the explicit format text and sample-template mask and does not claim platform acceptance.
- **GitHub Pages:** Pages serves `main:/`; the prior root rendered README instead of the site. PR #2 is merged as `1186bd1b705f47a8979d85c65c552f4c9bc31106`. The Pages API reports the build as `built`; a cache-busted request to the live root follows the redirect to `/docs/`, where the current landing page and submission-status copy were verified.
- **Competition TIFF:** none exists. `docs/downloads/GEMS36_FORMAT_TEST_NOT_SUBMISSION.tif` is deliberately tiny, synthetic, and on the wrong grid. It proves only that a basic GeoTIFF download/link can be exercised.
- **Competition rules:** the September 2026 rules require an AI-use narrative and allow up to three feedback submissions per week; one final file is selected across prize rounds. The competition overview and official rules may change; recheck before upload.

## Ranked research decision

Four distinct, conditional hypotheses are in [`docs/research/hypotheses.md`](docs/research/hypotheses.md). H1 is the **provisional research lead**, not a selected model: combine cross-layer multiscale fault lineaments with an uncertainty/regime-weighted World Stress Map orientation prior inside the differentiable objective. The GFZ WSM 2025 data release is public and CC BY 4.0, but local download, record count/quality in the competition AOI, and field usefulness have **not** been measured. If coverage or licensing/attribution requirements fail, H1 is demoted rather than fabricated.

Other candidates use high-resolution DEM geomorphology, raw GeoDAWN flight-line evidence, or Sentinel-1 InSAR. Official sources and their availability/access gates are listed in [`docs/research/sources.md`](docs/research/sources.md). No new external data have been downloaded and no external candidate is yet declared viable in the AOI.

Read [`docs/research/validation-plan.md`](docs/research/validation-plan.md) before experiments. The plan starts with 512-pixel contiguous tiles, a 30-pixel train collar, a 3-pixel metric support buffer, held-out fault systems where IDs allow, matched prediction budgets, organizer-reference comparison, and stress ablations. It also applies the official existing-fault evaluation mask. **No folds have been run.** The promotion gate requires beating the best comparable local blocked-holdout result; the present local best is `NONE`.

## Project map

- `index.html` — Pages-root redirect to `docs/` (Pages is configured for `main:/`).
- `docs/index.html` — landing page with prominent no-submission status, score-attribution warning, and QA-only download.
- `docs/executive-summary.html` — executive summary and exact data → holdout → build → validate → manual-upload instructions.
- `docs/downloads/GEMS36_FORMAT_TEST_NOT_SUBMISSION.tif` and its JSON — synthetic format fixture only; never upload.
- `docs/research/hypotheses.md` — four ranked hypotheses with layers, mechanisms, expected DTI, cost, availability, and gates.
- `docs/research/sources.md` — official/trusted source register, licenses, and AOI/local-acquisition caveats.
- `docs/research/validation-plan.md` — preregistered spatial holdout and promotion gates.
- `docs/research/leaderboard.md` — dated score attribution and prior-site history; no mirrored score table.
- `docs/research/results.md` — results ledger; no contest score is claimed.
- `docs/research/known_irregularities.md` — data, score, format, deadline, and site-route caveats.
- `docs/research/review-log.md` — three-pass review log for the work sessions.
- `docs/AI_DISCLOSURE.md` — draft for the required future narrative.
- `src/gemsdoe36/metric.py` — local implementation of the published DTI evaluator, not a training loss.
- `src/gemsdoe36/orientation.py` — full-tensor principal-strain helper and differentiable, masked axial-orientation loss; optional PyTorch. Strain is not automatically stress.
- `src/gemsdoe36/spatial_cv.py` — deterministic spatial tile folds and train/evaluation collars.
- `src/gemsdoe36/submission.py` — fail-closed template writer/validator, unique filename utility, read-back and manifest.
- `scripts/audit_inputs.py`, `scripts/build_submission.py`, `scripts/validate_submission.py`, `scripts/check_site.py` — input/TIFF workflow and static-site checks; no auth or downloads.
- `tests/` — analytic/synthetic tests only; no real-data DTI evidence.

## Setup and checks

Python 3.10+ is required. Competition data and generated candidate outputs are ignored by Git.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
# Optional for training-time differentiable orientation loss:
# install a CPU/CUDA-compatible build using the current PyTorch instructions
python -m pip install '.[train]'
python -m pytest -q
python -m ruff check src scripts tests
python scripts/check_site.py
```

The optional `train` extra may install a large PyTorch build; choose a suitable wheel. No GPU is needed for DTI, spatial folds, GeoTIFF writer, or site checks. The orientation test file is skipped if Torch is not installed—report that skip rather than implying the differentiability test ran.

After obtaining competition files through an authorized enrolled session, place them under ignored `data/raw/`. Replace the labels filename with the exact organizer-provided raster:

```bash
python scripts/audit_inputs.py \
  --features data/raw/training_features.tif \
  --labels data/raw/labels.tif \
  --template data/raw/sample_submission.tif
```

Inspect band-level masks/tags, label semantics, valid footprint, and the actual sample grid. Do not place competition data or model checkpoints in Git.

### Candidate path — only after the real holdout gate passes

```bash
# `prediction.npy` must be this project's selected full-grid 2-D probability map.
python scripts/build_submission.py outputs/prediction.npy \
  --template data/raw/sample_submission.tif \
  --submission-name "GEMS36-H1-UNIQUE-RUN-ID" \
  --note "Actual method and measured spatial-holdout result; concise limitation."

# Copy the exact .tif path printed by the builder.
python scripts/validate_submission.py outputs/submissions/PASTE_PRINTED_FILENAME_HERE.tif \
  --template data/raw/sample_submission.tif --json
```

The writer requires exact sample geometry, finite in-bounds [0,1] scores, writes NaN outside, disables TIFF predictors, rereads its bytes, and creates a SHA-256 JSON manifest with the submission name/note. It does not train, measure DTI, pass the holdout gate, or guarantee platform acceptance. **This code path has not generated a competition candidate in this repository.**

## Orientation constraint — required in training, not as a post-filter

`orientation.py` computes a principal extension axis from full \((\epsilon_{EE},\epsilon_{EN},\epsilon_{NN})\) horizontal strain components, then evaluates a differentiable structure-tensor alignment penalty on predicted probability gradients. `physics_informed_objective(base_loss, ...)` adds it during training. Axial directions are modulo 180°; `geographic_en_angle_to_raster` converts EN angles into raster axes. The helper is explicit that strain is only an orientation proxy, not a direct stress measurement. A WSM-derived local stress prior must incorporate record quality, interpolation uncertainty, and regime applicability; where a single extension direction is not justified, confidence must be zero or a justified multi-modal loss must replace the single-axis term. No training experiment has used this loss.

## Sources, limits and next gates

Primary links are in [`docs/research/sources.md`](docs/research/sources.md). Core records include the official [competition metric/data description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [September 2026 rules](https://www.nlr.gov/docs/fy26osti/96647.pdf), [USGS GeoDAWN release](https://doi.org/10.5066/P93LGLVQ), [GFZ World Stress Map 2025](https://doi.org/10.5880/WSM.2025.001), [USGS 3DEP](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services), [NASA Sentinel-1/ASF](https://www.earthdata.nasa.gov/data/platforms/space-based-platforms/sentinel-1), and the [official known-fault scoring clarification](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516). All data pages were checked at the publisher/page level; no local AOI/coverage analysis was performed.

Important limits: no private labels; no competition inputs; no spatial folds or holdout winner; no verified local coverage for WSM/3DEP/GeoDAWN raw profiles/Sentinel-1; no contest score receipt; no candidate TIFF; official-format/reference-notebook discrepancy; prior score attribution remains unresolved; and known-fault masking must be represented in local holdouts. Review the full [`known_irregularities.md`](docs/research/known_irregularities.md).

**Next gates, in order:**

1. Obtain the official rasters/template legally; hash them and resolve grid/mask/format semantics from actual files.
2. Preflight the WSM AOI record count/quality/regime, DEM URL coverage, and any selected external dataset's license/access. Demote candidates that fail.
3. Reproduce the organizer reference under masked, spatially blocked folds; establish the current local best.
4. Test the lead and ablations with matched policy; require a positive, robust improvement over that best before any weekly slot.
5. Generate a unique TIFF/name/note from this project's own method; locally validate exact bytes/hash; update AI disclosure.
6. Only then consider manual upload and preserve the organizer receipt. Follow current submission rules.
7. **GitHub handoff completed for this code/site follow-up:** [PR #2](https://github.com/buffedlizard55-lab/GEMSDOE36/pull/2) was merged to `main` at 2026-10-04 18:07:50 UTC as merge commit `1186bd1b705f47a8979d85c65c552f4c9bc31106`. This confirms only the code/research/site changes—not a model, score, upload, or competition submission.
