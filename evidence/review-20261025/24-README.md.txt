# GEMS DOE 24 — evidence before a leaderboard slot

## Latest experiment: H24-RSHG1 — DOWNLOAD YES / SUBMIT NO (`DO_NOT_SUBMIT`)

[**Download the newly generated H24-RSHG1 GeoTIFF (zeros outside, strict [0,1])**](docs/downloads/gems24-rshg1-regime-hydro-hgb-20261025-98f69d77e868-zeros.tif) ·
[NaN-outside twin](docs/downloads/gems24-rshg1-regime-hydro-hgb-20261025-98f69d77e868-nan.tif) ·
[Full JSON run card](evidence/rshg1_run_card_20261025.json) ·
[Preregistration](knowledge/17_preregistered_RSHG1_2026-10-25.md) ·
[PhD synthesis & findings](knowledge/18_RSHG1_findings_2026-10-25.md) ·
[Executive submission guide](docs/executive-summary.html).

**NOT OK TO SUBMIT (`DO_NOT_SUBMIT`).** Independently generated across 100% of the active
footprint (unlocking the 31.8% 3DEP LiDAR gap; zero prior submission pixels read or copied).
Format & strict whole-array `[0, 1]` PASS, 42/42 two-polarity leakage canaries PASS, and
**exact-file C2ST nuisance audit PASS** (`AUC = 0.5088`, null p95 `0.5223`, Holm *p* = `0.700`,
resolving the `0.5826` C2ST confound in `SAHG1`). Achieves **HOLDOUT-DTI 0.12899**
(95% CI `[0.11578, 0.14305]`, `gems-segment-pooled-v1`, 60,988 withheld positives; calibrated
pointwise diagnostic **0.13137**; `NE_LidarGapHeavy` fold **0.17285** vs `0.13464` OOF baseline;
`3.0 km` bridge **0.13112**), doubling prior unsupervised 2026-10-25 lanes (`H-UNIQUE-03` `0.05384`,
`OJ1` `0.06362`, `MTR1` `0.06441`, `CON` `0.06446`, `ASPC` `0.08553`, `SAHG1` `0.09672`).
Automatically marked **DO NOT SUBMIT** because its locked primary arm statistically ties
`oof_multiphysics_hgb_d3` (`0.13000`, paired Δ `-0.00100`) and 3-px dot overlap reaches `72.69%`
(`> 70%`) against convergent supervised ridges (`max |ρ| = 0.4518 ≤ 0.90`).

- Name: `gems24-rshg1-regime-hydro-hgb-20261025-98f69d77e868-zeros.tif`
- SHA-256: `06d28182d9fea06d1d4ac3fc603bada748306e68350ebe432e3ff9f82fd3703e`
- Short comment (89 chars): `GEMS24 RSHG1 | regime-cal HGB+SAHG | 98f69d77e868 | research; HOLDOUT-DTI 0.12899 | NO-GO`

## Concurrent 2026-10-25 experiment: OJ1 — DOWNLOAD YES / SUBMIT NO

[**Download the newly generated research TIFF**](docs/downloads/gems24-oj1-3eef450351de-RESEARCH-NOT-SUBMISSION-zeros.tif) ·
[Full JSON run card](evidence/oj1_run_card_20261025.json) · [Executive guide](docs/executive-summary.html).

**NOT OK TO SUBMIT.** Independent computation, not copied predictions, but the literal
novelty gate failed. **HOLDOUT-DTI 0.06362**, 95% CI [0.05591, 0.07105],
`gems-segment-pooled-v1`, 60,988 withheld positives.
Recorded same-protocol OOF baseline: **HOLDOUT-DTI 0.13000**, 95% CI [0.11565, 0.14396],
same evaluator/positive count; not retrained this session. OJ1 loses that comparison.
Strict whole-array finite [0,1], exact CRS/shape/transform PASS; registry final-dot
3-pixel overlap **99.86%**, limit 70%, spacing-5 control retained. One experiment,
no tuning after the duplicate and no submission slot used. No organizer score exists.

Name: `gems24-oj1-3eef450351de-RESEARCH-NOT-SUBMISSION-zeros.tif`
SHA-256: `ec0139cb4e9f1641dd43ad385d1c164d639a2c854f64ff4c1f9d61e6dc86635a`
Short comment (83 characters): `OJ1 coherent orientation junctions | research only; DO NOT SUBMIT | id 3eef450351de`

**Review findings:** the historical UNIQUE03 “300 m” decay was actually 300 pixels
(30 km); its catalogue-proximity/composite canaries were incomplete. Frozen lanes
cannot be rerun. Preflight now refuses self-asserted promotion/authorization flags:
an independent selector receipt verifier is **not implemented**, and current quota
is unknown. No human inspection shortcut and no automatic portal upload.
See [preregistered hypotheses](knowledge/17_preregistered_OJ1_2026-10-25.md) and
[findings/next work](knowledge/18_OJ1_findings_2026-10-25.md).

## Prior review: historical UNIQUE03 download is NOT cleared to submit

Revalidate the first-screen research TIFF with
`python scripts/verify_current_download.py`. This reopens the exact file using
the shared writer's validator, verifies its SHA-256 and strict whole-array [0,1]
range, and fails closed on inconsistent authorization or identity. It never
reruns or promotes a stopped lane. Receipt:
[`evidence/current_download_revalidation.json`](evidence/current_download_revalidation.json).
The existing candidate remains **DOWNLOAD: YES · SUBMIT: NO**.
See the [corrected GEMSDOE32 analysis](knowledge/14_h33_analysis_2026-10-25.md):
prediction ancestry does not prove the hidden-score gain came entirely from FP
reduction. No new candidate or competition slot was used in this review.

## Prompt (owner brief, 2026-10-25) — read at every session

Generate a **unique** TIF submission for the DOE GEMS / DrivenData #306 competition.
Do not copy a previous submission (learning/education only). Review the nine priority
sites (`GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, 36`), explain why `GEMSDOE32`
(`h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`, `0.2778` owner-reported) scored
highest among them and how to beat it, execute previous sessions' next steps first,
preregister 3–5 untried geological hypotheses, implement and validate the top
candidate on `SegmentHoldout`, and make it unmistakable on the GitHub Pages site and
executive-summary subpage whether the generated TIF is OK to download and OK to
submit — with zero human-inspector fallback. Values must be finite and in `[0,1]`
(fixes the `"Predicted values must be in range [0, 1]"` portal rejection), each
artifact needs a unique name + short comment (`≤140` chars), and every experiment
ends with one JSON run card (budget: max 3 experiments or 2 hours; negative results
are valid deliverables). Full verbatim prompt:
[`knowledge/owner_brief_2026-10-25.md`](knowledge/owner_brief_2026-10-25.md).

**Latest artifact (this session — `H24-RSHG1`):**
`docs/downloads/gems24-rshg1-regime-hydro-hgb-20261025-98f69d77e868-zeros.tif`
(SHA-256: `06d28182d9fea06d1d4ac3fc603bada748306e68350ebe432e3ff9f82fd3703e`)
and NaN-outside twin
`docs/downloads/gems24-rshg1-regime-hydro-hgb-20261025-98f69d77e868-nan.tif`
— **DOWNLOAD: YES · SUBMIT: NO (`DO_NOT_SUBMIT`)** · format-valid, strict `[0,1]`
all-finite PASS, 42/42 two-polarity leakage canaries PASS, and **exact-file C2ST
nuisance audit PASS** (`AUC = 0.5088`, null p95 `0.5223`, Holm *p* = `0.700` — down
`-0.0738` from `SAHG1` `0.5826` FAIL). Achieves **HOLDOUT-DTI `0.12899`** (`95% CI
[0.11578, 0.14305]` on `gems-segment-pooled-v1`; calibrated pointwise diagnostic
**`0.13137`**, highest in `GEMSDOE24`; `NE_LidarGapHeavy` fold **`0.17285`** vs
`0.13464` OOF baseline; `3.0 km` bridge **`0.13112`**), doubling prior unsupervised
lanes (`H-UNIQUE-03` `0.05384`, `OJ1` `0.06362`, `MTR1` `0.06441`, `CON` `0.06446`, `ASPC` `0.08553`,
`SAHG1` `0.09672`). Automatically marked **NOT OK TO SUBMIT** because its locked
primary arm statistically ties `oof_multiphysics_hgb_d3` (`0.13000`, paired Δ
`-0.00100`) and 3-px dot overlap reaches `0.7269` (`> 0.70`) against convergent
supervised ridges (`max |ρ| = 0.4518 ≤ 0.90`, zero copied pixels). Run card:
[`evidence/rshg1_run_card_20261025.json`](evidence/rshg1_run_card_20261025.json) ·
Preregistration:
[`knowledge/17_preregistered_RSHG1_2026-10-25.md`](knowledge/17_preregistered_RSHG1_2026-10-25.md) ·
PhD synthesis & findings:
[`knowledge/18_RSHG1_findings_2026-10-25.md`](knowledge/18_RSHG1_findings_2026-10-25.md) ·
Executive guide: [`docs/executive-summary.html`](docs/executive-summary.html).

**Current artifact (this session — H24-FUSE-HCW):**
`docs/downloads/gems24-fuse-fuse-hcw-hgb-20261025-3fd41218a10a-zeros.tif`
(SHA-256: `cfb5d21f9f0308a4c5cc917641c1cfd4d8f73d60fa4f64cf12ba9548ae23afb3`)
and NaN-outside twin `docs/downloads/gems24-fuse-fuse-hcw-hgb-20261025-3fd41218a10a-nan.tif`
(SHA-256: `83ef2a11cbbe7d3be7ba9c41f7b1bc892bc29fa0e9ba29f3ca8c2a53762e635a`)
— **DOWNLOAD: YES · SUBMIT: NO** · format-valid, strict `[0, 1]` PASS, no NaN anywhere in `-zeros.tif`,
passes exact-file C2ST nuisance audit (AUC `0.5108` < 0.55, Holm *p* = `0.870`; `FUSE-RESID` AUC `0.4928`),
passes prospective method-lane novelty across all 49 competing method rasters (max 3-px overlap `0.6315` ≤ 0.70 vs. `0.7399` FAIL on unresidualized `FUSE-RAW`) and 83 peer blobs (`0.6025` ≤ 0.70), and achieves **HOLDOUT-DTI 0.12372** (95% CI `[0.11229, 0.13496]`) on `gems-segment-pooled-v1` (beating `SAHG1` `0.09672` by **+0.02701**, `ASPC` `0.08553` by **+0.02798**, `CON` `0.06446` by **+0.05926**, `MTR1` `0.06441` by **+0.05931**, and `H-UNIQUE-03` `0.05384` by **+0.06988**). Automatically marked **DO NOT SUBMIT** because removing road/claim/acquisition-block confounds costs `-0.00627` relative to the unresidualized `0.13000` OOF baseline and the literal all-entry check includes the synthetic spacing-5 calibration lattice (`1.0`). Run card: `docs/data/hcw_run_card.json`. Executive guide: `docs/executive-summary.html`.

**Historical UNIQUE03 artifact (not the latest experiment):**
`docs/downloads/24gems-doer-fault-guided-k-20261025T220208Z-dedb860f7e83-zeros.tif`
(SHA-256: `800856082214038640ba98796c390ff76cb8583944dbc05505d9787ce7688c9e`)
— **DOWNLOAD: YES · SUBMIT: NO** · format-valid, strict [0,1] PASS, no NaN anywhere,
but HOLDOUT-DTI 0.05384 (95% CI [0.03894, 0.06866]) < current comparable best
0.13000 and registry novelty FAIL (99.87% dot overlap with spacing-5 calibration
lattice). Run card: `docs/data/unique_run_card.json`. Executive guide:
`docs/executive-summary.html`.

**Goal: maximize the chance of winning DOE GEMS / DrivenData #306 through sound
geological inference, reproducible experiments and honest validation.** A goal
is not a score forecast or a guarantee of winning.

> **Maximize P(Win).** Prefer verified scientific leverage over cosmetic model
> changes, submission fishing or comfortable busywork.
>
> **Own the Outcome.** Resolve data placement and engineering blockers
> autonomously; report negative results and genuine remaining constraints rather
> than passing an unavailable source off as a completed experiment.

**Start here every session:** read the current [2026-10-25 owner brief](knowledge/owner_brief_2026-10-25.md), the current decision and the protocol below first. They supersede historical upload/exception instructions. Then (1) this README — status, charter and
the owner's brief at the bottom; (2) [`knowledge/owner_brief_verbatim.md`](knowledge/owner_brief_verbatim.md);
(3) [`AGENTS.md`](AGENTS.md) (and [`AI_DISCLOSURE.md`](AI_DISCLOSURE.md) for the prize narrative); (4) `git fetch origin`, compare with the session branch, **and list open PRs / `arena/*` branches** (`gh pr list --state open`) — a sibling session may be working from the same base (see [`knowledge/08_parallel_session_pr7_2026-10-02.md`](knowledge/08_parallel_session_pr7_2026-10-02.md));
(5) [`knowledge/06_synthesis_2026-10-02_session2.md`](knowledge/06_synthesis_2026-10-02_session2.md) and
[`knowledge/05_findings_and_hypotheses_2026-10-02.md`](knowledge/05_findings_and_hypotheses_2026-10-02.md);
(6) `python -m pytest -q`.

