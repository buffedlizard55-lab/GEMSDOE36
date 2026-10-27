# GEMSDOE36 repository review — 27 October 2026

## Executive decision

**No current artifact is cleared to submit. Do not spend a competition slot.** This review generated no new TIFF and ran no geological experiment. The experiment count is **0/3** and no weekly slot was selected or used.

The session's protocol says to remain in one specifically assigned method lane, but the brief does not identify a single method paragraph that assigns that lane. It also says to stop when the final-dot overlap with any registry raster exceeds 70%. The reproduced prior KPL-36 artifact fails that literal gate against `reg-052` at **99.1687%**. That is a duplicate-gate measurement, not a competition score. A separate pigeonhole bound shows a 37,654-dot submission would have at least **82.3418%** overlap with the lattice's 3-pixel coverage, regardless of where those dots were placed. This makes the existing 37,654-dot release template ineligible under the literal rule. The bound does *not* prove that every lower-density candidate would pass, or that a low-density candidate would be useful.

The user-requested new TIF was therefore **not** generated. Creating an arbitrary raster without a named lane, testing the surface before placement, and demonstrating a buffered whole-segment holdout gain would violate the supplied protocol. The repository already contains research-only TIFFs, including S2D-36; those files do not have submit authorization. No newly proposed method has demonstrated a gain over the current held-out best under this session's allowed lane.

## Nine-site executive audit

These are the highest historical file/score pairs recorded in the pinned Focus-9 audit and supplied owner history, not fresh leaderboard reads or submission-page receipts. The local audit hashes the referenced GitHub mirror bytes; it cannot authenticate a score. The “unique?” column asks whether the file passes the specified pairwise 3-pixel-overlap / rank-correlation rule against all other Focus-9 rasters. **None does.** Exact pixel-identical relationships are called out separately where the audit records them.

