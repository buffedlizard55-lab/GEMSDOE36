# Cross-repository review and historical submission shortlist — 2026-10-26

## Executive decision

**Do not download any historical TIFF as the proposed new entry, and do not submit it. No new competition TIFF has been generated or approved in this review.** The artifacts in `docs/downloads/` are prior-run/QA files; the landing page correctly marks the historical ones “DO NOT SUBMIT.” A unique raster has not been proven unique merely because it has a new filename.

The strongest historical result in the user's supplied nine-site list is GEMSDOE32's `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`, reported as **0.2778**. This is an owner-supplied score, not an organizer receipt independently verified in this checkout. It is a useful experimental incumbent for forensics, not a safe current upload recommendation. None of the nine sites establishes a validated route to exceed the present competition best; user-provided leaderboard figures conflict (0.4413 and 0.3195), and neither was checked against a current organizer leaderboard in this environment.

## Highest reported candidate per site

Scores and names in this table transcribe the user's prompt. They are **OWNER-REPORTED / UNVERIFIED** and are not labeled ORGANIZER-CONFIRMED. “Best” means highest reported score among the items supplied for that site, not an independently recomputed rank across every artifact that site ever published. Check the linked site and versioned local snapshots for manual review. Do not upload based on this table.

| Site | Highest submission supplied | Supplied score | Interpretation / disposition |
|---|---|---:|---|
| [GEMSDOE24](https://buffedlizard55-lab.github.io/GEMSDOE24/) | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan` | 0.2477 | Highest of the two values provided (later `gvc1` value 0.0859); historical only. |
| [GEMSDOE25](https://buffedlizard55-lab.github.io/GEMSDOE25/) | `dotted-h19-5-d2-8-20261002-e56ea318af89-nan` | 0.2600 | Highest of the supplied pair; historical only. |
| [GEMSDOE27](https://buffedlizard55-lab.github.io/GEMSDOE27/) | `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan` | 0.2449 | Higher than the later supplied hydrothermal-piedmont value (0.2190); historical only. |
| [GEMSDOE28](https://buffedlizard55-lab.github.io/GEMSDOE28/) | `h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan` | 0.2710 | Highest of the four supplied scores (0.2649–0.2710); historical only. |
| [GEMSDOE30](https://buffedlizard55-lab.github.io/GEMSDOE30/) | `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca` | 0.2600 | Higher than the later supplied 0.1462 entry; historical only. |
| [GEMSDOE31](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/) | `h27-4-solo-d28-20261004-8acb75e1-nan` | 0.2708 | One supplied scored item; historical only. |
| [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` | **0.2778** | Highest of the nine supplied values. The pinned local page calls this owner-reported; not a receipt. Do not re-submit it. |
| [GEMSDOE33](https://buffedlizard55-lab.github.io/GEMSDOE33/) | `h33d-analog-tip-stepover-r30-20261004-cb490425926e` | 0.2632 | One supplied scored item; historical only. |
| [GEMSDOE36](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/) | `anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros` | 0.2750 | Highest reported for this site; previous repository narrative overstated its promotion status. Do not submit. |

Versioned page/README snapshots and commit IDs for these nine repositories are in [`sources.json`](../../evidence/review-20261025/sources.json); saved page text is in [`evidence/review-20261025/`](../../evidence/review-20261025/). These snapshots help audit what the pages claimed at capture time; they do not prove the current public page, a submitted score, or the contents of a linked raster. The saved GEMSDOE32 page also contains later candidate information and a warning that no organizer score exists for those newer artifacts. That does not authenticate the older 0.2778 number.

## Why the reported GEMSDOE32 result may have led this list

The available page text describes an earlier sparse detector and a B=2 catalogue-flank exclusion. The proposed score-mechanics explanation is plausible: if known catalogue faults are excluded from scoring, removing predictions near known faults may reduce false-positive penalty mass while preserving credit from predictions near hidden targets. Sparse spatial coverage can also avoid spending predictions repeatedly on the same trace. This is a mechanism hypothesis, **not established causal attribution**.

What cannot be concluded from the supplied numbers alone:

- that the 200 m exclusion caused the whole gain (would require matched ablations, same labels/metric, and comparable submission settings);
- that all near-catalogue predictions earn zero credit or that a 200 m halo is organizer policy (only the precise organizer evaluation mask/rules can establish this; see the staff clarification link in `sources.md`);
- that this raster best identifies geothermal vents (the scored target is faults, not vents);
- that it beats a current official best, or that a transformation from it will exceed 0.2778;
- that any current sibling-site TIFF is unique pixelwise relative to a complete registry.

The local GEMSDOE32 snapshot contains conflicting descriptions and later artifacts, and its current copy reports the 0.2778 as owner-reported in at least one status passage. The correct label here is therefore **OWNER-REPORTED / UNVERIFIED**. The user's listed current-best figures (0.4413 and 0.3195) also conflict and were not independently fetched. No projection is presented as a score.

## Candidate hypotheses to investigate (ranked judgment, not results)

Ranking is a qualitative expected-value-versus-effort judgment only. These are proposals based on bands named in the repository's historical `data/prepared_manifest.json` and the research notes; actual data rasters/cached stack are absent from the current checkout. None has been run on a valid holdout. A “could reveal” rationale is not evidence that a fault exists.

| Rank | Hypothesis and layers | Physical signature | Why it might find an unrecorded fault | Difference from existing repository work | Main non-fault mimic | Cost / expected DTI |
|---|---|---|---|---|---|---|
| 1 | **Basin-floor flexural hinge:** `depth_to_base_surf`, `iso_grav_anom`, `det_elev` | Signed, multiscale second-derivative hinge pairs: a persistent basement-depth break with an asymmetric shallow shoulder, conditioned on smooth surface relief | Could respond to buried displacement under basin fill without a sharp mapped scarp | Tests signed profile-pair topology rather than the implemented gradient-family belief, dip projection, or dot-emission rule | Sedimentary compaction or an erosional basin margin | Medium; expected benefit is a testable but unquantified possibility; no DTI projection. |
| 2 | **Electrical–basement discordance:** `cond_surf`, `depth_to_base_surf`, `iso_grav_anom_hg` | Spatially blocked residual of conductivity conditional on basement depth/gravity, then oriented ridge persistence | A narrow conductive anomaly not explained by basin-fill geometry could be consistent with a concealed fluid pathway/fault | Conditional residualization avoids simple raw-layer multiplication used by existing belief-family combination | Saline playa brine or clay alteration | Medium; unquantified and especially sensitive to spatial resolution/confounding. |
| 3 | **Open-versus-closed magnetic contact curvature:** `rtp`, `tmi_vg`, `depth_to_base_surf` | Oriented RTP inflection pairs with concordant basement-depth change; discriminate open line contacts from closed compact anomalies | Could identify a displaced buried contact without a surface trace or catalogue trace | Adds contact topology and depth concordance, unlike standalone gradient magnitude/orientation priors | Intrusive body or lithologic contact | Medium–high; unquantified. |
| 4 | **Lithology-conditioned geomorphic tilt asymmetry:** `det_elev`, `det_elev_slope`, `rtp` | Compare integrated opposing-flank profiles after matching/conditioning on magnetic texture and scale | May detect broad warped alluvial surfaces when the scarp is subdued | Paired-flank asymmetry rather than current scarp magnitude or ridge-support features | Alluvial-fan deposition, drainage incision, or differential erosion | High; unquantified and weaker fault specificity. |

**Lane/protocol stop:** the current checkout does not identify the single assigned method paragraph required by the parallel-run protocol. Therefore no candidate is selected or implemented here. Do not substitute a different lane, privately fork a supposedly shared evaluator, or generate a TIFF to satisfy a format check while scientific gates are absent.

## Repository review: verified locally

- Branch observed: `arena/2c322d39-gemsdoe36`; clean at review start.
- The current landing page and executive summary visibly say **DO NOT SUBMIT** and distinguish research downloads from approved files. This is correct and should remain prominent.
- `docs/current-run.json` is a negative/blocked run card with null holdout, novelty, raster hash and format checks; `submit_ready=false`, `slot_approved=false`. This is more truthful than historical promotion claims.
- Historical TIFFs remain under `docs/downloads/`; `docs/downloads/GEMS36_FORMAT_TEST_NOT_SUBMISSION.tif` is synthetic QA. These are not new outputs.
- `data/raw`, `data/processed`, and `data/study` are absent. Only prepared/restoration metadata JSON files are present. Therefore there is no live feature cache or training input to run, despite hash/manifests describing earlier data availability.
- `scripts/run_holdout.py` exits at the beginning with an explicit warning that the old H6 evaluation exposes SGMC truth for placement and is not a valid promotion gate. Do not treat its retained historical code as an acceptable evaluator.
- `scripts/run_pipeline.py` is also guarded as a legacy entry point. The referenced shared `evaluate_holdout.py` and `submission_writer.py` are absent; local `src/gemsdoe36/protocol.py` calls itself audit primitives, and its callback interface alone cannot prove no hidden-label leakage.
- `docs/research/sources.md` is the source register; it distinguishes official sources and access limits. Current organizer portal/leaderboard access, an authenticated submission receipt, and a current weekly cap were not verified.
- `README.md` contains a current fail-closed notice and a historical long-form prompt/claims. Some historical prose presents old TIFs, metric outputs, or projected scores as if approved. The top notice says this is superseded, but readers should treat the rest as archival, not operational instructions.

## Submission / uniqueness decision

**Unique TIFF generated: no. Safe to download and submit a newly generated file: no.** The missing assigned lane, cached inputs, official shared evaluator and complete raster registry prevent the required pre-placement screen and holdout. No new scores, CI, AUC canaries, overlap statistics, or validator results were manufactured. Prior TIFF download links on the landing page are expressly labeled for research / not for submission.

A complete promotion record needs, at minimum: (1) assigned method paragraph; (2) authorized, hash-verified feature stack and exact organizer template; (3) correct shared whole-segment hide-and-recover evaluator using visible-only features and pixel-exact visible-fault masking; (4) each-feature leakage canary; (5) pooled HOLDOUT-DTI, evaluator version, withheld positive count and spatial-block CI, beating a frozen comparable best; (6) full registry and surface/dot novelty comparisons before placement and final emission; (7) exact-file format/range/no-NaN-inside-footprint validation and SHA-256; and (8) separate selector approval before any weekly slot.

## Official links for follow-up

- [DrivenData challenge overview and rules](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [DrivenData problem statement / metric / format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [DrivenData about page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/)
- [DrivenData authenticated data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) (login is required; data not present locally)
- [DrivenData leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) (current values not checked here)
- [Organizer reference-solution repository](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS GeoDAWN official data release page](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [Great Basin Center for Geothermal Energy / INGENIOUS](https://gbcge.org/current-projects/ingenious/)
- [Official GEMS rules PDF (NLR)](https://docs.nlr.gov/docs/fy26osti/96647.pdf) — verify current rules/version directly before use.
- More detailed citations/access qualification: [`sources.md`](sources.md).

## Three-pass review and checks

1. **Inventory/source pass:** reviewed branch, current site, run card, manifests, protocol code, legacy entry-point guards, nine pinned site snapshots and source register. No organizer receipt or complete TIFF registry found in this checkout.
2. **Bug/edge-case pass:** attempted the documented check script. Plain Python lacked `pytest`; installed project/dev dependencies in ignored `.venv/` (no tracked environment files). Test suite then passed: **69 passed, 1 skipped** (optional PyTorch unavailable). Site check passed. Ruff failed with pre-existing repository-wide lint findings (including missing executable bits, obsolete `noqa`, style warnings); those are not evidence of model validity and were not bulk-reformatted in a scientific review.
3. **Request re-check:** compared each requested site and candidate/holdout/uniqueness/submission criteria to available evidence. The site-by-site summaries and ranked ideas are delivered, but actual performance validation and a unique upload-ready TIFF are blocked by missing lane/data/evaluator/registry. Therefore no candidate is promoted and no submission slot is recommended or used.

## Required run card

```json
{
  "hypothesis": "No assigned lane; basin-floor flexural hinge is a ranked proposal only",
  "mechanism": "Signed multiscale second-derivative hinge pairs from depth_to_base_surf, iso_grav_anom, and det_elev",
  "non_fault_mimic": "Sedimentary compaction or erosional basin margin",
  "holdout_dti": {
    "label": "HOLDOUT-DTI",
    "evaluator_version": null,
    "withheld_positives": null,
    "value": null,
    "ci95": null,
    "status": "not run; assigned lane, feature cache, and shared segment evaluator unavailable"
  },
  "correlation_overlap_vs_registry": {
    "surface_rank_correlation": null,
    "dot_overlap_within_3px": null,
    "status": "not run; no new raster and registry completeness unavailable"
  },
  "raster_sha256": null,
  "validator_output": {
    "no_nan_inside_footprint": null,
    "values_in_0_1": null,
    "crs_shape_transform_match": null,
    "status": "no candidate raster generated"
  },
  "submission_name": null,
  "note": "Blocked review only; no new TIFF, no promotion, no slot used.",
  "verdict": "negative"
}
```
