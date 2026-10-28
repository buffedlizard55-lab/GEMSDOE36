# Review — 28 October 2026, session B (owner brief re-supplied)

**Decision: NO SUBMISSION TIFF. Verdict negative.** No candidate was generated, no experiment was run (0 of 3 budgeted), and no weekly slot was used. The run card is [`evidence/session_review_20261028b_run_card.json`](../../evidence/session_review_20261028b_run_card.json).

Core values applied: **Maximize P(Win)** — the blocked path is named, not forced. **Own the Outcome** — every blocker is listed with the decision that unblocks it.

## 1. Two blockers stop a unique TIFF — both need your decision

| # | Blocker | Verified evidence | What unblocks it |
|---|---|---|---|
| A | **No lane paragraph.** The protocol says "Your lane is the single method paragraph below." The text below that line is the starting-points list, not a method. | Read the full brief (this file's [source](../../knowledge/owner_brief_20261028.md)). | You supply the method paragraph, or pick one of the ranked leads in §3. |
| B | **Literal 70%/3-px gate is unpassable for any real candidate.** `reg-052` has 206,895 dots and covers 5,160,724 of 5,167,373 footprint pixels within 3 px (99.87%). Any 37,654-dot set must overlap ≥31,005 dots (**82.34%**); failure is forced from **22,164** dots upward. | `python scripts/registry_feasibility.py` re-run today; output identical to [`evidence/literal_bound_20261027.json`](../../evidence/literal_bound_20261027.json). | You decide the gate. Options are in §5. This session did **not** change any threshold. |

Consequence: the protocol says "log it as a duplicate and stop." Following that rule, no file is produced. Producing one labelled "research only" would repeat the earlier pattern and still fail the gate.

## 2. Why GEMSDOE32 B2 reportedly scored 0.2778 — verified mechanism, unverified score

**Verified lineage (reproduced today from pinned bytes, [`scripts/verify_focus_content_20261028.py`](../../scripts/verify_focus_content_20261028.py), output [`evidence/focus9_content_checks_20261028.json`](../../evidence/focus9_content_checks_20261028.json)):**

- B2 has 37,654 positive pixels. It is a **strict subset** of the 44,090-dot D2.8 raster in the GEMSDOE25 repository (`gems25-dotted-h19-5-d2-8…`). 44,090 − 37,654 = **6,436 removed; 0 added.**
- All 6,436 removed dots lie **1–2 px** from the USGS/INGENIOUS catalogue (`labels.tif`, 60,988 positive pixels). **No** kept B2 dot lies within 2 px of the catalogue.

**Code confirms the same mechanism.** `scripts/build_h6_submission.py` (line 63) applies a "200 m catalogue-flank exclusion" as `binary_dilation(catalogue > 0, structure disk r = 2 px)`, the same ≤2 px removal. Its comment says it was "validated: lifted the incumbent 0.2708→0.2778". No validation artifact for that comment was located, so it is an **unverified repository claim** (see §8).

**Why that could raise the score (metric reasoning, not a measurement):**

1. The official metric scores *new* faults that are not in the USGS database ([official problem page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)). A dot sitting on a *known* fault, with no hidden fault within 3 px, adds full weight to FP: `FP_w = Σ p(x)[1 − max_g k(d(x,g))]`, where `k(d)=max(1−d/3,0)`.
2. Weight 0.2 per FP unit versus 0.8 per FN unit means removing an unsupported dot helps unless it was the only credit for a hidden fault. The upper bound on FP reduction from removing the 6,436 dots is 0.2 × 6,436 = **1,287** weight units.
3. Whether TP is lost depends on how often a hidden fault lies within 3 px of a catalogue-adjacent dot (for example, a parallel splay or en-échelon strand). That is an empirical question.

**Score status:** the 0.2600 → 0.2778 difference is **OWNER-REPORTED**. No organizer receipt links these hashes to these scores. The owner page for GEMSDOE32 states the file is "already submitted — do not resubmit" ([owner page](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html)). The prompt treats it as a candidate to beat. These two statements are not reconciled.

**Can a new file beat 0.2778?** Not established. The removal lever is already used. Further gains need a hypothesis tested on holdout, not a leaderboard guess. A consistency check does support determinism: GEMSDOE25 and GEMSDOE30 have identical pixels and were both reported at 0.2600 (see §4).

## 3. Ranked candidate hypotheses (3 leads; none implemented or tested)

Rank = expected DTI improvement per unit implementation cost, with a qualitative basis only. No DTI number is projected.

| Rank | Layer(s) / data | Physical signature targeted | Why it should hit an off-catalogue fault | How it differs from what exists | Named non-fault mimic | Cost / gate |
|---|---|---|---|---|---|---|
| **1** | `labels.tif` (catalogue) + the dot raster; the segment-hide holdout tools already exist | **Flank-radius threshold sweep with a per-dot marginal-gain rule:** test removal radii 0, 1, 2, 3 px and 200 m as the catalogue-flank cut, choosing each dot's keep/drop by its marginal DTI gain on the holdout rather than a fixed radius. | Dots on known faults are FP for the new-fault target unless a hidden strand is adjacent; the cut is a threshold on distance to the catalogue. | Already tried at 2 px (B2 and H6, both hard cuts). `docs/research/lane36_20261025.md` attributes ≈ +0.007 to the B=2 prune; that matches the owner-reported 0.2708→0.2778 difference, but neither figure is validated here. The lane36 notes propose a *budget* curve (20k→80k dots). **Not found in the evidence:** a *radius* sweep judged on a segment-hide holdout. **Soft decay is de-prioritised:** the metric is linear-fractional in each dot's p except the max-credit TP, so a binary dot map is near-optimal. H6's docstring makes the same point. This is an argument, not a test. | Splay faults and en-échelon strands beside mapped faults would be removed wrongly. A 3 px cut removes more dots and risks more TP. | **Low cost.** Needs `scripts/evaluate_holdout.py`, a feature leakage canary and a segment-hide holdout. Strongest candidate because the mechanism is verified. |
| 2 | Cached DEM (`det_elev`, `det_elev_slope`, band map in `docs/research/band_map.txt`) plus the NGMDB geologic map | **Multi-contact displacement consensus:** two or more independent mapped contacts offset consistently across one corridor. | A consistent offset across independent contacts points to a fault that the catalogue lacks. | Repo tests contact orientation and crosscuts (MTO); a multi-contact matched-offset statistic is not implemented. | Depositional pinch-outs, unconformities, map generalisation, registration error. | Medium-high cost. Map coverage and rights are **not verified** for this session. |
| 3 | USGS observed groundwater levels (Water Data API) | **Persistent head discontinuity** across several wells and seasons, read as a low-permeability core. | An offset in hydraulic head independent of scarps can reflect a concealed barrier. | `src/gemsdoe36/gvsc_features.py` uses a **DEM-derived** hydraulic-head proxy, not observed wells. | Pumping cones, screen depth, recharge change, lithologic boundaries. | High cost. A one-well exploratory query returned one location and no time series. Coverage is **not** established. |

Not implemented anywhere in `src/` or `scripts/` (grep, 28 Oct): **Landsat thermal persistence** and **NGMDB multi-contact consensus**. Both appear only in review documents. Landsat remains a high-cost lead; scene coverage and processing rights are unverified.

**Recommendation:** if you assign a lane, lead with rank 1. It is the only candidate whose mechanism is supported by a verified lineage and whose test uses existing, validated tools.

## 4. Nine-site table — re-derived today, and one content duplicate

Re-run of [`scripts/audit_focus_uniqueness.py`](../../scripts/audit_focus_uniqueness.py) from pinned bytes (9 files fetched from GitHub commits by `scripts/fetch_pinned_focus_rasters.py`): output identical to the committed [`evidence/focus_sites_pairwise_uniqueness_20261026.json`](../../evidence/focus_sites_pairwise_uniqueness_20261026.json).

- **72 of 72 directed pairs** exceed the 70% dot-overlap ceiling. The lowest is **86.72%** (GEMSDOE27 → GEMSDOE32). **22 of 72** also exceed the |Spearman| 0.90 ceiling.
- **Content duplicate:** GEMSDOE30's raster and GEMSDOE25's raster have the same 44,090 positive pixels and identical in-footprint values. Only the outside-footprint encoding differs (GEMSDOE25 NaN, GEMSDOE30 zeros). Both are reported at 0.2600. Submitting both would be a duplicate.
- The GEMSDOE30 filename tag `91eae1ca` matches **GEMSDOE25's** SHA prefix, not its own (`8cf893ead566…`). This is an irregularity for review.

The public executive page now shows a data-derived "highest reported file" callout and the duplicate note ([executive guide](../executive-summary.html)).

## 5. Gate decision needed (I did not change any threshold)

The 70%/3-px rule compares against registry rasters that already cover almost the whole footprint. That makes it a gate no non-trivial candidate can pass. Options to decide between:

1. **Keep the literal gate.** Result: no submission is possible from any method in this family.
2. **Replace with a passable, pre-declared gate** (for example a 1-px tolerance, which the owner would state in advance). This must be decided before any experiment, to avoid choosing a gate after seeing results.
3. **Allow research-only TIFFs** marked "do not submit" with no gate, so experiments can run while the gate is decided.

## 6. Format validation — one real defect fixed

**Irregularity (fixed):** `scripts/validate_submission.py` relaxed the outside-footprint rule when a filename ended in `-zeros.tif`. Byte-identical rasters received different verdicts depending on name (verified: NaN-named file FAIL, zeros-named file PASS, 7,111,787 finite values outside the footprint in both). The official format says data outside the bounds is "null or nan" ([official submission format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)), and the organizer sample is NaN outside, with 0 finite values outside (checked). **Fix:** zeros-outside now requires an explicit `--zeros-mode`; the filename is ignored. Regression test: `tests/test_validate_submission_cli.py` (2 passed).

**Not fixed, flagged:** `scripts/audit_release.py` uses the same filename rule for archived format audits. I did not change it because it writes archived audit evidence, and changing it would alter published records without re-review.

**Still unknown:** the reported portal error "Predicted values must be in range [0, 1]". No rejected file or portal trace is available. Historical zeros-outside files, including B2 (owner-reported as scored), are not what the official text describes. Whether the portal accepts zeros outside is **unverified**. Do not treat either profile as proven.

## 7. Rules verified from the official PDF (September 2026)

- Source: [official rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) (also linked from [HeroX](https://www.herox.com/GEMSPrize/resource/2274)); the [DrivenData rules page](https://www.drivendata.org/competitions/306/competition-doe-gems/rules/) links to it.
- §3.2: a single GeoTIFF with a single raster layer at 100 m; "three submissions per week" per the competition website limits.
- §1.1 and §3.2: **"Participants will submit a single entry"**; the score is evaluated on the chosen submission. A.3: awards go to one "designated primary submitter."
- A.5(1): the submission is "an original work by the competitor," with third-party content disclosed.
- §3.2: generative-AI use must be indicated in the narrative.

**Compliance flag for review (not a finding of misconduct):** this repository's portfolio includes many separately hosted GitHub Pages sites under different account names, some sharing identical rasters. That may conflict with the single-entry and original-work terms if one person or team controls them. Please review with the rules and counsel before any further upload from any of them.

## 8. Irregularities flagged for review

1. Parallel-protocol lane paragraph absent (§1A).
2. Literal gate guaranteed to fail above 22,163 dots (§1B).
3. GEMSDOE30 is content-identical to GEMSDOE25 (§4).
4. Validator filename bypass (§6) — fixed; `audit_release.py` open.
5. Official outside-bounds rule vs. historical zeros-outside files (§6).
6. Portal "[0, 1]" error cause unknown (§6).
7. Prompt leaderboard figures (0.3195, 0.4413) conflict with the public top of **0.4544** on 28 Oct ([leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)); the prompt's figures are not verified.
8. GEMSDOE32 owner page says B2 is already submitted; the prompt treats it as a candidate. Not reconciled.
9. HOLDOUT-DTI is not comparable across repositories. The GEMSDOE32 owner page uses `GEMSDOE32-HIDE-RECOVER-v3.0` with a Champion of 0.099202. This repo's S2D-36 uses `gems-segment-pooled-v1` at 0.200766. Different evaluator versions.
10. GEMSDOE32 owner page claims H51-1-EWSP beats the Champion on its holdout and passes 610 detector rasters. Not reproduced here; the owner marks it DO NOT SUBMIT.
11. Registry `local` paths point to `data/registry/scored/`; `restore_data.py` writes `data/raw/scored/`. `audit_focus_sources.py` also needs solo files that were not restored, so **it was not re-run** this session.
12. Compliance flag on multi-account portfolio (§7).
13. `scripts/build_h6_submission.py` line 63 states the 200 m flank exclusion was "validated: lifted the incumbent 0.2708→0.2778". No validation artifact for that statement was located. It is a self-reported figure, not a verified result.

## 9. Sources checked this session

| Source | Status | Link |
|---|---|---|
| Official problem and metric | Fetched, both pages | [page/967](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) |
| Official rules PDF | Fetched; §1.1, §3.2, A.3, A.5 read | [PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) |
| Public leaderboard | Fetched 28 Oct; top 0.4544 | [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) |
| GEMSDOE32 owner page | Fetched; B2 claim owner-reported | [index](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) |
| GEMSDOE36 owner page | Fetched; nine-site table | [docs](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/) |
| Pinned nine-site bytes | Fetched from GitHub commits; hash-prefix matched | [`scripts/fetch_pinned_focus_rasters.py`](../../scripts/fetch_pinned_focus_rasters.py) |
| Competition data (template, labels) | Restored from SHA-pinned owner mirrors; **not organizer-authenticated** | [`registry/data_manifest.json`](../../registry/data_manifest.json) |
| GeoDAWN | Not fetched this session | [USGS](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) |
| DOE GDR 1391 | Not fetched this session | [gdr.openei.org](https://gdr.openei.org/submissions/1391) |
| USGS Water Data API, Landsat L2 | Not fetched this session | — |

## 10. Next actions

- **Needs you:** the lane paragraph (or a choice of rank 1–3) and the gate decision in §5. Then one experiment (rank 1 holdout, with leakage canary) fits the 3-experiment budget.
- **Engineering, no approval needed:** fix `audit_release.py`'s filename rule with a re-review plan; make `restore_data.py` and the registry paths agree; restore the remaining focus files so `audit_focus_sources.py` runs.
- **Compliance:** review the multi-account and identical-raster issue (§7) before any further upload from any of those repositories.