| Site | Highest recorded file to inspect (pinned source) | Reported result (not an estimate) | Unique vs the other listed sites? | Submit decision |
|---|---|---:|---|---|
| GEMSDOE24 | [gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif](https://github.com/buffedlizard55-lab/GEMSDOE24/blob/fc2bc6f350bf5c6ce8da5d7a2ab03578ea1259d1/docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif) | 0.2477 USER-REPORTED | **No** — pairwise max overlap 100%; reported as a subset of GEMSDOE27 | **Do not copy or submit** |
| GEMSDOE25 | [gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif](https://github.com/buffedlizard55-lab/GEMSDOE25/blob/e40b9b5e3871cb34d138f586bde97f5099658d01/docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif) | 0.2600 OWNER-REPORTED | **No** — exact in-footprint duplicate of GEMSDOE30 D2.8 | **Do not copy or submit** |
| GEMSDOE27 | [gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif](https://github.com/buffedlizard55-lab/GEMSDOE27/blob/927322eadbde56be42ae129ccdfb9b37540d8e60/docs/downloads/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif) | 0.2449 OWNER-REPORTED | **No** — pairwise max overlap 98.02% | **Do not copy or submit** |
| GEMSDOE28 | [gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif](https://github.com/buffedlizard55-lab/GEMSDOE28/blob/e6321461066f89080e3b1bb670d3951ab20d3638/docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif) | 0.2710 OWNER-REPORTED | **No** — pairwise max overlap 100%; its `h27-4-r1-solo` alternative is pixel-identical to GEMSDOE31 | **Do not copy or submit** |
| GEMSDOE30 | [gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif](https://github.com/buffedlizard55-lab/GEMSDOE30/blob/760af3005dd40b9f36d8fef97d6dc384fd9f2a2f/docs/downloads/gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif) | 0.2600 OWNER-REPORTED | **No** — exact in-footprint duplicate of GEMSDOE25 D2.8 | **Do not copy or submit** |
| GEMSDOE31 | [gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif](https://github.com/buffedlizard55-lab/GEMSDOE31/blob/597b04cd1afb65d1ebbe3e9417fd952be48e3d74/docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif) | 0.2708 OWNER-REPORTED | **No** — exact in-footprint duplicate of GEMSDOE28 solo | **Do not copy or submit** |
| GEMSDOE32 | [gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/5fc7792c5887735ecd3aa9a612787da588a7bf2c/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif) | 0.2778 OWNER-REPORTED | **No** — exact member of the D2.8/B2 thinning family; pairwise audit fails | **Do not copy or submit** |
| GEMSDOE33 | [GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif](https://github.com/buffedlizard55-lab/GEMSDOE33/blob/f618cc54773bd9b4d6c2b3ebf78103a05cc10cb6/docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif) | 0.2632 OWNER-REPORTED | **No** — pairwise max overlap 99.71% | **Do not copy or submit** |
| GEMSDOE36 (historical) | [gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif](https://github.com/buffedlizard55-lab/GEMSDOE36/blob/c5a8ae7da3bd2fcff5aa5855afd44c7a3346c16f/docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif) | 0.2750 OWNER-REPORTED | **No** — 97.58% max overlap; contains all GEMSDOE32 B2 dots plus 1,200 dots | **Do not copy or submit** |

**Interpretation:** GEMSDOE32's 0.2778 is a useful forensic clue, not evidence that its pixels independently detected more faults. The pinned raster analysis records B2 as D2.8 with a near-catalogue collar removed. In the weighted Tversky metric, removing predictions close to known faults can reduce false-positive penalty while sacrificing little credit, because mapped faults are masked. GEMSDOE25 D2.8 and GEMSDOE30 are pixel-identical in the footprint; GEMSDOE28 and 31 include another pixel-identical pair. Therefore the scores in this family are neither independent method replications nor valid out-of-sample evidence for a new raster. This is a plausible metric mechanism, not proof of why any hidden label was scored as it was.

**Can we claim a score above 0.2778? No.** The best prior internal GEMSDOE36 record cited in the repository is `HOLDOUT-DTI 0.200766` (evaluator `gems-segment-pooled-v1`, 60,988 withheld positives, 95% CI `[0.186488, 0.215333]`). It is not a leaderboard score and does not calibrate transfer to hidden test labels. No numeric leaderboard estimate is supportable for a new candidate. The prompt contains conflicting top-score figures (0.3195 and 0.4413); neither was refreshed in this session, and no score receipt was provided. Don't select an existing high-score TIFF as a new submission.

## Repository and release findings

1. **Guardrails are implemented and fail closed.** `scripts/review_literal_release.py` reproduces the KPL duplicate decision and the geometric bound. The stored run card reports `verdict: negative`, `submit_ok: false`, `slot_selected: false`, a null calibration estimate, and an unrerun surface correlation because no new surface was produced. The final-dot gate is decisive; do not mislabel the missing surface calculation as a pass.
2. **The site's large historical material needs careful reading.** It labels download artifacts `research only` and presents a literal stop first. The executive summary keeps historical owner-reported results distinct from `HOLDOUT-DTI` and has all nine requested sites. The newer S2D/TCD artifacts are also explicitly negative; their local format validation must not be read as submission authorization.
3. **Current holdout claims are archived evidence, not rerun measurements.** The S2D/TCD scores are prior cards, not this session's experiment. The cross-site scores above are owner-reported. There is no organizer-confirmed receipt in this audit.
4. **Data availability was restored for reproducible local work.** This audit restored and SHA-256-verified all 30 manifest entries from pinned GitHub owner mirrors: 4 core files, 14 external-data files, and 12 scored comparison rasters. Competition `training_features.tif` is 418,912,844 bytes. These are owner-mirror copies, not authenticated official competition downloads. Raw data is ignored by Git and is not part of the deliverable.
5. **The full test suite passes, with one optional-dependency skip.** `167 passed, 1 skipped`; the skipped orientation test requires optional PyTorch. Ruff and the static GitHub Pages site check pass. `scripts/verify_release_gate.py`, `verify_csdl36_release.py`, `verify_gvsc36_release.py`, `verify_mto_release.py`, and `review_literal_release.py` were also run and returned negative/no-submit release decisions with their checks passing. The first attempt at `review_literal_release.py` failed because the raw TIFFs were absent; it passed after restoring the pinned inputs. A second test run exposed that external test input was also absent; restoring all manifest groups resolved it. Those were incomplete local inputs, not algorithmic failures.
6. **External status is not current.** The competition login data page, live leaderboard, official rules PDF, and USGS/GDR pages were not fetched in this session. The repository/network environment is limited to GitHub/PyPI access for this work; provided official URLs remain useful for manual review but are not represented here as independently refreshed.
7. **No candidate estimates are available.** Historical reported scores and internal holdout DTI are different quantities. No transfer model was validated/calibrated, no organizer receipt was present, and no leaderboard projection is provided.

## Three review passes

### Pass 1 — implementation and verification

Read the standing brief in `README.md`, inspected the current decision/run cards, the site/executive summary, the pinned Focus-9 evidence, shared holdout/writer modules, release gates, tests, and data restore manifest. Restored all three manifest groups and SHA-verified the 30 owner-mirror assets. Re-ran the release review and uniqueness bound. The 37,654-dot artifact remains over the literal 70% rule; no alternative emission was made.

### Pass 2 — bug, assumption, and edge-case review

Checked that (a) “download for research” is not conflated with “OK to submit”; (b) user-reported scores are not called organizer-confirmed; (c) DTI holdout scores do not become leaderboard predictions; (d) a null rank-correlation value is represented as not run, not zero; (e) restore receipts match files actually available; and (f) the overlap threshold is treated as strict `> 70%` for the stipulated rule. Initial missing-data failures were resolved by hash-pinned restores. One optional PyTorch test remains skipped.

### Pass 3 — final requirement check

The nine-site table is explicit; each row names the historical highest file and reported value, pairwise uniqueness conclusion, and no-submit decision. GEMSDOE32 B2 is analyzed as a family-thinning result, not copied as a candidate. The candidate-level score estimate is unavailable, rather than invented. No unique competition-ready TIF exists in this decision because the assigned lane is unspecified and the extant dense files fail the literal uniqueness gate. This review honors the no-slot budget and stops before any unauthorized experiment.

## Candidate research hypotheses: ranked, not tested here

The report `review-20261027.md` contains a prior hypothesis ranking and explains why it is not a lane assignment. Here is the short actionable set, with proposed signatures and primary confounds:

1. **Rank 1 — Displaced independent geophysical contacts** *(qualitative upside: potentially moderate, very uncertain; implementation cost: medium-high).* Layers: competition magnetics/radiometrics plus DEM; pair matched contact-edge segments across a narrow offset corridor. This differs from simple line coherence/contact-strength scoring and could identify buried displacement not already catalogued. Mimics: depositional contacts and raster-registration error. Existing layers suffice in principle. Requires a named-lane decision and surface/canary/holdout validation.
2. **Rank 2 — Signed multi-scale magnetic edge sequence** *(qualitative upside: low-to-moderate, very uncertain; cost: low-to-medium).* Layer: total-field magnetic data; combine analytic-signal amplitude with oriented edge-polarity sequences to target deep faults whose orientation makes a single derivative weak. This differs from scalar lineament persistence. Mimics: dikes and remanent magnetization. No new data appears necessary, but no measured gain is claimed.
3. **Rank 3 — Repeated drainage deflection with common displacement sense** *(qualitative upside: potentially moderate, high resolution risk; cost: medium-high).* Layers: detrended DEM / USGS 3DEP; detect spatially coherent stream elbows across adjacent channels rather than isolated curvature peaks. This differs from local scarp/toe curvature. Mimics: stream capture, lithologic boundaries, roads. Existing DEM permits an initial test; high-resolution 3DEP tile coverage must be checked against the AOI before claiming that version is viable.
4. **Rank 4 — Cross-flight-line magnetic profile repeatability** *(qualitative upside: unknown; cost: high; currently blocked).* Layer: raw USGS GeoDAWN profiles; seek cross-over/repeat structure independent of survey-line direction. This differs from gridded 2-D lineaments but has already been proposed in the registry preflight, so it is not new to this repository. Mimics: dikes and residual levelling artifacts. Raw-data availability/AOI coverage was not verified.

These are hypotheses, not expected DTI scores. For experiment triage only, the relative prior is: (1) paired displaced contacts may have the greatest geological upside but cost medium-high implementation; (2) signed magnetic edge sequences offer a lower-cost first falsification and potentially modest upside; (3) repeated drainage deflection could add independent geomorphic evidence but has higher implementation/data-resolution risk; (4) raw-flight crossover analysis is blocked and was already proposed. **No numerical expected DTI improvement is supported by this evidence.** The first three use existing competition layers in principle; high-resolution drainage needs AOI-specific 3DEP tiles whose availability is not verified here. None is assigned to this session's parallel lane. The precise method paragraph must be identified before any is chosen.

## Limitations and next work

- Obtain the explicit single-paragraph lane assignment. Do not infer it from the brainstorm list.
- If a candidate is authorized, use the existing cached feature stack and shared `scripts/evaluate_holdout.py` / `scripts/submission_writer.py`; first test every feature alone as a leakage canary. Withhold complete fault segments plus buffer, refit catalogue-derived features using only visible faults, and score pooled DTI with the locked evaluator.
- Evaluate registry surface rank-correlation before placement and final-dot overlap after placement. Refresh the registry from pinned and newly identified candidates. This session cannot treat the owner-mirror registry as an organizer registry.
- Resolve the strict literal uniqueness constraint with a scientific emission-density/preregistration plan before running experiments. Passing a geometric bound is necessary only; it does not establish novelty or useful performance.
- Only after a candidate beats the current held-out best under the same fold/bootstrap protocol and clears every literal release gate should a separate weekly selector consider it. The weekly cap and currently eligible entry are not refreshed here.
- Official references for follow-up: [DrivenData problem statement](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [competition data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/), [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/), [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [USGS 3DEP](https://www.usgs.gov/3d-elevation-program), [DOE GDR 1391](https://gdr.openei.org/submissions/1391), [INGENIOUS](https://gbcge.org/current-projects/ingenious/), and the [organizer reference implementation](https://github.com/drivendataorg/gems-prize-reference-solution). Links are supplied for follow-up; they were not all fetched in this session.

## Reproduction commands

```bash
python -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/python scripts/restore_data.py --group core
.venv/bin/python scripts/restore_data.py --group scored
.venv/bin/python scripts/restore_data.py --group external
.venv/bin/python scripts/review_literal_release.py
.venv/bin/python scripts/registry_feasibility.py --dots 37654  # expected exit 2: guaranteed stop
.venv/bin/pytest -q
.venv/bin/ruff check src scripts tests
.venv/bin/python scripts/check_site.py
```

## Run card (session review; no new raster)

```json
{
  "hypothesis": "A newly authorized detector of previously uncatalogued faults can exceed the 0.2778 owner-reported B2 result only if it contributes genuine, off-catalogue hidden-fault coverage rather than merely thinning the existing D2.8 family.",
  "mechanism": "Not tested in this session: no single method paragraph assigned the lane. The recorded B2 gain is consistent with pruning predictions near known-fault masking, which reduces false-positive mass; the available analysis does not establish hidden-label causality.",
  "named_non_fault_process_that_could_mimic_it": "Long roads and railways, shoreline benches, erosional range-front facets, lithologic contacts, and DEM/acquisition artifacts.",
  "holdout_dti": {
    "label": "HOLDOUT-DTI (historical S2D-36 EXP-2; not rerun this session)",
    "evaluator_version": "gems-segment-pooled-v1",
    "withheld_positives": 60988,
    "dti": 0.200766,
    "ci95": [
      0.186488,
      0.215333
    ]
  },
  "correlation_overlap_vs_registry": {
    "candidate_surface_rank_correlation": null,
    "candidate_surface_status": "NOT RUN: no candidate surface generated",
    "prior_KPL_final_dot_overlap_3px_vs_reg_052": 0.991687,
    "prior_KPL_status": "FAIL; prior artifact only",
    "37,654_dot_geometric_lower_bound_overlap_3px": 0.823418
  },
  "raster_sha256": null,
  "validator_output": {
    "no_nan_inside_footprint": null,
    "values_in_0_1": null,
    "crs_shape_transform_match": null,
    "status": "NOT APPLICABLE: no new raster generated"
  },
  "submission_name": null,
  "submission_note": "No new TIFF generated; no slot authorized.",
  "verdict": "negative"
}
```
