# Current result — 2026-10-25 S18-MXTP (read first every session)

## NEW UNIQUE TIFF GENERATED — **DO NOT SUBMIT: HOLDOUT GATE FAILED**

[**Download the new unique research TIFF**](docs/downloads/gems28-s18-mxtp-20261025-3e95505c011a-allfinite.tif)
· [Executive summary / submission process](docs/executive-summary.html)
· [Current full JSON run card](evidence/s18_mxtp_run_card.json)
· [Scientific result, sources and next steps](knowledge/54_s18_result.md)

The new 11,082-dot migration-extrapolated TMI/gravity raster is independently generated, not copied
from a previous submission. Both pre-placement and final-dot uniqueness pass against 166 pinned
valid-grid rasters across the nine requested repositories plus local research artifacts. Exact-file
checks pass: no NaN anywhere, values {0,1}, single-band float32, template CRS/shape/transform.
**It is safe to download for research, NOT approved to submit.** Format validity and novelty do
not compensate for failed scientific validation; no human inspector or competition slot was used.

**HOLDOUT-DTI** (shared eval_set **v2** → metric.dti_binary, buffered whole-system LOSFO,
seeds 310–314, 20 cells, 76,869 pooled withheld positives / 45,155 unique): **0.020384**
(95% CI **[0.016438, 0.024729]**) vs recomputed registered H38-1 candidate **0.108239**;
paired gain **−0.087855** (95% CI **[−0.112958, −0.059642]**). Four-geographic-block bootstrap;
local recovery proxy, not an organizer score. All three experiments used; lane closed.

**Current source corrections:** the official leaderboard displayed **0.4413** on 2026-10-25
(one-off public source observation, NOT a submission-page receipt). The September rules §§3.2/3.4
state **three submissions/week**; the authenticated account's remaining allowance is unknown.
[Source review](evidence/s18_official_source_review.json). No score for a GEMSDOE raster has an
organizer receipt here. Fresh byte forensics confirm that the reported GEMSDOE32 champion is
solo-r1 minus 2,545 catalogue-flank dots; its reported 0.2778 association remains unverified.

**Parallel-run addendum (Session 18B, H42-1, same date):** another concurrent run executed
the H42-1 migration-vector relocation lane
([preregistration](knowledge/52_preregistration_H42-1_migration_relocation.md),
[result](knowledge/54_s18b_h42_1_result.md), run card `evidence/s18b_run_card.json`). It
generated a genuinely unique TIFF (`290553965159`, 34,492 dots) that passed binding
scored-registry uniqueness and format validation but **failed its frozen LOSFO gate**
(HOLDOUT-DTI Δ −0.004957, 95 % CI [−0.006577, −0.003294], 1/20 cells; anti/random controls
equally negative). Verdict `negative`; 🔴 DO NOT SUBMIT. It independently reserved seeds
310–314 and reproduced the identical pooled D0 of the parallel H39-5 gate (also negative,
Δ −0.010731) — corroboration that migration-extrapolated placement is falsified, not one
pooled experiment; never combine the parallel sessions' numbers
(`s18b-session-label-collision` in `registry/irregularities.json`). One disclosed deviation:
support-averaged (not coherence-weighted) vector combination
(`s18b-vector-combination-deviation`); the falsification is direction-agnostic, so the lane
stays closed and seeds 310–314 are spent for it. Still **no file approved**.

### Standing owner prompt — start here every session

Read the [current normalized owner request](knowledge/53_current_request.md), the
[frozen S18 ranking and method](knowledge/52_s18_preregistration.md), and the result above.
The request is archived as an operational requirements record, **not a verbatim export of this
chat**; historical verbatim prompts below remain historical. The chat remains authoritative.
Core values: **Maximize P(Win)** and **Own the Outcome**. Do not relabel a rejected candidate,
retune spent seeds, copy a previous raster, or spend a slot without a separate selector.

- Unique TIFF + obvious first-screen upload decision; no human geological inspection gate.
- One lane; cached features + shared evaluator/writer; buffered whole-system hide/recover;
  visible-only catalogue features; exact visible masking; pooled α=.2 / β=.8 / triangular 300 m DTI.
- Feature-alone leakage canaries; pre-placement AND final-dot comparisons to registry; duplicate
  stop at Spearman >.90 or >70% within 3 px. Snapshot scope must be explicit.
- Versioned HOLDOUT-DTI with withheld positives and 95% CI. ORGANIZER-CONFIRMED only from a
  submission-page receipt; never turn owner claims or projections into verified scores.
- Before implementation rank 3–5 physical hypotheses by expected benefit/cost, distinguishing
  faults from lithologic contacts and vents. Official free-source availability/provenance gates.
- Stop at 3 experiments or 2 hours; JSON run card (hypothesis, mechanism, non-fault mimic, DTI+CI,
  registry checks, SHA-256, validator, name, note ≤140 characters, promote/negative verdict).
- Three implementation/review passes; automated exact-file validation; clean Pages executive
  summary; auditable official sources; no automatic competition upload. PR then merge after checks.

**Shared fix:** eval_set v2 now delegates to the existing tested metric to prevent phantom TP on
empty predictions and to mask truth consistently. Historical outputs were not silently rewritten.
**Erratum:** the frozen rank-2 hypothesis mislabeled conductive-base depth as basement thickness;
it is rejected as stated. No alternative experiment was run.

**Limitations / next session:** explicit exclusive lane paragraph was absent; S18 followed the
repo's recommended next step and discloses that interpretation. Registry is pinned, not synchronized
across every parallel run. Owner-mirror bytes are hash-verified, not organizer-authenticated.
No private labels, DrivenData login, account quota, eligibility verification or receipt. S18 used the
repository-existing harness/writer; equivalence to the later restored upstream template APIs is not
established, so this is not a fully protocol-certified submission. Restore the
17 pinned inputs via the existing tools to reproduce file checks; CPU classifier training worked.
Keep S18 closed. Establish a synchronized registry and one frozen best baseline before a fresh,
provenance-audited scarp-displacement hypothesis with road/shoreline controls.

---

## Parallel review integration