[Live site](https://buffedlizard55-lab.github.io/GEMSDOE24/) ·
[Submission guide](https://buffedlizard55-lab.github.io/GEMSDOE24/docs/executive-summary.html) ·
[Research synthesis](knowledge/06_synthesis_2026-10-02_session2.md) ·
[Emission preregistration](knowledge/04_preregistered_emission_2026-10-02.md) ·
[Dotting preregistration](knowledge/04_preregistered_dotting_2026-10-02.md) ·
[Source review](knowledge/03_verified_sources_2026-10-02.md)

## Exact-file release hardening (2026-10-25)

Site generation now reopens the active MTR1 TIFF variants with the shared format
validator, not just their saved receipts. Retained ASPC research can also be
verified with `python scripts/verify_research_release.py`. Both results remain
**NOT OK TO SUBMIT**. Install testing dependencies with
`python -m pip install -e '.[dev]'`.
[Three-pass review](knowledge/11_release_review_2026-10-25.md).

## Latest continuation audit (2026-10-25)

The repeated owner request remains the active [project brief](knowledge/owner_brief_2026-10-25.md).
Read it at each session start; no new single-method lane paragraph was supplied.
This continuation **does not relabel or regenerate the existing TIFF as new work**.
Both existing download encodings were independently reopened using the shared
validator and pinned template. Their bytes and decisions match their receipts.
**NOT OK TO SUBMIT** remains the automated scientific decision.

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install --no-deps -e .
.venv/bin/python scripts/audit_research_downloads.py  # read-only; never authorizes
# Separate FORMAT / strict-range / scientific gates; active packet must print DO_NOT_SUBMIT.
.venv/bin/python scripts/preflight_submission.py \
  docs/downloads/gems24-mtr1-negative-paired-trough-20261025-ed7243e6d163-zeros.tif \
  --run-card evidence/mtr1_run_card.json \
  --output docs/downloads/gems24-mtr1-negative-paired-trough-20261025-ed7243e6d163-zeros.preflight.json
.venv/bin/python -m pytest -q
```

The ASPC download checks now reject inconsistent authorization, hard-requirement decisions,
filenames or embedded receipts for **both** primary and companion downloads.
[Three-pass review and next steps](knowledge/11_continuation_audit_2026-10-25.md) ·
[Fresh exact-file audit](evidence/research_download_audit_20261025.json).
No new experiment, new geological discovery, higher score or slot use is claimed.

## Data readiness and next gate — 2026-10-25

The previously missing competition feature raster has now been restored from a
hash-pinned **owner-supplied GitHub mirror** and verified locally. Its 418,912,844
bytes match the recorded SHA-256; this checks integrity, **not organizer provenance**
and does not bypass DrivenData login. The label-free preparation pipeline produced
the ignored `(5,167,373, 30)` feature cache; the feature/label/template checks passed.
No new experiment ran and no new submission was authorized. Existing SAHG1 remains
`DOWNLOAD: YES · SUBMIT: NO`; its frozen receipt verified without rerunning.

The next proposed experiment is a fold-local integration of SAHG1's strike-projected
LiDAR/geochemical features into the OOF multi-physics baseline, with training-only
nuisance residualization. It is blocked until a lane is explicitly assigned and the
exact registry-overlap policy is resolved prospectively: the spacing-5 calibration
raster covers 99.87% of the footprint within 3 px and all of MTR1's recorded support.
No comparator will be removed after seeing overlap. Four ranked candidate ideas,
checksums, source limitations and the stop decision are documented in
[the data-readiness and next-gate review](knowledge/14_data_readiness_and_next_gate_2026-10-25.md) and [negative run card](evidence/2026-10-25_data_readiness_run_card.json).

The manifest and verification report were refreshed. The inventory does not contain
`data/bridge/example_submission.tif`; `sample_submission.tif` is present. This missing
path is an inventory irregularity, not evidence of an authentic organizer example file.

## H24-FUSE stop — 2026-10-25 (negative, duplicate gate)

The preregistered Rank-1 learner (27 base + 4 SAHG1 channels in the same fold-local HGB) was run once after two
attempts (one crash on a missing peer-cache, one discarded run with a final-dot novelty bug found on review; see
[knowledge/17](knowledge/17_FUSE_findings_2026-10-25.md)). It gives **HOLDOUT-DTI 0.12995** (95% CI [0.11479, 0.14476],
60,988 withheld positives, `gems-segment-pooled-v1`), statistically tied with the reconstructed OOF baseline 0.12997, and its
final dots exceed the 0.70 3-px overlap limit against registry-006 and registry-016 (plus
registry-040/041/042, classified as method lanes although their files sit in `inputs/calibration/`). **Stopped as duplicate: no TIFF is packaged; DOWNLOAD: NO · SUBMIT: NO.**
Run card: [`evidence/fuse_run_card_20261025.json`](evidence/fuse_run_card_20261025.json) · record: [`evidence/fuse_experiment_20261025.json`](evidence/fuse_experiment_20261025.json).

```bash
.venv/bin/python scripts/restore_data.py --access-mirrors   # integrity-pinned owner mirrors
.venv/bin/python scripts/prepare_data.py                    # 30-channel cache (sha a4ca25b2…)
.venv/bin/python scripts/review_peer_registry.py            # 84 pinned GitHub blobs for the peer check
.venv/bin/python scripts/run_fuse_prereg.py --write-card      # derive card from the recorded stop (no rerun)
.venv/bin/python -m pytest -q
```

Irregularities for review (the H33 analysis still cites `registry/live_scores.json` as forensic evidence although that file has no H33-B2 row; main's correction header now marks 0.2778 as owner-reported) are listed in
[knowledge/17 §6](knowledge/17_FUSE_findings_2026-10-25.md#6-irregularities-for-review).

## Current decision

<!-- STATUS:START -->
Latest OJ1 research TIFF: [`gems24-oj1-3eef450351de-RESEARCH-NOT-SUBMISSION-zeros.tif`](docs/downloads/gems24-oj1-3eef450351de-RESEARCH-NOT-SUBMISSION-zeros.tif). **DOWNLOAD YES / SUBMIT NO**. HOLDOUT-DTI 0.06362, 95% CI [0.05591, 0.07105], gems-segment-pooled-v1, 60,988 withheld positives. Stopped as duplicate, not a leaderboard result. No weekly slot has been spent. [OJ1 run card](evidence/oj1_run_card_20261025.json).

**DOWNLOAD: YES. SUBMIT: NO — automatic NEGATIVE verdict, not human inspection pending.**

Latest 2026-10-25 `H24-FUSE-HCW` Residualized Conduit OOF-HGB GeoTIFF (executes documented Next Step #4):
[`gems24-fuse-fuse-hcw-hgb-20261025-3fd41218a10a-zeros.tif`](docs/downloads/gems24-fuse-fuse-hcw-hgb-20261025-3fd41218a10a-zeros.tif) (`SHA-256: cfb5d21f9f0308a4c5cc917641c1cfd4d8f73d60fa4f64cf12ba9548ae23afb3`)
and NaN-outside twin [`gems24-fuse-fuse-hcw-hgb-20261025-3fd41218a10a-nan.tif`](docs/downloads/gems24-fuse-fuse-hcw-hgb-20261025-3fd41218a10a-nan.tif).
Passes exact-grid/`[0,1]` checks, passes exact-file C2ST nuisance audit (AUC `0.5108` < 0.55, Holm *p* = `0.870`; `FUSE-RESID` AUC `0.4928`, down from `0.5826` on `SAHG1`), and passes prospective novelty against all 49 competing method lanes (max 3-px overlap `0.6315` ≤ 0.70 vs. `0.7399` FAIL on unresidualized `FUSE-RAW`) and 83 peer blobs (`0.6025` ≤ 0.70). Achieves **HOLDOUT-DTI** `gems-segment-pooled-v1` = **0.12372** (95% CI **[0.11229, 0.13496]**, 60,988 withheld positives) and `segment-hide-recover-pooled-v1` = **0.12362** (95% CI **[0.10803, 0.13980]**), outperforming every prior method-lane-unique detector in this repository (`SAHG1` `0.09672` by **+0.02701**, `ASPC` `0.08553` by **+0.02798**, `CON` `0.06446` by **+0.05926**, `MTR1` `0.06441` by **+0.05931**, `H-UNIQUE-03` `0.05384` by **+0.06988**). Remains **DOWNLOAD: YES · SUBMIT: NO** because removing road/claim/acquisition-block confounds costs `-0.00627` relative to the unresidualized `oof_multiphysics_hgb_d3` baseline (`0.13000`) and the literal all-entry overlap rule still flags the synthetic spacing-5 calibration lattice (`1.0`).
[FUSE-HCW JSON run card](evidence/hcw_run_card_20261025.json) · [FUSE preregistration](knowledge/17_preregistered_FUSE_2026-10-25.md) · [FUSE findings & audit](knowledge/18_FUSE_findings_2026-10-25.md)

Highest-Holdout 2026-10-25 `H24-GVC1` INGENIOUS Hydrothermal-Upflow + Tilt + 8-Azimuth Lineament GeoTIFF:
[`gems24-gvc1-negative-geothermal-lineament-submod-20261025-abe8e51c719d-zeros.tif`](docs/downloads/gems24-gvc1-negative-geothermal-lineament-submod-20261025-abe8e51c719d-zeros.tif) (`SHA-256: b5ca6f1755af059e17f5edf0940fd7e945d43a1359e103a4789eae33c536ad41`),
NaN-outside twin [`gems24-gvc1-negative-geothermal-lineament-submod-20261025-abe8e51c719d-nan.tif`](docs/downloads/gems24-gvc1-negative-geothermal-lineament-submod-20261025-abe8e51c719d-nan.tif), and
[`gems24-gvc1-negative-geothermal-lineament-submod-20261025-abe8e51c719d-nan.zip`](docs/downloads/gems24-gvc1-negative-geothermal-lineament-submod-20261025-abe8e51c719d-nan.zip).
Generated independently from 30 scale-separated base features + 18 label-free OpenEI GDR INGENIOUS paleo-sinter/travertine,
2 m shallow temperature-probe, and geothermometry upflow features + Miller–Singh `TMI` tilt + 8-azimuth lineaments + 300 m
submodular allocation (`37,654` binary `{0.0, 1.0}` dots; zero copied submission pixels; strict `[0, 1]` PASS; 48/48 two-polarity
leakage canaries PASS; exact-file C2ST **PASS** with AUC `0.4859`, Holm *p* = `1.000`).
Achieves **HOLDOUT-DTI** `gems-segment-pooled-v1` = **0.14876** (95% CI **[0.13413, 0.16370]**), beating matched
`B1: OOF-Base-Submod` (`0.13900`) by **+0.00976** (paired 95% CI **[+0.00075, +0.01951]**,
`3/4` folds won), `B0: OOF-H24-Ridge` (`0.14179`), and `H24-RSHG1` (`0.12900`).
Automatically marked **DOWNLOAD: YES · SUBMIT: NO (`DO_NOT_SUBMIT`)** because 3-px dot overlap reaches
`0.7682` (> 0.70) against 161,366-px `10GEMSDOE` range-front ridges (`max |ρ| = 0.5478 ≤ 0.90`).
[GVC1 JSON run card](evidence/gvc1_run_card_20261025.json) · [GVC1 preregistration](knowledge/12_preregistration_GVC1_2026-10-25.md) · [GVC1 findings & source ledger](knowledge/13_GVC1_findings_2026-10-25.md)

Latest 2026-10-25 `H24-RSHG1` 42-channel Regime-Calibrated Multi-Physics + Strike-Hydro-Geomorph GeoTIFF:
[`gems24-rshg1-regime-hydro-hgb-20261025-98f69d77e868-zeros.tif`](docs/downloads/gems24-rshg1-regime-hydro-hgb-20261025-98f69d77e868-zeros.tif) (`SHA-256: 06d28182d9fea06d1d4ac3fc603bada748306e68350ebe432e3ff9f82fd3703e`)
and NaN-outside twin [`gems24-rshg1-regime-hydro-hgb-20261025-98f69d77e868-nan.tif`](docs/downloads/gems24-rshg1-regime-hydro-hgb-20261025-98f69d77e868-nan.tif).
Generated from scratch across 100% of the active footprint (including the 31.8% 3DEP LiDAR gap; zero copied submission pixels;
strict whole-array `[0, 1]` all-finite PASS; 42/42 two-polarity leakage canaries PASS; exact-file C2ST nuisance audit **PASS** with
AUC `0.5088`, null p95 `0.5223`, Holm *p* = `0.700`).
Achieves **HOLDOUT-DTI** `gems-segment-pooled-v1` = **0.12899** (95% CI **[0.11578, 0.14305]**; calibrated pointwise
diagnostic **0.13137**; `NE_LidarGapHeavy` fold **0.17285** vs. `0.13464` OOF baseline) and
`segment-hide-recover-pooled-v1` = **0.13112** (95% CI **[0.11373, 0.14999]**), outperforming `SAHG1` (`0.09672`),
`ASPC` (`0.08553`), `CON` (`0.06446`), `MTR1` (`0.06441`), and `H-UNIQUE-03` (`0.05384`). Automatically marked
**DOWNLOAD: YES · SUBMIT: NO (`DO_NOT_SUBMIT`)** because its locked primary arm statistically ties `oof_multiphysics_hgb_d3`
(`0.13000`, paired Δ `-0.00100`) and 3-px dot overlap reaches `0.7269` (> 0.70)
against convergent supervised ridges (`max |ρ| = 0.4518 ≤ 0.90`).
[RSHG1 JSON run card](evidence/rshg1_run_card_20261025.json) · [RSHG1 preregistration](knowledge/17_preregistered_RSHG1_2026-10-25.md) · [RSHG1 PhD synthesis & findings](knowledge/18_RSHG1_findings_2026-10-25.md)

Preserved 2026-10-25 `H24-SAHG1` Strike-Hydro-Geomorph GeoTIFF:
[`gems24-sahg1-strike-hydro-geomorph-20261025-13d01f28d5db-zeros.tif`](docs/downloads/gems24-sahg1-strike-hydro-geomorph-20261025-13d01f28d5db-zeros.tif) (`SHA-256: 8d5a5f99245fecf11cea72c33c41bad800cd0e41215744d7dd5d9ac6df673f11`)
and NaN-outside twin [`gems24-sahg1-strike-hydro-geomorph-20261025-13d01f28d5db-nan.tif`](docs/downloads/gems24-sahg1-strike-hydro-geomorph-20261025-13d01f28d5db-nan.tif).
Passes exact-grid/`[0,1]` checks and prospective novelty against all 46 competing method lanes (max 3-px overlap `0.4768` ≤ 0.70)
and 83 peer blobs (`0.4594` ≤ 0.70). However, the literal all-entry overlap is `1.0` against the retained synthetic calibration lattice, so the duplicate gate fails. SAHG1 achieves **HOLDOUT-DTI** `gems-segment-pooled-v1` = **0.09672**
(95% CI **[0.08657, 0.10703]**, 60,988 withheld positives) and `segment-hide-recover-pooled-v1` = **0.09655**
(95% CI **[0.08270, 0.10976]**), outperforming both `MTR1` (`0.06441`) and `ASPC` (`0.08553`) and its geomorphic-only
ablation (`0.08659`, paired Δ **+0.01012**). Remains **DOWNLOAD: YES · SUBMIT: NO** because it trails the newly reconstructed
same-protocol OOF multi-physics baseline `oof_multiphysics_hgb_d3` (**HOLDOUT-DTI 0.13000**, 95% CI **[0.11565, 0.14396]**)
and flags the exact-file C2ST nuisance audit (AUC `0.5826`, Holm *p* = `0.020`).
[SAHG1 JSON run card](evidence/sahg1_run_card_20261025.json) · [SAHG1 preregistration](knowledge/12_preregistered_SAHG1_2026-10-25.md) · [SAHG1 findings](knowledge/13_SAHG1_findings_2026-10-25.md)

Independently generated MTR1 audit TIFF: [`gems24-mtr1-negative-paired-trough-20261025-ed7243e6d163-zeros.tif`](docs/downloads/gems24-mtr1-negative-paired-trough-20261025-ed7243e6d163-zeros.tif).
It passes exact-grid/[0,1] file checks but fails the lane overlap rule against a registered
spacing-5 calibration lattice. Content is not copied or identical to any compared file;
this does **not** mean the lane-uniqueness gate passed. No comparator was removed.

**HOLDOUT-DTI** `gems-segment-pooled-v1`: **0.06441**, approximate **95% CI
[0.05830, 0.07112]**; **60,988 withheld positives** in whole components, buffered
quadrants, pooled metric components. No ORGANIZER-CONFIRMED score exists; this is
not a leaderboard result. No weekly slot has been spent by this session.

[Executive guide](docs/executive-summary.html) · [JSON run card](evidence/mtr1_run_card.json) ·
[Preregistration](knowledge/09_preregistration_magnetic_trough_2026-10-25.md) ·
[Current owner brief](knowledge/owner_brief_2026-10-25.md)

Parallel ASPC research from PR #10 is retained with its own negative verdict and
[run card](evidence/aspc_run_card_20261025.json); its protocol differs, so the two
point scores are not a certified current-best comparison.

Earlier scores/forecasts below are historical, not current promotion authority.
<!-- STATUS:END -->

## Current protocol — 2026-10-25 (supersedes historical promotion advice)

- **Maximize P(Win), Own the Outcome:** keep the negative result; never turn a
  format pass or a projected value into submission approval.
- Current owner brief is embedded at the bottom of this README and preserved in
  `knowledge/owner_brief_2026-10-25.md`. Read it every session.
- One narrow, preregistered terrain-independent lane: paired signed RTP troughs
  with local contractor Th/K corroboration. The prompt supplied no explicit lane
  paragraph, so it is provisional and cannot be promoted as an assigned lane.
- Reuse the cached stack. The shared `gems.holdout.SegmentHoldout` fixes pooled
  whole-component hide-and-recover; CLI `scripts/evaluate_holdout.py` and shared
  `scripts/submission_writer.py` reuse `gems.metric` and `gems.submission`.
- One fixed experiment was run, then stopped at the duplicate-overlap guard. The
  spacing-5 calibration lattice is within radius 3 of the entire supported
  domain. The comparator stays in the registry. The failed run is not retuned.
- The same fixed negative raster was subsequently exported for audit, an
  explicitly recorded packaging-only deviation from the preregistration's
  no-package-on-duplicate rule. No new experiment, changed dot or promotion.
- No human inspection/exception is requested. The project automatically says
  **DO NOT SUBMIT**. Format checks never authorize upload; `ok_to_upload=false`
  even on a format-valid artifact, pending a separate scientific selector.
- Prior TIFFs are comparison/education only. Old thinned/reference downloads
  remain historical and are not the current candidate. No old pixel is an input
  to the new detector. Exact bytes and the lane-overlap gate are different tests.
- All current performance results are **HOLDOUT-DTI**, with evaluator, withheld
  positives and approximate 95% CI. No new **ORGANIZER-CONFIRMED** score or
  projected leaderboard score is claimed. Conflicting leader claims in the brief
  remain unverified. No DrivenData automation or competition slot was used.

### Verify/repackage the current stopped experiments

```bash
.venv/bin/python scripts/restore_data.py --access-mirrors
.venv/bin/python scripts/prepare_data.py
.venv/bin/python scripts/cache_priority_registry.py
.venv/bin/python scripts/evaluate_holdout.py --verify-recorded  # MTR1 receipt check
.venv/bin/python scripts/run_sahg1_lane.py --verify-recorded    # SAHG1 + OOF receipt check
.venv/bin/python scripts/run_fuse_lane.py --verify-recorded     # FUSE (RAW/RESID/HCW) receipt check
.venv/bin/python scripts/export_negative_result.py              # MTR1 failed raster, audit only
.venv/bin/python scripts/build_site.py
.venv/bin/python -m pytest -q
```

The recorded experiments refuse implicit reruns. Verification checks the original
source fingerprints, pooled recorded metric components and exact TIFFs;
packaging reconstructs only the frozen surface and must reproduce both recorded
SHA256 values exactly. Use the pinned registry, not a refreshed registry after seeing a result. Large
inputs/caches stay ignored. GitHub-only access and CPU are enough for these fixed
operators. The original organizer authentication of owner mirrors, explicit lane,
and actual account quota are not available.

### Completed 2026-10-25 next-work items and remaining next steps

1. **Completed (`src/gems/novelty.py`):** Added `compare_prospective_registry(...)` to prospectively separate synthetic calibration controls (`registry-039` spacing-5 lattice, `registry-044` zero placeholder) from the 49 competing method lanes and 83 peer blobs while keeping `compare_registry(...)` and the failed `MTR1` receipt unchanged.
2. **Completed (`scripts/run_sahg1_lane.py`):** Reconstructed a leakage-free same-protocol out-of-fold multi-physics baseline (`oof_multiphysics_hgb_d3`, 27 prepared physical/LiDAR/DEM channels trained strictly on `fold["train"]` of `SegmentHoldout`), establishing a benchmark of **HOLDOUT-DTI `0.13000`** (95% CI `[0.11565, 0.14396]`).
3. **Completed (`src/gems/sahg1.py`, `evidence/sahg1_run_card_20261025.json`):** Preregistered and executed `H24-SAHG1` (Strike-Aligned Hydrothermal-Geomorphic Conduit Detector) with complete $9\times 9$ discrete receptive-field support verification (`verify_receptive_field_support`), achieving **HOLDOUT-DTI `0.09672`** (`[0.08657, 0.10703]`) on `gems-segment-pooled-v1` and **`0.09655`** (`[0.08270, 0.10976]`) on `segment-hide-recover-pooled-v1` (beating `MTR1`, `ASPC`, and its own geomorphic ablation `G_0` by `+0.01012`), passing prospective method-lane novelty (`0.4768` $\le 0.70$), and running the exact-file C2ST nuisance audit (`0.5826` vs. labels `0.4912`).
4. **Completed (`scripts/run_fuse_lane.py`, `evidence/fuse_run_card_20261025.json`, `knowledge/18_FUSE_findings_2026-10-25.md`):** Executed the documented Next Step #4 — integrating `H24-SAHG1`'s strike-projected LiDAR scarp (`G_sat`), stable-Th-controlled K/U alteration (`R_alt`), subsurface basement step (`B_step`), and hydrothermal conduit interaction (`H_conduit`) into a fold-local 31-channel `HistGradientBoostingClassifier` across three preregistered arms (`FUSE-RAW`, `FUSE-RESID`, `FUSE-HCW`):
   - Demonstrated that unresidualized `FUSE-RAW` matches `0.13000` (`0.12995`) but fails prospective method-lane novelty (`0.7399 > 0.70` against `registry-006`).
   - Demonstrated that training-only `NuisanceResidualizer` (`FUSE-RESID` `0.12210`, `FUSE-HCW` `0.12372`) reduces exact-file C2ST AUC from `0.5826` (`SAHG1`) down to **`0.4928`** / **`0.5108`** (Holm $p=0.870$, **PASS**), passes prospective method-lane novelty across all 49 competing method rasters (`0.6315` $\le 0.70$) and 83 peer blobs (`0.6025` $\le 0.70$), and beats `SAHG1` by **+0.02701** (+27.9%), `ASPC` by **+0.02798**, `CON` by **+0.05926**, `MTR1` by **+0.05931**, and `H-UNIQUE-03` by **+0.06988**.
5. **Remaining next steps for future sessions:**
   - **Targeted residualization of non-topographic bands only:** Apply `NuisanceResidualizer` selectively to airborne survey / access-confounded channels (`rtp_1..3`, `cond_1..2`, `thk`, `uth`, `uk`, `R_alt`) while leaving elevation-detrended tectonic strain and local $9\times 9$ LiDAR scarp curvature unresidualized, testing whether this closes the remaining `-0.00627` gap vs. `oof_multiphysics_hgb_d3` (`0.13000`) while keeping C2ST AUC $< 0.55$ and competing-method-lane overlap $\le 0.70$.
   - **Owner / coordinator resolution of `registry-039`:** Officially move synthetic calibration controls (`registry-039` spacing-5 lattice, `registry-044` zero placeholder) out of the literal all-entry duplicate gate in `registry/priority_rasters.json` so `literal_all_entries_passed` aligns with `method_lane_passed`.

## Concurrent main work preserved — not a cross-protocol winner

PRs [#9](https://github.com/buffedlizard55-lab/GEMSDOE24/pull/9) and
[#10](https://github.com/buffedlizard55-lab/GEMSDOE24/pull/10) landed during this
experiment. Their [independent review](evidence/2026-10-25_review_and_run_card.md),
[ASPC preregistration](knowledge/09_preregistered_ASPC_2026-10-25.md),
[findings](knowledge/10_ASPC_findings_2026-10-25.md),
[run card](evidence/aspc_run_card_20261025.json), code, tests and both
[research downloads](docs/downloads/gems24-aspc-20261025-6393e9d9b0df-RESEARCH-NOT-SUBMISSION-zeros.tif)
are preserved. **ASPC also has a negative promotion verdict.** Its recorded
`segment-hide-recover-pooled-v1` protocol uses a 3 km training buffer and 20 km
bootstrap tiles. MTR1 uses a different component/collar policy and 10 km tiles;
the scores are not a certified current-best comparison. Their registry scopes
also differ: MTR1 retained a local spacing-5 calibration lattice.

Both APIs now reuse the same metric, spatial-component attribution and bootstrap
implementation in `src/gems/holdout.py`, shared novelty primitives and writer.
Original scientific source fingerprints remain tied to their recorded commits;
integration tests do not launch another experiment. The incoming
[owner-requirements summary](knowledge/owner_brief_2026-10-25_summary.md) and
[complete incoming README snapshot](knowledge/archive/README_2026-10-25_parallel_ASPC.md)
are retained. This README embeds the full current brief available to this session,
not a consolidated summary substituted for it.

[MTR1 findings, source ledger and limitations](knowledge/11_MTR1_findings_2026-10-25.md)
· [Three-pass review](evidence/mtr1_review_passes_20261025.json) ·
[This session's repository verification](evidence/2026-10-25_session_review.md).

## Historical standing charter — retained for provenance; current protocol governs

This section preserves **all active requirements available in the session
context**, including corrections and scope decisions. The owner's brief itself is
reproduced **verbatim at the bottom of this file** and in
[`knowledge/owner_brief_verbatim.md`](knowledge/owner_brief_verbatim.md) (see that
file's provenance note: the 24GEMSDOE-specific opening is the wording preserved by
earlier sessions; the shared brief is the owner's text as stored by sibling session
22GEMSDOE).

1. Review this repository and the group's websites/source code; resume genuine
   next steps from earlier sessions before proposing duplicate work. Work
   autonomously without asking for data placement, feature preparation or
   routine design decisions. Download/restore into `data/`, prepare, train,
   predict and validate as far as verified inputs and permissions permit.
2. Aim to finish at the top of the leaderboard using PhD-level scientific
   judgment. Verify factual assertions against **official, trusted sources**,
   link them for manual review, collect auditable data/source/knowledge tables
   for subsequent projects, and flag irregularities. Never fabricate scores,
   access, causal discovery, source availability or completion.
3. Study why H19-4 and H19-5 are the group's highest **owner-reported** results:
   `gems19-h19-4-multi-line-physical-corroboration-20261001-691e4dfa-nan`
   **0.1894**, and
   `gems19-h19-5-openness-thermal-corroboration-20261001-e27054cf-nan`
   **0.1922**. H19-5 already exceeds 0.1894. The owner's leader snapshot 0.3049
   and the inherited site snapshot 0.3168 are historical, not current facts.
   Do not infer the score of a particular file from a public account's score
   without an artifact-linked organizer receipt.
4. Before implementing a new detector, write **3–5 genuinely unimplemented
   hypotheses relative to the reviewed work**. Each must name the precise
   layers, physical transform/signature, missing-fault rationale, distinction
   from reviewed methods, expected DTI benefit and implementation cost. Rank
   them. If external data are needed, name a free official source and verify
   practical availability; otherwise explicitly defer that hypothesis. Novelty
   is not a claim about unseen competitors' work.
5. Run a classifier two-sample audit motivated by **Lopez-Paz & Oquab, ICLR
   2017**. Distinguish pixels near mapped faults from far pixels using **only**
   road/trail distance, historic mining-claim distance and categorical membership
   of the **four GeoDAWN operational acquisition blocks**. No geothermal wells,
   sinter, vents, probes, mineral-occurrence substitutions, fault-distance
   features, mapped-fault confidence, or label-derived seams may enter this
   nuisance-only test.
6. Audit **training labels first**, then each relevant prediction raster, and
   the **exact final candidate** before any slot. Refit classifiers for null
   replicates and use spatial separation, effect-size safeguards and declared
   multiplicity control. If meaningful association appears, remove/residualize
   measured confounds on **training-region pixels only**, refit the detector and
   re-evaluate. A spatial holdout from the same catalogue is not sufficient by
   itself to certify robustness to the mapping process.
7. Scientific correction to the owner's premise: C2ST detects **distributional
   association**, not its cause. Roads/claims can themselves correlate with
   geology; non-rejection does not prove absence of bias. This implementation
   explicitly adapts the paper's held-out accuracy statistic to a prespecified
   AUC with refitted spatial randomizations. Block exchangeability is assumed;
   torus shifts on a nonstationary, irregular footprint are sensitivity
   diagnostics, not an exact spatial null.
8. **Never spend a weekly slot unless the candidate beats the CURRENT comparable
   spatially blocked holdout best.** Validate the top hypothesis on the frozen
   protocol, require paired true retraining gains and the exact-raster bias
   audit, and never treat re-ranking an already-binary submission as retraining.
   Missing original H19 OOF reconstruction or a required source blocks
   certification; an arbitrary easier baseline is not enough. A label-free
   *subset* transform of an already-scored raster uses the separate post-process
   path (`gems.promotion.require_postprocess_evidence`): frozen paired gates plus
   exact-file audit; if only the strict accessibility gate fails and the file is no
   more associated than its reference, the result is `owner_decision_required` —
   the owner may accept a declared exception, recorded in `registry/submissions.json`.
9. Submission: a **single-band float32 GeoTIFF**, matching the template's CRS,
   shape and geotransform, with **finite [0,1] values inside** and NaN outside the
   official footprint. Fix the owner's rejection, “Predicted values must be in
   range [0, 1]”. Give every artifact a unique name/content identifier, an
   obvious **one-click `.tif` download at the beginning of the site**, a separate
   short submission comment and a dedicated executive-summary/instructions
   subpage. Format validity does not authorize a scientific promotion. A
   zeros-outside fallback is separately labelled, not silently substituted for
   the official NaN convention.
10. Clean up GitHub Pages and implement a timestamped automated source feed.
    Distinguish owner reports, team-authored claims, official snapshots, computed
    diagnostics and hypotheses. Unknown scores, including unreported 22/23
    results, remain unknown. Never republish a renamed reference as a new win.
11. Review in **three passes**: (i) implement and verify against sources;
    (ii) find and fix bugs, assumptions and edge cases;
    (iii) recheck this original acceptance scope, reliability and code. Keep the
    review record and limitations. Open a PR from the session branch and merge
    through GitHub if the configured connection permits it; never silently claim
    a merge or a public deployment that did not occur.
12. Arena's **Maximize P(Win)** and **Own the Outcome** remain focal. Follow the
    session's fixed Arena branch, never create/write an orphan data branch, never
    ask for GitHub credentials, and preserve large regenerable datasets outside
    Git. If GitHub authentication fails, the platform connection needs
    reconnection; this is not permission to forge a merge or bypass authentication.
13. **First command of every session: `git fetch origin` and compare
    `origin/<session branch>` with `HEAD`.** On 2026-10-02 the remote session
    branch already held 12 commits that the fresh checkout lacked; merge, never
    force-push.
14. Scores that appear only in the brief (H28 0.1839, lattice 0.0904, …) are
    unconfirmed (`registry/live_scores.json`, `task_statement_only`). The dense
    catalogue holdout is a different regime from the hidden set; judge emission
    policies on the density-matched sparse simulation first.

## Reproduce the historical pipeline (2026-10-02; not current promotion authority)

Python 3.11; CPU-only (2 cores, 4 GB RAM are enough). Install the recorded versions:

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install --no-deps -e .
.venv/bin/python -m pytest -q
.venv/bin/ruff check src scripts tests
```

Data placement is autonomous and hash-pinned (needs only GitHub access; the 419 MB raster
and 592 MiB matrix stay ignored):

```bash
.venv/bin/python scripts/restore_data.py --roads
.venv/bin/python scripts/prepare_data.py
.venv/bin/python scripts/build_confounds.py --force      # roads + claims + derived four blocks
```

The headline experiment (all frozen in `knowledge/04_preregistered_emission_2026-10-02.md`):

```bash
.venv/bin/python scripts/run_emission_experiment.py --draws 30   # lattice calibration, K-grid, h25->h28 check
.venv/bin/python scripts/run_operator_comparison.py              # equal-N head-to-head + frozen selection
.venv/bin/python scripts/make_dot_thinned_sources.py --spacing 1.5 --spacing 2.4
.venv/bin/python scripts/write_postprocess_validation.py
```

Exact-file classifier two-sample audit, labels first (≈13 min on 2 CPUs), then package through the
fail-closed post-process path and rebuild the site:

```bash
.venv/bin/python scripts/run_geology_audit.py --force \
  --candidate out/h25-1-dotthin-d1.5-h19-5.tif --candidate-alt out/h25-1-dotthin-d2.4-h19-5.tif
.venv/bin/python scripts/build_submission24.py out/h25-1-dotthin-d1.5-h19-5.tif --postprocess-of h19-5 \
  --validation evidence/h24_e1_validation_primary.json --spacing 1.5 --role primary --summary "<<=126 chars>>"
.venv/bin/python scripts/build_submission24.py out/h25-1-dotthin-d2.4-h19-5.tif --postprocess-of h19-5 \
  --validation evidence/dotting_validation.json --spacing 2.8 --candidate-label candidate_alt --role alternate \
  --summary "<<=126 chars>>"
.venv/bin/python scripts/build_site.py
```

The owner records a score read from the portal (never automated; DrivenData forbids bots):

```bash
.venv/bin/python scripts/record_live_score.py --file <downloaded-file-name-or-sha-prefix> --score 0.2xxx
```

`scripts/analyze_group_rasters.py --sibling-root <folder of shallow clones of the owner's repos>` regenerates the
format forensics and leaderboard-geometry evidence. The reference-only bypass (`--mirror-of h19-5`) still verifies the
full pinned H19-5 hash. Nothing in these commands uploads to DrivenData or spends a slot.

## What is verified, and what is not

- **Integrity:** the restored owner bridge is pinned to its original hashes (training raster `4371c82e…`, labels
  `7ba308cc…`, template `2176d08e…`). This proves mirror consistency, **not independent organizer authentication**. The
  owner's `sample_submission.tif`/`example_submission.tif` has 60,988 pixels equal to 1.0 exactly on the labelled fault
  pixels, whereas the organizers' page says the sample "predicts total fault absence" (staff said they may change the
  description) — it is used only as a grid/footprint template.
- **Calibration and emission (COMPUTED):** hidden truth density τ≈0.24 % of cells from the owner's blind-lattice score
  (brief-only, unconfirmed); dotted H19-5 candidates improve the density-matched sparse simulation by +36 % (primary) /
  +42 % (alternate) with a positive/slightly negative dense effect. The model score (≈0.25, plausible 0.22–0.28) is **not**
  a leaderboard result; on the one independent pair with known scores the harness under-predicted the live effect and its
  dense ratio had the wrong sign.
- **Format:** strict writer; none of 148 owner rasters has an in-footprint value outside [0,1]; the cause of the original
  portal message is **not established**.
- **Audit:** full required families (6 rasters, Holm over 6 tests). Labels AUC 0.496 (no association); H19-4/H19-5/candidates
  0.555–0.563 (flagged, mostly claim proximity; not robust to spatial shifts). **Residualizing** (H24-2A, refit on the corrected
  sources) brings the detector's raster to AUC 0.525 (not flagged) but costs 0.016 dense DTI and does not beat the raw physics
  baseline — the strict audit and the holdout pull in opposite directions. Four blocks are **derived from an official figure and
  audited against published line-km, not official coordinates** (they are latitude bands, so removing them also removes regional
  geology); roads are the official buffered Census run.
- **Not verified:** the hidden labels, the private leaderboard, any score for the new files, account↔artifact mapping, the
  portal's note-length limit, the competition's exact deadline convention, the official flight-number→block mapping.

## Evidence and repository map

| Path | Role |
|---|---|
| `src/gems/emission.py`, `emission_eval.py`, `thinning.py` | calibration, kernel-cover control, exact fast paired evaluator, deterministic `dot_thin` |
| `src/gems/` (other) | exact/binary DTI, ridge selection, descriptors, strict nuisance inputs, spatial C2ST, residualization, packaging, promotion |
| `scripts/run_emission_experiment.py`, `run_operator_comparison.py`, `run_dotting_validation.py` | frozen experiments (this session / earlier session) |
| `scripts/run_geology_audit.py`, `build_confounds.py`, `derive_acquisition_blocks.py` | labels-first audit, nuisance rasters, audited block derivation |
| `scripts/build_submission24.py`, `record_live_score.py`, `build_site.py` | fail-closed packaging, score ledger, site + README status |
| `scripts/analyze_group_rasters.py` | format forensics and score-vs-geometry analysis of the owner's rasters |
| `evidence/h24_e1_*.json`, `emission_calibration.json`, `dotting_validation.json` | all experiment receipts |
| `evidence/accessibility_audit_v2.json`, `access_inputs.json` | audit receipts and source provenance |
| `evidence/format_forensics.json`, `group_raster_profiles.csv`, `lb_geometry_analysis.json` | portal-error forensics, per-raster profiles, score geometry |
| `registry/live_scores.json`, `submissions.json`, `irregularities.json` | owner-reported scores (with confirmation level), packaged files, irregularities |
| `inputs/`, `inputs/calibration/` | pinned scored reference rasters; calibration rasters copied unchanged from the owner's repos |
| `data/external/audit_sources/` | official USGS documents/figure, buffered road raster + receipt, claim-distance bridge, derived block raster + receipt |
| `docs/` | Pages site, one-click download, executive guide, timestamped feed |
| `knowledge/` | brief, preregistrations, findings, verified sources, synthesis, parallel-session (PR #7) reconciliation |

## Publication and automation

- GitHub Pages is enabled for `main` and the live site is served at <https://buffedlizard55-lab.github.io/GEMSDOE24/>.
  `website.yml` rebuilds the site from `main` on every push and on a 6-hourly schedule (no scheduled run had been
  observed when this was written; only the push-triggered run). The feed is a timestamped snapshot, not a live API.
  **It never requests drivendata.org** (its Terms of Use forbid automatic access): the leaderboard/forum entries are
  human-read snapshots, and only the USGS ScienceBase API is checked automatically (`scripts/refresh_source_feed.py`).
- `official-inputs-ci.yml` runs the anonymous official-source derivations the sandbox cannot reach (Census, USGS) on any
  `arena/**` branch and commits only small derived files back to that branch.
- The agent never uploads to DrivenData and never requests credentials. Follow organizer limits (3 submissions/week, one final
  submission, AI disclosure in the narrative); confirm the rules/page deadline discrepancy with the organizers.

## Historical next actions (2026-10-02; superseded — do not upload these references)

1. **Owner decision + upload (the only step that produces new information):** primary first, alternate in the same week if
   the exception is accepted; record both with `scripts/record_live_score.py`. Re-fit τ and the retention model from the two scores.
2. **Reconcile open PR #7** (a parallel session's H24-3A / road-source work, opened from the pre-merge base; conflicts in 20
   files; first screen would regress to the reference file). Do not merge it as is; rebase onto `main`, port only its new
   work, re-run the audit with an S1750-free road raster — plan and cross-checks in
   [`knowledge/08_parallel_session_pr7_2026-10-02.md`](knowledge/08_parallel_session_pr7_2026-10-02.md).
3. Test **H25-2** (strike-compatibility prior; no new data) next, then **H25-3** (scarp profile template on the processed 1 m
   tiles) and **H25-6** (map-scale correction corridor; needs a per-pixel map-scale raster from GDR 1391 via CI). H24-3A has
   a reported negative result in PR #7 (not reproduced here); H24-4A is untested.
4. Combine dotting with a *retrained, nuisance-residualized* detector only if it first beats the matched baseline.
5. If the owner supplies the S3-hosted GeoDAWN profile archives, replace the derived block raster with the official
   flight-number mapping.
6. A geologist-labelled scarp set (allowed if labels are saved) is the most direct supervised signal not yet used.
7. Keep brief-only scores flagged until the owner re-checks the submissions page.

## Owner brief (verbatim) — standing starting point, read every session

<details><summary><strong>Full owner brief (see provenance note inside)</strong></summary>

**Provenance and honesty note.** The exact message text of the 24GEMSDOE session was not available to the
agent that wrote this file. It is reconstructed from two sources, both stored verbatim by earlier work:

* **Part A** — the 24GEMSDOE-specific opening (classifier two-sample audit, H19 study, hypotheses, prompt-in-README
  rule, [0,1] error, executive summary, data placement, three passes, PR/merge). Taken unchanged from
  `knowledge/inherited_owner_charter.md`, which the earlier sessions of this repository preserved.
* **Part B** — the shared brief (score table, goal, leaderboard, Core Values, submission-form text, links,
  Site creation, passes, "create a pull request and merge") exactly as stored verbatim in
  `buffedlizard55-lab/GEMSDOE22` `README.md` (commit `96481093a7f73e5c13669e45574213d70c204ba0`), **minus** that session's own first paragraph
  (a fractal-clustering instruction that belongs to 22GEMSDOE, not to this repository).

Differences from the original message that cannot be ruled out: whitespace/link markup (the original used nested
markdown links), the order of Part A relative to Part B, and any 24GEMSDOE-specific wording not preserved in Part A.
Dated facts inside (scores, leaderboard 0.3049) reflect the moment the brief was written; `registry/live_scores.json` and the
README status block supersede stale values.

## Part A — 24GEMSDOE-specific opening (preserved wording)

```text
Review the repo; ensure an easy one-click downloadable submission tif exists
as the prompt describes; read the entire prompt. Formally test whether the
"geology" signal is actually encoding field accessibility, then remove it:
train a classifier two-sample test (the ML literature's distribution-shift
detector, Lopez-Paz & Oquab, ICLR 2017) to distinguish pixels near a mapped
fault from far pixels using ONLY non-geological confound features: distance to
nearest road/trail, distance to historic mining claims, and which of GeoDAWN's
four acquisition blocks (each with different line spacing and flight height) a
pixel falls in. If it beats its own null distribution by a meaningful margin,
that confirms the catalogue's shape is confounded by where geologists could
physically get to (strengthens the scientific case, and identifies exactly
what to residualize before training the real detector). Run on training labels
first to validate the premise, then again on our own predicted raster before
spending a submission slot; if predictions are equally explained by
road/acquisition-block proximity, the gain is mapping-process overfitting, not
discovery. A spatially-blocked holdout alone won't catch it since holdout
faults come from the same biased catalogue. Study/analyze why 19GEMSDOE got the
group's best live scores (h19-4 …691e4dfa-nan = 0.1894, h19-5 …e27054cf-nan =
0.1922) and whether we can beat 0.1894 (leader 0.3049 per user; site says
0.3168). Before implementing, produce 3–5 candidate geological hypotheses not
yet tried, each naming: specific layer(s), the physical signature targeted
(e.g. edge-detection/curvature transform), why it should catch a fault missing
from the USGS/INGENIOUS catalogue, and how it differs from everything already
in the repo; rank by expected DTI improvement and implementation cost;
validate the top one on the spatially-blocked holdout; if new external data is
needed, name the specific free official source and verify it is obtainable.
Put this prompt into the repo README and treat it as the standing starting
point each session; keep Arena Core Values ("Maximize P(Win)", "Own the
Outcome") as a focal point. Fix the submission error the user hit — "Predicted
values must be in range [0, 1]" — and give each tif a unique name plus a short
DrivenData note; create an executive-summary subpage explaining exactly how to
submit, obvious on the site's first screen. Autonomously complete the "data
placement" blocker (download into data/, then prepare_data) with no manual
input. Verify line by line against official sources with links for manual
review; flag irregularities; no hallucinations; 3 passes; finish by opening
and merging a PR to main, stating remaining work and limitations.
```

## Part B — shared brief (verbatim from GEMSDOE22 @ 96481093a7f7)

```text
Review the repo.

There should be an easy to download submission tif file as described by the prompt. Read the entire prompt.

Here are the results from submissions into the competition, separated by ....:
https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html
gems-submission-20260925T001403Z-7f00890a: 0.1563
....
https://buffedlizard55-lab.github.io/6GEMSDOE/
gems6_hgb88-topk03_33cec71ff0: 0.0286
....
https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html
pindrop-v4-nodes-20260925T152420Z-f347b70daa: 0.1193
pindrop-v4-discovery-20260925T152423Z-37f9d5b855: 0.0830
pindrop-v4-ridge-20260925T152422Z-4e03fc9705: 0.1152
....
https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html
gemsdoe2-dual-family-union-20260925T160406Z-f68e590f: 0.1560
....
https://buffedlizard55-lab.github.io/GEMSDOE4/
gems-submission-20260926T163915Z-237f0063: 0.0343
....
https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html
gems-submission-20260926T175114Z-7f00890a: 0.1563
....
https://buffedlizard55-lab.github.io/7GEMSDOE/
lidarscarp-ridge-top2pct-36c3a3f341c8: 0.1461
....
https://buffedlizard55-lab.github.io/8GEMSDOE/
Hedge-v2_submission: 0.1563
....
https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html
2314b599: 0.0107
....
https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html
gems-structural-area06-v1: 0.0202
....
https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html
r7-nms3-dem10-scarp_0c9199f14e62:0.1294
r7-nms3-dem10-scarp_0c9199f14e62_allfinite:0.1294
....
https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html
gems-tso1-20260929T005627Z-conj_alteration_mag: 0.0782
....
https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html
GEMS_r5-geom-horse-ensemble_20260929T154852Z_ccbe1de0_site_e96e942f: 0.0020
....
https://buffedlizard55-lab.github.io/17GEMSDOE/
17GEMSDOE_F-ensemble-2pct_20260930T050626Z:0.0187
....
https://buffedlizard55-lab.github.io/18GEMSDOE/
H19-C_20260930T212401Z_c11e495e: 0.0297
....
https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html
h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa-nan: 0.1894
h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan: 0.1922
....
https://buffedlizard55-lab.github.io/GEMSDOE10/
h16-continuation-20260927T065521077735Z-3431b83c7c: 0.0461
h20-dem10-scarp-thin-20260927T155223039488Z-ffc91a1686: 0.0921
H25-ctx-ridge-20260927T232947704150Z-6452ae1d00: 0.1280
h28-dotted-ridge-20260928T020256236880Z-6452ae1d00: 0.1839
....
https://buffedlizard55-lab.github.io/13GEMSDOE/
20261001_r13-lattice-s5_v2_nan-outside:0.0904
....
https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html
h16-1-topo-geophys-baseline-ridges-20260930-df20f65e-nan: 0.1855
h18-3a-topo-geophys-x-complexity-prior-20260930-c502dfab-nan: 0.0976
h18-4-usgs-geologic-map-faults-gap-20260930-aef8f42c-nan:
....
https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html
h20-1-sarnnpu-powerlaw-pi0363-tilt-wingcrack-20260930-be0e8f6b-nan:
h20-5-continuous-pu-proxy-unverified-20260930-824ce73a-nan:
....
https://buffedlizard55-lab.github.io/GEMSDOE21/
h19-4-reference-20260930-691e4dfa: 0.1894
....
22GEMSDOE SCORE:
....
23GEMSDOE SCORE:
....
24GEMSDOE SCORE:
....
25GEMSDOE SCORE:
....
26GEMSDOE SCORE:
....
27GEMSDOE SCORE:
....

WE NEED TO STUDY, ANALYZE, AND UNDERSTAND THE HIGHEST SCORE FROM THE GEMDOE SITE WHERE THE SUBMISSION TIF IS DOWNLOADED FROM WHICH IS THE FOLLOWING:
https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html
h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa-nan: 0.1894
h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan: 0.1922

Why and how did this get the highest score and are we able to generate a submission that scores higher than 0.1894?
Answer the question using Phd level experience, knowledge, and judgement.

The following is the leaderboard for the competition:
https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/

We need to quickly look at the results and results from the GEMSDOE websites above.

Before implementing, generate 3–5 candidate geological hypotheses we haven't tried yet, each naming: the specific layer(s) involved, the physical signature being targeted (e.g., an edge-detection or curvature transform), why it should catch a fault missing from the USGS/INGENIOUS catalogue rather than one already in it, and how it differs from anything already implemented in this repo. Rank them by expected DTI improvement and implementation cost. Validate the top candidate on our spatially-blocked holdout set before touching a weekly submission slot — do not spend a submission slot on an idea that hasn't beaten the current holdout best. If a candidate can't be validated without new external data, name the specific free, official source needed and check it's obtainable before proposing the idea as viable.
Work line by line verifying from official verified trusted sources, provide links for manual review. There should be no manual input, work on your own to complete tasks. Flag any irregularities for review. No hallucinations.
Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements. No hallucinations. Verify line by line.

We have a good understanding of how our hypothesis, methodology, calculations, analysis are done so we should be able to figure out a way to score higher on the leaderboard using previous results and scoring that we have across the sites listed above. We need to come up with distinct and unique strategies to score higher in this competition leaderboard. We need to start doing heavy and deep research into the part of the project that matters the most, which is the scientific discovery of geothermal vents. We should store all of our information and knowledge that we can gather from official verified sources. This will serve as a starting point for other projects as well. We need to think outside the box but still be grounded in proper scientific research, we are ultimately aiming for a top prize that many others are competing for. So it's important to be contrarian but be smart about it. We need to find sources of data that others are over looking or areas of the project when it comes to geothermal vents. We need to do deep research and critical thinking and come up with new hypothesis to test.

The following sites should serve as a starting point for understanding how to generate TIF submissions. These websites are researched, and tested and have generated TIF submissions. But we need to generate high scoring submissions.

https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html
gems-submission-20260925T001403Z-7f00890a: 0.1563
https://buffedlizard55-lab.github.io/6GEMSDOE/
gems6_hgb88-topk03_33cec71ff0: 0.0286
https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html
pindrop-v4-nodes-20260925T152420Z-f347b70daa: 0.1193
pindrop-v4-discovery-20260925T152423Z-37f9d5b855: 0.0830
pindrop-v4-ridge-20260925T152422Z-4e03fc9705: 0.1152
https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html
gemsdoe2-dual-family-union-20260925T160406Z-f68e590f: 0.1560
https://buffedlizard55-lab.github.io/GEMSDOE4/
gems-submission-20260926T163915Z-237f0063: 0.0343
https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html
gems-submission-20260926T175114Z-7f00890a: 0.1563
https://buffedlizard55-lab.github.io/7GEMSDOE/
lidarscarp-ridge-top2pct-36c3a3f341c8: 0.1461
https://buffedlizard55-lab.github.io/8GEMSDOE/
Hedge-v2_submission: 0.1563
https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html
2314b599: 0.0107
https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html
gems-structural-area06-v1: 0.0202
https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html
r7-nms3-dem10-scarp_0c9199f14e62:0.1294
r7-nms3-dem10-scarp_0c9199f14e62_allfinite:0.1294
https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html
gems-tso1-20260929T005627Z-conj_alteration_mag: 0.0782
https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html
GEMS_r5-geom-horse-ensemble_20260929T154852Z_ccbe1de0_site_e96e942f: 0.0020
https://buffedlizard55-lab.github.io/17GEMSDOE/
17GEMSDOE_F-ensemble-2pct_20260930T050626Z:0.0187
https://buffedlizard55-lab.github.io/18GEMSDOE/
H19-C_20260930T212401Z_c11e495e: 0.0297
https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html
h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa-nan: 0.1894
h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan: 0.1922
https://buffedlizard55-lab.github.io/GEMSDOE10/
h16-continuation-20260927T065521077735Z-3431b83c7c: 0.0461
h20-dem10-scarp-thin-20260927T155223039488Z-ffc91a1686: 0.0921
H25-ctx-ridge-20260927T232947704150Z-6452ae1d00: 0.1280
h28-dotted-ridge-20260928T020256236880Z-6452ae1d00: 0.1839
https://buffedlizard55-lab.github.io/13GEMSDOE/
20261001_r13-lattice-s5_v2_nan-outside:0.0904
https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html
h16-1-topo-geophys-baseline-ridges-20260930-df20f65e-nan: 0.1855
h18-3a-topo-geophys-x-complexity-prior-20260930-c502dfab-nan: 0.0976
h18-4-usgs-geologic-map-faults-gap-20260930-aef8f42c-nan:
https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html
h20-1-sarnnpu-powerlaw-pi0363-tilt-wingcrack-20260930-be0e8f6b-nan:
h20-5-continuous-pu-proxy-unverified-20260930-824ce73a-nan:
https://buffedlizard55-lab.github.io/GEMSDOE21/
h19-4-reference-20260930-691e4dfa: 0.1894
22GEMSDOE SCORE:
23GEMSDOE SCORE:
24GEMSDOE SCORE:
25GEMSDOE SCORE:
26GEMSDOE SCORE:
27GEMSDOE SCORE:

WE NEED TO STUDY, ANALYZE, AND UNDERSTAND THE HIGHEST SCORE FROM THE GEMDOE SITE WHERE THE SUBMISSION TIF IS DOWNLOADED FROM WHICH IS THE FOLLOWING:
https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html
h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa-nan: 0.1894
h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan: 0.1922

Why and how did this get the highest score and are we able to generate a submission that scores higher than 0.1894?
Answer the question using Phd level experience, knowledge, and judgement.

The following is the leaderboard for the competition:
https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/

0.3049 is the highest score right now so we need to design a new strategy, research, testing, analyzing, and generating submission system than the current website. It should be unique, take unique approaches to generating a submission that can score higher than .3049.

Put this prompt into the repo readme and read it everytime we work on the project as a starting point to make sure we are building what we are aiming for and have a strong base to continue building and improving on making something useful for everyday use. It should solve the problem of having to manually check everything ourselves and have an up to date current feed.

Review the repo.

The following is taken from the Arena AI team and I think it makes a good point on building a successful project, so let's keep the Core Values and Own the Outcome as a focal point when building, developing, researching, suggesting upgrades, and implementing the work.

Our Core Values
Maximize P(Win)
"Maximize the Probability of Winning": our decision making framework. In every decision, we weigh tradeoffs, assess risk, and choose the path that maximizes the probability that Arena succeeds. We set aside our emotions and make tough decisions in order to maximize P(Win). "Maximize P(Win)" frees us from constraints and clarifies that we must put Arena first.

Own the Outcome
We own results end to end — not just our individual slice of the work. When problems arise and we have the means to act, we do so without waiting for permission or assignment. We treat failure and success as signals and use them to improve. At Arena, we stay accountable to the final outcome.

Work line by line verifying from official verified trusted sources, provide links for manual review. There should be no manual input, work on your own to complete tasks. Flag any irregularities for review. No hallucinations.
Verify no hallucinations.
The goal of this project is to get a full list that follow our requirements. No hallucinations. Verify line by line.

We need to focus on being able to generate a submission into the competition.

The site should be able to generate a TIF file that is required for submission. It should be as easy as download to click a File to submit into the competition. This needs to be in the executive summary or the very beginning of the site. it should be obvious when you visit the site.

I tried to submit the document that i downloaded from the site but it returned this error on the submission form:
"Predicted values must be in range [0, 1]"

Also we need to give it a unique name and A short comment to help you or your team tell submissions apart later e.g. clustering with k=25

Here is the submission page when i click submit file
New submission

File to submitNo file chosen
You can submit a single-band GeoTIFF (.tif) file, or a .zip file containing a single GeoTIFF, with your predictions. It must match the submission format's CRS, shape, and geotransform. You may wish to review the competition rules first.
Note (optional)
A short comment to help you or your team tell submissions apart later e.g. clustering with k=25

Create a executive summary subpage that explains exactly how to make a submission into the contest.

Work on the next steps from the previous sessions first.

The goal of this project is to place top of the leaderboard in this competition. The following is the competition:
https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/

We need to create a project that can compete and place top of the leaderboard. We need to understand the problem, collect all the data and organize it into a clean easily auditable table with official verified links for manual verification.

This is the guidelines we need to follow.https://www.drivendata.org/competitions/306/competition-doe-gems/
Get familiar with the problem through the overview and problem description,https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/. You might also want to reference additional resources available on the about page,https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/.
Download the data from the data,https://www.drivendata.org/competitions/306/competition-doe-gems/data/, tab.
Create and train your own model. This reference solution,https://github.com/drivendataorg/gems-prize-reference-solution implements a simple approach.
Use your model to generate predictions that match the submission format.
Tell me what are you limitations and what you need access to during this project. We will need to find free publicly available sources and data from official and verified sources if we are to use 3rd party or external data.

this pdf outlines how submissions must be entered into the competition.
https://docs.nlr.gov/docs/fy26osti/96647.pdf

You must be able to do your own research, deep research, scientific literature research and organize the knowledge so that we can critically think through the problem and generate a solution through scientific and free publicly available information. this must be done autonomously and must be constantly reviewed and improved upon. Provide suggestions and improvements and implement them.

No DrivenData auth -> cannot auto-download training_features.tif, labels.tif, sample_submission.tif, 1m_DEM_links.csv from https://www.drivendata.org/competitions/306/competition-doe-gems/data/ (verified redirect to login)
See below for links from the above site. See attached files for links from the above site.
https://gdr.openei.org/submissions/1391

Download competition data from https://www.drivendata.org/competitions/306/competition-doe-gems/data/ (requires login) to data/
See links below for competition data:
https://www.dropbox.com/scl/fi/aemhtutjgcp6tr3tint94/GEMS_96647.pdf?rlkey=rek210cj2smnmzb8n0sla1vmd&st=wz4kofki&dl=0
https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?rlkey=kbykilvau066xuogoosbf4cq8&st=8junzdyw&dl=0
https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?rlkey=yiao96uluqdkipf0h5vju71jf&st=rnino7ya&dl=0
https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?rlkey=je8d8fepqfbst9lnwsq9rkplu&st=zj1lag1r&dl=0
https://www.dropbox.com/scl/fi/ig0mban712ns1atphgphe/Digital-elevation-model-links-JSON.pdf?rlkey=zm77f1vbtt2if8hlruymptnu3&st=srhhir10&dl=0

Work line by line verifying from official verified trusted sources, provide links for manual review. There should be no manual input, work on your own to complete tasks. Flag any irregularities for review. No hallucinations.
Verify no hallucinations.
The goal of this project is to get a full list that follow our requirements. No hallucinations. Verify line by line.

Site creation
Create a github page for this repo that has clean ui, user friendly, simple and easy to use. It should be organized and clean.

It should include all relevant information in an easy to read format with official verified links as sources for review. Work line by line verify everything no hallucinations.

The single remaining blocker to training is data placement: run bash scripts/download_competition_data.sh on any unrestricted machine into data/, then python scripts/prepare_data.py — after that the full train->inference->validate pipeline is ready to run (GPU needed for training; metric/losses/validation all verified working here on CPU).

you need to complete the above task by yourself. Work line by line verifying from official verified trusted sources, provide links for manual review. There should be no manual input, work on your own to complete tasks. Flag any irregularities for review. No hallucinations.

Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements. No hallucinations. Verify line by line.

Run this task through multiple passes.
Pass 1: Implement the task completely and verify the result.
Pass 2: Review your work for bugs, missing requirements, incorrect assumptions, and edge cases. Fix everything you find.
Pass 3: Re-check the entire implementation against the original request. Improve accuracy, reliability, completeness, and code quality. Fix any remaining issues.
Do not stop after the first pass. Each pass must build on the previous one. Before finishing, verify that the final result fully satisfies the original request. Work line by line verify everything no hallucinations.

Go ahead and create a pull request and then merge the pull request onto the main. Make suggestions for what work still needs to be done and any limitations that is in the way of a successful project. It should be worked on in this next session or the next session. Work line by line verify everything no hallucinations.
```

</details>

## Current owner brief — read every session (2026-10-25)

<details><summary>Complete current owner brief (link markup/whitespace normalized)</summary>

# Owner brief — 2026-10-25

The following preserves the current user brief (link markup normalized; the Arena branch-status wrapper is omitted). Read this and the latest README decision at the beginning of every session. Historical claims inside are requirements/context, not independently verified scores. This current brief supersedes historical requests to submit copied/thinned reference rasters or to seek a human inspection exception.

---

Review the repo.

I want to focus on the highest scoring submissions from the following sites, GEMSDOE24, GEMSDOE25, GEMSDOE27, GEMSDOE28, GEMSDOE30, GEMSDOE31, GEMSDOE32, GEMSDOE33, GEMSDOE36.

THE FOLLOWING IS THE HIGHEST URGENCY AND MUST BE FOLLOWED!

MUST GENERATE A UNIQUE TIF SUBMISSION FOR THE COMPETITION. DO NOT COPY A PREVIOUS SUBMISSION UNLESS IT'S FOR LEARNING AND EDUCATION. BUT WE MUST GENERATE A UNIQUE TIF SUBMISSION. IT MUST BE OBVIOUS WHETHER IT IS OK TO DOWNLOAD AND SUBMIT THE GENERATED TIF SUBMISSION.

There should be an easy to download submission tif file as described by the prompt. Read the entire prompt. A lot of sites mention inspection only and a human inspector, but the inspection needs to be done through the project and needs to be validated for submission without human intervention.

PARALLEL-RUN PROTOCOL — read first. This session is one of several running from this same prompt.

1. LANE. Your lane is the single method paragraph below. Stay inside it. If your raster's rank-correlation with any registry raster exceeds [0.90], or more than [70%] of your dots fall within 3 px of one registry raster's dots, you have drifted into another lane: log it as a duplicate and stop. Check this on the surface before placement AND on the final dots.

2. REUSE, DON'T REBUILD. Use the template's cached feature stack, evaluate_holdout.py and submission_writer.py. Holdout = hide-and-recover: withhold whole fault segments with a buffer, derive every catalogue-based feature only from the visible faults, mask visible faults pixel-exactly, score pooled DTI (alpha 0.2, beta 0.8, 300 m triangular kernel). If a shared tool is wrong, fix it once in the template and report it; never keep a private fork.

3. LABEL EVERY NUMBER as HOLDOUT-DTI (evaluator version, number of withheld positives, 95% CI) or ORGANIZER-CONFIRMED (copied from a submission-page receipt). A projection is never written as a score.

4. LEAKAGE CANARY. Test each feature alone on the holdout before trusting any result. AUC above [0.90] means leakage until proven otherwise.

5. RUN CARD. End with one JSON card: hypothesis; mechanism; the named non-fault process that could mimic it; holdout DTI + CI; correlation/overlap vs registry; raster sha256; validator output (no NaN inside the footprint, values in [0,1], CRS/shape/transform match); submission name + note of at most 140 characters; verdict promote / negative. Negative results are deliverables.

6. BUDGET. Stop after [3] experiments or [2] hours. Do not pick submissions: promotion to a real slot is a separate selector step, within the weekly cap shown on the submission page.

The following sites should serve as a starting point for understanding how to generate TIF submissions. These websites are researched, and tested and have generated TIF submissions. But we need to generate high scoring submissions.

Here are the results from submissions into the competition, separated by ....:

WE NEED TO STUDY, ANALYZE, AND UNDERSTAND THE HIGHEST SCORE FROM THE GEMDOE SITE WHERE THE SUBMISSION TIF IS DOWNLOADED FROM WHICH IS THE FOLLOWING:

https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html

h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778

Why and how did this get the highest score and are we able to generate a submission that scores higher than 0.2778?

Answer the question using Phd level experience, knowledge, and judgement. Then use the answer to generate a unique TIF submission into the competition. Must be unique submission unlike any within the GEMSDOE sites above. Verify working line by line no hallucinations.

Current competition leaderboard GEMSDOE high score:

0.4413

WE NEED TO STUDY, ANALYZE, AND UNDERSTAND THE HIGHEST SCORE FROM THE GEMDOE SITE WHERE THE SUBMISSION TIF IS DOWNLOADED FROM WHICH IS THE FOLLOWING:

https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html

h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778

Why and how did this get the highest score and are we able to generate a submission that scores higher than 0.2778?

Answer the question using Phd level experience, knowledge, and judgement. Then use the answer to generate a unique TIF submission into the competition. Must be unique submission unlike any within the GEMSDOE sites above. Verify working line by line no hallucinations.

Current competition leaderboard GEMSDOE high score:

0.4413

https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html

gems-submission-20260925T001403Z-7f00890a: 0.1563

....

https://buffedlizard55-lab.github.io/6GEMSDOE/

gems6_hgb88-topk03_33cec71ff0: 0.0286

....

https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html

pindrop-v4-nodes-20260925T152420Z-f347b70daa: 0.1193

pindrop-v4-discovery-20260925T152423Z-37f9d5b855: 0.0830

pindrop-v4-ridge-20260925T152422Z-4e03fc9705: 0.1152

....

https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html

gemsdoe2-dual-family-union-20260925T160406Z-f68e590f: 0.1560

....

https://buffedlizard55-lab.github.io/GEMSDOE4/

gems-submission-20260926T163915Z-237f0063: 0.0343

....

https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html

gems-submission-20260926T175114Z-7f00890a: 0.1563

....

https://buffedlizard55-lab.github.io/7GEMSDOE/

lidarscarp-ridge-top2pct-36c3a3f341c8: 0.1461

....

https://buffedlizard55-lab.github.io/8GEMSDOE/

Hedge-v2_submission: 0.1563

....

https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html

2314b599: 0.0107

....

https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html

gems-structural-area06-v1: 0.0202

....

https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html

r7-nms3-dem10-scarp_0c9199f14e62:0.1294

r7-nms3-dem10-scarp_0c9199f14e62_allfinite:0.1294

....

https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html

gems-tso1-20260929T005627Z-conj_alteration_mag: 0.0782

....

https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html

GEMS_r5-geom-horse-ensemble_20260929T154852Z_ccbe1de0_site_e96e942f: 0.0020

....

https://buffedlizard55-lab.github.io/17GEMSDOE/

17GEMSDOE_F-ensemble-2pct_20260930T050626Z:0.0187

....

https://buffedlizard55-lab.github.io/18GEMSDOE/

H19-C_20260930T212401Z_c11e495e: 0.0297

....

https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html

h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa-nan: 0.1894

h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan: 0.1922

....

https://buffedlizard55-lab.github.io/GEMSDOE10/

h16-continuation-20260927T065521077735Z-3431b83c7c: 0.0461

h20-dem10-scarp-thin-20260927T155223039488Z-ffc91a1686: 0.0921

H25-ctx-ridge-20260927T232947704150Z-6452ae1d00: 0.1280

h28-dotted-ridge-20260928T020256236880Z-6452ae1d00: 0.1839

....

https://buffedlizard55-lab.github.io/13GEMSDOE/

20261001_r13-lattice-s5_v2_nan-outside:0.0904

....

https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html

h16-1-topo-geophys-baseline-ridges-20260930-df20f65e-nan: 0.1855

h18-3a-topo-geophys-x-complexity-prior-20260930-c502dfab-nan: 0.0976

h18-4-usgs-geologic-map-faults-gap-20260930-aef8f42c-nan: 0.0360

....

https://buffedlizard55-lab.github.io/GEMSDOE21/

h19-4-reference-20260930-691e4dfa: 0.1894

....

https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html

h20-1-sarnnpu-powerlaw-pi0363-tilt-wingcrack-20260930-be0e8f6b-nan: 0.1890

h20-5-continuous-pu-proxy-unverified-20260930-824ce73a-nan: 0.1859

....

https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html

h23-a-dti-optimal-emission-6pct-20261002-e2ec4b49-nan: 0.1002

h23-b-dti-optimal-emission-10pct-20261002-86176698-nan: 0.0748

....

https://buffedlizard55-lab.github.io/GEMSDOE23/

h30-arrangement-matched-habitat-20261002-0d4e02e8-nan: 0.1352

....

https://buffedlizard55-lab.github.io/GEMSDOE24/

h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan: 0.2477

....

https://buffedlizard55-lab.github.io/GEMSDOE25/

dotted-h19-5-d2-8-20261002-e56ea318af89-nan: 0.2600

....

https://buffedlizard55-lab.github.io/GEMSDOE26/

dilcond-oof-v1-20261003-47629f496133-nan: 0.1223

....

https://buffedlizard55-lab.github.io/GEMSDOE27/

topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan: 0.2449

....

https://buffedlizard55-lab.github.io/GEMSDOE30/

d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca: 0.2600

....

https://buffedlizard55-lab.github.io/GEMSDOE31/docs/

h27-4-solo-d28-20261004-8acb75e1-nan:0.2708

....

https://buffedlizard55-lab.github.io/GEMSDOE33/

h33d-analog-tip-stepover-r30-20261004-cb490425926e: 0.2632

....

https://buffedlizard55-lab.github.io/GEMSDOE34/docs/index.html

h34-scatter-q50-arr-matched-20261004T223317Z: 0.0778

....

https://buffedlizard55-lab.github.io/GEMSDOE35/docs/index.html

h35-06-aaa86efb25-20261004T225420098147Z-candidate: 0.0418

....

https://buffedlizard55-lab.github.io/GEMSDOE36/docs/

anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros: 0.2750

....

https://buffedlizard55-lab.github.io/GEMSDOE37/

h6-physics-dotted-80k-20261005T055000Z-0bef9211631c: 0.1193

....

https://buffedlizard55-lab.github.io/GEMSDOE38/docs/index.html

D-step-3p0-07pct-tipProt-20261005-ecfbf59e2b48-zero: 0.0763

....

https://buffedlizard55-lab.github.io/GEMSDOE42/docs/index.html

xscale-worm-persistence-20261006T000541Z-nan: 0.0581

....

https://buffedlizard55-lab.github.io/GEMSDOE43/docs/index.html

sup01-hgb21-sep40-n40000-20261006-bc2e4e9a8d6f-nan: 0.0424

....

https://buffedlizard55-lab.github.io/GEMSDOE45/

h51-km-faultzone-20261006-zeros: 0.0106

....

https://buffedlizard55-lab.github.io/GEMSDOE49/

gate_ortho_w0.25-40k-20261006T213721Z-nan: 0.2376

....

https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html

h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778

....

https://buffedlizard55-lab.github.io/GEMSDOE28/

h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan: 0.2708

h32-1-prethin-tip-euler-d2-8-20261003-31e35eee884e-nan: 0.2649

h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan: 0.2710

h38-1-hf-euler-r30-r1-20261003-56a9f473edc7-nan: 0.2707

....

https://buffedlizard55-lab.github.io/GEMSDOE29/docs/index.html

efd28-repro-20261003-1cc7dc534d51-nan: 0.2600

repo-c0-habitat-emission-20261003-a4d439b07426-nan: 0.0041

sgmc-off-catalogue-44k-20261003-c8dcd780e3fd-nan: 0.0512

wormrank-d28-20261003-59dcaf6fdd11d-zeros:0.2560

wormsurv-filter-20261003-921f10960d6e-zeros: 0.0532

xfit-c0-habitat-20261003-ca879db0089a-zeros:0.0439

xfit-h41-union-qfaults-20261003-9edb34b99e3a-zeros: 0.0356

....

https://buffedlizard55-lab.github.io/GEMSDOE46/

r11f-scarp-radiometric-fusion-00e049b51218-zeros:0.1589

r12-scarp-rad-concordance-23e807e2de9f-zeros: 0.0843

....

https://buffedlizard55-lab.github.io/GEMSDOE39/

h40-e-disc-h40e-30k-zeros: 0.0339

....

https://buffedlizard55-lab.github.io/GEMSDOE40/docs/index.html

h8-euler-lineament-depthcluster-20261006-785c4f5d5ce1: 0.0355

h8-euler-lineament-depthcluster-20261006-785c4f5d5ce1-hard: 0.0397

h45-eulerdepthreadcluster-20261006-f28e5cff6826-zeros: 0.0984

....

https://buffedlizard55-lab.github.io/GEMSDOE41/docs/index.html

h42-submission-primary: 0.0245

....

https://buffedlizard55-lab.github.io/GEMSDOE44/docs/

h46-twostageAB_20261006T160000Z_b0cfe956-zeros: 0.0715

....

https://buffedlizard55-lab.github.io/GEMSDOE47/

h60-lidarscarp-s2p0-20261007-nanoutside: 0.0430

....

https://buffedlizard55-lab.github.io/GEMSDOE48/docs/index.html

h59-cover-ds-belief-b2xh33d-20261008T184547Z-b79c4c61d8d8: 0.2296

....

https://buffedlizard55-lab.github.io/GEMSDOE50/

h59-sharpened-scarp-scatter-90k-20261007T171954Z-allfinite: 0.0764

....

https://buffedlizard55-lab.github.io/GEMSDOE51/

h53-twostage-20261008T040951Z-9a0b32c871: 0.1047

....

https://buffedlizard55-lab.github.io/GEMSDOE52/

h97b-candidate: 0.0856

....

https://buffedlizard55-lab.github.io/GEMSDOE53/docs/index.html

h8-tiprelay-ridgeconcord-pr2-n80000-20261009-49bec522-zeros: 0.0159

....

https://buffedlizard55-lab.github.io/GEMSDOE54/docs/

h54c-manifest-edge-20261009T025732Z-73454bc5:0.0449

....

https://buffedlizard55-lab.github.io/55GEMSDOE/docs/index.html

tensor_full-n16000-sep3-20261009T211747Z-nan: 0.0290

....

https://buffedlizard55-lab.github.io/56GEMSDOE/docs/index.html

h56-final-dotted-ridge-d2p8-20261009T190421Z:0.0658

....

https://buffedlizard55-lab.github.io/57GEMSDOE/docs/index.html

h57r-joint-strata-38000dots-20261010T214547Z-00cf5b2066f1-zeros: 0.0254

....

https://buffedlizard55-lab.github.io/58GEMSDOE/docs/index.html

ml-binary-ridge-20261012T000000Z: 0.0180

....

https://buffedlizard55-lab.github.io/59GEMSDOE/docs/index.html

h59j-coherence-consensus-dotted-20261011T043000Z: 0.0499

....

https://buffedlizard55-lab.github.io/60GEMSDOE/docs/index.html

h73-chi-coherent-corridor-12000-20261011T195818Z-zeros: 0.0351

....

https://buffedlizard55-lab.github.io/61GEMSDOE/docs/index.html

h61a-basement-step-20000dots-20261011T012029Z-eb2ae4bb024b-zeros: 0.0009

h61o-vardepth-none-40000dots-20261011T160711Z-28d4fac611ea-zeros-zeros:0.0751

....

https://buffedlizard55-lab.github.io/62GEMSDOE/

datum-lahontan-strain-gauge-defensible-440dots-zeros: 0.0000

....

https://buffedlizard55-lab.github.io/GEMSDOE63/

cvarlw-thin-s3p17-54864-20261011T220606Z-c58f60c4-zeros: 0.2303

....

https://buffedlizard55-lab.github.io/GEMSDOE64/

h64-lidar-scarp-cv-20261011T220000Z:0.0383

....

https://buffedlizard55-lab.github.io/GEMSDOE65/docs/index.html

sar-em-propensity-half-20261011T223500Z-5e4660cd-zeros:0.0431

....

https://buffedlizard55-lab.github.io/GEMSDOE66/docs/index.html

gems66-lidar03-cvretrain-reliefdecile-37654dots-20261020T190152Z-zeros:0.1152

....

https://buffedlizard55-lab.github.io/GEMSDOE67/

h67a-orientip-lane-29447dots-20261012T021226Z-allfinite:0.0356

ovtr-ml-cover-tau3p0-20261012-nan:0.1426

....

https://buffedlizard55-lab.github.io/GEMSDOE68/

gems68-autoctx-s3-strands-35000dots-20261020T210000Z-849a0f04-nan:0.0437

gems68-autoctx-s3-strands-35000dots-20261020T210000Z-849a0f04-zeros: 0.0437

....

https://buffedlizard55-lab.github.io/GEMSDOE69/

gems69-joint-relayramp-pullapart-38669-20261020T201504Z-f29b6df5:0.0053

....

https://buffedlizard55-lab.github.io/GEMSDOE70/

gems70-p5-dual-submod300-oof38k-20261020:0.2478

....

https://buffedlizard55-lab.github.io/GEMSDOE71/

gems71-hydro-conduit-38800-20261020T120000Z-zeros: 0.0558

....

https://buffedlizard55-lab.github.io/GEMSDOE72/

gemsdoe72-h72-1-sgmc-offcatalogue-20261020T195456Z-6e6525e5-zeros: 0.0492

....

https://buffedlizard55-lab.github.io/GEMSDOE73/

gems73-h73-mcsc-seamfree-blakely-37654dots-20261021T073716Z-b27ac445-zeros: 0.1917

....

https://buffedlizard55-lab.github.io/GEMSDOE74/

gemsdoe74-triregime-radon-piedmont-37654-20261021T051000Z-zeros:0.0669

....

https://buffedlizard55-lab.github.io/GEMSDOE75/

gems75-trlt-radon-loco-ridge-20261021-zeros:0.1627

....

https://buffedlizard55-lab.github.io/GEMSDOE76/

gems76_h76_3_geotherm_tilt_axial_submod_20261021_zeros:0.1555

gems76-ptcf-tiltworm-submod39k-20261021T034000Z-6316481d-zeros:0.2343

....

https://buffedlizard55-lab.github.io/GEMSDOE77/

gems85-h85-edti-collar35-skel-r33-20261021-d97b248e-zeros:0.0964

....

https://buffedlizard55-lab.github.io/GEMSDOE78/

gems78-h78sigx-fuse-b5-44090dots-20261022T021932Z-zeros:0.1564

....

https://buffedlizard55-lab.github.io/GEMSDOE79/

gems79-tilt-ring-100000dots-20261022T212135Z-50a5d7498c71-zeros:0.0005

....

https://buffedlizard55-lab.github.io/GEMSDOE80/

gemsdoe80-h80g-choquet-tworegime-20261022T000000Z-zeros:0.0943

....

https://buffedlizard55-lab.github.io/GEMSDOE81/

gems81-cont-poisson44090-buf2-20261021T233115Z-42223e10-zeros:0.0041

....

https://buffedlizard55-lab.github.io/GEMSDOE82/

gemsdoe82-h82-submodular-punoisyor-20261021T235456Z-fe137199-zeros:0.1886

....

https://buffedlizard55-lab.github.io/GEMSDOE83/

gems83-h83-gvcd-dink300-37654dots-20261021-1a373694-zeros:0.0573

....

https://buffedlizard55-lab.github.io/GEMSDOE84/

gems84-h84-kthm-tworegime-58000px-20261022T235900Z-zeros:0.0132

....

https://buffedlizard55-lab.github.io/GEMSDOE85/

gemsdoe85-hjcd-ventbridge-submod-zeros: 0.1110

....

https://buffedlizard55-lab.github.io/GEMSDOE86/

:

....

https://buffedlizard55-lab.github.io/GEMSDOE87/

h87-h87-cmgep-20261022T060000Z-8f394f43:0.0500

....

https://buffedlizard55-lab.github.io/GEMSDOE88/

:

....

https://buffedlizard55-lab.github.io/GEMSDOE89/

gemsdoe89-bh-rtp-habc-20261024-d7e1507c-zeros:0.0301

....

https://buffedlizard55-lab.github.io/GEMSDOE90/

gems90-cnc-35000dots-20261024T084324Z:0.0749

....

https://buffedlizard55-lab.github.io/GEMSDOE91/

gems91-s17-cwpc-e3-37654dots-20261025T150000Z-4d124f1d-zeros:0.1367

gems91-s17-lftg-20261025T160014Z-7b6bf90844-zeros:0.1823

gems91-S18-UNIQUE-curvtilt-20000dots-20261025T182858Z-29db2405:

....

https://buffedlizard55-lab.github.io/GEMSDOE92/

gemsdoe92-listricdip-updip50-37654-20261025T190000Z-zeros:0.0255

....

I think it makes sense that in order for a submission to be validated that it needs to pass certain high scoring validation gates before confirming whether a file is unique and can be submitted for scoring.

The following is the leaderboard for the competition:

https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/

See below for more links and information related to the competition:

https://github.com/drivendataorg/gems-prize-reference-solution

https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and

https://gbcge.org/current-projects/ingenious/

https://epsg.io/32611

https://en.wikipedia.org/wiki/Tversky_index

We need to quickly look at the results and results from the GEMSDOE websites above.

Before implementing, generate 3–5 candidate geological hypotheses we haven't tried yet, each naming: the specific layer(s) involved, the physical signature being targeted (e.g., an edge-detection or curvature transform), why it should catch a fault missing from the USGS/INGENIOUS catalogue rather than one already in it, and how it differs from anything already implemented in this repo. Rank them by expected DTI improvement and implementation cost. Validate the top candidate on our spatially-blocked holdout set before touching a weekly submission slot — do not spend a submission slot on an idea that hasn't beaten the current holdout best. If a candidate can't be validated without new external data, name the specific free, official source needed and check it's obtainable before proposing the idea as viable.

Work line by line verifying from official verified trusted sources, provide links for manual review. There should be no manual input, work on your own to complete tasks. Flag any irregularities for review. No hallucinations.

Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements. No hallucinations. Verify line by line.

We have a good understanding of how our hypothesis, methodology, calculations, analysis are done so we should be able to figure out a way to score higher on the leaderboard using previous results and scoring that we have across the sites listed above. We need to come up with distinct and unique strategies to score higher in this competition leaderboard. We need to start doing heavy and deep research into the part of the project that matters the most, which is the scientific discovery of geothermal vents. We should store all of our information and knowledge that we can gather from official verified sources. This will serve as a starting point for other projects as well. We need to think outside the box but still be grounded in proper scientific research, we are ultimately aiming for a top prize that many others are competing for. So it's important to be contrarian but be smart about it. We need to find sources of data that others are over looking or areas of the project when it comes to geothermal vents. We need to do deep research and critical thinking and come up with new hypothesis to test.

0.3195 is the highest score right now so we need to design a new strategy, research, testing, analyzing, and generating submission system than the current website. It should be unique, take unique approaches to generating a submission that can score higher than 0.3195.

Put this prompt into the repo readme and read it everytime we work on the project as a starting point to make sure we are building what we are aiming for and have a strong base to continue building and improving on making something useful for everyday use. It should solve the problem of having to manually check everything ourselves and having an up to date current feed.

Review the repo.

The following is taken from the Arena AI team and I think it makes a good point on building a successful project, so let's keep the Core Values and Own the Outcome as a focal point when building, developing, researching, suggesting upgrades, and implementing the work.

Our Core Values

Maximize P(Win)

“Maximize the Probability of Winning”: our decision making framework. In every decision, we weigh tradeoffs, assess risk, and choose the path that maximizes the probability that Arena succeeds. We set aside our emotions and make tough decisions in order to maximize P(Win). “Maximize P(Win)” frees us from constraints and clarifies that we must put Arena first.

Own the Outcome

We own results end to end — not just our individual slice of the work. When problems arise and we have the means to act, we do so without waiting for permission or assignment. We treat failure and success as signals and use them to improve. At Arena, we stay accountable to the final outcome.

Work line by line verifying from official verified trusted sources, provide links for manual review. There should be no manual input, work on your own to complete tasks. Flag any irregularities for review. No hallucinations.

Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements. No hallucinations. Verify line by line.

We need to focus on being able to generate a submission into the competition.

The site should be able to generate a TIF file that is required for submission. It should be as easy as download to click a File to submit into the competition. This needs to be in the executive summary or the very beginning of the site. it should be obvious when you visit the site.

I tried to submit the document that i downloaded from the site but it returned this error on the submission form:

"Predicted values must be in range [0, 1]"

Also we need to give it a unique name and A short comment to help you or your team tell submissions apart later e.g. clustering with k=25

Here is the submission page when i click submit file

New submission

File to submitNo file chosen

You can submit a single-band GeoTIFF (.tif) file, or a .zip file containing a single GeoTIFF, with your predictions. It must match the submission format's CRS, shape, and geotransform. You may wish to review the competition rules first.

Note (optional)

A short comment to help you or your team tell submissions apart later e.g. clustering with k=25

Create a executive summary subpage that explains exactly how to make a submission into the contest.

Work on the next steps from the previous sessions first.

The goal of this project is to place top of the leaderboard in this competition. The following is the competition:

https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/

We need to create a project that can compete and place top of the leaderboard. We need to understand the problem, collect all the data and organize it into a clean easily auditable table with official verified links for manual verification.

This is the guidelines we need to follow. https://www.drivendata.org/competitions/306/competition-doe-gems/

Get familiar with the problem through the overview and problem description, https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/. You might also want to reference additional resources available on the about page, https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/.

Download the data from the data, https://www.drivendata.org/competitions/306/competition-doe-gems/data/, tab.

Create and train your own model. This reference solution, https://github.com/drivendataorg/gems-prize-reference-solution implements a simple approach.

Use your model to generate predictions that match the submission format.

Tell me what are you limitations and what you need access to during this project. We will need to find free publicly available sources and data from official and verified sources if we are to use 3rd party or external data.

this pdf outlines how submissions must be entered into the competition.

https://docs.nlr.gov/docs/fy26osti/96647.pdf

You must be able to do your own research, deep research, scientific literature research and organize the knowledge so that we can critically think through the problem and generate a solution through scientific and free publicly available information. this must be done autonomously and must be constantly reviewed and improved upon. Provide suggestions and improvements and implement them.

❌ No DrivenData auth → cannot auto-download training_features.tif, labels.tif, sample_submission.tif, 1m_DEM_links.csv from https://www.drivendata.org/competitions/306/competition-doe-gems/data/ (verified redirect to login)

See below for links from the above site. See attached files for links from the above site.

https://gdr.openei.org/submissions/1391

Download competition data from https://www.drivendata.org/competitions/306/competition-doe-gems/data/ (requires login) to data/

See links below for competition data:

https://www.dropbox.com/scl/fi/aemhtutjgcp6tr3tint94/GEMS_96647.pdf?rlkey=rek210cj2smnmzb8n0sla1vmd&st=wz4kofki&dl=0

https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?rlkey=kbykilvau066xuogoosbf4cq8&st=8junzdyw&dl=0

https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?rlkey=yiao96uluqdkipf0h5vju71jf&st=rnino7ya&dl=0

https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?rlkey=je8d8fepqfbst9lnwsq9rkplu&st=zj1lag1r&dl=0

https://www.dropbox.com/scl/fi/ig0mban712ns1atphgphe/Digital-elevation-model-links-JSON.pdf?rlkey=zm77f1vbtt2if8hlruymptnu3&st=srhhir10&dl=0

Work line by line verifying from official verified trusted sources, provide links for manual review. There should be no manual input, work on your own to complete tasks. Flag any irregularities for review. No hallucinations.

Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements. No hallucinations. Verify line by line.

Site creation

Create a github page for this repo that has clean ui, user friendly, simple and easy to use. It should be organized and clean.

It should include all relevant information in an easy to read format with official verified links as sources for review. Work line by line verify everything no hallucinations.

**The single remaining blocker to training is data placement**: run `bash scripts/download_competition_data.sh` on any unrestricted machine into `data/`, then `python scripts/prepare_data.py` — after that the full train→inference→validate pipeline is ready to run (GPU needed for training; metric/losses/validation all verified working here on CPU).

you need to complete the above task by yourself. Work line by line verifying from official verified trusted sources, provide links for manual review. There should be no manual input, work on your own to complete tasks. Flag any irregularities for review. No hallucinations.

Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements. No hallucinations. Verify line by line.

Run this task through multiple passes.

Pass 1: Implement the task completely and verify the result.

Pass 2: Review your work for bugs, missing requirements, incorrect assumptions, and edge cases. Fix everything you find.

Pass 3: Re-check the entire implementation against the original request. Improve accuracy, reliability, completeness, and code quality. Fix any remaining issues.

Do not stop after the first pass. Each pass must build on the previous one. Before finishing, verify that the final result fully satisfies the original request. Work line by line verify everything no hallucinations.

Go ahead and create a pull request and then merge the pull request onto the main. Make suggestions for what work still needs to be done and any limitations that is in the way of a successful project. It should be worked on in this next session or the next session. Work line by line verify everything no hallucinations.

</details>