Parallel PRs #37/#38 ran no experiment because their checkouts lacked inputs and an explicit lane.
Their [blocked review card](evidence/s18_run_card.json) is preserved, distinct from
[this experiment's S18-MXTP card](evidence/s18_mxtp_run_card.json). Their schema-only readiness fix
and withdrawal of historical H38 uniqueness/promotion claims remain in force. S18-MXTP restored
data autonomously and discloses its lane interpretation; it is still rejected and not slot-approved.
PR #39’s separate no-experiment audit, upstream tool pins, stronger validator/gate and publication
checks are also retained. Its original hashed manifest is archived without changing its old card.
PR #42’s root-route compatibility test and observed historic deployment evidence are retained
([prior release proof](evidence/current_deployment_verification.json), not proof for the new TIFF).
Final local integration: **478 tests pass, zero skips; 347 independent file checks pass; Ruff clean**.
Do not combine these sessions' numbers or treat the blocked review's missing-data statement as
current after this restoration.

Concurrent PR #41's **different** H39-5 run is retained under
`evidence/s18_h39_5_run_card.json` / manifest `s18_h39_5_candidate`, with its negative TIFFs
in the archive. It is not MXTP, not independent replication, and not part of our frozen 166-raster
snapshot. Shared seed/method-family collision is logged; no global exclusivity is claimed.

## Historical notices and prior standing briefs (superseded by current result above)

# Current session safety notice — 2026-10-25 Session 16 (read first)

**NO FILE IS CURRENTLY APPROVED FOR SUBMISSION.** The Session 16 H40-1 migration TIFF
(`5f2efa891ce7`) failed both its frozen holdout-spread gate and the strict uniqueness
gate; it is inspection-only. The older H36-1/H38-1 downloads are historical research
artifacts, not unique candidates for this run and not approved by the separate selector.
Do not upload any file from this repository unless a future candidate passes its frozen
holdout, uniqueness, and exact-file gates and is separately approved by the selector.
Read [the Session 16 result](knowledge/50_s16_result.md) and its
[preregistration](knowledge/49_preregistration_H40-1_migration.md) before the historical
standing prompt below. Session 16 re-verified why the OWNER-REPORTED 0.2778 champion won
(emission hygiene: `solo-r1` minus the d_cat≤2 px ring; a ring-3 copy would be a >95 %
duplicate and was not built), ran the leakage canary (PASS), the frozen LOSFO gate on
seeds 300–304 (**G2 spread FAIL**: pooled HOLDOUT-DTI Δ +0.00126, 95 % CI
[−0.0034, +0.0063], 9/20 cells), and the uniqueness check (**FAIL**: prediction-surface Spearman(prob_D1, prob_D0)
0.990; 91.3 % of final dots within 3 px of a dense probe raster; 41.3 % vs the scored champion). The S16 run card does not retain a per-registry pre-placement surface-correlation table, so that subcheck is unverified; the final-dot overlap alone exceeds the duplicate-stop limit.
The all-finite variant passes whole-array [0,1] format checks; that is not scientific or
selector approval. It is only a possible file-format remedy for the prior portal range
error, whose actual cause remains unconfirmed. No score here is ORGANIZER-CONFIRMED;
projections are never scores. Negative results are deliverables. Do not copy an old
submission.

## Current-session protocol (read before every run)

- **Objective:** maximize competition performance with auditable science; independently
  verify official facts; clearly distinguish organizer receipts, owner-reported scores,
  local HOLDOUT-DTI, and projections. The user-reported GEMSDOE32 value `0.2778` is not an
  organizer receipt in this checkout. Its byte-level forensic explanation is in
  [`knowledge/50_s16_result.md`](knowledge/50_s16_result.md); do not claim it proves
  organizer score attribution.
- **Lane and budget:** the authorized Session 16 method is the single H40-1 paragraph in
  [`knowledge/49_preregistration_H40-1_migration.md`](knowledge/49_preregistration_H40-1_migration.md).
  It is already executed (3/3 experiments) and failed. Do not switch lanes, rerun those
  seeds, exceed the experiment/time cap, or create another variant under that frozen
  preregistration. A new session needs its own explicit lane and fresh preregistration.
- **Holdout before any future slot:** hide whole fault segments with a buffer; compute
  catalogue-based features only from visible faults; pixel-exactly mask visible faults;
  score pooled DTI with α=0.2, β=0.8, and a 300 m triangular kernel. Test each feature
  alone first; AUC >0.90 is leakage until proven otherwise. Report evaluator version,
  withheld positives and 95% CI. Never call a projection a score.
- **Uniqueness:** compare the pre-placement surface and final dots to every registry
  raster. Spearman correlation >0.90 or >70% of dots within 3 px of any one registry
  raster means duplicate: log it and stop. A format-valid TIFF is not necessarily unique,
  scientifically validated, or approved.
- **Submission artifact:** the current site must say plainly whether any TIFF is safe to
  upload. Current answer: **NO**. Keep historical downloads inspection-only. A future
  artifact must pass no-NaN-inside-footprint, [0,1] values, single-band, exact CRS/shape/
  transform, content hash, registry uniqueness, and holdout superiority gates. Slot
  promotion/selection is separate. Never upload automatically.
- **End-of-run card:** include hypothesis, mechanism, named non-fault mimic, HOLDOUT-DTI +
  CI, registry correlation/overlap, raster SHA-256, exact validator results, unique name,
  note ≤140 characters, and `promote`/`negative` verdict. Failed and blocked runs are
  valid deliverables.

This is the current operational form of the owner's full project brief; the earlier
verbatim task text below remains part of the audit trail. The Session 17 three-pass
submission-safety review is in
[`evidence/review_s17_submission_safety_2026-10-25.md`](evidence/review_s17_submission_safety_2026-10-25.md).
Primary manual-review links:
[official competition](https://www.drivendata.org/competitions/306/competition-doe-gems/),
[official rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf),
[USGS GeoDAWN data](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and),
[DOE GDR submission 1391](https://gdr.openei.org/submissions/1391), and
[DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution).

**Follow-up (parallel merged run):** [registry-coverage gate review and next steps](knowledge/48_gate_review_2026-10-25.md). Note the H40-1 label collision flagged in `registry/irregularities.json` (`s16-h40-id-collision`): main also carries a parallel H40-1 thermal-vent / H41-1 thermal-spring experiment — do not combine its numbers with Session 16 migration numbers.

This is an operational summary of the 2026-10-25 request, **not a verbatim copy** of the full prompt.
Historical verbatim prompts below remain historical. Core values remain Maximize P(Win) and Own
the Outcome: fail closed rather than spending a slot on unverified evidence.

## This session's operative requirements (2026-10-25 — read first every session; the full chat transcript is authoritative, see knowledge/48 §Pass 3)

- **MUST generate a UNIQUE TIF submission.** Do not copy a previous submission unless it is for learning and education. It must be obvious whether it is OK to download and submit the generated TIF.
- **Easy one-click download:** there must be an easy-to-download submission `.tif` as described by the prompt, obvious on arrival at the site (executive summary or the very beginning of the site).
- **Inspection is automated through the project:** no human inspector; every number validated without human intervention before any file is offered for download.
- **Evidence classes:** label every number HOLDOUT-DTI (evaluator version, withheld positives, 95% CI) or ORGANIZER-CONFIRMED (copied from a submission-page receipt). A projection is never written as a score.
- **Leakage canary:** test each feature alone on the holdout; AUC above 0.90 means leakage until proven otherwise.
- **Run card (JSON, end of session):** hypothesis; mechanism; named non-fault mimic; holdout DTI + 95% CI; correlation/overlap vs registry; raster sha256; validator output (no NaN inside the footprint, values in [0,1], CRS/shape/transform match); submission name + note ≤ 140 chars; verdict promote / negative. Negative results are deliverables.
- **Budget:** stop after 3 experiments or 2 hours. Do not pick submissions — promotion to a real slot is a separate selector step within the weekly cap.
- **Hypotheses:** generate 3–5 not-yet-tried candidates (layers, physical signature, why off-catalogue vs USGS/INGENIOUS, difference from repo); rank by expected DTI improvement × cost; validate the top candidate on the spatially-blocked holdout before touching a weekly submission slot.
- **Submission mechanics:** single-band GeoTIFF (or zip of one), matching the submission format's CRS/shape/geotransform, values in [0,1] — this fixes the "<em>Predicted values must be in range [0, 1]</em>" portal error; unique name + short note (≤ 200 chars); executive-summary subpage explaining exactly how to submit.
- **Data:** no DrivenData auth in this environment; inputs restored from hash-pinned public mirrors via `scripts/download_competition_data.sh` (never contacts DrivenData); external data only from free official verified sources.
- **Process:** work line by line, verify from official verified trusted sources with links for manual review, no manual input, flag irregularities in `registry/irregularities.json`, no hallucinations. Run three passes (Pass 1 implement & verify; Pass 2 review & fix; Pass 3 re-check against the request), then open a pull request and merge onto `main`.

---

# GEMSDOE28 — Fault Mapping for the Great Basin (`DrivenData #306`)

## Standing Prompt & Arena AI Core Values (Read First Every Session)

- **Core Value 1 — Maximize P(Win):** Prioritize the highest-leverage geological and mathematical actions that measurably increase expected Distance-Tolerant IoU (DTI) on the hidden test set; never spend a weekly submission slot on an idea that has not beaten the current holdout best on a spatially-blocked holdout set.
- **Core Value 2 — Own the Outcome:** Work autonomously end-to-end with zero manual input required, verify every claim line by line from official verified trusted sources with links for manual review, flag any irregularities in `registry/irregularities.json`, and run three full verification passes (Pass 1, Pass 2, Pass 3) before opening and merging a pull request onto `main`.

### Verbatim Task Prompt (Session 14, 2026-10-03 — read first every session)

> **Read this first, every session.** It is the owner's standing brief, reproduced word-for-word at the
> top of the repository so that every session starts from the same base instead of re-deriving it.
>
> **Euler deconvolution for depth, not just location.** Gradient and tilt-derivative features mark where
> a potential-field anomaly changes, but not how deep the source sits — and depth is exactly what a
> geologist uses to judge whether a lineament is a shallow dike, a buried contact, or a fault plane.
> Euler deconvolution (Reid, Allsop, Granser, Millett, and Somerton, *Geophysics*, 1990) solves Euler's
> homogeneity equation across a moving window of the field and its gradients to jointly estimate a
> source's location and depth, and the original paper validates it on real, structurally complex terrain,
> reporting that it yields "depth-labeled Euler trends which mark magnetic edges, notably faults, with
> good precision." Run it with the structural index appropriate to a fault contact, cluster the resulting
> depth-labeled solutions, and treat a cluster with shallow estimated depth aligned to a candidate
> lineament as corroboration distinct from a gradient peak alone — two unrelated methods agreeing there is
> both an edge and a shallow source at the same place is stronger evidence than either one, and it's a
> concrete detail a Phase 2 reviewer can actually evaluate.
>
> **Why and how did `dotted-h19-5-d2-8` (`GEMSDOE25`) get the highest score, and can we generate a
> submission that scores higher than `0.26`?** Answer with PhD-level experience, knowledge, and
> judgement. The official public leaderboard lists **`0.3195` at #1**, so design a strategy that can
> exceed `0.3195`.
>
> **Generate 3–5 candidate geological hypotheses we have not tried yet**, each naming the specific
> layer(s) involved, the physical signature being targeted, why it should catch a fault *missing* from
> the USGS/INGENIOUS catalogue rather than one already in it, and how it differs from anything already
> implemented in this repo. Rank them by expected DTI improvement and implementation cost. **Validate the
> top candidate on the spatially-blocked holdout set before touching a weekly submission slot** — do not
> spend a submission slot on an idea that has not beaten the current holdout best. If a candidate cannot
> be validated without new external data, name the specific free, official source needed and check that
> it is obtainable before proposing the idea as viable.
>
> **Deep research mandate.** Study, analyse and understand the science of geothermal-vent and fault
> discovery; store everything gathered from official verified sources as a starting point for other
> projects. Be contrarian but grounded; find sources of data and angles others are overlooking.
>
> **Submission mechanics, verbatim from the owner.** "There should be an easy to download submission tif
> file as described by the prompt… The site should be able to generate a TIF file that is required for
> submission. It should be as easy as download to click a File to submit into the competition. This needs
> to be in the executive summary or the very beginning of the site. It should be obvious when you visit
> the site." A past upload returned **"Predicted values must be in range [0, 1]"**; submissions need a
> unique name and a short note (≤ 200 characters). Create an executive-summary subpage that explains
> exactly how to make a submission into the contest. The project must also "solve the problem of having
> to manually check everything ourselves and having an up to date current feed."
>
> **Process (verbatim, unchanged).** Work line by line verifying from official verified trusted sources,
> provide links for manual review; there should be no manual input — work autonomously to complete tasks;
> flag any irregularities for review; no hallucinations; verify no hallucinations. Run three passes
> (Pass 1 implement and verify; Pass 2 review for bugs, missing requirements, wrong assumptions and edge
> cases, and fix; Pass 3 re-check the entire implementation against the original request and improve
> accuracy, reliability, completeness and code quality). Then create a pull request and merge it onto
> `main`, with suggestions for what still needs to be done and any limitations in the way of success.
>
> **Arena AI Core Values (focal points for every decision).** **Maximize P(Win)** — in every decision
> weigh tradeoffs, assess risk, and choose the path that maximises the probability of winning; set aside
> emotions. **Own the Outcome** — own results end to end, not just one slice; when problems arise and we
> have the means to act, act without waiting for permission; treat failure and success as signals.
>
> **Legacy verbatim prompt (Session 9, kept for the audit trail — the scorecard it carries is the
> owner's own list and is reproduced in §2).**
> **Euler deconvolution for depth, not just location.** Gradient and tilt-derivative features mark where a potential-field anomaly changes, but not how deep the source sits. Euler deconvolution (Reid, Allsop, Granser, Millett, and Somerton, *Geophysics*, 1990, DOI `10.1190/1.1442774`) solves Euler's homogeneity equation across a moving window of the field and its gradients to jointly estimate a source's location and depth. Run it with the structural index appropriate to a fault contact, cluster the depth-labeled solutions, and treat a cluster with shallow estimated depth aligned to a candidate lineament as corroboration distinct from a gradient peak alone — two unrelated methods agreeing is stronger evidence than either one.
>
> **Scorecard (owner sites → reported live scores).** GEMSDOE `0.1563` · 6GEMSDOE `0.0286` · GEMSDOE3 nodes `0.1193` / discovery `0.0830` / ridge `0.1152` · GEMSDOE2 `0.1560` · GEMSDOE4 `0.0343` · 5GEMSDOE `0.1563` · 7GEMSDOE `0.1461` · 8GEMSDOE `0.1563` · GEMSDOE9 `0.0107` · 11GEMSDOE `0.0202` · 12GEMSDOE `0.1294` · 15GEMSDOE `0.0782` · 14GEMSDOE `0.0020` · 17GEMSDOE `0.0187` · 18GEMSDOE `0.0297` · 19GEMSDOE `0.1894`/`0.1922` · GEMSDOE10 `0.0461`/`0.0921`/`0.1280`/`0.1839` · 13GEMSDOE `0.0904` · 16GEMSDOE `0.1855`/`0.0976`/`0.0360` · GEMSDOE21 `0.1894` · 20GEMSDOE `0.1890`/`0.1859` · GEMSDOE22 `0.1002`/`0.0748` · GEMSDOE23 `0.1352` · GEMSDOE24 `0.2477` · **GEMSDOE25 `dotted-h19-5-d2-8` = `0.2600` (our best)** · GEMSDOE26 `0.1223` · GEMSDOE27 `0.2449` · 28–33GEMSDOE: no score yet.
>
> **Study the highest score.** Site `https://buffedlizard55-lab.github.io/GEMSDOE25/`, submission `dotted-h19-5-d2-8-20261002-e56ea318af89-nan: 0.2600`. Why and how did it get the highest score, and can we generate a submission scoring higher than `0.26`? Answer with PhD-level experience, knowledge, and judgement. Official public leaderboard: `https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/` — `0.3195` is the current #1, so design a new strategy that can score higher than `0.3195`.
>
> **Generate 3–5 candidate geological hypotheses we haven't tried yet**, each naming: the specific layer(s) involved, the physical signature targeted, why it catches a fault missing from the USGS/INGENIOUS catalogue, and how it differs from anything already implemented here. Rank by expected DTI improvement and implementation cost. **Validate the top candidate on the spatially-blocked holdout set before touching a weekly submission slot** — never spend a slot on an idea that hasn't beaten the current holdout best. If a candidate needs new external data, name the specific free official source and check it's obtainable first.
>
> **Deep research mandate.** Research the science of geothermal-vent/fault discovery heavily; store all knowledge from official verified sources as a starting point for future projects. Be contrarian but grounded; find overlooked data sources and angles. Official anchors: competition `https://www.drivendata.org/competitions/306/competition-doe-gems/` · problem `…/page/967/` · about `…/page/968/` · data tab (login-walled) · reference solution `https://github.com/drivendataorg/gems-prize-reference-solution` · official rules `https://docs.nlr.gov/docs/fy26osti/96647.pdf` · GDR `https://gdr.openei.org/submissions/1391`.
>
> **Submission mechanics.** The site must make it easy to download the submission `.tif` — one-click, in the executive summary / very beginning of the site, obvious on arrival. A past upload failed with `"Predicted values must be in range [0, 1]"` — address it. Give each submission a unique name and a short note (≤ 200 chars) to tell submissions apart. Provide an executive-summary subpage explaining exactly how to submit. Single-band GeoTIFF (or zip of one), matching the submission format's CRS, shape, and geotransform, values in `[0, 1]`.
>
> **Known limitation.** No DrivenData auth → cannot auto-download `training_features.tif`, `labels.tif`, `sample_submission.tif`, `1m_DEM_links.csv` (login-walled). Workaround in use: hash-pinned public owner mirrors restored by `scripts/restore_data.py` (never contacts DrivenData). Find free, public, official, verified sources for any external data.
>
> **Process.** Work line by line verifying from official verified trusted sources with links for manual review; no manual input; flag irregularities in `registry/irregularities.json`; no hallucinations; verify no hallucinations. Run three passes (Pass 1 implement & verify; Pass 2 review for bugs/missing requirements/wrong assumptions/edge cases and fix; Pass 3 re-check against the original request and improve). Then create a pull request and merge it onto `main`, with suggestions for remaining work and limitations.
>
> **Arena AI Core Values (focal points for all building, developing, researching, suggesting, and implementing).**
> - **Maximize P(Win):** in every decision, weigh tradeoffs, assess risk, and choose the path that maximizes the probability of winning; set aside emotions; prioritize the project's success above all else.
> - **Own the Outcome:** own results end to end, not just our slice; when problems arise and we can act, act without waiting for permission; treat failure and success as signals and improve; stay accountable to the final outcome.

---

## AI-use disclosure and claim boundaries

Generative AI (Arena.ai Agent Mode) assisted research synthesis, hypothesis planning, Python implementation, testing, data audits, documentation and this static site. The project owner supplied the standing brief and retains responsibility for independent scientific, code, provenance and submission review. The agent did not access a DrivenData account, login-walled competition data, submit a file, query a private score, or obtain an organizer receipt. Local model/holdout results, owner-reported scores and public leaderboard observations are distinct evidence classes; no repository result is an organizer-verified GEMSDOE28 score. See [`AI_DISCLOSURE.md`](AI_DISCLOSURE.md) and the [official rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf). The disclosure file is a review aid; the required final-round narrative must still state AI use in the organizer's requested format.

---

## Session 15 — High-Score Review, Fresh-Hypothesis Slate & No-Slot Gate (Read Before Work)

Before every substantive session, reread this README and [`knowledge/00_standing_brief.md`](knowledge/00_standing_brief.md). For this research track, also read [`knowledge/47_session15_high-score-review_and_blocked-experiment.md`](knowledge/47_session15_high-score-review_and_blocked-experiment.md) and its structured card [`evidence/session15_review.json`](evidence/session15_review.json). The card is an explicit **negative/blocked result**, not a competition submission.

The user-provided list reports `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` at `0.2778` as the highest score among the listed GEMSDOE24/25/27/28/30/31/32/33/36 sites. The cross-site audit identifies the owner-repository TIFF paths and summarizes the page's H33-2-B2 method as pruning an existing dotted base by excluding predictions close to the catalogue; it also reports that the owner page says no organizer score exists for those artifacts. The raw TIFF bytes, full method code, and submission receipt are not available here, so the user-supplied `0.2778` is not organizer-confirmed and cannot be causally explained. The prompt also gives two current-leaderboard maxima (`0.4413` and `0.3195`), which conflict; the dated 2026-10-03 repository snapshot is not a current refresh. Do not infer a score, artifact identity, or winning mechanism from any of these claims.

**Critical experiment controls:** the current parallel-run prompt references a single method paragraph defining the authorized lane, but no such paragraph is included. Do not guess the lane, run a non-lane experiment, fabricate a TIFF, or place anything in a submission slot. The checkout has no cached input rasters/features/template/labels under `data/`, and `rasterio`/`pytest` are unavailable in the current Python environment. The existing shared `src/gems27/holdout.py` documents random component withholding in quadrants; do not assume it satisfies the newer buffered whole-segment hide-and-recover requirement without auditing/fixing it once in the shared template.

The four unrun research directions and their explicit source/data gates are ranked in the session-15 review. Any eventual candidate must pass one-feature-at-a-time leakage checks (AUC >0.90 is a stop pending proof), buffered whole-segment holdout with alpha 0.2/beta 0.8 and a 300 m triangular kernel, a paired 95% CI, and pre-/post-placement registry correlation/3 px overlap gates. Do not write or present a new submission TIFF until it beats the frozen holdout comparator and passes the exact grid/range/hash/uniqueness validator. A failed or blocked experiment is a valid deliverable.

---

## 1. Archived GeoTIFF research artifacts (`docs/downloads/`) — inspection-only, no current file approved

All submission artifacts in `docs/downloads/` are verified by `scripts/verify_downloads.py` (**`247/247` checks PASS, `0` failures**, `evidence/submission_file_audit.json`; the count grew from `208` because Session 14 added the `H38-1` multi-physics corroborated package at `secondary` while retaining `H37-1` under `h37_1_falsified`): single-band `float32`, exact template grid (`EPSG:32611`, `3730 × 3292`, `100 m` pixels, `5,167,373` inside-footprint cells), values strictly in `{0.0, 1.0} ⊂ [0, 1]` inside the footprint, zero internal `NaN`s, `NaN` outside the footprint (`-nan.tif`, with an `-allfinite.tif` fallback having `0.0` outside and no `NaN` anywhere), zero overlap with the `60,988` known catalogue pixels, content-addressed 12-hex ID, single-member `.zip`, and a registered note $\le 200$ characters.

| Slot | Filename (`docs/downloads/`) | Content ID | Emitted px | 4-Fold Spatial-CV & LOSFO Far-Field Holdout | Hybrid Model vs `0.2600` Anchor | Registered Note ($\le 200$ chars) |
|---|---|---|---:|---|---:|---|
| **Primary (One-Click) — Verified on Interleaved AND LOSFO Far-Field** | `gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif` | `b531dae0a36f` | `37,660` | **`+0.002599` interleaved (`10/10` seeds `240–249`, replicated `+0.002675` on `250–259` and `+0.002804` on `270–279`) AND `+0.001713` LOSFO far-field (`16/20` cells, `5/5` seeds `265–269`, `F1–F4` ALL PASS, $e_{\text{far}} = 0.01359 < \tau_{\text{live}} = 0.05485$)** | `0.2717–0.2727` (live-anchored dose ladder) | `28GEMSDOE H36-1 rung3.0+r1 \| …` |
| **Secondary — H38-1 Multi-Physics Corroboration (`C1–C4` ALL PASS)** | `gems28-h38-1-hf-euler-r30-r1-20261003-56a9f473edc7-nan.tif` | `56a9f473edc7` | `37,860` | **`0.07724` LOSFO credit/dot (`+0.000792`, `17/20` cells, `4/5` seeds) on `d=2.8`; `0.06993` credit/dot (`+0.000747` over `H36-1`, `+0.002460` over `d=2.8`, `16/20` cells, `4/5` seeds) on `H36-1`; `+0.000543` interleaved over `H36-1` (`27/40` cells, `8/10` seeds `270–279`)** | `0.2722–0.2735` (adds `200` corroborated dots onto `H36-1`) | `28GEMSDOE H38-1 hf+euler+r30r1 \| … \| id 56a9f473edc7` |
| **Tertiary** | `gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif` | `8acb75e1f2cc` | `40,199` | +0.001766 (`10/10` seeds, `4/4` folds) — replicated `+0.001761` on fresh seeds 235–239 (`5/5` seeds, `4/4` folds) AND `+0.002249` LOSFO far-field (`20/20` cells, exact `0.00` TP lost) | `0.2686` | `28GEMSDOE H27-4 d2.8 solo \| ΔDTI +0.00177 (10/10 seeds 180-189) replicated +0.00176 on fresh 235-239 (5/5 seeds, 4/4 folds) \| 0.2600 d2.8 base, no T-v2 \| id 8acb75e1f2cc` |
| **Quaternary** | `gems28-h32-1-prethin-tip-euler-d2-8-20261003-31e35eee884e-nan.tif` | `31e35eee884e` | `42,294` | +0.001399 (`10/10` seeds, `4/4` folds) | `0.2669` | `28GEMSDOE H32-1 d2.8 pre \| OOF ΔDTI +0.00140 (10/10 seeds, 4/4 folds, seeds 180-189) pre-thinning d2.8; no T-v2 \| id 31e35eee884e \| UNSCORED, not slot-approved` |
| **Conservative alternative (kept audited)** | `gems28-h32-1-tip-euler-dejitter-d2-8-20261003-c3aeda1d31a3-nan.tif` | `c3aeda1d31a3` | `41,656` | +0.001272 (`10/10` seeds, `4/4` folds) — conservative alternative: protects fault tips and shallow Euler depth clusters | `0.2663` | `28GEMSDOE H32-1 d2.8 post \| OOF ΔDTI +0.00127 (10/10 seeds, 4/4 folds, seeds 180-189) on 0.2600 d2.8 base; no T-v2 \| id c3aeda1d31a3 \| UNSCORED, not slot-approved` |
| **Falsified packing comparator (kept audited)** | `gems28-h37-1-coverprob-h19-5-r1-20261003-0bbddf41eb6d-nan.tif` | `0bbddf41eb6d` | `37,447` | `+0.007289` interleaved (`10/10` seeds, `4/4` folds) but `−0.000037 ± 0.000832` far field (LOSFO seeds `210–214`, `9/20` cells) — demoted per pre-committed rule | withdrawn (was `0.278–0.286`) | `28GEMSDOE H37-1 cover+h19 \| … \| UNSCORED, not slot-approved` |
| **Reference** | `gems27-h27-4-r1-pruned-d1-5-20261003-450eb6859636-nan.tif` | `450eb6859636` | `54,714` | `+0.0022` on `d=1.5` (seeds `130–139`, `4/4` folds) | `0.2598` (on `0.2477` `d=1.5`) | `28GEMSDOE H27-4 r1 reference \| OOF DTI gain +0.0022 solo (4/4 folds); UNSCORED, unconfirmed \| id 450eb6859636 \| research only` |

**Primary submission name:** `GEMSDOE28-h36-1-rung30-blind-r1-b531dae0a36f`

**Exact registered note (`192/200` characters):** `28GEMSDOE H36-1 rung3.0+r1 | OOF dDTI +0.00260, 10/10 seeds, 4/4 folds (seeds 240-249); re-pack beats matched-N random drop by +0.00261; no T-v2 | id b531dae0a36f | UNSCORED, not slot-approved`

**One-click routes that do not depend on GitHub Pages.** The primary (`H36-1`, `37,660` px) and secondary (`H38-1`, `37,860` px) files are reachable directly from the repository:

```
# Primary (H36-1, 37,660 px, SHA-256 5556aa1438fd67376b60d5ffc99228ec09dcc11a8408298a743ccb88d6163641)
https://github.com/buffedlizard55-lab/GEMSDOE28/raw/main/docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif

# Secondary (H38-1, 37,860 px, SHA-256 81d5b87bc8424f162a8f56aa9aac8fbe630c61646b9cac24d5ebbdc1b1951783)
https://github.com/buffedlizard55-lab/GEMSDOE28/raw/main/docs/downloads/gems28-h38-1-hf-euler-r30-r1-20261003-56a9f473edc7-nan.tif
```

### Session 15 (2026-10-25) — 🔴 NEWEST CANDIDATE: DO NOT SUBMIT (auto-validated, no human inspection)

**The newest generated TIF must NOT be submitted.** `gems28-h39-1-depthslice-persist-b2-20261025-a86b8ed33727-nan.tif` (37,695 px, SHA-256 `a33fe4c2cd4cfe9b8ea684f3855333eb72ebda784813aade1bfa337cc7f78168`) is format-perfect (all validator hard checks PASS: no NaN inside the footprint, values exactly `{0,1} ⊂ [0,1]`, `EPSG:32611` / `3730×3292` / template transform, 0 dots on the catalogue; all-finite zeros variant included for strict range validators) **but it FAILED its frozen science gates**, so downloading it for the portal would spend a weekly slot on a rejected idea. Unique submission name (for the record only): `GEMSDOE28-h39-1-depthslice-persist-b2-a86b8ed33727`. Exact note (102/140 chars): `28GEMSDOE H39-1 depthslice B2 | LOSFO GATE FAIL dDTI -0.0016 (290-294) DO NOT SUBMIT | id a86b8ed33727`. Inspection download (same warning applies): `docs/downloads/gems28-h39-1-depthslice-persist-b2-20261025-a86b8ed33727-nan.tif` (+ `-allfinite.tif`, `-nan.zip`). Run card: `evidence/s15_run_card.json`; preregistration `knowledge/47…` (frozen at `dae869b` before the seeds); result `knowledge/48_s15_result.md`. The one-click primary above (H36-1) is **unchanged**; promotion to a real slot remains a separate selector step and no slot was spent.

- **Gate (HOLDOUT-DTI, LOSFO seeds 290–294, 20 paired cells, 74,557 withheld truth px):** D1 (32 frozen bands + 5 depth-slice bands, persistence-weighted) pooled ΔDTI **−0.00160** vs D0, mean paired −0.00260, 95% CI [−0.00739, +0.00208], 9/20 cells → frozen gate **FAIL** (G1/G2/G3 fail; integrity + leakage canary pass, single-feature AUCs 0.476–0.543).
- **Uniqueness:** only 37.2% of its dots lie within 3 px of the 0.2778 champion (genuinely re-derived), but 76.8%/79.9% lie within 3 px of two dense unscored detector-ridge probes in `docs/downloads`, and Spearman(prob_D1, prob_D0) = 0.977 → **FAIL** under the strict any-registry-raster rule (logged, `s15-uniqueness-dense-probes`).
- **Why the 0.2778 champion won (byte-verified, `knowledge/47` §1):** it is exactly the owner-reported 0.2708 solo file minus every dot within 200 m of the catalogue (0 px symmetric difference). Rings 1–2 yielded a near-constant ≈2.76×10⁻⁶ owner-reported DTI per deleted dot — pure false-positive-mass removal, not new detection. The obvious ring-3 continuation is a subset of the champion, hence a duplicate lane, and was not shipped.
- **Can we beat 0.2778?** Not with this lane, and no file in this repository is validated above the champion. Beating it needs new dots earning > τ ≈ 0.059 credit/dot on genuinely unmapped structure; every live owner-reported addition test in the group so far (T-v2 −0.0028; GEMSDOE36 conduits −0.0028) and now H39-1's far-field holdout say current novel-dot sources do not clear that bar. Next ranked lanes (fresh preregistration + seeds 295+): H39-2 radiometric alteration lineaments, H39-3 drainage-chain collinearity, H39-4 artifact-swap (`knowledge/47` §2, `knowledge/48` §4). All live scores quoted are **OWNER-REPORTED**; no organizer receipt exists in any fetched repository, so none is ORGANIZER-CONFIRMED.

---

## 2. PhD-Level Analysis of the `0.2600`, `0.2449`, and `0.1223` Live Scores

We restored the inversion scripts (`scripts/fetch_scored_corpus.py`, `scripts/invert_live_scores.py`, `scripts/optimize_budget.py`) and performed a local inversion over **24 hash-matched raster/score records** (`evidence/scored_corpus.json`, `evidence/live_inversion.json`, `evidence/budget_optimum.json`, plus `evidence/why_026_won.json`) at the blind-lattice-calibrated truth-size estimate $|G| = 12{,}226\text{ px}$. The SHA-256 checks authenticate the recovered local raster bytes against repository records; they do **not** authenticate a DrivenData receipt or prove which portal upload received a score. The `0.2600` GEMSDOE25 score is owner-reported, and this inversion is conditional on the recorded score-to-file pairing and estimated $|G|$; no organizer-verified result for GEMSDOE28 exists.

A separate one-off manual read of the official public leaderboard, recorded in `registry/leaderboard_snapshot_2026-10-03.json`, observed `DARD` at #1 with `0.3195` and a `wbg1` row at #15 with `0.2600`. That page observation does not identify the owner, establish that the `wbg1` row is the repository's `GEMSDOE25` submission, or prove a private score. No organizer receipt or score-to-file confirmation is stored.

$$\text{DTI} = \frac{\text{TP}_w}{0.2\,\text{TP}_w(1 - \rho) + 0.2\,N + 0.8\,|G|}, \qquad \rho = \frac{\text{MP}_w}{\text{TP}_w}$$

| Submission | Repo | Content ID | Off-catalogue `N` (px) | Recorded score (owner-reported corpus) | Crowding `ρ` | Implied `credit_TPw` (px) | Credit / `|G|` |
|---|---|---|---:|---:|---:|---:|---:|
| **`dotted-h19-5-d2-8`** | `GEMSDOE25` | `e56ea318af89` | `44,090` | **`0.2600`** | `1.179` | `4,791.05` | `0.3919` |
| **`dotted-h19-5-d1-5`** | `GEMSDOE24` | `989f59505db1` | `60,069` | **`0.2477`** | `1.429` | `5,286.13` | `0.4324` |
| **`topo-gap-closure-t-v2-on-d1-5`** | `GEMSDOE27` | `5512495c6bd1` | `61,328` | **`0.2449`** | `1.425` | `5,288.78` | `0.4326` |
| **`H20-5` (blend parent)** | `GEMSDOE20` | `85ef8fb66294` | `102,434` | **`0.2072`** | `2.186` | `6,030.72` | `0.4933` |
| **`h19-5` (solid ridge parent)** | `GEMSDOE19` | `c85ac61b088b` | `121,131` | **`0.1922`** | `2.460` | `6,188.80` | `0.5062` |
| **`dilcond-oof-v1`** | `GEMSDOE26` | `47629f496133` | `58,670` | **`0.1223`** | `1.132` | `2,606.25` | `0.2132` |

### 2.1 Local explanation of the reported `0.2600` (conditional inversion)
1. **Exact construction**: `dotted-h19-5-d2-8` (`data/dotted_h19_5_d2_8_nan.tif`, SHA-256 `91eae1ca42ec845eaa8c2ba32da49806e24751743459b8a10017c479bbe639b8`) takes the 1-px ridge skeleton of the 6-expert scarp/geophysics blend `H19-5` (`121,131` off-catalogue pixels, live `0.1922`), zeroes the `60,988` known catalogue pixels, and applies priority-ordered Poisson-disk thinning (`dot_thin(min_dist=2.8)`), emitting **`44,090` binary pixels** (`0.8532%` of footprint) with minimum Euclidean spacing $\ge \sqrt{8} \approx 2.828\text{ px}$ ($283\text{ m}$).
2. **What the conditional inversion says about the reported `d=2.8` vs `d=1.5` pairing (`0.2477` $\to$ `0.2600`) and the 2D geometric model (`0.2550` $\to$ `0.2600`)**:
   - Under the official linear distance-decay kernel $k(d) = \max(0, 1 - d/300\text{ m})$, two dots spaced at $s \in [2.828, 3.0]\text{ px}$ along a 1D fault trace have their midpoint at $d = s/2 \in [1.414, 1.50]\text{ px}$, where every intermediate truth pixel still receives $k(d) \in [0.50, 0.529]$ credit via the $\max_{x \in S} k(\|g - x\|)$ operator.
   - Meanwhile, the false-positive denominator penalty $0.2\,\text{FP}_w$ is **additive** over all emitted pixels: thinning from `60,069` px (`d=1.5`) to `44,090` px (`d=2.8`) removes `15,979` redundant dots (`-26.60%` budget), cutting $0.2\,\Delta N = 3{,}195.8$ denominator units and reducing kernel crowding $\rho$ from `1.429` to `1.179`.
   - Crucially, the 2D isotropic uniform-truth retention formula (`evidence/budget_optimum.json`) predicted $c(d=2.8)/c(d=1.5) = 0.8896$ (`0.2550`), whereas the **measured live credit retention is $4{,}791.05 / 5{,}286.13 = 0.9063$ (`+1.88%` higher than 2D isotropic retention)**! Because hidden truth $G$ is a **1D curvilinear fault network colinear with the `H19-5` ridge crest**, 1D crest thinning at $d=2.8\text{ px}$ loses much less credit than 2D area-coverage geometry predicts.

### 2.2 Why `topo-gap-closure-t-v2-on-d1-5` (`5512495c6bd1`) scored `0.2449` (`-0.0028` vs `0.2477`)
- `5512495c6bd1` added `1,259` non-redundant straight-line `T-v2` gap-closure dots across `345` links (`1–4 km` gaps between published Qfaults tips) onto `d=1.5` (`60,069` $\to$ `61,328` px).
- Inverting `0.2449` vs `0.2477` reveals that `credit_TPw` rose by only **`+2.65 px`** (`5,286.13` $\to$ `5,288.78` px), an empirical marginal efficiency of **`0.00210` credit/dot — `23.5x` below the `0.0495` live break-even threshold**!
- **Why catalogue holdouts overstated `T-v2` by `100x`**: Hiding pieces of already-compiled NBMG polylines artificially severs continuous mapped traces (`230/345` `T-v2` links were same-FID sub-parts) and rewards straight-line interpolation across those artificial cuts. In reality, the hidden organizer test set $G$ consists of **newly mapped faults omitted from the compilation**, not un-digitised straight lines between existing Qfaults tips. Every previously built candidate in `GEMSDOE27`/`GEMSDOE28` that bundled `T-v2` (`1113fba5f6cb`, `23ad46a4d7ba`, `3ebd51534bb1`, `d466b251f309`) was paying `-0.0028` to `-0.0033` of pure false-positive drag.

### 2.3 Can we generate a submission that scores higher than `0.2600`?
- **Yes — to `~0.2665–0.2701` directly on the `0.2600` (`d=2.8`) base by removing `100 m` catalogue-flank digitisation shadow (`c3aeda1d31a3`, `31e35eee884e`, `8acb75e1f2cc`) without `T-v2` drag**:
  - In `dotted-h19-5-d2-8` (`44,090` px, `0.2600`), **`3,891` dots (`8.83%` of all emitted pixels)** sit at $d_{\text{cat}} = 1.0\text{ px}$ ($100\text{ m}$) immediately adjacent to masked known catalogue faults (`2,434` along interior segments with $d_{\text{end}} > 300\text{ m}$, $\text{cat\_nbrs} \ge 2$, $d_{\text{Euler}} > 300\text{ m}$; and `1,457` within $300\text{ m}$ of a catalogue tip or shallow Euler $N=0$ depth cluster).
  - Because `labels.tif` masks only the 1-px rasterised USGS trace while the true 1 m LiDAR scarp expression is offset by `100–400 m` (Hermant et al., 2025, Fig. 2 & Fig. 9B), `H19-5` fires heavily on the $100\text{ m}$ flank of known faults — pixels that are almost pure false-positive mass (`0.0040` credit/FP on mid-segment flank shadow vs `0.0549` break-even at `0.2600`).
  - Removing those `2,434` mid-segment flank-shadow pixels on `d=2.8` (`c3aeda1d31a3`, `41,656` px) passes all 4-fold spatially-blocked holdout gates (`+0.001272` mean ΔDTI, `10/10` seeds, `4/4` folds on seeds `180–189`) and projects to **`0.2665`** (`+0.0065` over `0.2600`), while pre-thinning de-jittering (`31e35eee884e`, `42,294` px, `+0.001399` mean ΔDTI) projects to **`0.2685`** and solo `H27-4` `r=1` on `d=2.8` (`8acb75e1f2cc`, `40,199` px, `+0.001766` mean ΔDTI) projects to **`0.2701`**.

---

## 3. Session 10 — The Reachability Frontier and a Far-Field Harness

Two new results, both reproducible from a committed script and an evidence file named in the same
sentence. Full write-up: `knowledge/20_strategy_after_reachability_frontier.md`.

### 3.1 What beating `0.3195` costs, in pixels of credit

`scripts/reachability_frontier.py` → `evidence/reachability_frontier.json`. The closed form
$\text{DTI} = \text{TP}_w / (0.2\,\text{TP}_w(1-\rho) + 0.2N + 0.8|G|)$ is **checked numerically against
`metric.dti_binary` on 23 synthetic grids before use** — max absolute residual `2.22e-16`, and the
substitution $\text{FP}_w = N - \text{MP}_w$ holds in every case.

| Emitted px $N$ | credit for `0.2600` | credit for `0.2701` | credit for **`0.3195`** |
|---:|---:|---:|---:|
| 40,199 (tertiary) | 4,633 | 4,813 | 5,694 |
| **44,090 (the `0.2600` file)** | 4,836 | 5,024 | **5,942** |
| 60,069 (the `0.2477` file) | 5,667 | 5,887 | 6,963 |

The best owner-anchored submission earns **4,791 px of credit (`39.2%` of $|G| = 12{,}226$ px)** at
$N = 44{,}090$.

> **The gap to `0.3195` at that budget is `+1,151` px of credit — `24.0%` more credit than the entire
> `0.2600` submission captures, `9.42` points of $|G|$.**

**Why budget reallocation cannot close it.** Holding credit/dot at the current *average* efficiency
(`0.1087`), DTI tends to `0.5433` as $N \to \infty$ and `0.3195` would arrive at $N \approx 69{,}800$ —
but the *marginal* efficiency governs whether the next dot helps, and the programme has one
exactly-controlled live measurement of it: thinning the same ridge from `d=1.5` (`60,069` px,
`0.2477`) to `d=2.8` (`44,090` px, `0.2600`) removed **`15,979` dots and lost `495.08` px of credit**,
i.e. **`0.03098` credit/px**, below the break-even `0.05485` at `0.2600`. A dot earning that little
never clears the `0.2·target` charge, so **no quantity of dots at the current marginal efficiency
reaches `0.3195`.** The actionable form:

| marginal credit per new dot $e$ | new dots needed for `0.3195` |
|---:|---:|
| `0.20` | `8,459` |
| `0.30` | `4,876` |
| **`0.40`** | **`3,425`** |
| `0.50` | `2,640` |

**Conclusion: the gap is a detection gap, not a budget gap.** ~`2,600–3,400` dots that land on
genuinely unmapped fault traces would reach `0.3195`. Every arm this repository has run — including
`H33-1` as preregistered — is a *pruning* arm worth `~0.001–0.010`. Those are still worth taking
(free, and they compose), but they are not the path.

### 3.2 A far-field holdout that can finally gate *addition* arms

`evidence/arm_habitat_decomposition.json` (Session 4) showed the standing holdout hides catalogue
components **interleaved** with the known catalogue, so **`100%` of its hidden truth lies at distance
`0` from the published catalogue** (habitat-A truth `= 0` of `120,983` px). Since
`scripts/verify_downloads.py` requires zero pixels on catalogue cells, that protocol contains no
truth in the only habitat a submission can occupy — **it cannot validate any arm that proposes dots
where nothing is catalogued**, which §3.1 says is the only class that can reach `0.3195`.

Session 10 added `src/gems27/losfo.py` + `scripts/run_losfo_harness.py` →
`evidence/losfo_farfield_diagnostic.json` (5 seeds × 4 folds, 20 paired cells, 757 s):

- `60,988` catalogue px grouped into **`758` fault systems** (8-connected components of the catalogue
  dilated `300 m`, so en-echelon segments of one structure are held out together);
- **`190` systems / `13,156` px** held out per seed, quadrant-blocked;
- a **`600 m` buffer around every held-out system erased from the training labels**, so truth is
  **`>= 800 m`** from every pixel the detector saw as positive (median `3.4 km`), and `90.0%` of
  emitted dots are `>= 300 m` from any known pixel.

| Arm | Mean DTI | Credit TPw | recall_w | Credit/dot |
|---|---:|---:|---:|---:|
| `losfo` (600 m buffer erased) | `0.09974` | `11,160.6` | `0.1439` | `0.0465` |
| `leaky` (unmasked control, same truth) | `0.10155` | `11,291.3` | `0.1456` | `0.0462` |

Pooled ratio `losfo/leaky` = **`0.9884`** (credit). **Read with its uncertainty:** per-fold credit
ratios are NW `0.892`, NE `0.876`, SW `1.204`, SE `0.988` — a spread of roughly `-12%` to `+20%` — so
with 5 seeds this harness **cannot resolve effects smaller than about `±12%` per fold**. The honest
statement is *"no large catalogue-interpolation inflation was detected"*, not *"the inflation is
1.2%"*. Two confounds are recorded rather than smoothed over: the masked arm also has `21.6%` fewer
positive training pixels (`47,832` vs `60,988`), and held-out systems are still *mapped* faults, so
this measures an **upper bound** on performance against genuinely unmapped faults.

What is solidly gained: **a far-field truth set on which addition arms can be gated**, with a
measured base operating point (recall_w `0.1439`, credit/dot `0.0465`) to beat.
`tests/test_losfo.py` guards the no-leakage invariant, including a
`scipy.ndimage.binary_dilation(iterations=0)` trap that returns an **all-True** array and would have
silently merged all `758` systems into one.

### 3.3 Re-ranked H33 series (supersedes `knowledge/18`)

The ranking rule changed: **an arm that can only prune cannot reach the target, so addition arms rank
above pruning arms regardless of individual expected ΔDTI.**

| Rank | ID | Class | Ceiling | Data gate (2026-10-03) |
|---:|---|---|---|---|
| 1 | **H33-3** heat-flow residual × 2 m probe conjunction | **ADD** | can add credit | OPEN — `sb_heat_flow_zip` `130,154,244` B `e7fd62c6…` |
| 2 | **H33-4** drainage-network neotectonics from 1 m DEMs | **ADD** | can add credit | free official source; scope tile volume first |
| 3 | **H33-5** Phase-2 discovery budget | **ADD** (bounded) | Phase-2 optionality | none external |
| 4 | **H33-1** kinematic reactivation favourability gate | PRUNE | `+0.0005…+0.0030` | preregistered `knowledge/19`; bridge landed, **data not yet held locally** |
| 5 | **H33-2** multi-depth MT conductance alignment | PRUNE/score | `+0.0000…+0.0022` | both probed GeoTIFFs pin-verified |

### 3.4 The H33-1 data bridge (blocker removed this session)

The availability probe streams and discards bytes, so *"data gate OPEN"* never meant *"data
available"*. `scripts/fetch_external_layers.py --derived all` now keeps one pinned release,
re-verifies its SHA-256 against `registry/external_pins.json` (the four runner-recorded hashes),
opens the vector layer(s) inside, clips them to the competition footprint
(`src/gems27/external_clip.py`) and writes `docs/data/sb_slip_tendency_in_footprint.{csv,json}`.
The whole path — stream → hash → pin compare → archive → clip → write, plus pin-mismatch,
no-vector-layer and no-pin failure modes — is covered by `tests/test_external_bridge_derived.py`
(exercised on a `file://` pin because `sciencebase.gov` is unreachable from the sandbox) and
`tests/test_external_clip.py`. `knowledge/19_preregistration_H33-1.md` freezes a hard
precondition: **no seed is spent on H33-1 until that derived file exists and its schema lists
slip/dilation-tendency fields.**

**It landed, after three defects that each hid behind a green job.** Merging to `main` triggered the
runner three times. Each failure was a real bug, and two of them would have committed an unusable
table while reporting success:

| Run | Outcome | Root cause |
|---|---|---|
| `37145601551` | HTTP 200, `35,912,323` B, **`pin_match: true`** — but **`n_records: 0`** and job exit 0 | ScienceBase URLs carry no file suffix (`…?f=__disk__33%2Fb0%2F91%2F…`), so `fetch()` named the payload `.bin` and GDAL refused to open a zip wearing that extension. The per-layer error *was* recorded as `LAYER_UNREADABLE`, but the aggregate row still said `DERIVED_WRITTEN`. |
| `37145919044` | Failed loudly (**correct**) | `ImportError: geopandas is required to use pyogrio.read_dataframe()` — the workflow installed `pyogrio shapely pyproj pandas` but not `geopandas`. It ran locally only because `geopandas` was present in the sandbox; **the sandbox masked a runner-environment gap.** |
| `37146168753` | **`DERIVED_WRITTEN`, 84,484 records** | — |

Fixes now in place: `resolve_payload_format()` decides the archive type from **magic bytes first**
(`PK\x03\x04` → zip) and copies to a correctly-suffixed name *without mutating the hashed original*;
`build_sciencebase_derived` reports `LAYER_UNREADABLE` / `DERIVED_EMPTY` / `NO_VECTOR_LAYER` /
`ARCHIVE_UNREADABLE` as distinct non-success statuses; the workflow **fails the job** on any of them
plus `PIN_MISMATCH`, and asserts all five readers import *before* any fetch.

### 3.5 H33-1 was run on its reserved seeds — and refuted, `0` of `6` criteria

With the data in hand, H33-1 was executed before any new arm was designed, because it was the only
preregistered hypothesis that was actually runnable. Full record:
`knowledge/21_result_H33-1_refuted_2026-10-03.md`, `evidence/h33_1_holdout.json`.

The precondition was verified **from the bytes** first: **84,484 fault segments** (17,369 km of
trace, median segment 189 m) clipped from Siler (2022), DOI `10.5066/P9YL58W6`, carrying `TS`, `TD`,
`TS_norm`, `TD_TS`, `ShearStres`, `NormalStre` and stress-orientation fields, reprojected from NAD83
Albers Equal Area Conic to EPSG:32611. This **confirms from the data** the reading that
`knowledge/19` had to treat as unconfirmed (the sandbox cannot reach `api.datacite.org`). The source
`Strike` attribute was verified to be a geographic azimuth — median absolute difference `4.27°`
against the geometric azimuth of the clipped vertices on 4,000 segments.

| Variant | mean DTI | ΔDTI | seeds won | folds | Δdots/seed | credit per removed FP |
|---|---:|---:|---:|---:|---:|---:|
| `base_oof_d28` | 0.094633 | — | — | — | — | — |
| **`h33_1_prune_p10`** (primary) | 0.091618 | **−0.003014** | **0/10** | **0/4** | −582.4 | **0.12855** |
| `h33_1_prune_p05` (dose) | 0.093018 | −0.001615 | 0/10 | 0/4 | −290.0 | 0.14020 |
| `control_top_p10` (direction) | 0.092426 | −0.002207 | 0/10 | 0/4 | −582.4 | 0.10104 |

**All six frozen criteria failed** (`gate_passed: false`): ΔDTI `−0.003014` vs `+0.0010`; folds `0`
vs `3`; seeds `0` vs `8`; removed credit/FP `0.12855` vs break-even `0.019292`; direction control
`0.10104` — *better* than the primary, so the sign is inverted; `fav` coverage **`11.95%`** vs the
`60%` precondition.

Three things this teaches, in `knowledge/21` §2:

1. **A hard coverage ceiling of ~12%.** Only `11.95%` of emitted dots (worst fold `9.61%`) had a
   catalogued segment within 1 km whose strike agreed within 20°. The other 88% are neutral by
   construction. The cause is structural, not tunable: **candidate dots are emitted off-catalogue by
   design.** Any arm that transfers an attribute *from* mapped faults *to* off-catalogue candidates
   inherits that ceiling. This closes a *class*, not a parameterisation.
2. **The sign of the physics is inverted.** Dots the score called unfavourably oriented carried
   *more* credit (`0.12855`) than the ones it called favourable (`0.10104`).
3. **Pruning is exhausted as a family.** All three arms removed pixels at `0.101–0.140` credit per
   FP against a break-even of `0.019292` — the discarded pixels were worth **5–7× break-even**.
   With H31-1 and H32-2, that is three independent pruning arms failing the same way, reaching the
   §3.1 frontier conclusion from a completely different direction.

Per the preregistration: recorded, not retuned, not re-run on a fresh decade, no candidate TIFF,
**no slot spent**. Seeds `200–209` are spent; the next arm takes `220–229`. **Seed disclosure:**
seed `200` was invoked four times while fixing four implementation defects (metre/pixel unit
confusion in the borrow radius, `np.column_stack(np.flatnonzero(...))` returning shape `(1, 2)`, a
per-dot vector reshaped as a grid, float indices used to subscript an array). The harness is
deterministic and no frozen constant was ever changed, so those invocations returned the recorded
numbers; disclosed in `knowledge/21` §3 and `registry/irregularities.json`.

---

### 3.5 H34 — the packing ladder, and a threshold every arm was judged against

`scripts/analyze_operating_point_h34.py` → `evidence/h34_operating_point.json`;
`scripts/run_h34_holdout.py` → `evidence/h34_holdout.json` (seeds `220–229`, 40 cells).
Preregistration `knowledge/21_preregistration_H34.md`, result `knowledge/22_h34_result.md`.

**The ladder is finite.** `thinning.dot_thin` keeps a pixel iff no already-kept pixel is strictly
closer than `min_dist`, so its output changes only when `min_dist` crosses a distance two integer
cells can actually realise ($\sqrt{a^2+b^2}$). There is no continuum to search — only 29 rungs below
8 px. The current file sits at rung `2.828` ($N = 44{,}090$).

**The gate FAILED and the arm is closed.** Preregistered on four criteria; three passed, one did not:

| # | Criterion | Observed | Verdict |
|---|---|---:|---|
| 1 | `e(2.828→3.000) < tau_live` | **0.01914** (10/10 seeds, 4/4 folds) | PASS |
| 2 | direction control: `e(3.000→3.162) > tau_live` | **0.02814** | **FAIL** |
| 3 | seed/fold consistency | 10/10 and 4/4 | PASS |
| 4 | monotone emission, probabilities in `[0,1]`, grid pinned | 40/40 | PASS |

Criterion 2 says the proxy cannot locate a *stopping* rung — it rates both steps profitable, and it
would keep thinning forever. **Cause quantified:** removal efficiency scales with credit per dot, and
the proxy earns `0.0393` credit/dot against the surface's `0.1087` (`2.77×`), which flattens its
efficiency ladder by `1.4×`–`2.3×`. Per the preregistration: no confirmation run, no retuning on
`220–229`, **no candidate TIFF, no weekly slot, and rung 3.0 is not promoted.** The primary download
is unchanged.

**What did survive is bigger than the arm: the threshold was wrong.** Differentiating the metric, a
pixel class with removal efficiency $e = |d\text{TP}_w/d\text{FP}_w|$ is worth dropping iff
$e < \tau = 0.2\,\text{DTI}/(1-0.2\,\text{DTI})$, which **rises with DTI**. The catalogue-holdout
proxy scores `0.095` → $\tau = 0.0193$. The `0.2600` submission those harnesses inform scores `0.26`
→ $\tau = 0.0548$, i.e. **2.85× more permissive**. Every pruning arm in this repository has been
gated against the proxy's threshold, so **any arm whose efficiency lies in `(0.019, 0.055)` was
rejected by a threshold that does not apply to it.**

The rule itself is now confirmed empirically to ~1 %: on 40 independent holdout cells the proxy's
ΔDTI crosses zero at measured $e = 0.01914$ against a predicted $\tau_{\text{proxy}} = 0.019265$
(ΔDTI `−0.000031`), and the next step at $e = 0.0281 > \tau$ gives ΔDTI `−0.00227` — right sign, right
magnitude, on data the framework never saw.

**A modelling error found and fixed while building the test for this.** `src/gems27/operating_point.py`
closed the metric as $\text{FP} = N - A$, charging every emitted pixel full false-positive mass and
ignoring the crowding excess $\tilde{A} - A$ — which the inversion measures as `0.18×`, `0.43×` and
`1.46×` of $A$ on the three anchors, so no fitting can absorb it. Corrected to
$\text{FP} = (1-\gamma)N$ with $\gamma = \tilde{A}/N$ **measured** on the anchors as
`0.12569 / 0.12576 / 0.12811` — constant to `1.9 %`, exactly what non-selective thinning predicts (and
what H32-1's own evidence showed: `11.6 %` on-catalogue before thinning, `11.7 %` after). A second
error: the retention curve is measured on a network with `1:1` dot-to-truth density while the H19-5
surface runs `~10:1`, so a single fitted **density scale** $s$ rescales the loss. With $L$, $|G|$ and
$\gamma$ all measured, the model has **one** free parameter and reproduces three hash-authenticated
live scores to $\le 1.08\times10^{-3}$:

| anchor | $N$ | live score | model | residual |
|---|---:|---:|---:|---:|
| h19-5 solid | 121,131 | 0.1922 | 0.192201 | `+7.6e-07` |
| dotted-h19-5-d1-5 | 60,069 | 0.2477 | 0.246618 | `−1.08e-03` |
| dotted-h19-5-d2-8 | 44,090 | 0.2600 | 0.260627 | `+6.3e-04` |

The old two-parameter fit is **rejected**: it fits to `3.2e-04` but recovers $|G| = 9{,}698$,
**20.7 % below** the blind lattice, because two free parameters cannot separate the crowding term from
the density mismatch. The corrected model agrees that rung 3.0 is optimal (`+0.00303`, stable for
$s \in [0.79, 0.87]$) and *does* satisfy the direction control ($e(3.0\!\to\!3.162) = 0.0659 > \tau =
0.0556$) — but a model projection is not a validated result, so the arm stays closed.

> **Consistency note.** The corrected closure is algebraically identical to the one
> §3.1's reachability frontier already used, $\text{DTI}=\text{TP}_w/(0.2\,\text{TP}_w(1-\rho)+0.2N+0.8|G|)$:
> substituting $\rho = \gamma N/A$ makes the denominators equal term for term, and the frontier's own
> $\rho = 1.17909$ at this anchor reproduces $\gamma = 1.17909 \times 4791.05 / 44090 = 0.12811$. The
> two sessions' arithmetic agrees; only the new module had the bug.

**Cross-check against the H33-1 result merged from `main`.** The parallel session ran the
preregistered H33-1 prune on seeds `200–209` and refuted it — 0 of 6 criteria, mean ΔDTI `−0.003014`,
`0/10` seeds, `0/4` folds. Its measured removal efficiency is **`0.12855`**, which is not merely above
$\tau_{\text{proxy}} = 0.0193$ but **2.3× above $\tau_{\text{live}} = 0.0548$** — so the threshold
correction does **not** rescue it, and its refutation is stronger than it looked. Two of its criteria
are independently damning: the direction control went the *wrong* way (a naive top-10 % prune destroys
less credit per unit of mass, $e = 0.10104$, than the kinematically-targeted prune does), and kinematic
favourability covers only `11.95 %` of the emission against a required `60 %`.

> **The pruning family is now exhausted.** H32-2 (`e = 0.0344`), H33-1 (`e = 0.1286`) and H34
> (criterion 2 failed) have all been measured and all fail, and §3.1 shows the gap to `0.3195` is a
> detection gap no prune can close. Future effort belongs on **addition** arms (H33-3, H33-4, H33-5),
> gated against $\tau_{\text{live}}$ on the LOSFO far-field truth set.

**Two re-readings follow, recorded as re-readings and not promoted.** `H32-2` (archived $e = 0.0344$)
flips from FAIL to profitable at the live threshold, worth `+0.0047` modelled — it stays closed
because it needs its own fresh decade, not a re-reading. The `LOSFO` far-field **addition** gate
(`knowledge/20` §3) is the one that changes a plan: measured far-field credit/dot is `0.0465`, which
clears the cell threshold `0.0204` but **not** $\tau_{\text{live}} = 0.0548$, so base-quality
far-field dots would *lower* the live score. That gate must be restated against the live threshold.


### 3.7 Session 11 — five addition hypotheses, one refutation, and a slot decision made on fresh seeds

Session 10 ended with a hard constraint (§3.1): beating `0.3195` from the `0.2600` emission needs
`+1,151 px` of credit, more than the whole submission captures, and thinning efficiency (`0.03098`) is
below break-even (`0.05485`). That is a **detection gap**, so only new dots on uncovered structure can
close it. Session 11 therefore designed an addition series and measured the first member of it.

**The H35 ledger** (`knowledge/23_h35_hypotheses.md`, ranked by expected ΔDTI × cost, with the
obtainability check actually performed for each):

| Rank | ID | Class | Physical signature | Cost | Obtainable in-sandbox? |
|---:|---|---|---|---|---|
| 1 | `H35-1` hydrothermal-discharge conjunction | ADD | point process of thermal discharge — not a derivative field | low | **yes**, bytes in hand |
| 2 | `H35-4` bounded Phase-2 discovery budget | ADD (bounded) | a budget rule, not a transform | low | yes, nothing to fetch |
| 3 | `H35-2` heat-flow residual × 2 m probe | ADD | conductive residual from a genuinely different field | high | **no** — `sciencebase.gov` returns HTTP `000`; Actions bridge only |
| 4 | `H35-3` drainage-network neotectonics | ADD | channel offsets / knickpoints from 716 1 m DEM tiles | very high | **no** — `prd-tnm.s3.amazonaws.com` returns `000`; Actions only |
| 5 | `H35-5` vent-corridor control | CONFIRM | vent alignment — only `21` points, re-ranking only | low | yes, in hand |

#### 3.7.1 `H35-1` is refuted — 3 of 4 frozen criteria failed, arm closed

Preregistered in `knowledge/23_h35_hypotheses.md` §5 **before** the run; executed on its reserved seeds
`230–234` with the LOSFO far-field instrument (`450 s`, `evidence/h35_1_thermal_farfield.json`).

| # | Criterion | Required | Observed | Result |
|---|---|---|---|---|
| G1 | Profitability | `>= tau_live = 0.054852` credit/dot | `0.013195` | **FAIL** (4.2× short) |
| G2 | Differential vs matched-count control | thermal `>` control pooled and `>= 4/5` seeds | `0.013195` vs `0.023781`; `1/5` seeds | **FAIL** |
| G3 | Support | `>= 200` added dots/seed | `6,856.8` | PASS |
| G4 | End-to-end | pooled mean ΔDTI `> 0` | `-0.001805` (control `+0.000354`) | **FAIL** |

The dose-response is flat-to-wrong in every pre-declared variant, so **no tighter subset rescues it**:
`temp_c >= 50 C` `0.015812`, quartz geothermometry `>= 100 C` `0.011717`, radius `1 px` `0.020949`,
radius `6 px` `0.010640` — every one at or below the control and 2.6–5× below `tau_live`.

**Mechanism.** Great Basin hydrothermal discharge is overwhelmingly basin-margin and fault-controlled,
which is precisely why those faults are already catalogued and why the blended detector already fires
along those margins. The base emission has therefore already spent its budget on the structure the
springs mark; the candidate pool (`ridge AND active AND NOT base`) is left with redundant neighbouring
slop. The control draws candidates `> 6 px` from any thermal site and **beats** the arm — on this grid,
sitting beside a mapped-margin hot spring is a mild *negative* indicator for the credit a new dot can
still earn. Radius confirms it: the association is strongest at `1 px` and dissolves by `6 px`, the
opposite of a geological control.

**Scope, stated so the record is not over-read.** LOSFO truth is *mapped* geometry, so the stronger
claim (a concealed unmapped permeable structure is marked by a spring) is **untested, not refuted**.
But because LOSFO is an upper bound, failing it closes the arm as constructed. Per the frozen reading
rule: no candidate TIFF, no weekly slot, no confirmation, no retuning. `knowledge/24_h35_1_result.md`.

#### 3.7.2 The defect review found: the one-click file was dominated

Review of our own site found the advertised primary (`c3aeda1d31a3`) **strictly dominated on every
published statistic** by the file sitting in its own *tertiary* slot (`8acb75e1f2cc`) — mean gain
`+0.001272` vs `+0.001766`, worst-seed gain `+0.000907` vs `+0.001370`, all four folds lower, removed
credit per removed FP `0.00402` vs `0.00598`, hybrid projection `0.26650` vs `0.27013`. Registered as
`one-click-primary-dominated-by-tertiary` (severity **high**) in `registry/irregularities.json`.

The honest cause is a multiple-comparison error in the *other* direction: the primary came from a
**preregistered** gate, while the candidate that beat it is the maximum of **four correlated variants
scored on one holdout run**. Re-ranking on the same run that selected the winner is exactly the error
the preregistration discipline exists to prevent. So the tie was broken on **unused seeds** with the
frozen runner **unmodified**, under a rule frozen in
`knowledge/25_preregistration_H35-6_candidate_adjudication.md` before the run: largest mean gain, and
`>= 4/5` seeds, and `>= 3/4` folds, else no change.

| Variant (slot *before* the adjudication) | Seeds `180–189` | **Seeds `235–239` (fresh)** | Seeds won | Folds |
|---|---:|---:|---:|---:|
| H27-4 solo r=1 `8acb75e1f2cc` (tertiary) | `+0.001766` | **`+0.001761`** | `5/5` | `4/4` |
| H32-1 post-thinning `c3aeda1d31a3` (primary) | `+0.001272` | `+0.001251` | `5/5` | `4/4` |
| H32-1 pre-thinning `31e35eee884e` (secondary) | `+0.001399` | `+0.000944` | `5/5` | `4/4` |
| anti-selective control (prune the *protected* pixels) | `+0.000479` | `+0.000490` | `5/5` | `4/4` |

**The ranking replicated**: `8acb75e1f2cc` won again, in all four folds, at `+0.001761` against
`+0.001766` on the older decade — a difference of `5e-6`. The control stayed far below the winner
(`0.000490`), so this is a **selective** prune, not a generic prune-harder effect. The promotion rule is
met, and the **one-click primary is now `8acb75e1f2cc`** (`knowledge/25...`,
`evidence/h35_6_candidate_headtohead.json`). The demoted file is retained as the *conservative*
alternative because it protects fault tips and shallow SI-0 Euler depth clusters. Five seeds cannot
resolve a `+0.0005` gap: this is a decision under uncertainty, stated as one.

#### 3.7.3 What Session 11 changes about the plan

The ADD arm that could be measured **failed**, and it failed below its own random control. That is now
the second independent route to the same conclusion as the reachability frontier, reached from the
opposite direction: at this operating point **new dots are expensive** and a layer must be extremely
specific to clear `tau_live = 0.0548`. Meanwhile the H34 threshold study rates every archived *removal*
arm `PRUNE` (`e = 0.004`, `0.03435`, `0.008`, all `< 0.055`) and puts the optimal packing rung at `3.0`
rather than the shipped `2.828`. Calibration effort therefore belongs on the axis that measurably pays.
Ranked next: (1) a rung-`3.0` re-thin combined with the flank prune, validated on a fresh decade;
(2) `H35-2` heat-flow residual via the Actions bridge; (3) `H35-3` drainage neotectonics.

---

### 3.8 Session 12 — the data blocker is closed, and the packing rung was re-measured

**Blocker closed.** `bash scripts/download_competition_data.sh` now runs end to end in this sandbox:
`17/17` pins restored and hash-verified (`evidence/restore_audit.json`, `data/restore_receipt.json`),
`data/prepared/features.npy` rebuilt at shape `(5,167,373, 32)` `float32`
(`83ed2704…`), and `evidence/submission_file_audit.json` re-audited. The earlier
"cannot download the competition data" note was an environment artefact, not a repository one:
`.venv` + `pip install -r requirements.txt` plus `gh api` (which *is* reachable) is sufficient.
**Egress from the sandbox is GitHub-only** — `raw.githubusercontent.com`, `sciencebase.gov`,
`prd-tnm.s3.amazonaws.com`, `api.datacite.org`, `drivendata.org` and `doi.org` all fail at the TLS
handshake, so any external layer still has to arrive through the Actions bridge (§3.4).

**A measurement that changed the arm before it ran.** The rung ladder had been described as a
"re-thin". It is not a thinning. On the full footprint the shipped `0.2600` file is *exactly*
`thinning.dot_thin(h19_5_surface, 2.8)` (44,090 px, 0 px symmetric difference — an independent
confirmation that the published artifact's construction is what the repo says it is), but
`dot_thin(surface, 3.0)` shares only 30,666 px with it, **adds 10,667 px and drops 13,424 px**. Because
`dot_thin` is a greedy lowest-raster-index cascade, raising `min_dist` *re-seeds* the packing instead
of deleting dots; 24,091 px change hands. The ladder is therefore a **layout** choice, not a budget
cut, and that is falsifiable — which is what the new control is for.

**H36-1, gate frozen in `knowledge/26_preregistration_H36-1.md` (commit `aaa659c`) before seeds
`240–249` were touched** (`evidence/h36_1_holdout.json`, `knowledge/27_h36_1_result.md`):

| Variant (vs the same-run rung-2.828 control, OOF DTI 0.094132) | ΔDTI | seeds | folds |
|---|---:|---:|---:|
| `rung30_unpruned` — the H34 claim in isolation | +0.000956 | 10/10 | 4/4 |
| **`rung30_blind_r1` — re-pack + H27-4 blind flank prune** | **+0.002599** | **10/10** | **4/4** |
| `rung30_flank_mid` — re-pack + H32-1 mid-segment prune | +0.002188 | 10/10 | 4/4 |
| `h27_4_blind_r1_d280` — the Session-11 incumbent | +0.001715 | 10/10 | 4/4 |
| `control_random_drop_matched_n` — **delete the same 2,649 dots at random** | **−0.001657** | **0/10** | **0/4** |
| `control_rung30_protected_only` — anti-selective control | +0.001352 | 10/10 | 4/4 |

All five frozen criteria pass: the rung effect is positive in every seed and fold (G1); the re-pack
beats the matched-`N` random drop by **+0.002613**, so the effect is layout and not budget (G2); every
prune's removal efficiency (0.0096–0.0098) is far below `tau_live = 0.054852` (G3); the winner beats
the incumbent by +0.000884 ≥ the pre-declared +0.0005 margin (G4); and the anti-selective control sits
below the winner, so the prunes are still selective (G5).

**The anti-budget control is the load-bearing result.** A coin-flip deletion of exactly the 2,649 dots
the rung removes *loses* 0.001657 — in `0/10` seeds and `0/4` folds — while the re-pack at the same
count gains 0.000956. That also falsifies the natural reading of H34: under its `gamma`-invariance
assumption removal is non-selective and a random deletion to the same `N` should have matched. It does
not. `gamma`-invariance held to 1.9 % across the three live anchors of one surface and does not survive
this test, because `dot_thin` re-seeds.

**Promoted artifact.** `docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif`
(content id `b531dae0a36f`, 37,660 px, SHA-256 `5556aa14…`). `scripts/verify_downloads.py` → **PASS,
179 checks, 0 failures**. Live-anchored hybrid projection **0.2717–0.2727** (H34's ladder for the
re-pack, +0.002834; the gate's measured prune efficiency for the flank prune, 3,673 px at 0.0098447).
The range, not a point value, is deliberate — `operating_point.prune_gain` is a first-order expansion
and over-states a 9 %-of-`N` prune by ~0.001, now registered as
`prune-gain-linearisation-overstates-large-prunes`. **No weekly slot is used by this arm; a gate is not
a submission.** Do not preregister further rung arms: `3.1623` removes a further 6,516 px for no
measured retention gain and H34 rates it worse, so the family is bounded on both sides.

**Also fixed this session (defect review, `registry/irregularities.json`).** The first H36-1 build
shipped a submission note reading `28GEMSDOE 28GEMSDOE H36-1 … re-pack beats matched-N random d | …` —
a duplicated family token (the caller passed it *and* `make_note` prepends it) and a mid-word
truncation (the summary exceeded the 200-character budget and `make_note` slices silently). The note is
the text a human pastes into the organiser's Note field, so it is human-facing even though every raster
check passed. Rebuilt at 192/200 with an assertion in the builder that fails the build rather than
truncating, and the builder is now idempotent (re-running it previously demoted its own output into the
secondary rank). The site's above-the-fold paragraph was also split — it had become a single run-on
`<p>` concatenating historical H31/H32-structural/H35-1 failures onto the current status.

### 3.9 Session 13 — the emission rule itself was the leak, and it is now measured

Session 12 closed with the emission step (`thinning.dot_thin`) unchanged: it keeps a pixel iff no
already-kept pixel is closer than `min_dist`, walking candidates in **ascending raster index**, so the
detector's evidence never influences the layout. H36-1 had already shown the *layout* is worth
`+0.0026`/`−0.0017` at fixed count (`knowledge/27` §2). Session 13 replaced the rule and gated it.

**Hypothesis H37-1.** Replace the raster-order cascade with a lazy-greedy **maximum expected coverage**
of the detector's probability field under the official triangular kernel
(`k(d) = max(1 − d/300 m, 0)`, `R = 3 px`), at a **matched dot count**, followed by the unchanged
`H27-4` blind 1-px catalogue-flank prune:

$$\text{gain}(x \mid S) = \sum_q p(q)\,\max\!\big(0,\; k(|x-q|) - C(q)\big), \qquad C(q) = \max_{y \in S} k(|y-q|)$$

That is the official metric's own true-positive term used as the packing objective, so the objective
and the score are the same object. `gain` is monotone and submodular, so the greedy order carries the
`1 − 1/e` guarantee and lazy evaluation selects the same set. Implementation: `src/gems27/packing.py`,
tests `tests/test_packing.py` (including a brute-force `(1 − 1/e)` bound check and a
determinism contract). Every design choice below was fixed by an exploratory pass on **spent** seeds
`181`/`185` (`evidence/_scratch/packing_h37_explore{,_v2,_v3}.json`) before the gate was frozen in
`knowledge/29_preregistration_H37-1.md`.

**Frozen gate, fresh seeds `250–259`, 40 cells (`evidence/h37_1_holdout.json`, 442.6 s).**

| Variant | mean OOF DTI | ΔDTI vs `d=2.8` | vs incumbent | seeds | folds |
|---|---:|---:|---:|---:|---:|
| `base_oof_d280` | 0.098186 | — | — | — | — |
| `rung30_blind_r1` (H36-1 incumbent) | 0.100860 | +0.002675 | — | — | 4/4 |
| **`cover_prob_r1` (PRIMARY)** | **0.105475** | **+0.007289** | **+0.004614** | **10/10** | **4/4** |
| `cover_prob_pool3x_r1` (pool probe, 2.45 % density) | 0.105522 | +0.007336 | +0.004661 | 10/10 | 4/4 |
| `cover_prob_1p5n_r1` (dose, not promotable) | 0.108626 | +0.010440 | +0.007765 | 10/10 | 3/4 |
| `control_random_matched_n` (content-blind) | 0.053502 | −0.044684 | −0.047359 | 0/10 | 0/4 |

All five frozen criteria passed (G1 direction, G2 margin `+0.004614 ≥ +0.0005`, G3 `10/10` seeds and
`4/4` folds, G4 content-control margin `+0.0520`, G5 integrity 0 violations in 40/40 cells). Two
findings matter as much as the headline:

* **The instrument reproduced.** The H36-1 incumbent returned `+0.002675` here against `+0.002599` on
  seeds `240–249` — a `7.6e-5` difference on an independent decade.
* **The pool probe is what makes the artifact transferable.** The gate's primary drew from *every*
  ridge pixel (≈16 % of the footprint); the shipped H19-5 surface is only **2.34 %**. The probe
  restricted to a 2.45 % pool measured the same effect (`+0.004661`, 10/10 seeds, 4/4 folds), so the
  artifact is a measured analogue, not an extrapolation.

**Artifact.** `docs/downloads/gems28-h37-1-coverprob-h19-5-r1-20261003-0bbddf41eb6d-nan.tif` —
**37,447 px** at the same 41,333-px pre-prune budget as the incumbent, SHA-256 `4557311baedb4e66…`,
`verify_downloads.py` → **PASS, 208 checks, 0 failures**. The weight field is the full-fit detector
probability (the emission-time analogue of the gate's out-of-fold field). A second, **not-promoted**
probe (`…-probe-union-pool-r1-…`, 38,545 px) records the union-pool emission (H19-5 + the detector's
own ridges) because the live record already punishes that content: 26GEMSDOE `dilcond-oof-v1`, a pure
detector-product emission, scored `0.1223`.

**Far-field falsification: F1 FAILED.** The test frozen in `knowledge/32` ran on its dedicated LOSFO
decade (seeds `210–214`, whole fault systems removed with a 600 m buffer) after freeze commit `7e637c9`.
The unmodified base arms reproduced the stored diagnostic to eight decimals, so the instrument is stable;
the new rule then earned `−0.000037` against the raster cascade (95 % interval `±0.000832`, 9/20 cells,
3/5 seeds) while the field coverage it achieved rose slightly (`15,570.2 → 15,670.8`). The interleaved
`+0.007289` therefore does not transfer off the catalogue: habitat decomposition
(`evidence/arm_habitat_decomposition.json`) had already shown that 100 % of interleaved truth is
catalogue pixels, and the LOSFO truth lies ≥ 8 px from anything the detector saw. F2's pass
(`+0.002091` vs a random order) is **not** cited as an ordering result — the two ordering arms are
capacity limited (10,975 / 10,992 dots against the requested 12,001), so the only exactly matched
comparison is F1, which failed. The artifact is demoted to secondary by the pre-committed rule, both
numbers are printed on its card, and `knowledge/33` withdraws the live projection. Registered as
`h37-1-farfield-effect-is-zero` and `ordering-packers-are-capacity-limited`.

#### 3.9b H37-3 Euler SI-0 depth-coherence licence — REFUTED as a promotable arm (mechanism positive)

Rank-2 of `knowledge/31` was preregistered at `knowledge/34` (freeze commit `0788eec`) and run on its own
LOSFO decade, seeds `260–264` (20 paired cells, exit 0, ≈13 min; `evidence/losfo_h37_3_licence.json`,
analysis `scripts/analyze_h37_3.py`, integrity `evidence/h37_3_licence_integrity.json`). The licence rule
was frozen in advance: the 1,435 of 6,309 SI-0 Euler clusters with `depth_mad_m ≤ 60` **and**
`median_depth_m ≤ 400` **and** `n_solutions ≥ 8`, mapped one dot per cluster, excluding catalogue and
already-emitted pixels, at the shipped 2.8 px spacing; 296 dots added per cell on average. Three arms
were scored on the identical far-field truth, cell by cell: `base`, `base+licence`, and
`base+same-count random control` drawn from the same off-catalogue eligible region.

| criterion | result | verdict |
|---|---|---|
| **C1** mean ΔDTI(licence − base) > 0, ≥15/20 cells, ≥4/5 seeds | **+0.000576** ±0.000451, 13/20 cells, 5/5 seeds | **FAIL** (spread) |
| **C2** pooled credit per added dot ≥ `τ_live` 0.0548 | **0.031157** (57 % of the bar) | **FAIL** |
| **C3** mean ΔDTI(licence − random control) > 0, ≥15/20 cells | **+0.000699** ±0.000452, 16/20 cells | **PASS** |
| **C4** integrity | same-seed base arms bit-identical to the pre-patch harness; fresh-decade base arms inside the documented LOSFO spread | **PASS** |

**Verdict by the pre-committed rule: refuted as a promotable arm**, with the mechanism recorded as real and
this session's second honest negative. The licence's dots earn **1.65×** what the same number of random
dots earn in the same region — the depth-dispersion statistic does carry off-catalogue information — but
0.0312 < 0.0548, so adding dots at this rate *lowers* the live score (296 dots: `0.260627 → 0.260294`;
the arm's full 5,916-dot scale: `→ 0.254356`). One of four folds is negative (`NE_LidarGapHeavy`
−0.000390 against `NW` +0.001186, `SE` +0.000893, `SW` +0.000617), which is why C1's spread rule exists.
Seed ledger: **260–264 spent by H37-3; 265–269 spent by Session 14 LOSFO (`H36-1` + `H38`); 270–279 spent by Session 14 interleaved (`H38-1`); 215–219 and 280+ free.** Registered as `h37-3-licence-real-but-below-the-live-rate` and
`cross-seed-baseline-comparison-is-not-an-integrity-check` in `registry/irregularities.json`.

#### 3.10a Session 14a (parallel branch) — the far-field attribution, a new-information arm, and a slot that stayed closed

**Why the session started where it did.** Session 13 ended with H37-1 demoted by its own far-field rule
(§3.9). Session 14 began by asking *which* construction that rule had actually falsified, because the
F1 arm `packing_arms` in `scripts/run_losfo_harness.py` packs the **top-k ridge pool** at the `d=2.8`
count, while the H37-1 gate and the shipped file pack **all ridge pixels** at the rung-3.0 count.

**Finding 1 — the falsification was construction-specific (`knowledge/39`).**
`scripts/run_losfo_cover_variants.py` crossed both factors on one detector, one truth set and one count
ladder (`evidence/losfo_cover_variants.json`, seeds `215–219`, 20 cells, `integrity_violations: []`,
and an independent re-reading in `evidence/losfo_cover_variants_analysis.json`):

| arm (vs `base_d28` = 0.106476) | candidates | target | mean DTI | ΔDTI | cells / seeds / folds up |
|---|---|---|---:|---:|---|
| `pool_cover_nbase` — the arm `knowledge/33` tested | top-k pool | `d=2.8` count | 0.10730 | **+0.000819** | 12/20, 3/5, 2/4 |
| `pool_cover_npre` | top-k pool | rung-3.0 count | 0.10671 | +0.000235 | 9/20, 2/5, 2/4 |
| `all_cover_nbase` | all ridges | `d=2.8` count | 0.11274 | **+0.006269** | 16/20, 5/5, 3/4 |
| `all_cover_npre` | all ridges | rung-3.0 count | 0.11163 | **+0.005158** | 16/20, 5/5, 3/4 |

The head-to-head contrasts isolate one factor at a time: **+0.005450** (candidate set at the `d=2.8`
count, 5/5 seeds) and **+0.004923** (at the rung-3.0 count, 5/5 seeds). `all_cover_npre` reproduces the
independent probe's `cover_n` to `0.0` on all 20 cells and `base_d28` reproduces its `thin_d28` to
`0.0` — the two runs agree exactly on their shared arms. The same run measured the H36-1 **dose** axis
far field for the first time: raster-order `d=3.0` minus `d=2.8` is `−0.000116` while emitting 677
fewer dots, i.e. the restored one-click primary's re-layout is far-field **neutral**, which discharges
the remedy queued in `h37-1-farfield-effect-is-zero`.

**Finding 2 — the detector had never seen a radiometric measurement, and the organisers shipped one.**
A band-identity audit of the whole stack against every owner-mirrored GeoDAWN channel found that
`training_features.tif` band 6 (`"tc - Tilt angle or total curvature - magnetic field derivative"`) is
**rank-identical to the GeoDAWN radiometric total count** (Spearman `1.0000` on the in-footprint
overlap, `0.999` over the full training extent), and that `scripts/prepare_data.py` **excludes** that
band as mislabelled. Every other training band sits at the trend background (`0.90–0.93`) against every
GeoDAWN channel, so nothing else is a hidden duplicate. The detector was therefore blind to
radiometrics, including the one radiometric channel the organisers put in the stack.

**Finding 3 — a new-information arm was frozen, gated, and then refused by its transfer test.**
`H38-1` adds six channels (`geodawn_rad` K, Th, U; `geodawn_extensions` Th/K, U/K, U/Th; `TMI_up150` and
`rad_TC` excluded with measured reasons) to the frozen 32-band matrix. Two harness defects were found
and disclosed before any re-run (`knowledge/38` §§7–8): the pilot decade `260–269` voided because the
G5(b) check compared the **post-prune** emission to the **pre-prune** request, and `270–279` was void
for gating because `G2_promotion` used the fold split against the wrong reference. The gated third
decade `280–289` passed every criterion:

| arm (seeds 280–289, 40 cells) | detector | emission | mean DTI | mean dots |
|---|---|---|---:|---:|
| `base_d280` | D0 (32 bands) | raster `d=2.8` reference rule | 0.09552 | 12,231.2 |
| `cover_r1` (incumbent) | D0 | coverage packing + blind `r1` prune | 0.10513 | 11,335.0 |
| `rad_base_d280` | D1 (+6 radiometrics) | raster `d=2.8` | 0.10180 | 12,203.9 |
| **`rad_cover_r1`** | D1 | coverage packing + prune, count-matched | **0.10800** | 11,328.7 |
| `control_random_matched_n` | D0 | content-blind draw at the same count | 0.05316 | 11,320.3 |

`G1 = +0.002869` (9/10 seeds, 4/4 folds), `G2` pass, `G3` do-no-harm `+0.006282` (10/10, 4/4),
`G4` content-control margin `+0.054841`, `G5` clean, `passed: true`. `scripts/analyze_h38_1.py`
re-derived every gated statistic from the stored per-cell records (max DTI recompute error `0.0`, all
count identities hold). **Then the transfer test refused it** (`knowledge/42`, seeds `220–224`): the
count-matched far-field effect is `+0.000959` with a 95 % interval of `±0.004469`, `2/5` seeds, `2/4`
folds and `4/20` cells worse than the incumbent by more than `0.005` — unresolved at best, and the
run's reproduction guard-rail F4 fired because the tolerance in the preregistration was mis-calibrated
(the probe's own seed-level SD is `0.0080–0.0100`, so five-seed means differ by ~`0.006` at random;
registered as `h38-1-farfield-f4-band-miscalibrated`).

**Outcome: nothing was promoted.** No H38-1 file was built, `docs/downloads/manifest.json` is unchanged,
the one-click primary is still H36-1 (`b531dae0a36f`), and no weekly slot was spent. The arm's status is
*interleaved gate passed, far-field unresolved* — the honest next move is a properly powered far-field
decade (≥ 10 seeds), not another interleaved re-run.

**What the session hands forward.** The far-field run did replicate one thing twice: the **all-ridge
coverage packing construction with the frozen D0 detector** scored `+0.005881` with `5/5` seeds and
`4/4` folds against the raster cascade (seeds `220–224`), on top of `+0.005275` on seeds `215–219`. That
is the strongest far-field signal the repository has, it belongs to a construction that has never been
gated for promotion, and its credit density (`0.0499–0.0506`) is still below the live break-even
`0.054852`. It is now the top-ranked next arm (`registry/next_hypotheses.json:session14_addendum`),
together with a ≥ 10-seed continuation for H38-1 and the untouched H38-4/H38-3/H38-2/H38-5 set
(`knowledge/37_hypotheses_session14.md`).

**Three cross-cutting records.** (i) `knowledge/39` — the far-field attribution, with the H36-1 dose
axis measured neutral. (ii) `knowledge/38` §§7–8 — both harness errata, each costing one gate decade,
each disclosed before its re-run. (iii) The band-identity audit that shows the competition's own stack
carries a mislabelled radiometric channel the detector was excluded from. Irregularities raised this
session: `farfield-arm-did-not-match-gate-construction`, `h36-1-dose-change-is-far-field-neutral`,
`h38-1-g5b-checked-post-prune-count`, `h38-1-g2-fold-statistic-used-base-not-incumbent`,
`h38-1-farfield-f4-band-miscalibrated`, `cover-rule-far-field-gain-replicated-not-gated`, plus the
`tc-band-mislabelled` re-confirmation.

---

#### 3.10b Session 14b — `H36-1` LOSFO Far-Field Verification (`F1–F4` ALL PASS) & `H38-1` Multi-Physics Corroboration (`C1–C4` ALL PASS)

Full write-up: `knowledge/43_hypotheses_heatflow_euler.md` (5 ranked hypotheses), `knowledge/44_preregistration_H36_1_and_H38_farfield.md` (frozen at commit `ff85e30`), `knowledge/45_h36_1_and_h38_1_result.md` (results), and `knowledge/46_session14b_closeout.md` (closeout).

1. **Part A — `H36-1` (`b531dae0a36f`, `37,660` px) verified on LOSFO far-field truth (`seeds 265–269`, 20 paired cells, `evidence/losfo_session14_h36_1_and_h38.json`):**
   - **F1 (`rung30_unpruned` vs matched-N random drop): PASS** — `+0.002073` mean DTI (`17/20` cells, `5/5` seeds).
   - **F2 (`2.828 -> 3.0` far-field removal efficiency): PASS** — pooled $e_{\text{far}} = 0.025293 < \tau_{\text{live}} = 0.054852$ (`19/20` cells below $\tau_{\text{live}}$).
   - **F3 (`rung30_blind_r1` vs `d=2.8` base): PASS** — **`+0.001713` mean LOSFO $\Delta\text{DTI}$** (`16/20` cells, `5/5` seeds, pooled $e_{\text{far}} = 0.013587 < \tau_{\text{live}}$) and **`+0.005810` over matched-count random drop in `20/20` cells**.
   - **F4 (`h27_4_blind_r1_d280` zero-loss check): PASS** — removes `11,599` flank-shadow dots across 20 cells and loses **exact `0.00` TP** (`20/20` cells, `+0.002249` mean $\Delta\text{DTI}$).
2. **Part B — `H38-1` Conductive Heat-Flow Residual (`DeAngelo et al., 2022`, DOI `10.5066/P9BZPVUC`) + Shallow SI=0 Euler Lineament Corroboration (`src/gems27/heatflow_euler.py`):**
   - Uses the newly landed USGS Great Basin heat-flow borehole clip (`docs/data/sb_heat_flow_in_footprint.json`, `1,546` in-footprint wells, `753` with conductive heat-flow residual `hf_resid >= 50.0 mW/m²`) and shallow Reid et al. (1990) SI=0 Euler contact clusters aligned within `300 m` of the 1-px detector ridge (`score_mult = 1 + 0.5*hf + 0.5*eu`, capped at `75` dots/cell).
   - **On `d=2.8` base (`h38_1_joint`): `ALL_PASS = True` (`C1–C4` all True).** Earns **`0.077241` credit/added dot** (`1.41x` $\tau_{\text{live}} = 0.054852$, vs `0.040983` uncorroborated sub-ridge control and `0.023326` random control), **`+0.000792` mean LOSFO $\Delta\text{DTI}$** (`17/20` cells, `4/5` seeds, `4/4` folds), and **`+0.000656` mean interleaved $\Delta\text{DTI}$** on fresh seeds `270–279` (`27/40` cells, `9/10` seeds, `4/4` folds, `0.064399` credit/dot, `evidence/h38_1_interleaved_holdout.json`).
   - **On `H36-1` primary (`h38_1_joint_on_r30_r1`): `ALL_PASS = True` (`C1–C4` all True).** Earns **`0.069930` credit/added dot** (`1.28x` $\tau_{\text{live}}$, vs `0.032268` sub-ridge control and `0.026814` random control), **`+0.000747` mean LOSFO $\Delta\text{DTI}$ over `H36-1`** (**`+0.002460` over `d=2.8` base**, `16/20` cells, `4/5` seeds, `4/4` folds), and **`+0.000543` mean interleaved $\Delta\text{DTI}$ over `H36-1`** on fresh seeds `270–279` (`27/40` cells, `8/10` seeds, `4/4` folds).
   - **Why `H38-1` succeeded where `H37-3` (`0.03116` credit/dot) failed:** `H37-3` emitted at the raw `1 km × 1 km` Euler window centroid $(x_0, y_0)$, which has `100–300 m` horizontal position uncertainty relative to the `100 m` surface trace; snapping shallow SI=0 Euler clusters within `300 m` to the `100 m` 1-px detector ridge crest (`ridge_nms`) and combining with conductive borehole heat-flow residual (`hf_resid >= 50 mW/m²`) lifts marginal efficiency by `2.48x` (`0.03116 -> 0.07724`).
   - **Secondary arm `H38-2` (`h38_2_low_relief_euler`) REFUTED:** Restricting Euler ridge additions to flat basin interiors (`relief <= P35`) earned only `0.013976` credit/dot (`-0.000045` $\Delta\text{DTI}$, `5/20` cells) because hidden truth in `labels.tif` is itself scarp-biased.
   - **Companion Artifact:** `docs/downloads/gems28-h38-1-hf-euler-r30-r1-20261003-56a9f473edc7-nan.tif` (`37,860` px = `37,660` `H36-1` + `200` corroborated dots, SHA-256 `81d5b87bc8424f16…`), slotted at `secondary` (the contemporaneous mainline audit reported `237/237`; after PR-28 reconciliation added explicit unique submission-name metadata, the current audit reports `247/247` in `evidence/submission_file_audit.json`).

**Answer to the standing question.** Why is `0.2600` reported, and can we beat it? Conditional on the owner-reported score-to-file pairing, the local inversion explains the reported `0.2600` by Poisson-disk thinning at `d = 2.8`: it cut 63 % of the H19-5 pixels while retaining an estimated 90.6 % of the `d=1.5` credit (`knowledge/01`). This mechanism is a reproducible local inference, not independent organizer verification of that score. `H36-1` (`b531dae0a36f`, `37,660` px) re-packs the `H19-5` surface at rung `3.0`
and prunes the `100 m` catalogue flank shadow, passing both the 10-seed interleaved gate (`+0.002599` on
`240–249`, `+0.002675` on `250–259`, `+0.002804` on `270–279`) and the 5-seed LOSFO far-field gate
(`+0.001713` on `265–269`, `F1–F4` ALL PASS, projecting to `0.2717–0.2727` live). And `H38-1`
(`56a9f473edc7`, `37,860` px) is the first addition arm in the repository to clear $\tau_{\text{live}} = 0.05485$
on LOSFO far-field truth (`0.06993–0.07724` credit/dot, `C1–C4` ALL PASS). Beating `0.3195` still needs
`+1,151 px` of credit (`knowledge/20` §3.1) and remains a **detection** problem; the ranked geological
candidates for Session 15 are in `knowledge/43_hypotheses_heatflow_euler.md` and `knowledge/46_session14b_closeout.md`.

**Plausibility of beating the reported `0.3195`.** It is mathematically possible, but not supported as a likely near-term outcome by current evidence. At the 44,090-dot budget, the conditional inversion requires about 1,151 additional weighted-credit pixels (24% above the reported `0.2600` estimate). Existing locally validated additions show positive LOSFO signal but the current artifact projections remain around `0.272–0.274`, not `0.3195`. The only credible route described here is a substantially more precise detector of genuinely off-catalogue faults; no present experiment demonstrates the required scale of gain. This is a research assessment, not an organizer score prediction.

**Infrastructure irregularity found and reported this session.** GitHub Pages for this repository is
**not deploying**: the Pages API reports `status: errored`, the last successful legacy build was at
`2026-10-03T21:11Z`, and the runs after it (`e429135` → `"Page build failed."`; `a667805` → stuck
`building`) leave the published site stale. The repository's own Actions deployment
(`.github/workflows/pages.yml`, `actions/deploy-pages`) succeeds and the two paths are configured
against each other (`build_type: legacy`, source `main:/`). Registered in
`registry/irregularities.json: github-pages-legacy-build-errored`; whatever is published at
`https://buffedlizard55-lab.github.io/GEMSDOE28/` should be treated as possibly stale until the Pages
source is switched to **GitHub Actions**.

---

## 4. Euler Deconvolution for Depth (Reid et al., *Geophysics*, 1990) & Screen Ledger

Implemented in `src/gems27/euler.py` (`scripts/build_euler_features.py`, `evidence/h31_1_euler_feature_audit.json`, `evidence/h31_1_euler_clusters.csv`):
1. **Formulation (Reid, Allsop, Granser, Millett, & Somerton, 1990, [DOI:10.1190/1.1442774](https://doi.org/10.1190/1.1442774))**:
   $$(x - x_0)\frac{\partial T}{\partial x} + (y - y_0)\frac{\partial T}{\partial y} + (z - z_0)\frac{\partial T}{\partial z} = N(B - T)$$
   Solved via moving $10 \times 10$ ($1\text{ km} \times 1\text{ km}$) least-squares windows across `tmi` (band 14) with all three derivatives ($\partial_x T, \partial_y T, \partial_z T$) derived self-consistently from the same `tmi` field (`80.265%` valid vertical-derivative coverage).
2. **Primary Structural Index $N=0$ (Fault Contact) & Depth-Labeled Clustering**:
   - Retains `118,089` accepted $N=0$ source solutions (`depth_m` median `296.4 m`, P10 `155.3 m`, P90 `614.1 m`), of which `22,718` have *Euler-estimated source coordinates* $(x_0, y_0)$ aligned within `200 m` of an independent `tmi` horizontal-gradient ridge, forming **`6,309` depth-coherent clusters** (`evidence/h31_1_euler_clusters.csv`).
   - Descriptive sensitivity runs at $N=1$ (`5,665` clusters) and $N=2$ (`4,661` clusters) confirm substantial centroid shift (`41.0%` and `30.2%` match within `600 m` of $N=0$), documented in `evidence/h31_1_euler_feature_audit.json`.
3. **Why `H31-1` (GBDT feature injection) and `H32-1` (structural-step GBDT screen) failed while our `180–189` Euler depth-cluster structural protection gate succeeded**:
   - Feeding 3 rasterised Euler cluster channels into a 41-band `HistGradientBoostingClassifier` (`H31-1`, seeds `160–169`, `evidence/h31_1_euler_screen.json`) failed its frozen screen (`-0.001947` mean ΔDTI, `1/4` folds, `2/10` seeds), and feeding 6 structural-step derivative features (`src/gems27/structural_step.py`, seeds `170–179`, `evidence/h32_1_structural_step_holdout.json`) also failed its frozen screen (`-0.001570` mean ΔDTI, `3/4` folds, `3/10` seeds).
   - In contrast, using the `6,309` shallow $N=0$ Euler depth-coherent clusters (`evidence/h31_1_euler_clusters.csv`) as an **independent subsurface contact corroboration gate** during $100\text{ m}$ flank-shadow de-jittering on `d=2.8` on fresh seeds `180–189` (`evidence/h32_1_holdout.json`) shows that pixels protected by fault tips or shallow $N=0$ Euler depth clusters exhibit **`2.29x` higher hidden-fault credit density (`0.00919` vs `0.00402` credit/FP)** than mid-segment flank-shadow pixels, improving DTI in **`10/10` seeds and `4/4` spatial folds**.

---

## 5. Candidate Geological Hypotheses

**Current ledger: `knowledge/43_hypotheses_heatflow_euler.md` (Session 14)** — five ranked arms (`H38-1` through `H38-5`), each naming
its layers, physical signature, why it catches a fault *missing* from the catalogue rather than one
already in it, and how it differs from everything already implemented, plus a per-claim obtainability
ledger:
- **Session 14 close-out (deliverables, three passes, limitations, queued next steps):** `knowledge/46_session14b_closeout.md`.
- **Session 14 preregistration & results:** `knowledge/44_preregistration_H36_1_and_H38_farfield.md`, `knowledge/45_h36_1_and_h38_1_result.md`.
- **Session 13 ledger & close-out:** `knowledge/31_hypotheses_session13.md`, `knowledge/36_session13_closeout.md`.
- **Session 11 ledger:** `knowledge/23_h35_hypotheses.md`.
- **Session 10 ledger:** `knowledge/20_strategy_after_reachability_frontier.md` (re-ranks `knowledge/18_new_hypotheses_H33_series_2026-10-03.md`).

**Ranking rule changed in Session 10.** §3.1 shows the gap to `0.3195` is `+1,151` px of credit that
only an *addition* arm can supply, so **addition arms now rank above pruning arms regardless of
individual expected ΔDTI** — the ordering below differs from `knowledge/18` for that reason.

- **`H36-1` — EXECUTED Session 12 (interleaved `seeds 240–249`) & VERIFIED Session 14 (LOSFO far-field `seeds 265–269`), PROMOTED PRIMARY (`b531dae0a36f`, `37,660` px):** Re-pack the H19-5 surface from packing rung `2.828` to rung `3.0` (`41,333` px) and apply the `H27-4` blind 1-px catalogue-flank prune (`37,660` px). Passed 10-seed interleaved gate (`+0.002599` on `240–249`, replicated `+0.002675` on `250–259` and `+0.002804` on `270–279`) AND passed all four frozen LOSFO far-field criteria `F1–F4` on `seeds 265–269` (`+0.001713` mean LOSFO $\Delta\text{DTI}$, `16/20` cells, `5/5` seeds, $e_{\text{far}} = 0.01359 < \tau_{\text{live}} = 0.054852$, and exact `0.00` TP lost by the blind `r=1` prune).
- **`H38-1` — EXECUTED Session 14, FROZEN LOSFO (`seeds 265–269`) & INTERLEAVED (`seeds 270–279`) GATES PASSED, SECONDARY (`56a9f473edc7`, `37,860` px):** Conductive borehole heat-flow residual (`hf_resid >= 50 mW/m²`, `DeAngelo et al., 2022`, DOI `10.5066/P9BZPVUC`, `docs/data/sb_heat_flow_in_footprint.json`) + shallow Reid et al. (1990) SI=0 Euler clusters aligned within `300 m` of the 1-px detector ridge (`src/gems27/heatflow_euler.py`). Passed `C1–C4` on LOSFO `seeds 265–269` (`0.07724` credit/dot, `+0.000792`, `17/20` cells, `4/5` seeds on `d=2.8`; `0.06993` credit/dot, `+0.000747` over `H36-1`, `+0.002460` over `d=2.8`, `16/20` cells, `4/5` seeds on `H36-1`) and passed interleaved `seeds 270–279` (`+0.000656` on `d=2.8`, `9/10` seeds, `4/4` folds; `+0.000543` on `H36-1`, `8/10` seeds, `4/4` folds).
- **`H38-2` — EXECUTED Session 14, FROZEN GATE FAILED (`seeds 265–269`, CLOSED):** Concealed basin-fill conjunction (`relief <= P35` × shallow SI=0 Euler cluster on 1-px ridge) earned `0.01398` credit/dot (`-0.000045` LOSFO $\Delta\text{DTI}$, `5/20` cells) because hidden truth in `labels.tif` is itself scarp-biased (`knowledge/45`).

#### Parallel branch reconciliation — local Euler × gravity × low-relief attempt (not evaluable)

A separate Arena branch froze a distinct shallow SI-0 Euler × gravity-gradient × low-valid-relief rule as “H38-1” (commit `cf1d036`; its single-use run commit was `9880ca6`). The label-free screen found 140 candidates, but its one LOSFO invocation on seeds `265–269` failed in the analyzer (`numpy.int64` JSON serialization); no C1–C5 report or gate decision exists. During PR-28 merge reconciliation, mainline evidence showed that PR #27 had already used the same decade for H36-1 and its heat-flow/Euler test before this branch started (`evidence/losfo_session14_h36_1_and_h38.json`; main merge `68b9f0a` at `2026-10-04T01:04:41Z`; local run start `01:46:40Z`). The pre-run scan covered only the branch checkout and missed that mainline artifact. Thus this local attempt was not an independent fresh holdout even apart from the analyzer failure. Seeds are burned; do not rerun or recompute them. This is not a result for, or refutation of, the separate upstream radiometric or heat-flow/Euler experiments also labeled H38-1. This run wrote no summary; after the merge, `evidence/h38_1_holdout.json` is the distinct upstream 280–289 radiometric report, not this branch-local attempt. Full audit: [`knowledge/39_session14_closeout_2026-10-03.md`](knowledge/39_session14_closeout_2026-10-03.md); failed claim SHA-256 `d425e976f117463967a0f7cc99eef40b88cd15bbd36537ccd31748a82f99635b`.

- **`H32-1-dejitter` — VALIDATED PASS (seeds `180–189`):** Tip- & Euler-Depth-Cluster-Protected Mid-Segment Flank-Shadow De-Jittering on `d=2.8` (`+0.001272` post-thinning / `+0.001399` pre-thinning, `10/10` seeds, `4/4` folds; `evidence/h32_1_holdout.json`). Retained as `quaternary` (`31e35eee884e`) and `conservative_alternative` (`c3aeda1d31a3`).
- **`H32-2` — EXECUTED Session 9, FROZEN GATE FAILED (seeds `190–199`, CLOSED):** shallow-over-deep magnetic de-screening scored `−0.003767` mean paired ΔDTI (`0/10` seeds, `0/4` folds; `evidence/h32_2_holdout.json`, `knowledge/17_h32_2_result.md`). Run-1 sentinel defect disclosed and repaired (`evidence/h32_2_holdout_run1_invalid_2026-10-03.json`). The direction control supported the physics (shallow dots carry more credit/FP: `0.0383` vs `0.0343`) but the deep class sits far above the OOF inclusion threshold (`0.0193`), so pruning it loses. No confirmation, no retuning, no slot.
- **Queued Session 15 candidates (`knowledge/43_hypotheses_heatflow_euler.md` & `knowledge/46_session14b_closeout.md`):**
  1. **`H38-3` (`= H33-2`) Multi-depth MT crustal conductance pipe alignment — ADD/corroboration arm.** DOI `10.5066/P9TWT2LU` (`Bedrosian et al., 2022`; ScienceBase `62979746d34ec53d276c113b`); all 5 GeoTIFFs runner byte-verified (`registry/external_pins.json`). Next step: add raster-clip step to `scripts/fetch_external_layers.py`.
  2. **`H38-4` (`= H37-5`) Cultural & constructional shoreline artifact-morphology suppression with budget-neutral `H38-1` reallocation.** Prunes zero-potential-field, ultra-linear 1 m LiDAR steps along constant `det_elev` contours and replaces them 1-for-1 with `H38-1` corroborated dots at fixed $N = 37{,}660\text{ px}$.
  3. **`H38-5` (`= H37-4 / H35-3`) 1 m 3DEP bare-earth DEM piercing-line and drainage-deflection neotectonics.** Competition `data/dem_links.json` (`716` USGS 3DEP tiles, free/public on `prd-tnm.s3.amazonaws.com`); requires Actions streaming bridge.
  4. **`H33-5` Phase-2 discovery budget — bounded ADD arm.** Policy-only Phase-2 optionality (`<= 600` px).
- **`H35-1` — EXECUTED Session 11, FROZEN GATE FAILED (seeds `230–234`, CLOSED).** Hydrothermal-discharge conjunction; credit/dot `0.013195` against `tau_live = 0.054852`, `1/5` seeds, mean ΔDTI `−0.001805`, and **below its own matched-count random control** (`0.023781`). Every pre-declared dose variant was at or below the control, so no tighter subset rescues it. Closed with no candidate TIFF and no weekly slot (§3.7.1, `knowledge/24_h35_1_result.md`, `evidence/h35_1_thermal_farfield.json`). **Do not re-run on a fresh decade and do not add another point-process layer without a new instrument.**
- **`H35-6` — ADJUDICATION, COMPLETED (seeds `235–239`).** Not a geological arm: a fresh-seed tie-break of the four candidate files under a frozen promotion rule. Promoted `8acb75e1f2cc` to the one-click slot (`+0.001761`, `5/5` seeds, `4/4` folds) after review found the previous primary dominated (§3.7.2, `knowledge/25_preregistration_H35-6_candidate_adjudication.md`, `evidence/h35_6_candidate_headtohead.json`).
- **`H33-1` — EXECUTED IN SESSION 10, FROZEN GATE FAILED (seeds `200–209`, CLOSED).** The only preregistered arm whose data had actually landed, so it was run first (§3.5). Mean paired ΔDTI `−0.003014`, `0/10` seeds, `0/4` folds, `fav` coverage `11.95%` against a `60%` precondition — **`0` of `6` criteria** (`evidence/h33_1_holdout.json`, `knowledge/21_result_H33-1_refuted_2026-10-03.md`). Do not re-run on a fresh decade, do not widen its radii, do not substitute another tendency field.
- **Standing consequence — pruning is closed as a family.** H31-1, H32-2 and H33-1 have now all failed the same way: the pixels they removed were worth `0.101–0.140` credit per FP against a `0.019292` break-even. **No further pruning arm should be preregistered.** The remaining budget goes to *addition* arms, validated on LOSFO (§3.2), never on the interleaved holdout.
- **Data-gate status (corrected this session).** `registry/irregularities.json` → `h33-external-byte-verify-pending` previously reported the two MT conductance probes as `FILE_NOT_LISTED` and `H33-2` as still gated; that text was **stale**. The facet-aware probe re-ran and the inventory committed at `2026-10-03T18:03:14Z` records **all four sources as `AVAILABILITY_FETCHED`**. All four hashes were promoted to `registry/external_pins.json`, so a later fetch is pin-checked rather than merely re-listed.
- **New this session — `interleaved-holdout-has-no-far-field-truth` (severity high).** The standing holdout cannot validate addition arms (§3.2). LOSFO is the instrument that fixes this; the first frozen addition-arm gate must run on LOSFO, requiring added dots to beat the measured base far-field credit/dot of `0.0465` and the inclusion threshold at the cell DTI, in `>= 3/4` folds and `>= 8/10` seeds.

---

## 6. Reproducibility & Verification Commands

```bash
# Session 14 (all local, no external requests; each writes JSON into evidence/):
#   far-field attribution of the H37-1 rule (seeds 215-219, ~7 min)
.venv/bin/python scripts/run_losfo_cover_variants.py --seeds 215-219 --out evidence/losfo_cover_variants.json
.venv/bin/python scripts/analyze_cover_variants.py           # independent re-reading of both LOSFO files
#   H38-1 radiometric gate (seeds 280-289, ~5 min) and its independent verification
GEMS_DATA_DIR=$PWD/data .venv/bin/python scripts/run_h38_1_holdout.py --seeds 280-289 --out evidence/h38_1_holdout.json
.venv/bin/python scripts/analyze_h38_1.py                    # max DTI recompute error must be 0.0
#   H38-1 far-field transfer test (seeds 220-224, ~13 min)
GEMS_DATA_DIR=$PWD/data .venv/bin/python scripts/run_losfo_rad_farfield.py --seeds 220-224 --out evidence/losfo_rad_farfield.json
#   the H38-1 artifact builder exists but was NOT executed (no transfer licence was earned)
# 1. Restore all 17 hash-pinned rasters/tables and build the 32-band prepared feature matrix
PYTHON=.venv/bin/python bash scripts/download_competition_data.sh

# 2. Fetch and invert the 24 SHA-256-authenticated live-scored submissions
.venv/bin/python scripts/fetch_scored_corpus.py
.venv/bin/python scripts/invert_live_scores.py --tomo
.venv/bin/python scripts/optimize_budget.py

# 3. Run the 4-fold spatially-blocked holdout validation on seeds 180-189 (H32-1 PASS)
.venv/bin/python scripts/run_h32_1_holdout.py --seeds 180-189

# 3a. Session 11: H35-1 hydrothermal-discharge ADDITION arm (seeds 230-234, ~8 min)
#     Executed: GATE FAILED 3/4 criteria -> arm CLOSED. Kept as the reproduction command.
GEMS_DATA_DIR=$PWD/data .venv/bin/python scripts/run_h35_1_thermal_farfield.py \
    --seeds 230-234 --out evidence/h35_1_thermal_farfield.json

# 3a-bis. Session 11: fresh-seed adjudication of the candidate ladder (seeds 235-239, ~2 min)
#     Executed with the frozen runner UNMODIFIED so the result is comparable with seeds 180-189.
GEMS_DATA_DIR=$PWD/data .venv/bin/python scripts/run_h32_1_holdout.py \
    --seeds 235-239 --out evidence/h35_6_candidate_headtohead.json

# 3b. H32-2 frozen screen on seeds 190-199 (executed session 9: GATE FAILED, arm closed)
.venv/bin/python scripts/run_h32_2_holdout.py --seeds 190-199

# 3c. Session 10: reachability frontier (identity-checked against metric.dti_binary)
.venv/bin/python scripts/reachability_frontier.py

# 3d. Session 10: leave-fault-system-out FAR-FIELD diagnostic (seeds 210-214, ~13 min)
#     Measurement instrument, NOT a promotion gate. Trains 2 detectors per seed (40 GBDT fits).
.venv/bin/python scripts/run_losfo_harness.py --seeds 210-214

# 3f. H34 live-anchored operating point (ladder, threshold, gamma closure) - ~35 s
.venv/bin/python scripts/analyze_operating_point_h34.py
# 3g. H34 preregistered holdout on seeds 220-229 - ~200 s. Result: GATE FAIL (direction
#     control). Arm closed; nothing is promoted from it.
.venv/bin/python scripts/run_h34_holdout.py --seeds 220-229
# 3e. Runner-bridge only: pin-verify and clip an official release to the footprint.
#     Cannot run in the agent sandbox (sciencebase.gov returns HTTP 000); runs on GitHub Actions.
python scripts/fetch_external_layers.py --derived all --external-pins registry/external_pins.json \
    --datasets paleo,probes,volcanics --out /tmp/gdr/out --pins /tmp/gdr/pins.json

# 3f. H33-1 frozen holdout (RUN 2026-10-03, seeds 200-209, REFUTED - do not re-run on a fresh
#     decade). Requires docs/data/sb_slip_tendency_in_footprint.json from 3e first; it aborts with
#     exit 2 if the clip schema lacks TS/TD. ~152 s for 10 seeds x 4 folds.
python scripts/run_h33_1_holdout.py --seeds 200-209 --out evidence/h33_1_holdout.json

# 3i. Session 13: exploratory packing passes (SPENT seeds only; they chose the variant, they do not gate it)
GEMS_DATA_DIR=$PWD/data .venv/bin/python scripts/explore_packing_h37.py     --seeds 181,185
GEMS_DATA_DIR=$PWD/data .venv/bin/python scripts/explore_packing_h37_v2.py  --seeds 181,185
GEMS_DATA_DIR=$PWD/data .venv/bin/python scripts/explore_packing_h37_v3.py  --seeds 181,185

# 3j. Session 13: H37-1 frozen gate (seeds 250-259, ~7.5 min). Preregistration knowledge/29 was committed
#     (424401b) BEFORE the decade was touched; the runner is unmodified since.
GEMS_DATA_DIR=$PWD/data .venv/bin/python scripts/run_h37_1_holdout.py --seeds 250-259
#     Executed: ALL FIVE CRITERIA PASSED -> cover_prob_r1 +0.007289 vs d=2.8 (+0.004614 over H36-1),
#     10/10 seeds, 4/4 folds, content-blind matched-N control -0.044684, integrity clean.
GEMS_DATA_DIR=$PWD/data .venv/bin/python scripts/build_h37_1_submissions.py

# 3k. Session 13b: H37-1 far-field falsification test (LOSFO decade 210-214, ~12.6 min). The preregistration
#     knowledge/32 is committed at the freeze commit 7e637c9 BEFORE the run; base arms reproduce the stored
#     diagnostic exactly. Result: F1 FAIL, F3 FAIL -> the interleaved gain does not transfer; the artifact
#     is demoted and the 0.278-0.286 projection withdrawn (knowledge/33).
GEMS_DATA_DIR=$PWD/data .venv/bin/python scripts/run_losfo_harness.py --seeds 210-214 --packing-variants \
    --out evidence/losfo_packing_farfield.json

# 3l. Session 13c: H37-3 Euler SI-0 depth-coherence licence, far-field test (LOSFO decade 260-264, ~13 min).
#     Preregistration knowledge/34 froze the rule, the arm and the criteria at commit 0788eec BEFORE the run.
#     Result: C1 FAIL (13/20 cells), C2 FAIL (0.031157 credit/dot vs the 0.0548 live bar), C3 PASS (1.65x its
#     matched random control), C4 PASS -> refuted as promotable, mechanism real (knowledge/35).
GEMS_DATA_DIR=$PWD/data .venv/bin/python scripts/run_losfo_harness.py --seeds 260-264 \
    --euler-licence evidence/h31_1_euler_clusters.csv --out evidence/losfo_h37_3_licence.json

# 3m. Session 14a: H36-1 LOSFO far-field verification (F1-F4 ALL PASS) + H38-1/H38-2 multi-physics
#     corroboration on LOSFO far-field seeds 265-269 (20 paired cells, ~8.8 min).
#     Preregistration knowledge/38 was committed at ff85e30 BEFORE seeds 265-269 were touched.
GEMS_DATA_DIR=$PWD/data .venv/bin/python scripts/run_losfo_harness.py --seeds 265-269 \
    --h36-1-dose --h38-corroboration --out evidence/losfo_session14_h36_1_and_h38.json

# 3n. Session 14b: H38-1 10-seed interleaved spatial-CV holdout on seeds 270-279 (40 paired cells, ~12.5 min)
#     and companion submission builder (37,860 px, content ID 56a9f473edc7).
GEMS_DATA_DIR=$PWD/data .venv/bin/python scripts/run_h38_1_interleaved_holdout.py \
    --seeds 270-279 --out evidence/h38_1_interleaved_holdout.json
GEMS_DATA_DIR=$PWD/data .venv/bin/python scripts/build_h38_1_hf_euler_submissions.py

# 3h. Session 12: H36-1 packing-rung re-pack + flank prune, frozen 10-seed gate (seeds 240-249, ~105 s)
#     Preregistration knowledge/26 was committed (aaa659c) BEFORE the run; runner frozen at that commit.
GEMS_DATA_DIR=$PWD/data .venv/bin/python scripts/run_h36_1_holdout.py \
    --seeds 240-249 --out evidence/h36_1_holdout.json
#     Executed: GATE PASSED -> rung30_blind_r1 +0.002599 (10/10 seeds, 4/4 folds), PROMOTE.
GEMS_DATA_DIR=$PWD/data .venv/bin/python scripts/build_h36_1_submissions.py

# 4. Build and audit all submission GeoTIFFs, seed ledgers, and static GitHub Pages HTML
.venv/bin/python scripts/build_h32_1_submissions.py
.venv/bin/python scripts/build_h36_1_submissions.py
.venv/bin/python scripts/verify_downloads.py
.venv/bin/python scripts/audit_euler_seed_reuse.py
.venv/bin/python scripts/build_site.py
.venv/bin/python -m pytest -q
```
