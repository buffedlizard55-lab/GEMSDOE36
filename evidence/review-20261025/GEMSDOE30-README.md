# GEMSDOE30 — DOE GEMS fault-discovery research

## START HERE — latest attempt **DUPLICATE-STOP; DO NOT SUBMIT**

**No new unique/approved competition TIFF was published.** The fixed TDX-C2
candidate crossed the mandatory duplicate limit, so all experimentation stopped.
It was **not** re-encoded, renamed, perturbed, or replaced with a better-looking
control. **No competition slot was selected or used.**

**[Open the site](https://buffedlizard55-lab.github.io/GEMSDOE30/) ·
[Executive submission guide](executive-summary.html) ·
[Latest scientific review](experiment-review.html) ·
[Final JSON run card](docs/research/texture-controls/run-card.json)**

**Archived download only:** [previous-session TDX-1 research TIFF](docs/downloads/gems30-TDX1-44090-20261025-5fc508ea81ac.tif).
It remains format-valid and downloadable for reproducibility, **not approved for
competition upload**, and is **not a new submission from this session**. The
latest duplicate's TIFF is deliberately private under ignored `outputs/`.

Read the [complete owner prompt](#current-owner-prompt), [current pointers](docs/current-run.json)
and [frozen TDX-C2 plan](docs/research/texture-controls/preregistration.md) before
working on this project. **Maximize P(Win):** protect organizer feedback slots for
unique reproducible improvements. **Own the Outcome:** deliver honest negative
results and automated decisions, not a manual-inspector handoff.

### Latest evidence — one fixed experiment, four arms, no tuning

All performance numbers in this table are **HOLDOUT-DTI**, evaluator
`component-holdout-v3-blockstats-20261025`, protocol
`buffered-quadrant-whole-components-v1-20261025`, **60,988** withheld positive pixels,
with **95% paired spatial-bootstrap CI**. This is a catalogue proxy on previously
inspected folds—not an organizer score, projection, or independent confirmation.

| Fixed arm / difference | HOLDOUT-DTI | 95% CI |
|---|---:|---|
| **TDX-C2: core19 + three magnetic displacement features** | **0.136061** | **[0.120028, 0.152034]** |
| Same-protocol core19 comparator | 0.139821 | [0.124178, 0.155905] |
| Matched zero-lag control | 0.136713 | [0.122039, 0.151906] |
| Matched local Fourier-phase control | 0.140185 | [0.124203, 0.155878] |
| Candidate − core19 (paired HOLDOUT-DTI difference) | −0.003760 | [−0.008176, 0.000704] |

**Interpretation:** no positive paired lower bound against any control; no
established incremental displacement benefit. The intervals cross zero: do not
call this statistically significant inferiority or select the phase control.

| Automated diagnostic (not a performance score) | Result |
|---|---|
| Observed registry | 179 source TIFFs; 164 distinct aligned byte sequences; one unaligned exclusion; all nine priority sites snapshotted; +2 post-stop S20 arrivals = 166 observed comparisons |
| Before-placement surface comparison | Max Spearman 0.156573; threshold not crossed; original/private surfaces still missing |
| Final-dot comparison | Max Spearman 0.063833; **79.090497%** within 3 px of G30-S19 — **DUPLICATE-STOP** (>70%) |
| Individual canaries | 28 distinct features × 4 folds; max bidirectional AUC 0.643433; no alarm above .90 |
| Local stopped-file validator | Passed: no NaN inside, values [0,1], exact CRS/shape/transform, one float32 band, NaN outside, zero positive catalogue pixels |
| Artifact distribution | **Not published; not downloadable.** Stored validator receipt is not a current public-byte reinspection |
| Execution budget | One experiment/four frozen arms; 373 seconds UTC start-to-stop; no second experiment |
| Approval | **Negative.** Format validity and a new SHA-256 cannot rescue duplicate/performance failures |

The mandatory stop takes precedence over manufacturing a “unique TIFF” delivery.
The accepted deliverable is the negative experiment and machine-bound JSON card,
not a falsely certified upload. No current portal limit, eligibility, deadline,
acceptance receipt or leaderboard value was invented.

[PR #30 — verified code review and delivery timeline](https://github.com/buffedlizard55-lab/GEMSDOE30/pull/30)

### Why H33 may have improved

Reproduced again: its **37,654-dot support** equals the **40,199-dot GEMSDOE28 base**
with all dots at catalogue distance ≤2 px deleted—**zero support mismatches**.
GEMSDOE25/30 and GEMSDOE28/31 references also have identical in-footprint values.
These are raster diagnostics, not scores. Pruning can save FP mass while preserving
max-kernel truth coverage; it can also remove genuine splays. This does not identify
a hidden-test cause or establish a new geological discovery. The owner's **0.2778**
attribution remains **unverified**, not ORGANIZER-CONFIRMED. [Detailed mathematical
analysis and all nine audited references](docs/research/texture-controls/review.md).

### Autonomous inspection (CPU, Python 3.11+)

```bash
python -m venv .venv
.venv/bin/pip install -e '.[research,test]' -c requirements-tdx1.txt
# Only the small pinned template is required for all publication checks.
.venv/bin/python scripts/restore_public_mirrors.py --ids sample_submission
.venv/bin/python scripts/verify_current_run.py
.venv/bin/python scripts/verify_stopped_attempt.py
.venv/bin/python scripts/build_research_site.py --check
.venv/bin/python -m pytest -q
# Both deliberately exit 2: no eligible competition candidate.
.venv/bin/python scripts/verify_current_run.py --require-promote
.venv/bin/python scripts/verify_stopped_attempt.py --require-promote
```

`verify_current_run.py` reopens the actual **retained archive**, rechecks its hash
and recomputes its uncertainty. `verify_stopped_attempt.py` recomputes the latest
holdout/canary/duplicate decision from immutable receipts, without claiming the
private TIFF is distributed. Add `--inspect-quarantine` only where ignored local
bytes exist to reopen them too. No human-inspector override, clipping workaround,
competition authentication or uploader exists.

The builder `scripts/run_texture_controls.py` intentionally refuses to overwrite
an already registered/stopped execution. Its exact executed version is frozen at
commit `79d1be92e578f4e555fe5a5ae8d273728221c8af`. A subsequent audit-only finalizer
fixed negative run-card logging; **no refit or replacement TIFF followed the stop**.
The shared evaluator/writer are `src/gemsdoe30/{holdout,submission}.py`; the literal
template filenames in the prompt are absent, so those shared equivalents are reused.

### Sources, constraints and next session

- Official GitHub [reference notebook](https://github.com/drivendataorg/gems-prize-reference-solution/blob/aebe92f7c8a990f0e3443451b7a825d9afd6336b/unet-mc-cv-reference-solution.ipynb)
  retrieved again: [hashes, saved band metadata and exact excerpts](docs/research/texture-controls/official-source-audit.json).
- Four ranked prospective geological hypotheses were frozen before implementation;
  only the habitat-conditioned displacement-specificity test ran. All use existing
  cached bands; no inaccessible external dataset was claimed viable.
- [Full results / bootstrap statistics](docs/research/texture-controls/results.json),
  [registry](docs/research/texture-controls/registry.json),
  [readiness](docs/research/texture-controls/readiness.json),
  [three-pass journal](docs/research/texture-controls/verification.md),
  [source/irregularity boundaries](docs/irregularities.md).
- Data placement is not the old blocker: pinned owner mirrors were restored and
  prepared, then verified cell-for-cell. Integrity ≠ organizer authentication.
  Large training data, arrays and stopped TIFFs remain ignored.
- The prompt omits an identifiable assigned-lane paragraph. This was an autonomous
  continuation of the previous next step, not an asserted external allocation.
- Complete private/parallel surfaces, the historical-best checkpoint, untouched
  evaluation regions and current organizer constraints remain unavailable. GPU is
  not required for this fixed CPU experiment; legacy UNet training is separate.
- Network access excludes DrivenData/USGS/GDR/NLR hosts. Official links are retained
  for review, not freshly verified claims. Fault mapping is not geothermal-vent
  detection: no temperature, permeability, flow or vent observations were used.

**Next session, in order:** preserve the stop; synchronize externally assigned lanes
and original continuous surfaces; restore a comparable historical-best model;
reserve untouched spatial evaluation; only then preregister a distinct mechanism
with matched physical controls. Do not move dots or rename this duplicate to pass.
Research promotion and a real weekly slot remain separate decisions.

### Concurrent PR #29 records retained (G30-S20)

Main advanced during this audit. The [G30-S20 run card](docs/research/2026-10-25-s20/run-card.json),
[analysis](docs/research/2026-10-25-s20/analysis.md) and two research TIFFs are
preserved as **peer records**, not new outputs or approved selections by this lane.
S20 also records a duplicate-stop against G30-S19; its different component-holdout
results are not ranked against the buffered TDX-C2 regional trials. No peer
`promote` claim allocates a weekly slot here. The retained TDX-1 addendum honestly
marks its missing continuous-surface comparisons against those arrivals unknown.
TDX-C2's saved states were checked against both post-stop arrivals: 166 total
observed comparisons, same maximum overlap. No model or dot changes followed.

---

> **Historical archive below.** Older status, score projections, zero-outside
> “ready” copy and data-placement blockers are retained as history, not current
> operating instructions. The current pointer, automated gates and TDX-1 report
> above supersede contradictory historical statements. Quoted owner text records
> requirements/claims, not verified scientific facts or organizer receipts.





## Concurrent main-branch lanes — retained records, not selected by TDX-1

The following session records were merged into main while this lane was running.
Their different evaluators/folds/budgets are **not comparable rankings** against TDX-1.
Their leaderboard/rules reads are recorded claims from those sessions, not a fresh
DrivenData lookup or organizer submission-page receipt by this lane. No slot was
selected here; TDX-1 remains negative. The current pointer above selects only TDX-1.

<details>
<summary>Preserved concurrent-session README notes (main at 7f3f4c7)</summary>

# GEMSDOE30 — DOE GEMS fault-discovery research


## START HERE — 2026-10-25 (Candidate C / Lane G30-S19 PROMOTED; A & B negative)

**✅ OK TO DOWNLOAD & SUBMIT — Candidate C:** [gemsdoe30-g30s19-habitat-edge-60000dots-20261025T210221Z-b527922d7f-zeros.tif](docs/downloads/gemsdoe30-g30s19-habitat-edge-60000dots-20261025T210221Z-b527922d7f-zeros.tif)
(SHA-256 `8a0301d5…f43cc9`; note: `G30-S19 habitat GBM (19-band, no catalogue-distance inputs) + EDGE 60k, off-cat >2px`).
HOLDOUT-DTI **0.2230 [0.2052–0.2396]** (component-holdout-v2, 20,870 withheld) vs proximity 0.1672 / Poisson 0.1945; canaries 43/43 clean; novelty vs H33 ρ=0.025/34.9% and vs A/B ρ≤0.007. Local proxy only — not a score; live leader 0.4413 (below). Evidence: [run card](docs/research/2026-10-25/lane-g30s19-run-card.json) · [analysis](docs/research/2026-10-25/lane-g30s19-analysis.md) · [preregistration](docs/research/2026-10-25/lane-g30s19-preregistration.md). No slot used; owner submits.

**Read every session before working:** this README, [OWNER_BRIEF.md](OWNER_BRIEF.md), and the [session report](docs/research/2026-10-25/session-report.md).

**Status in one place**

- **Candidate A — branch `arena/6a5f04fe-gemsdoe30` (residual-ridge gate):** [gemsdoe30-h3a-residual-ridge-gate-p400-7a88865b-nan.tif](docs/downloads/gemsdoe30-h3a-residual-ridge-gate-p400-7a88865b-nan.tif). Valid and unique in this repository. Holdout verdict negative: HOLDOUT-DTI 0.1222 [0.1139, 0.1306] against count-matched proximity 0.1770 [0.1681, 0.1857]. Not recommended.
- **Candidate B — branch `arena/6a157983-gemsdoe30` (H-CC1 dispersed 3 px, PR #25, merged to `main`):** [gemsdoe30-h-cc1-dispersed3px-32058dots-nan.tif](docs/downloads/gemsdoe30-h-cc1-dispersed3px-32058dots-nan.tif). Passes the local format validator (EPSG:32611, 3730×3292, float32, values 0–1, NaN outside). Holdout negative: HOLDOUT-DTI 0.0539 [0.0507, 0.0572], below a matched random control at 0.0659 [0.0631, 0.0687]. Not recommended.
- Labels are HOLDOUT-DTI (catalogue proxy), not competition scores. Neither candidate has an organizer score.
- **Official leaderboard** (read 2026-10-25): #1 = 0.4413. The prompt's "0.3195 is highest" matches only a 2026-10-03 snapshot (IR-30-057, IR-30-072).
- **Blockers:** training data must come from the owner's own DrivenData download (current restored copy is from public mirrors; see IR-30-056). The parallel-run method lane is not in the request (IR-30-058). The parallel registry is partial (IR-30-062).
- **Rules that govern uploads** (official PDF, as recorded in branch `6a157983`): one final entry; up to three feedback submissions a week; an AI-use disclosure is required. Source: <https://docs.nlr.gov/docs/fy26osti/96647.pdf>. Session A's rules check confirmed a single entry scored in both phases and U.S. eligibility.

**Standing request, condensed (not verbatim; the verbatim brief is in OWNER_BRIEF.md):**
produce a unique, format-valid GeoTIFF that is easy to download and submit; explain why the
GEMSDOE25/32 family scored well and whether a distinct method can beat 0.2778 (owner-reported)
and the official top 0.4413; generate 3–5 ranked geological hypotheses before implementing; validate
the top candidate on a spatially blocked holdout before spending any weekly slot; label every number
as HOLDOUT-DTI or ORGANIZER-CONFIRMED; flag irregularities; no manual input; no hallucinated facts.
Core values: *Maximize P(Win)* and *Own the Outcome*.

## Previous decision (2026-10-25, before this session)

**NOT APPROVED FOR SUBMISSION. No new unique TIFF was generated in that review.**
Historical downloads are educational references, not new submissions. The current
owner protocol takes precedence over contradictory ready-to-submit language in
older sections below. Read the [current owner-request amendment](docs/research/2026-10-25/owner-request.md)
at the start of every session (a requirements record, not a verbatim transcript).
The prior literal brief is preserved below for history.


**Candidate A — details**

| Item | Value |
|---|---|
| Download | [`docs/downloads/gemsdoe30-h3a-residual-ridge-gate-p400-7a88865b-nan.tif`](docs/downloads/gemsdoe30-h3a-residual-ridge-gate-p400-7a88865b-nan.tif) |
| Submission name | `gemsdoe30-h3a-residual-ridge-gate-p400-7a88865b` |
| Submission note (79 chars) | `GEMSDOE30 review-hyp3 residual-ridge gate, 3km catalogue corridor, 400m Poisson` |
| SHA-256 and validator | in the [run card A](docs/research/2026-10-25/run-card-residual-gate.json) (validator passed; independent rasterio re-read agrees) |
| Holdout (HOLDOUT-DTI, `component-holdout-v2-footprint-20261025`, 20,870 withheld positives, stand-in split) | candidate **0.1222** [0.1139, 0.1306] vs count-matched proximity comparator **0.1770** [0.1681, 0.1857] — **not promoted** |
| Duplicate checks | no duplicate (9-site registry and 12 repo TIFFs, including candidate B: Spearman −0.001, 10.2 % within 3 px); surface-stage check blocked; registry partial, so **no novelty certificate** |
| Organizer score | **none** — NOT ORGANIZER-CONFIRMED |

Raw data placement and preparation succeeded using the existing hash-pinned owner
mirrors; the current worktree was independently restored and prepared again on
2026-10-25. Do not treat the prompt's old data-placement blocker as current.
`data/raw/` and `data/processed/` are Git-ignored and are not distributed by
GitHub Pages; status-feed availability means present in the builder worktree at
generation time only. Organizer authentication is not established by mirror
hashes. No new geological experiment was run because the current method lane and
complete parallel registry are missing.
Requested shared-template filenames are absent; existing shared modules were reused.
Read first: [executive summary](executive-summary.html) · [candidate design, pre-registration and result](docs/research/2026-10-25/candidate-residual-gate.md) · [live official facts](docs/research/2026-10-25/live-verification.md) · [run card A](docs/research/2026-10-25/run-card-residual-gate.json) · [irregularities IR-30-066 to IR-30-077](docs/irregularities.md).

- **Live public leaderboard** (retrieved 2026-10-25): #1 **0.4413**. The owner's **0.3195** matches a 2026-10-03 snapshot, not today's table.
- **Historical 0.2778 claim** (GEMSDOE32 H33-B2): unverified. Its support matches a GEMSDOE28 reference after a 2-pixel catalogue-flank deletion (zero mismatching pixels), so it is emission pruning, not a new signal ([review](docs/research/2026-10-25/review.md)).
- Data placement works: pinned owner mirrors restore with SHA-256 checks (`scripts/restore_public_mirrors.py`), and `scripts/prepare_data.py` completes. Mirror integrity is not organizer authentication.
- Three experiments and the two-hour budget are used. Negative results are recorded as deliverables.

**Next session (in order):** (1) assign or declare a method lane (IR-30-073); (2) decide the buffer rule for catalogue-gated features, since a 3.5 km strict buffer structurally zeroes them (IR-30-066), and preregister it before reading results; (3) confirm the known-fault mask rule against the rules or forum (IR-30-071); (4) rebuild continuous surfaces so the pre-placement duplicate check can run (IR-30-069); (5) implement review hypothesis 1 (cross-contact texture displacement) with feature canaries first; (6) a single organizer-authenticated format check is the only way to test the portal range error (IR-30-074), and it costs a slot. Promotion and slot selection remain separate, and no leaderboard value is claimed here.

**Reproduce the candidate** (after `pip install numpy scipy rasterio shapely pyproj pytest` in a venv): `python scripts/restore_public_mirrors.py && python scripts/prepare_data.py && PYTHONPATH=src python scripts/residual_gate_holdout.py --buffer-m 0 --out docs/research/2026-10-25/residual-gate-holdout-buffer0.json && PYTHONPATH=src python scripts/build_residual_gate_candidate.py && python scripts/make_run_card.py`.

---


</details>

## Earlier readiness audit — archived, before TDX-1 (2026-10-25)

**NOT APPROVED FOR SUBMISSION. No new unique TIFF was generated in this review.**
Historical downloads are educational references, not new submissions. The current
owner protocol takes precedence over contradictory ready-to-submit language in
older sections below. Read the [current owner-request amendment](docs/research/2026-10-25/owner-request.md)
at the start of every session (a requirements record, not a verbatim transcript).
The prior literal brief is preserved below for history.

- [Current nine-site scientific review and four prospective hypotheses](docs/research/2026-10-25/review.md)
- [Submission guide](executive-summary.html) · [Run card](docs/research/2026-10-25/run-card.json)
- [Exact historical duplicate audit](docs/research/h33-historical-duplicate-audit.json)
- [Pinned nine-site artifact registry — explicitly partial](docs/research/priority-site-pins.json)

Raw data placement and preparation succeeded using the existing hash-pinned owner
mirrors. Do not treat the prompt's old data-placement blocker as still current.
Organizer authentication is not established by mirror hashes. No new experiment
was run because the current method lane and complete parallel registry are missing.
Requested shared-template filenames are absent; existing shared modules were reused.

The shared pooled holdout footprint bug was fixed in
`src/gemsdoe30/holdout.py` (version `component-holdout-v2-footprint-20261025`).
Old metrics are historical, not automatically comparable or valid promotion gates.
The GEMSDOE32 historical reference overlaps the GEMSDOE28 reference at **100% of
its dots within 3 pixels**, with rank correlation **0.967587** (novelty diagnostics,
not scores). Re-encoding/renaming that family does not satisfy the new protocol.

**Next session:** resolve the assigned lane/shared-template location; synchronize
all parallel registry rasters and surfaces; preregister buffered segment folds;
run single-feature leakage canaries and rerun the best comparator with the fixed
evaluator before any candidate experiment. Maximum three experiments/two hours.
Research promotion is separate from weekly slot selection. No current leaderboard
value or private portal acceptance is claimed here.

---

> **Complete persistent project brief — read the literal owner brief in the section *Read first — owner brief (verbatim)* and this section before every project session.** These are the standing scope, scientific, operational, and integrity requirements from the project request—not a session-status summary. Preserve every acceptance criterion when changing this brief. Keep `docs/score-ledger.csv`, `docs/irregularities.md`, and the linked official sources in sync when updating claims.

## Read first — owner brief (verbatim)

<details>
<summary><b>Literal owner brief (click to expand; re-read at the start of every session)</b></summary>

> **Objective and standing request.** Review the repo. There should be an easy to download
> submission tif file as described by the prompt. Read the entire prompt.
>
> **Metric-shaped loss.** Train against a loss shaped like the metric's own geometry. The
> competition scores within a 300 m kernel, not by exact pixel overlap — but plain cross-entropy
> or Dice optimizes for exact overlap, a different target than what's actually being rewarded.
> Kervadec, Bouchtiba, Desrosiers, Granger, Dolz, and Ben Ayed's boundary loss (2018) was built
> for precisely this kind of mismatch on other severely unbalanced segmentation problems:
> instead of summing over regions — which the paper shows produces loss contributions differing
> by orders of magnitude between a rare positive class and the dominant background — it computes
> a distance metric over contours, rewarding proximity to the true boundary, and the paper reports
> measurable gains in both accuracy and training stability under exactly this kind of imbalance.
> Implement a version using a distance transform built on the actual 300 m kernel radius, combine
> it with the existing regional loss rather than replacing it (as the original paper recommends),
> and check on holdout that it changes which near-misses the model is willing to make — it should
> start rewarding a prediction that lands close to, not exactly on, a held-out fault, since that's
> the credit the real metric already gives.
>
> **Highest-score study (the core question).** WE NEED TO STUDY, ANALYZE, AND UNDERSTAND THE
> HIGHEST SCORE FROM THE GEMSDOE SITE WHERE THE SUBMISSION TIF IS DOWNLOADED FROM WHICH IS
> `https://buffedlizard55-lab.github.io/GEMSDOE25/` — `dotted-h19-5-d2-8-20261002-e56ea318af89-nan: 0.2600`.
> Why and how did this get the highest score and are we able to generate a submission that scores
> higher than 0.26? Answer using PhD-level experience, knowledge and judgement. The leaderboard is
> `https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/`.
> **0.3195 is the highest score right now**, so design a new strategy, research, testing, analysis
> and submission system that is unique and can score higher than 0.3195.
>
> **Hypotheses before implementation.** Generate 3–5 candidate geological hypotheses we haven't
> tried yet, each naming: the specific layer(s) involved, the physical signature being targeted
> (e.g. an edge-detection or curvature transform), why it should catch a fault missing from the
> USGS/INGENIOUS catalogue rather than one already in it, and how it differs from anything already
> implemented in this repo. Rank them by expected DTI improvement and implementation cost.
> Validate the top candidate on our spatially-blocked holdout set before touching a weekly
> submission slot — do not spend a submission slot on an idea that hasn't beaten the current
> holdout best. If a candidate can't be validated without new external data, name the specific
> free, official source needed and check it's obtainable before proposing the idea as viable.
>
> **Integrity and verification.** Work line by line verifying from official verified trusted
> sources, provide links for manual review. There should be no manual input, work on your own to
> complete tasks. Flag any irregularities for review. No hallucinations. Verify no hallucinations.
> The goal of this project is to get a full list that follows our requirements.
>
> **Deep research.** We need to start doing heavy and deep research into the part of the project
> that matters most: the scientific discovery of geothermal vents. Store all information and
> knowledge gathered from official verified sources. Think outside the box but stay grounded in
> proper scientific research; we are aiming for a top prize that many others compete for, so it is
> important to be contrarian but smart. Find data sources others overlook. Do deep research and
> critical thinking and come up with new hypotheses to test.
>
> **Site and submission.** The site should be able to generate a TIF file required for submission:
> as easy as clicking a file to submit into the competition. This must be obvious at the very
> beginning of the site / in the executive summary. *(A previous attempt returned the portal error
> "Predicted values must be in range [0, 1]".)* Give it a unique name and a short comment to help
> tell submissions apart (e.g. "clustering with k=25"). Create an executive-summary subpage that
> explains exactly how to make a submission. Include a clean, user-friendly, simple GitHub Pages
> site with all relevant information in an easy-to-read format with official verified links, kept
> up to date automatically instead of by manual checking.
>
> **Competition facts to respect.** Overview and problem description
> `https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/`; about page
> `page/968`; data tab `/data/`; rules PDF `https://docs.nlr.gov/docs/fy26osti/96647.pdf`;
> reference solution `https://github.com/drivendataorg/gems-prize-reference-solution`; GDR 1391
> `https://gdr.openei.org/submissions/1391`.
>
> **Reported submission history supplied by the owner** (all owner/user-reported and unverified;
> retained in `docs/score-ledger.csv`): GEMSDOE `gems-submission-20260925T001403Z-7f00890a` 0.1563;
> 6GEMSDOE `gems6_hgb88-topk03_33cec71ff0` 0.0286; GEMSDOE3 `pindrop-v4-nodes-20260925T152420Z-f347b70daa`
> 0.1193, `pindrop-v4-discovery-20260925T152423Z-37f9d5b855` 0.0830, `pindrop-v4-ridge-20260925T152422Z-4e03fc9705`
> 0.1152; GEMSDOE2 `gemsdoe2-dual-family-union-20260925T160406Z-f68e590f` 0.1560; GEMSDOE4
> `gems-submission-20260926T163915Z-237f0063` 0.0343; 5GEMSDOE `gems-submission-20260926T175114Z-7f00890a`
> 0.1563; 7GEMSDOE `lidarscarp-ridge-top2pct-36c3a3f341c8` 0.1461; 8GEMSDOE `Hedge-v2_submission` 0.1563;
> GEMSDOE9 `2314b599` 0.0107; 11GEMSDOE `gems-structural-area06-v1` 0.0202; 12GEMSDOE
> `r7-nms3-dem10-scarp_0c9199f14e62` 0.1294 (and `_allfinite` 0.1294); 15GEMSDOE
> `gems-tso1-20260929T005627Z-conj_alteration_mag` 0.0782; 14GEMSDOE
> `GEMS_r5-geom-horse-ensemble_20260929T154852Z_ccbe1de0_site_e96e942f` 0.0020; 17GEMSDOE
> `17GEMSDOE_F-ensemble-2pct_20260930T050626Z` 0.0187; 18GEMSDOE `H19-C_20260930T212401Z_c11e495e` 0.0297;
> 19GEMSDOE `h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa-nan` 0.1894,
> `h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan` 0.1922; GEMSDOE10
> `h16-continuation-20260927T065521077735Z-3431b83c7c` 0.0461, `h20-dem10-scarp-thin-20260927T155223039488Z-ffc91a1686` 0.0921,
> `H25-ctx-ridge-20260927T232947704150Z-6452ae1d00` 0.1280, `h28-dotted-ridge-20260928T020256236880Z-6452ae1d00` 0.1839;
> 13GEMSDOE `20261001_r13-lattice-s5_v2_nan-outside` 0.0904; 16GEMSDOE
> `h16-1-topo-geophys-baseline-ridges-20260930-df20f65e-nan` 0.1855, `h18-3a-topo-geophys-x-complexity-prior-20260930-c502dfab-nan` 0.0976,
> `h18-4-usgs-geologic-map-faults-gap-20260930-aef8f42c-nan` 0.0360; GEMSDOE21 `h19-4-reference-20260930-691e4dfa` 0.1894;
> 20GEMSDOE `h20-1-sarnnpu-powerlaw-pi0363-tilt-wingcrack-20260930-be0e8f6b-nan` 0.1890,
> `h20-5-continuous-pu-proxy-unverified-20260930-824ce73a-nan` 0.1859; GEMSDOE22
> `h23-a-dti-optimal-emission-6pct-20261002-e2ec4b49-nan` 0.1002, `h23-b-dti-optimal-emission-10pct-20261002-86176698-nan` 0.0748;
> GEMSDOE23 `h30-arrangement-matched-habitat-20261002-0d4e02e8-nan` 0.1352; GEMSDOE24
> `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan` 0.2477; GEMSDOE25
> `dotted-h19-5-d2-8-20261002-e56ea318af89-nan` 0.2600; GEMSDOE26
> `dilcond-oof-v1-20261003-47629f496133-nan` 0.1223; GEMSDOE27
> `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan` 0.2449; 28–33GEMSDOE scores not yet supplied.
>
> **Core values.** *Maximize P(Win)* — weigh tradeoffs, assess risk, choose the path that
> maximizes the probability of winning. *Own the Outcome* — own results end to end, act without
> waiting for permission, treat failure and success as signals. Work in three cumulative passes:
> implement and verify; review for bugs, missing requirements and edge cases; re-check the whole
> implementation against the original request and fix what remains. Then open a pull request from
> `arena/01a10289-gemsdoe30` and merge it to `main`, and state what work remains and what limits it.

The distilled, non-negotiable acceptance criteria that follow from this brief are in
**Mission and non-negotiable requirements** below; if the two ever disagree, the literal brief above
wins and the distilled list must be corrected.

</details>

> **Branch note:** the literal owner brief above preserves the branch name recorded in the original request. This Arena session is fixed to `arena/01a103c1-gemsdoe30`; all changes, commits, pushes, and any PR from this session remain on that assigned branch. The brief's verbatim wording is preserved above unchanged.

## Mission and non-negotiable requirements

1. **Objective and historical review:** build an auditable, scientifically grounded workflow to identify previously unmapped geological faults in the DOE GEMS / GeoDAWN region and pursue a result above the user-reported 0.3195 public-leader score. Study the reported GEMSDOE25 D2.8 result and historical submissions; authenticate score-to-file attribution using a submission receipt, ID, hash, or equivalent evidence rather than assuming a score belongs to a named TIFF. Treat public leaderboard snapshots as dynamic feedback, not the private test set or the final award decision. Develop a defensible path to improvement, but never promise a score or prize.
2. **Metric-aware learning:** the official public metric is a distance-weighted Tversky index with a triangular 300 m support kernel on 100 m pixels, `alpha=0.2`, `beta=0.8`. Prefer training objectives that represent this geometry. Pair any distance/boundary term with a regional loss; compare them under a spatially blocked holdout and report how their near-miss behavior changes. A synthetic unit probe is not a real holdout result.
3. **Submission first:** when a scientifically promoted candidate exists, make a single-band float32 GeoTIFF with probabilities in `[0,1]`, on the exact sample-template CRS, shape, bounds, and transform; put null/NaN only outside the valid footprint. Check for NaN/Inf *inside* the footprint, which can trigger the portal's “Predicted values must be in range [0, 1]” error. Make the download and the submission instructions obvious at the top of the site. Give every run a unique filename and a short paste-ready submission note.
4. **No slot without evidence:** pre-register 3–5 genuinely distinct geological hypotheses. Each must state the exact layers, physical signature, why it could indicate a fault absent from USGS/INGENIOUS, what makes it different from prior work, likely DTI change and cost, official data source/license/access status, and a falsifiable holdout gate. Validate the leading candidate against the current spatial-holdout best, with confirmation, before spending a weekly submission slot. No holdout pass means no slot. Beyond the private holdout, require **three types of verification**, each with a pre-stated promotion criterion — spatial block-validation, probability calibration, and feature-perturbation stability — plus a qualitative note showing where a learned change helps and where it fails; the standing protocol is [docs/research/verification-protocol.md](docs/research/verification-protocol.md).
5. **Research and provenance:** use free, publicly accessible, official or otherwise authoritative data where allowed. Verify claims against the relevant official/primary source line by line where possible; store exact citations/URLs, access and licensing checks, source hashes, experiment protocols, results, and irregularities. Distinguish official facts from user-supplied claims, owner-mirror evidence, hypotheses, and model estimates. Record unavailable files, failed downloads, and other blockers. Never invent a score, source, file hash, access result, or holdout result.
6. **Competition integrity:** respect the rules and source terms. Do not bypass the DrivenData login, collect or store account credentials, submit files, or consume competition slots on the user's behalf. Public leaderboard values are time-stamped snapshots; do not build a robot/spider that monitors DrivenData.
7. **Autonomous execution and accountability:** complete what can be done without asking for manual input; identify hard blockers rather than disguising them. Review work in three cumulative passes: implement and verify; inspect bugs/edge cases; re-check against this brief and fix. Flag every unresolved irregularity.
8. **Core values:** **Maximize P(Win)** by choosing evidence-driven work with a plausible path to generalization, not by chasing attractive but unverified claims. **Own the Outcome** end-to-end: record failures, fix defects, keep the user-facing path usable, and state what remains blocked.
9. **Project governance:** use this repository as the research and submission-tooling home. Keep private/large competition data and generated rasters out of Git. The final competition entry must satisfy all eligibility, documentation, AI-disclosure, and submission rules; confirm current requirements with the organizer when ambiguous.
10. **Delivery:** complete the requested code, documentation, and user-facing site work autonomously where possible. When asked, open a pull request from the assigned project branch and merge it to `main` if GitHub permissions and repository policy allow; report any failure and never claim a PR or merge that did not occur.

## Current reviewed state — 2026-10-03 (after synchronizing with current `main`)

This is the authoritative current status; later dated experiment records below are supporting evidence, and older session narratives are history. The cumulative reviews are [the scientific/repository review](docs/research/review-checklist-2026-10-03.md) and [the current submission-format correction review](docs/research/submission-format-review-2026-10-03.md).

- **Data and sources:** the local grid, labels, template, and derived feature stacks are restored from SHA-256-pinned owner mirrors, not organizer-authenticated. The DrivenData data tab redirects to login; no credentials or bypass were used. Selected official GDR 1391 archives were downloaded and checksum-verified through the public runner bridge; a CRS/encoding ingestion defect was fixed in `scripts/fetch_external_layers.py`. Qfaults rasterization now produces local features, but its provenance overlaps the training catalogue and it is not independent truth. See [source register](docs/sources.md), `data/external/external_receipt.json`, and [irregularities](docs/irregularities.md).
- **Metric-shaped loss:** the 300 m geometry term remains paired with regional soft-Tversky. It changes near-miss allocation, but the fresh-seed confirmation was +0.000115 with 2/4 folds positive; a separate larger-budget confirmation was −0.00791 with 1/4 positive. The weight-sweep scorings disagreed. No boundary-loss setting is promoted.
- **H-31-02b / H-33-01 / H-32-05b:** the reduced-stack H-31-02b scarp screen failed its spatial-best and feature-perturbation gates. H-33-01's 80k gate was void at 68,573 active dots vs 80,000; its 40k sensitivity was active-count matched by code review but is not a promotion result. H-32-05b's 1.5 km p90 basement-edge variant improved on its own ablation but stayed below its spacing-and-distance-matched control. None is promoted.
- **H-31-02r promising but withheld:** the preregistered 1 m LiDAR scarp-dipole + 500 m strike-continuity transform beats its `step_max` ablation by 22.4%/20.2% on catalogue screen/confirmation and beats spacing/distance-matched controls on four independent USGS SGMC frames. However, the catalogue-component spatial check is negative (0.03323 vs 0.03585, Δ −0.00261; 2/4 quadrants); the three-check evaluation is split by frame, and the SGMC top-decile calibration-ratio criterion passes only 2/4 folds. The predeclared dual-frame promotion gate therefore fails. This is a promising measured feature, **not a promoted entry**; do not retune against the already-inspected SGMC labels. Evidence: [registered results](docs/research/h33-01-placement-and-scarp-holdout.md), [three-check results](docs/research/verification-checks-results.md), and IR-30-035.
- **Five genuinely untried geological hypotheses:** current shortlist and source/access/falsifiable gates are in [docs/hypotheses.md](docs/hypotheses.md) and [the review note](docs/research/untried-hypotheses-review-2026-10-03.md). H-31-04's GeoDAWN band-lineage/schema check is the lowest-cost new-hypothesis action; no unvalidated candidate gets a weekly slot.
- **Submission file — READY, one click, range-error hardened (session 7).** `index.html` and `executive-summary.html` now open with a single prominent download: `gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif` (806,758 B, SHA-256 `8cf893ea…129fd`). Independently re-read from disk: one `float32` band, EPSG:32611, 3730×3292, template transform `(100, 0, 243350, 0, -100, 4508550)`, **all 12,279,160 cells finite and in `[0, 1]`, 0 NaN anywhere, no nodata tag**, 44,090 predictions all off-catalogue, in-footprint values bit-identical to the source. A denser d1.5 alternate and a NaN-outside twin are linked beside it, each with a JSON sidecar and a paste-ready DrivenData note. No file was uploaded by this session and no weekly slot was used.
- **Range-error root cause — DIAGNOSED, superseding the earlier "undiagnosed" claim.** Both mechanisms were measured on the pin-matched mirrors: `training_features.tif` declares nodata as the float32 sentinel `-3.4028234663852886e+38` and carries it on **3,061 pixels inside the scoring footprint** per band (band 6 `tc`: 3,073; 58,171 band-pixels total), and band 1 calls only **5,165,852** pixels valid against the template's **5,167,373**, so a feature-derived footprint mask strands exactly **3,061 scored pixels as NaN**. Either alone produces the portal's rejection. See IR-30-044 and [the full measurement record](docs/research/range-error-root-cause-2026-10-03.md).
- **Zero-outside is now the default, reversing IR-30-038 (IR-30-045).** Two verifications: the organizer's own [reference solution](https://github.com/drivendataorg/gems-prize-reference-solution) writes its example with no `nodata` and finite values everywhere, and the owner ledger shows `r7-nms3-dem10-scarp_0c9199f14e62` = 0.1294 next to `…_allfinite` = 0.1294 — identical scores, so outside-footprint cells carry no scoring weight. `scripts/build_portal_submission.py` stages, validates, and only then publishes; it fails closed and leaves no raster behind on rejection (7 tests). `--outside nan` remains for the literal spec reading.
- **Verified scoring rule that changes strategy (IR-30-047).** DrivenData staff confirmed on [forum thread 11516](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516) that known USGS/INGENIOUS pixels are masked out of evaluation in **both** rounds, so mass on catalogue pixels earns no TP and no FP. The shipped file wastes 0 of 44,090; the OOF GBM artifact wastes 2,517.
- **Scores and TIFFs:** the dated public snapshot showed DARD 0.3195 and `wbg1` 0.2600 (rank 15); neither leaderboard row identifies a TIFF hash. The D2.8 attribution conflict is still open and is now logged as IR-30-048: the owner brief says 0.2600 while `mirror-pins.json` annotates that same SHA-256 (`91eae1ca…`) as an "unscored alternate" and the d1.5 raster (`68d0e2e4…`) as "labelled 0.2477". Catalogue-proxy DTI is **anti-correlated** with portal score (GBM 0.19020 > d2.8 0.16177 while the portal ordering is the reverse) and must never be used as a holdout — IR-30-046.
- **Session 30 (branch `arena/01a103f1-gemsdoe30`), metric-exact emitter and the catalogue-frame inversion:** `src/gemsdoe30/emitter_opt.py` (EDGE) emits the expected-marginal-credit greedy support of a belief field and stops at the published marginal threshold. In the registered component-holdout comparison (`docs/research/emitter-opt-holdout.json`, `…-convergence.json`, protocol in `emitter-opt-preregistration.md`) it beat every belief-ordered emission family on the same field: **0.19125 vs 0.13848** (+0.05277) on the proximity field, **0.18368 vs 0.14014** (+0.04354) on the hybrid field, **0.15784 vs 0.14015** (+0.01768) on external evidence — and it **lost** on the leak-contaminated GBM field (0.11834 vs 0.13326), which is reported in the same document. `IR-30-039` records the measured **sign inversion** between the full-catalogue proxy and the owner-reported leaderboard ordering of the `dot_thin` family; the consequence is that catalogue-derived frames can no longer adjudicate emission design (they remain mandatory degenerate-failure screens). The new `gemsdoe30-edge-hybrid-80k-02845bd4-nan.tif` download is published-format-validated, unpromoted, and 0 of its 80,000 dots lie on the training catalogue. See `docs/research/score-ceiling-analysis.md` for the 0.3195 coverage arithmetic.
- **Rules and verification:** all seven parsed chunks of the September 2026 official rules PDF were reviewed. The homepage/rules deadline-time conflict, eligibility, and final entrant-approved AI disclosure remain open. Final verification is recorded in the review checklist. PR [#15](https://github.com/buffedlizard55-lab/GEMSDOE30/pull/15) was merged to `main` at `44403fd67a92fd5b7658233e62af5b1d45811d1b` on 2026-10-03 21:50:40 UTC; its branch head was `e3967c590b43c65b4f3433f46d50d2781c286fdd`. Documentation-only PR [#16](https://github.com/buffedlizard55-lab/GEMSDOE30/pull/16) then recorded that merge in the review log; it merged to `main` at this session's base `1e377d4556445a3e9a80b64e129e36ed82e9a93f` on 2026-10-03 21:51:57 UTC.

## Historical session record — retained as an audit trail (superseded where noted)

Read the standing brief above every session. On 2026-10-03 we autonomously restored SHA-256-pinned **owner mirrors** via GitHub API and prepared the real 3730×3292 grid (5,167,373 valid pixels, 60,988 catalogue positives). This resolves local data placement, **not organizer authenticity**. `python scripts/restore_public_mirrors.py` reproduces restoration; immutable pins are in `docs/research/mirror-pins.json`. The mirrored template contains labels: footprint only, never use its values as model features/predictions.

A preregistered four-arm CPU pilot ran all four 800 m-buffered spatial folds. See [protocol](docs/research/pilot-preregistration.md), [complete results](docs/research/pilot-results.json), [data audit](docs/research/data-audit.json). The top runnable strain/conductance interaction **failed its screen** against the same-run context control. No model candidate promoted; no competition slot used. This limited pointwise pilot is not a full-capacity U-Net or a comparison against the archived best.

The D2.8 historical research TIFF is now a **local one-click download** on the site, independently format-checked against the mirrored template. It remains score-attribution-unverified and not slot-approved. 44 tests pass on this image (torch 2.14.1 and scipy 1.17.1 installed). Previous status text below describes the baseline, not today's restored state.

Later on 2026-10-03 the metric-aware emission line was exercised end to end: `src/gemsdoe30/emission.py` gained a masked-domain scorer fix and a count-matched candidate pool, `tests/test_emission.py` (19 tests) passes, and `scripts/emission_holdout.py` ran three count-matched arms on the four 300 m-buffered quadrants. **All three arms failed their registered gate** (adaptive minus uniform pooled ΔDTI +0.0008 to +0.0016, positive in only 1–2 of 4 folds): uniform Poisson-disk thinning stays the default, no candidate promoted, no slot used. Suite now collects 44 tests; 39 pass on this image and 5 torch-gated tests skip. Numbers: [emission-holdout-results.json](docs/research/emission-holdout-results.json). The owner-artifact audit in [artifact-structure.json](docs/research/artifact-structure.json) also records that catalogue-proxy DTI ordering is *inverted* relative to the owner-reported leaderboard ordering, consistent with the official rule that the Initial Prize Round scores only the private set of new expert-labelled faults.

Later still on 2026-10-03 three more real-data experiments completed. **(1) Paired regional-vs-boundary
loss ablation** — four 300 m-buffered spatial quadrants, identical recipes except the loss, screen
budget (2 × 20 steps, seed 30): pooled exact full-grid OOF DTI **0.062042 → 0.063990** (Δ **+0.001948**,
+3.14 % relative), 3/4 folds positive, fold 3 regressing −0.0009; the number of catalogue-truth pixels
left on partial-distance credit halved (80 → 40). **Confirmed only in part.** The fresh-seed confirmation (seed 31, identical protocol) reproduced the
behavioural effect — partial-distance truth coverage fell 1,889 → 724 — but **not** the DTI gain:
pooled ΔDTI **+0.000115** with only **2/4** folds positive (folds 0 and 3 flip sign versus the screen),
against the required 3/4. Verdict: **the boundary term changes near-miss allocation as designed but
does not reliably raise the proxy DTI at this budget; not promoted, no candidate file, no slot.**
Evidence: [loss-ablation-holdout.md](docs/research/loss-ablation-holdout.md),
[loss-ablation-holdout.json](docs/research/loss-ablation-holdout.json),
[seed-31 confirmation](docs/research/loss-ablation-holdout-seed31.json). **(2) Preregistered
metric-algebra emission holdout** — the registered gate **failed**: pooled cross-validated proxy DTI
`uniform` 0.18675, `adaptive` 0.18927, `dense` 0.13455, `metric` (greedy marginal rule) 0.13313; the
metric rule needed ≥ +0.005 versus both dense and uniform and came out −0.0014 and −0.0536, below
uniform in every fold, and adaptive's +0.0025 edge over uniform is under the threshold. No emission
family promoted. Mechanism: the greedy rule hit its candidate-pool cap (exactly 120,000 px per fold)
at 0.033–0.043 credit/px while uniform thinning emitted 3–6× fewer pixels at 2.4–4.7× the credit —
"thin, don't flood" again, matching the owner's sparse dotted masks. Evidence:
[metric-emission-holdout-results.md](docs/research/metric-emission-holdout-results.md) +
[metric-emission-holdout-results.json](docs/research/metric-emission-holdout-results.json).
**(3) H-31-01 relay-connector component holdout** — the connector geometry earned only **+1.2 %**
credit per emitted pixel over a proximity-matched control and fell below the unrestricted near-known
annulus, so the hypothesis is **not promoted as tested**; the dominant effect is the generic proximity
prior (~2.3× far-field). Evidence:
[relay-connector-holdout.json](docs/research/relay-connector-holdout.json). No GEMSDOE30 submission
TIFF exists, no slot has been used, and **no score is claimed** for any of this work.

### Session 2 (later on 2026-10-03) — historical range-error hypothesis, vent research base, H-32 register, H-32-01 gate

1. **Historical range-error investigation — unresolved and superseded by the format correction below.** The official sample template contains **7,111,787 NaN cells outside the footprint**. The earlier session hypothesized that a whole-array `[0,1]` check might reject NaNs; this was never verified and does **not** diagnose the reported error. The exact offending upload remains unknown. That hypothesis previously led to finite-zero-outside diagnostic copies; they do not match the published null/NaN-outside convention and are no longer presented as submission-format downloads. No upload was made. The current builder defaults to NaN outside; finite-all-cells checking and `scripts/make_portal_safe.py` remain diagnostic only.
2. **Verified knowledge base** (`docs/research/geothermal-vents-knowledge.md`): the official rules
   PDF was read line-by-line — training labels = INGENIOUS Great Basin compilation (DOI
   10.15121/1881483); **test labels = expert-new faults** (NLR/USGS, Qfaults + new); metric penalizes
   FN > FP; 3 submissions/week, one final entry across both prize rounds; **Phase 1 $50k split equally
   among top 5 on the private subset; Phase 2 $250k on the expert-revised label set**; finalists must
   ship reproducible code; AI use must be disclosed; eligibility is U.S.-only with certification under
   penalty of perjury (IR-30-020); deadline wording conflict confirmed in the PDF itself (IR-30-008).
   DOE/OSTI Faulds literature verified: step-overs/relay ramps host ~32 % of Great Basin geothermal
   systems, ~39 % of systems are blind (up to 75 % of resources), outflow can surface km from the
   source structure. Local GDR data measured: 27,092 wellspring rows (512 hot cells ≥ 60 °C, 256 ≥
   100 °C), 21 volcanic vents with **0 of 21 within 300 m of the catalogue**, 1,126 Qfaults traces
   (55 % of in-footprint centroids within 300 m of catalogue — circularity warning IR-30-021).
3. **Five never-tried H-32 hypotheses** registered and ranked (`docs/hypotheses.md` +
   `docs/hypotheses.html`): discharge corridors (H-32-01), un-catalogued Qfaults completion
   (H-32-04, validation-limited), buried pinch-out edges (H-32-05), geothermometer discordance
   (H-32-03), vent feeder alignments (H-32-02).
4. **H-32-01 ran its preregistered spatial component holdout and FAILED all three gate clauses** —
   pooled ΔDTI spring − proximity-matched control **−0.01494** (screen) and **−0.01537**
   (confirmation), **0/4** quadrants; spring zones earn ~3× less hidden credit per emitted pixel
   than matched random (0.0122 vs 0.0320 at 15k px), consistently across 4 zone arms × 3 budgets ×
   2 splits. Not promoted, no slot. Evidence:
   [h32-01-vent-corridor-holdout.md](docs/research/h32-01-vent-corridor-holdout.md) +
   [JSON](docs/research/h32-01-vent-corridor-holdout.json) +
   [preregistration](docs/research/h32-01-preregistration.md). Review found and fixed an unused
   `--confirm-threshold-c` flag; the supplementary ≥ 100 °C sensitivity run is recorded separately.
5. **Status feed automation:** `scripts/build_status.py` regenerates `docs/status.json` from the
   machine-readable artifacts (gate JSONs, download manifests, mirror pins, score ledger) — no more
   hand-edited status. The score ledger gained `evidence_class`/`as_of_utc` columns and six
   **official-snapshot** rows from the 2026-10-03 leaderboard read (DARD 0.3195 rank 1 … wbg1 0.2600
   rank 15). Suite now collects **60 tests**, all passing on this image.

### Independent session, same day — full-budget ablation, emitter frames, external-data bridge

A second autonomous session (`arena/01a102a1-gemsdoe30`, PR #8) ran three further real holdouts on
the same prepared grid. Where the two sessions overlap they **agree**, and where they differ the
difference is budget, not method.

**(A) The paired boundary-loss ablation at full budget.** Eight checkpoints, seed 30, **6 × 100
steps × batch 4 × 96 px (600 optimizer steps per fold)** — 15× the screen budget above. Pooled
exact full-grid OOF DTI **0.105026 (regional) → 0.097119 (combined)**, Δ **−0.00791**, positive in
**1 of 4** folds. Near-miss allocation again changed exactly as designed, and this time the direction
is measurable in both terms: truth pixels resolved exactly fell 48,491 → 47,964, the 200–300 m
near-miss bin rose 5,070 → 5,829, and far-field `FP_w` rose 1,044,121 → 1,151,942. The exchange rate
is roughly **1 unit of new near-miss credit per 85 units of new distant false-positive mass**, against
a metric that prices them at 1 : 0.2. Mechanism: `FP_w = Σ p(x)(1 − max_g k(d))` is linear in total
emitted mass over a 5.17 M-pixel footprint, so a boundary term built from the same kernel mostly
pushes probability inward *everywhere*. **Combined verdict across all three runs: the geometry term
reliably changes near-miss behaviour and never reliably raises the proxy DTI. Not promoted.**
Evidence: [loss-ablation-verdict.md](docs/research/loss-ablation-verdict.md) (+ `runs/loss-ablation/holdout.json`).

**(B) Emitter frames — historical diagnostics with an active-count correction.** The same out-of-fold
probability field scored **0.09712** as a dense field and **0.25461** after 400 m Poisson-disk
sparsification in the earlier catalogue proxy; this is an emission-operator diagnostic, not a
competition score. The SGMC comparison's archived `cand_t04s4` arm and blind-random arm each had
80,392 *global* dots, scoring **0.09526** and **0.07617** (+25.1 %) respectively; the 3 px lattice
scored 0.09395. However, active scored-domain counts were **72,310 candidate / 73,843 random /
80,388 archived**, so these were global-budget matched, **not active-count matched** (IR-30-037).
They do not describe the later 85,526-dot linked SGMC-hedge TIFF. The GBM diagnostic was likewise
not active-count matched: GBM had 90,358 global / 75,001 active dots, while its random control had
75,001 global / 68,848 active dots (DTI 0.07279 vs 0.07460). Do not interpret either comparison as
proof of a candidate advantage; no GEMSDOE30 score or promoted candidate results. Evidence:
[emitter-holdout.md](docs/research/emitter-holdout.md),
[novelty-holdout.md](docs/research/novelty-holdout.md),
`docs/research/{emitter-comparison,novelty-holdout,discovery-shift}.json`.
**Correction recorded for the audit trail:** an earlier draft of this section quoted "+4.4 % over a
blind lattice" for the model dots. That comparison used a lattice with 527,504 dots against an
80,392-dot candidate — unmatched budgets. The same-run budget-matched numbers above replace it, and
the direction of the conclusion survives only because the matched control is a *random* dot set
rather than a lattice; on the earlier unmatched comparison the sign alternates with the lattice's
spacing (74,288-dot lattice 0.08442, 97,028-dot lattice 0.09873).

**(C) A working official-data bridge.** A GitHub Actions runner downloads official layers,
SHA-256-verifies them, rasterises them onto the competition grid and commits the result back
(`data/external/external_receipt.json`). Verified: USGS SGMC `NV.zip` 69,056,094 B and `CA.zip`
24,977,406 B, plus GDR 1391 paleo-geothermal, Quaternary volcanics and 2 m temperature probes. The
SGMC derivation holds **21,160 features / 82,151 px** in the footprint, **75.1 % of them more than
300 m from every catalogue fault**. Falsification: **+2.9× enrichment** over chance against the
catalogue (positive) versus a **low-power** lidar corroboration test (AUC 0.520; the positive control
scores only 0.522) — recorded as inconclusive, not as a pass. Open irregularity: the Ingenious
Quaternary-fault v2 shapefile downloaded but rasterised to **zero** features inside the grid.

**(D) Metric theory.** Adding one prediction pixel whose triangular kernel credit against an
uncovered truth pixel is `k` changes the DTI denominator by exactly `0.2` and the numerator by `k`, so
**a dot helps iff `k > 0.2 × DTI`** — about **5.2 %** at the incumbent's operating point, and
**independent of the size of the hidden truth set**. This is why broad hedging across weak hypotheses
is near-optimal here, and why the SGMC layer is worth a bounded bet even though no local frame can
score it. Derivation and measured response surface: [metric-response-surface.md](docs/metric-response-surface.md).

**(E) Second published research TIFF and count-scope correction.** `docs/downloads/gemsdoe30-sgmc-hedge-d10-85k-20261003-ac08b41e.tif`
(SHA-256 `fed5232e…66da`; 85,526 dots; **zero** dots on the masked catalogue) adds a bounded SGMC
hedge (worst case ≤ 3 % of the DTI denominator) to model dots. Its 0.18343 SGMC mean is tautological
because the SGMC inventory is both an input to this TIFF and the scored inventory; it is not validation.
The earlier GBM diagnostic was 0.07279 vs 0.07460 random, but the active scored-domain counts were
75,001 vs 68,848 (despite matching 75,001 global random dots), so it is not an active-count-matched
comparison. The archived +25.1 % `cand_t04s4` result described above belongs to a different arm, not
to this 85,526-dot TIFF, and its active counts also differed. No file has a leaderboard score or is
promoted, and no weekly slot has been used.

### Session 4 (2026-10-03, branch `arena/01a10315-gemsdoe30`) — data blocker closed, H-32-05 falsified

**The standing "single remaining blocker to training is data placement" is closed, and the claim that
the brief's central loss deliverable was "verified working here on CPU" was not true until this
session.** Both were re-checked from scratch rather than trusted:

1. **Data placement — resolved without manual input.** Raw `curl` to `drivendata.org` and
   `dropbox.com` fails in this sandbox (TLS EOF), but `gh api` reaches the pinned owner mirrors. The
   three core rasters were fetched from the pinned refs and reassembled, then **SHA-256-verified
   against `docs/research/mirror-pins.json`**: `4371c82e…43123bc5` (418,912,844 B, 5 parts),
   `7ba308cc…5ae4093`, `2176d08e…54d35cbc`. `download_competition_data.sh` exits 0;
   `prepare_data.py` reproduces **`dataset_signature 291d3467…dee855ed`, byte-identical to the
   signature earlier sessions recorded** — the independent proof that this is the same data
   (5,167,373 valid pixels, 60,988 catalogue positives, 19 bands, EPSG:32611, 100 m). Training then
   ran on real data on CPU (`train_model.py --fold 0 --loss combined`, ~0.55 s/step).
   Mirrors remain **not organizer-authenticated** (IR-30-001 unchanged). See IR-30-024.
2. **Boundary-loss verification gap — closed.** With no torch installed, the 5 boundary-loss tests in
   `tests/test_optional_loss.py` were **skipping**, so the deliverable the brief centres on had never
   executed here. torch 2.14.1 installed; the suite now runs them: **67 passed, 11 subtests, 0
   skipped** — including the check that the geometry term equals `1 − distance_weighted_tversky(…)`
   to 10 decimal places and that near-misses are ranked by 300 m kernel distance. See IR-30-030.
3. **H-32-05 (buried range-front pinch-out edges) — preregistered, run, falsified.** Design frozen in
   [h32-05-preregistration.md](docs/research/h32-05-preregistration.md) *before* the run, on the real
   `depth_to_base_surf` / `iso_grav_anom_hg` / `tmi_hg` bands, with USGS-cited physics
   ([OFR 2005-1154](https://pubs.usgs.gov/of/2005/1154/of2005-1154.pdf),
   [OFR 2000-189](https://pubs.usgs.gov/of/2000/0189/pdf/of00-189.pdf),
   [USGS 70259621](https://pubs.usgs.gov/publication/70259621)). Registered gate **failed every
   scoring clause**: screen Δ −0.02614 vs matched random (needed ≥ +0.002), 0/4 quadrants,
   confirmation Δ −0.02591. The pre-declared *transform clause* passed (+0.0012 / +0.0034: the
   basement-surface **edge** does beat its raw **magnitude**), but the whole family sits ~10× below
   the random controls. **Not promoted; no slot spent.** [Result](docs/research/h32-05-basement-edge-holdout.md).
   Declared design defect: the `coherence ≥ 0.5` floor accepted 99.65 % of pixels, so the
   oriented-edge variant was never fairly tested (IR-30-029).
4. **Three real bugs found and fixed** while verifying, each with a reproduction: the status feed
   looked for mirrors in the wrong directory so it always reported "no data" (IR-30-025); 9 of 22
   scripts could not run on an uninstalled checkout even though the docs say to run them that way
   (IR-30-026, fixed and re-verified with the package uninstalled); and
   `fetch_external_layers.py` clobbered a committed audit receipt on *any* invocation, including
   `--help` (IR-30-027 — an accidental `--help` cost a 783-line deletion, restored from git; in-flight
   evidence now goes to a sidecar and the canonical receipt needs `--allow-overwrite`).
5. **Reading of three consecutive falsifications (H-31-01, H-32-01, H-32-05) against the same
   `random_near_matched` control (~0.029 DTI):** the binding constraint on this proxy is **where a
   fixed emission budget is placed relative to mapped structure**, not which scalar field ranks the
   pixels. The next registered experiment should be a placement-policy test, not a new detector.

### Session 5 (2026-10-03, this branch `arena/01a10330-gemsdoe30`) — emitter-order fix, score ledger, H-33-01 run to verdict

1. **IR-30-031: real library bug found and fixed.** `poisson_disk_select`/`adaptive_disk_select`
   documented a descending-score greedy but built `np.lexsort((-values, rows, cols))` — and
   `np.lexsort` keys on the **last** array, so visits were column-major (raster order), not
   score-first. Fixed at all three occurrences, regression tests added (`ScoreFirstVisitOrderTests`,
   `OrderedSelectionTests`, plus a `max_kept` prefix-equivalence test), and the affected-artifact
   caveat recorded in [docs/irregularities.md](docs/irregularities.md). Historical *relative*
   conclusions stand (arms and controls shared the same rule); prior absolute numbers are now
   labelled "measured under raster-order visiting".
2. **H-33-01 (placement policy) — preregistered, run, decided.** Frozen design in
   [h33-01-preregistration.md](docs/research/h33-01-preregistration.md) before any score was seen;
   harness `scripts/placement_policy_holdout.py` (tests: `tests/test_placement_policy.py`).
   The gate-budget screen (80,000 dots) hit a capacity wall — the 0.4-thresholded, 4 px-thinned
   pools hold only 68,573 dots, so every quota arm collapsed to the same union; the harness
   **voided** the gate instead of adjudicating a non-count-matched comparison, and the registered
   verdict is **not promoted** (IR-30-032 records the design undercount and the new pre-flight
   capacity rule). The count-matched 40 k sensitivity run is the substantive evidence:
   whole-domain score-first thinning **0.07608** beats blind random **+35 %** and beats **every**
   band-stratified arm (0.0721–0.0725), while pure proximity ranking is catastrophic (0.03660).
   Verdict: **the placement-policy line is closed** — placement is exhausted as a lever; the next
   registered experiment must improve the score field itself. Full numbers:
   [h33-01-placement-policy-holdout.md](docs/research/h33-01-placement-policy-holdout.md) ·
   [JSON](docs/research/h33-01-placement-policy-holdout.json).
3. **Regional OOF mosaic regenerated post-fix and verified**: `runs/oof/regional-oof.npy`,
   5,167,373 finite pixels (= template count), range [0, 1], mean 0.23551, 23.67 % > 0.4,
   scope sidecar matches the frozen 4-fold plan.
4. **Score ledger refreshed** with dated `official-snapshot` rows (2026-10-03 manual read, twice,
   consistent): leader DARD **0.3195**; `wbg1` 0.2600 at rank 15 confirmed; a rank-19 row of
   0.2449 numerically equals the owner-reported GEMSDOE27 score — recorded as coincidence, not
   attribution. No GEMSDOE30 file has been scored; target **> 0.3195** is not yet reached.
5. Full suite at that review: **80 passed + 11 subtests, 0 skipped**. The three then-current zero-outside diagnostic downloads passed 12/12 *finite-all-cells* checks; this was an internal diagnostic, not published-format compliance or portal acceptance. The NaN-outside source TIFFs and restored labels/template matched their SHA-256 pins byte-for-byte. The latest submission-format correction and sidecar rechecks are recorded below and supersede any earlier “portal-safe” wording.

## Superseded baseline snapshot — before owner-mirror restoration (historical)

The following notes describe an earlier checkout state and are retained as an audit trail only; they are superseded by **Current reviewed state** above and the later experiment records below.

- The recorded baseline commit for this checkout already contains the model/loss, tests, training/inference/validation scripts, and site scaffold. The Git history available here is shallow/grafted to that commit, so earlier claims about a prior README-only state cannot be independently verified from this repository. At the start of this review there were **no competition rasters, sample template, checkpoints, real holdout predictions, or generated GEMSDOE30 TIFFs**. The rasters have since been restored from SHA-256-pinned owner mirrors (not organizer-authenticated) and real-data training, OOF prediction, stitching and scoring all run locally; what remains blocked is organizer-authenticated data and the hidden expert labels.
- The DrivenData data page redirects an unauthenticated visitor to its login page. No DrivenData credentials/session or competition rasters are available here, and the shell cannot retrieve the public owner-mirror TIFFs in this environment. The safe data preflight is `bash scripts/download_competition_data.sh`; it reports missing inputs and does **not** attempt a login bypass.
- The official leaderboard was read on **2026-10-03**: the displayed leader was **DARD, 0.3195**. It is a live, changeable public score; it is not private-test performance. The supplied claim that the linked GEMSDOE25 D2.8 TIFF scored 0.2600 is **not authenticated to that exact file**: the GEMSDOE25 landing page currently describes that TIFF as unscored/not slot-approved, while the public leaderboard contains a 0.2600 row for participant `wbg1` at rank 15. See [analysis](docs/leaderboard-analysis.md) and [irregularities](docs/irregularities.md).
- The 300 m loss geometry and spatial-holdout pipeline are implemented. **44 tests pass** with NumPy, SciPy, rasterio, PyTorch, and pytest installed; the geometry term matches the independent metric on a masked grid, and a seam regression test confirms the pooled OOF score keeps 100 m near-miss credit across quadrants. Review fixed quadrant-component pooling, prevents fold-specific checkpoints from being relabeled across OOF folds, and checks prediction/checkpoint hashes and experiment recipes. A disposable synthetic 64×64 smoke passed paired four-fold training/inference, OOF stitching/evaluation, full-fit inference, and exact-template TIFF validation. Real-data spatial holdouts have now run (four-arm pilot, metric-emission holdout, paired loss ablation) and are recorded above; the loss screen is positive but unconfirmed, and **no candidate file has been promoted, no score is claimed, and no GEMSDOE30 TIFF has been produced.**
- The site exposes a one-click link to the pre-existing GEMSDOE25 research TIFF, clearly labeled external, unscored, and not slot-approved. It is not represented as this repository's model output or as an approved competition submission. A genuine GEMSDOE30 download will be generated only after data placement, training, holdout promotion, and exact-template validation.

## Start here

1. Read the [executive summary and submission guide](executive-summary.html).
2. Read the styled [leaderboard/file attribution analysis](docs/leaderboard-analysis.html), [ranked hypotheses](docs/hypotheses.html), [loss design](docs/loss-design.html), and [irregularity register](docs/irregularities.html).
3. Review the styled [official/primary source register](docs/sources.html); full claim-by-claim notes remain in `docs/sources.md`. Before any eventual entry, review the [working AI-use disclosure draft](docs/ai-disclosure-draft.md) against every team member's actual use.
4. Install the optional geospatial/training stack and run the test suite (optional geospatial and loss-gradient tests run when their dependencies are installed):

   ```bash
   python -m pip install -e '.[train,test]'
   python -m unittest discover -s tests -v
   python scripts/loss_geometry_probe.py
   ```

5. Place the competition files, downloaded through an authorized competition session, in `data/raw/` as `training_features.tif`, `labels.tif`, and `sample_submission.tif`. Then run:

   ```bash
   bash scripts/download_competition_data.sh
   python scripts/prepare_data.py
   ```

   **Status (verified 2026-10-03, this session): this step is complete and reproducible without any
   manual input.** `python scripts/restore_public_mirrors.py` fetches the SHA-256-pinned owner
   mirrors through the GitHub API and reassembles `training_features.tif` from its five parts; all
   three core rasters then hash-match `docs/research/mirror-pins.json` exactly
   (`4371c82e…43123bc5` / `7ba308cc…5ae4093` / `2176d08e…54d35cbc`), `download_competition_data.sh`
   exits 0, and `prepare_data.py` reproduces `dataset_signature 291d3467…dee855ed` — identical to the
   signature recorded by earlier sessions, which is the independent check that the mirror is the same
   data. `docs/status.json → data_placement` re-verifies placement and hashes on every regeneration.
   These remain **owner mirrors, not organizer-authenticated files**.

   The preparation script fails closed on CRS, transform, shape, label encoding, or footprint mismatch. It records SHA-256 values for the three source rasters and a dataset signature in the prepared manifest, then writes raw features and masks under the Git-ignored `data/processed/`. Each training run fits and stores its own robust normalization statistics using training-fold pixels only, never held-out pixels; the checkpoint is bound to that prepared dataset signature.

6. Run the *paired* loss experiment on all four buffered spatial folds with the same seed and optimization settings in both arms. For each fold `F` in `0 1 2 3`, run:

   ```bash
   python scripts/train_model.py --fold F --loss regional --output runs/fF-regional.pt
   python scripts/train_model.py --fold F --loss combined --output runs/fF-combined.pt
   python scripts/infer_model.py --checkpoint runs/fF-regional.pt --fold F --predictions-only --output runs/fF-regional.npy
   python scripts/infer_model.py --checkpoint runs/fF-combined.pt --fold F --predictions-only --output runs/fF-combined.npy
   ```

   Keep each inference `.json` sidecar beside its `.npy`. The stitcher checks prediction-array and checkpoint SHA-256 values, explicit checkpoint/fold identity, the source-bound prepared-grid/dataset signature, identical training recipes, and held-out-only masks before it creates a hashed OOF mosaic. The evaluator verifies both OOF manifests and paired recipes. It computes the exact pooled DTI once over the complete stitched OOF grid (retaining cross-quadrant 300 m interactions); fold-isolated values are diagnostics only. Then compare both arms with the exact metric and near-miss diagnostics:

   ```bash
   python scripts/stitch_oof_predictions.py --fold0 runs/f0-regional.npy --fold1 runs/f1-regional.npy --fold2 runs/f2-regional.npy --fold3 runs/f3-regional.npy --output runs/regional-oof.npy
   python scripts/stitch_oof_predictions.py --fold0 runs/f0-combined.npy --fold1 runs/f1-combined.npy --fold2 runs/f2-combined.npy --fold3 runs/f3-combined.npy --output runs/combined-oof.npy
   python scripts/evaluate_loss_ablation.py --regional runs/regional-oof.npy --combined runs/combined-oof.npy
   ```

   Repeat the complete paired design with preregistered fresh seeds for confirmation. Do not treat one fold or the synthetic probe as confirmation.

7. Only after a candidate clears the frozen holdout and confirmation gates should it be fit on all permitted training labels. `scripts/infer_model.py` or `scripts/build_submission.py` writes a uniquely named, template-matched TIFF and a JSON sidecar. The builder defaults to the published null/NaN-outside convention; it accepts `--note` or `--comment` for the paste-ready submission note. Run `python scripts/validate_submission.py FILE.tif --template data/raw/sample_submission.tif` for the published-format local check. `--finite-all-cells` is a stricter whole-raster diagnostic (with legacy alias `--portal-safe`), not an organizer requirement or acceptance claim. Building zero outside requires `--outside zeros --allow-nonstandard-zero-outside` and is diagnostic only; do not use it as the submission format unless the organizer explicitly clarifies the rule. The exact file behind the prior `[0,1]` error remains unidentified, so its cause is undiagnosed. Local validation is not promotion or upload approval; the authorized entrant must review current official instructions before any manual submission.

## Useful links

- [DrivenData competition homepage](https://www.drivendata.org/competitions/306/competition-doe-gems/) — navigate to Problem Description, About, Data, and Leaderboard. The requested direct pages are documented in `docs/sources.md`.
- [Official GEMS rules PDF (NLR, September 2026)](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS GeoDAWN data release, DOI 10.5066/P93LGLVQ](https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7)
- [DOE Geothermal Data Repository: INGENIOUS GDR 1391](https://gdr.openei.org/submissions/1391)
- [Kervadec et al., Boundary loss (2018 preprint; PMLR proceedings 2019)](https://proceedings.mlr.press/v102/kervadec19a.html)

## Repository map

- `index.html`, `executive-summary.html`, `docs/assets/site.css` — GitHub Pages landing page and submission instructions; the landing page links the external reference TIFF, not an approved GEMSDOE30 result.
- `docs/ai-disclosure-draft.md` — truthful current-session starting point for the rules-required entrant narrative; must be updated and reviewed before any entry.
- `src/gemsdoe30/metric.py` — reference DTI implementation; vectorized with NumPy/SciPy when installed, dependency-free for small tests.
- `src/gemsdoe30/losses.py` — regional soft-Tversky plus the 300 m metric-geometry term, inspired by (not a verbatim copy of) Kervadec et al.
- `src/gemsdoe30/cv.py`, `analysis.py` — buffered spatial blocks, exact full-grid OOF scoring, fold-isolated diagnostics, and near-miss profiles.
- `src/gemsdoe30/normalization.py` — deterministic robust scaling fit separately on each training-fold mask and saved in each checkpoint to prevent held-out feature leakage.
- `src/gemsdoe30/submission.py` — published-format GeoTIFF writer/validator (NaN outside by default) and auditable sidecar; strict finite-all-cells checking is diagnostic only.
- `scripts/` — data preflight, preparation, paired training arms, inference, validation, and probes.
- `docs/` — source ledger, reported-score ledger, hypothesis register, results interpretation, and irregularities.
- `data/raw/`, `data/processed/`, `outputs/`, `runs/` — local-only data and outputs; ignored by Git.

Later on 2026-10-03 a first GEMSDOE30 candidate file was built and published for download: a **4-fold out-of-fold GBM surface** (each pixel predicted by a model that never saw its quadrant; fold models from the metric-emission experiment) emitted with the LOFO-selected adaptive Poisson-disk rule (radius 5 px, gamma 1, pool 480k) → 90,358 dots, median nearest-neighbour spacing 2.83 px, 17.7 % within 300 m of the catalogue (2.1× the 8.6 % base rate). Local format validation passes all 11 checks (5,167,373 in-footprint values in [0,1], NaN outside, EPSG:32611, 100 m, template transform preserved). **It is not holdout-promoted** — its family beat uniform by only +0.0025 against a required +0.005 — and the site labels it accordingly with a paste-ready note. Artifacts: [candidate TIFF](docs/downloads/GEMSDOE30_oof-gbm-adaptive-r5_20261003T170425181215Z_aedb3d13-nan.tif), [manifest](docs/downloads/GEMSDOE30_oof-gbm-adaptive-r5_20261003T170425181215Z_aedb3d13-nan.json), [build record](docs/research/candidate-2026-10-03.md).

## Session 6 update (2026-10-03, branch `arena/01a10349-gemsdoe30`) — 1 m LiDAR scarp dipole (`H-31-02r`), 1.5 km coherent basement step ridge (`H-32-05b`), 6.38× clumping audit (`IR-30-033`), and three-check verification

Following the Session 4–5 next steps above, we preregistered
([`docs/research/h33-01-placement-and-scarp-preregistration.md`](docs/research/h33-01-placement-and-scarp-preregistration.md))
and executed (`scripts/placement_and_scarp_holdout.py` and `scripts/run_verification_checks.py`)
the spacing-matched placement-policy decomposition (`H-33-01`), the reduced 1 m LiDAR scarp dipole +
500 m strike continuity arm (`H-31-02r`), the 1.5 km `p90` coherent basement step ridge re-test
(`H-32-05b`), and the full three-check verification protocol across both the **Catalogue
Component-Holdout Proxy** and the **Independent USGS SGMC Fault Inventory** (both unclustered and
5 km clustered frames):

1. **Methodological discovery (`IR-30-033`) — 6.38× clumping confounder in legacy top-N holdouts:**
   `scripts/basement_edge_holdout.py` and `scripts/vent_corridor_holdout.py` emitted un-thinned
   `top_n_emission` blobs (`median_nn_px = 1.0 px`, `99.95 % ≤ 3 px`) while scoring them against
   dispersed `random_near_matched` dots (`median_nn_px = 5.10–8.94 px`). Under the 300 m (`3 px`)
   max-pooled kernel, clumped pixels cannibalize each other's true-positive footprint: on the exact
   same `depth_to_base_surf + iso_grav_anom_hg` feature surface, applying `r = 3.0 px` Poisson-disk
   thinning raises DTI from **`0.00373 → 0.02380`** (**6.38× multiplier** on screen, `4.88×` on
   confirm). All arms in `scripts/placement_and_scarp_holdout.py` enforce `r = 3.0 px` Poisson-disk
   spacing.
2. **Placement-policy decomposition (`H-33-01`):** On held-out catalogue components at `N = 15,000`
   Poisson-thinned dots, near-splay placement (`300–1,500 m` from known faults) achieves **`0.07234`**
   (screen) and **`0.07434`** (confirm) — **2.7×** uniform-domain placement (`0.02674` / `0.02694`)
   and **18.6×** far-basin placement (`> 5,000 m`, `0.00389` / `0.00326`). The `60/25/15 %`
   power-law hedge beats uniform placement on catalogue screen (`+0.02930`), catalogue confirm
   (`+0.01962`), and unclustered SGMC (`+0.00413`), but splits sign across the two 5 km clustered
   SGMC seeds (`−0.00274` on seed 31, `+0.00632` on seed 41; `promoted = false`).
3. **1 m LiDAR scarp dipole + 500 m strike continuity (`H-31-02r`):**
   * Beats its `step_max_only` ablation on both catalogue splits (`0.03323` vs `0.02715`, **+22.4 %**
     screen; `0.03066` vs `0.02551`, **+20.2 %** confirm; `transform_clause_pass = true`).
   * Crushes the spacing+distance-matched control on the **independent USGS SGMC fault inventory**
     by **+86.1 %** (`0.05913` vs `0.03178`, `4/4` quadrants) on seed 31 and **+82.8 %** (`0.05308`
     vs `0.02903`) on seed 41 in the unclustered frame, and by **+91.6 %** (`0.02916` vs `0.01522`)
     on seed 31 and **+60.5 %** (`0.01652` vs `0.01029`) on seed 41 in the 5 km clustered frame.
   * Check 2 calibration slopes are in range (**`0.9009`** catalogue; **`0.9101`** SGMC), and the
     catalogue top-decile ratio passes in **4/4** folds; the SGMC top-decile ratio passes only **2/4**,
     so the calibration gate is not satisfied across both frames. **Check 3** passes (permuting 1 m
     LiDAR channels on held-out SGMC removes **57.0 %** of gain; permuting full topography removes
     **97.2 %**; unrelated `iso_grav_anom_hg` retains **100.0 %**; `4/4` quadrants positive).
   * Check 1 is split by frame: catalogue proxy ΔDTI is `−0.00073` in the three-check protocol
     (`−0.00261` in the registered placement report; both `2/4` quadrants), while the SGMC frame is
     `+0.03670` (`4/4`). Real bedrock/range-front scarps outside the Quaternary catalogue are
     penalized by the catalogue proxy (`IR-30-035`). Per the pre-stated dual-frame/three-check gate,
     it is **withheld from weekly-slot promotion**.
   * Full evidence: [`docs/research/h33-01-placement-and-scarp-holdout.md`](docs/research/h33-01-placement-and-scarp-holdout.md) ·
     [`docs/research/verification-checks-results.md`](docs/research/verification-checks-results.md).
4. **1.5 km coherent basement step ridge (`H-32-05b`, fixing `IR-30-029`):** Computing the structure
   tensor on `dbs_edge` at a 1.5 km (`15 × 15 px`) scale (`median = 0.2588`, `p90 = 0.6545`) selects
   **10.00 %** (`516,432 / 5,164,312`) of footprint pixels (vs `99.65 %` in `IR-30-029`). The `p90`
   gate improves the Poisson-thinned basement step score on both catalogue screen (`0.02380 → 0.02574`)
   and confirm (`0.02566 → 0.02933`), but still trails the spacing+distance-matched control
   (`0.03660` / `0.03655`, `0/4` quadrants; `promoted = false`).

## Session 30 update (2026-10-03, branch `arena/01a103f1-gemsdoe30`) — metric-exact emitter (`EDGE`), catalogue-frame inversion (`IR-30-039`), H-34 register

**What was built.** `src/gemsdoe30/emitter_opt.py` (EDGE) and `src/gemsdoe30/fields.py` (belief
fields), with `scripts/emitter_opt_holdout.py` (registered comparison), `scripts/build_edge_candidate.py`
(candidate builder) and two test modules (`tests/test_emitter_opt.py`, `tests/test_fields.py`). EDGE
ranks candidate dots by the exact expected marginal credit
`dT(x) = Σ_δ π(x+δ)·max(0, k(δ) − C(x+δ))` and stops when `dT ≤ 0.2s/(1−0.2s)·dF`, i.e. at the exact
marginal condition of the published index. Bookkeeping is verified against an independent from-scratch
credit pass (relative error 1.95e-7); prefixes of the acceptance order reproduce the recorded cumulative
statistics.

**Registered result (frame fixed before running, `docs/research/emitter-opt-preregistration.md`).** Whole
8-connected catalogue components split seed 31 into a stand-in hidden half (20,870 px) and a known half
(40,118 px, masked from every metric term); four spatial quadrant folds; leave-one-fold-out parameter
choice per family. Pooled cross-validated DTI at each family's held-out choice:

| field | EDGE | best other family | margin | folds won |
| --- | ---: | ---: | ---: | ---: |
| proximity (known traces) | **0.19125** | adaptive 0.13848 | **+0.05277** | 4/4 |
| hybrid (proximity ∧ external evidence) | **0.18368** | adaptive 0.14014 | **+0.04354** | 3/4 |
| external (USGS SGMC + GDR layers) | **0.15784** | adaptive 0.14015 | **+0.01768** | 3/4 |
| gbm (leak-contaminated) | 0.11834 | adaptive **0.13326** | −0.01491 | 0/4 |

Uniform thinning (≈0.125), dense quantile emission (0.060–0.074) and the previously shipped
belief-ordered marginal rule (0.031–0.060) were beaten decisively in the same runs. The registered gate
(≥ +0.005 over the best other family, ≥ 3/4 folds) is met on all three legitimate fields and fails on the
leak-contaminated one, which is reported rather than hidden. Absolute values are **not comparable** with
the earlier registered 0.18675/0.18927 pair (different frame; its `data/processed/*.npy` inputs are absent
here). Registered limits: the stand-in hidden truth is half the same catalogue, so the margins are proxy
margins; the candidate should be taken at the measured prefix plateau, not at `accepted` (the proximity
peak is interior at 100,000 dots while the marginal rule kept accepting to the 160,000 cap).

**Candidate artifact (unpromoted).** `docs/downloads/gemsdoe30-edge-hybrid-80k-02845bd4-nan.tif`
(SHA-256 `f87d3fc008230ec12a2b2ad260de643d15b8e474135d28020dafd2c784d2cbd5`, 592,782 B): 80,000 dots,
binary, **0 on the training catalogue**, published-format validation passed, sidecar with the full
provenance. It is linked first on the site with an explicit "unpromoted" label; no slot was used.

**IR-30-039 — the catalogue proxy is inverted.** On hash-verified bytes: full-catalogue proxy DTI is
0.16635 (parent, 121,131 dots), 0.17193 (d1.5, 60,069) and 0.16177 (d2.8, 44,090) while the
owner-reported scores for the same three artifacts rise 0.1922 → 0.2477 → 0.2600. The official metric
deletes USGS/INGENIOUS pixels from every term, so a catalogue frame pays for exactly the dots the
competition removes. Consequences recorded in `docs/irregularities.md` and
`docs/research/score-ceiling-analysis.md`: catalogue frames stay as screens, never as promotion evidence;
the archived negatives under that frame are screen failures inside a biased frame, while the independent
SGMC-novelty results in those reports stand.

**Highest-score study (`docs/research/score-ceiling-analysis.md`).** The 0.3195 gap is a coverage gap,
quantified from the metric alone: at `s = 0.3195` a dot must sit within ≈280 m of a scored truth pixel
(`k > 0.0683`), and with the owner-model hidden mass the leader's statistics need `T = 3,466 + 0.0683·F`;
with perfect knowledge the same metric ceilings near 0.78. Also derived: a binary 0/1 raster strictly
dominates any graded map of the same support, so every submission must be sparse binary dots.

**H-34 register (`docs/hypotheses.md` §H-34, `docs/hypotheses.html`).** Four new ranked candidates that
target faults a surface catalogue cannot contain: **H-34-01** substrate-concealment prior from USGS SGMC
map-unit polygons (data on disk, next action); **H-34-02** potential-field depth lineaments (GeoDAWN tilt +
Euler deconvolution); **H-34-03** drainage χ/ksn (USGS NHD + 3DEP, blocked until the clipped product is on
disk); **H-34-04** heat-flow anomalies and borehole-gradient discontinuities (IHFC release 2024, power-check
first). Each names layers, physical signature, why it evades USGS/INGENIOUS, its difference from existing
work, expected index gain versus cost, an official free source verified this session (source register
addendum), and a falsifiable blocked-holdout gate. None is validated; none may consume a slot.

**Operations.** `.github/workflows/status-feed.yml` regenerates `docs/status.json` from repository
artifacts and re-runs the format checks on every relevant push and weekly (no DrivenData access, no
scraper). `IR-30-040` fixed the external-layer bridge trigger (it pointed at a stale branch name);
`IR-30-041` records the emitter-truncation semantics and the convergence re-run. Test suite:
**107 passed, 5 skipped (torch absent), 7 subtests passed**.

## Session 7 update (2026-10-03, branch `arena/01a10411-gemsdoe30`) — submission file shipped, range error diagnosed, masking rule verified

The standing brief opens with *"There should be an easy to download submission tif file as
described by the prompt."* At the start of this session that was not true: the site offered
three downloads, every one hedged as "research artifact, not a promoted entry, do not
submit", and the repository's own position was that the portal's `Predicted values must be in
range [0, 1]` error was **undiagnosed**. Both problems are fixed, and the fix rests on
measurements taken this session rather than on judgement.

1. **All three core rasters were re-restored and re-hashed.** `python3
   scripts/restore_public_mirrors.py` fetched `training_features.tif`, `labels.tif`, and
   `sample_submission.tif` from the pinned refs; `sha256sum` confirms
   `4371c82e…43123bc5` / `7ba308cc…5ae4093` / `2176d08e…54d35cbc`, matching every pin. The
   template measures 3292×3730 = 12,279,160 cells, EPSG:32611, 100 m, transform
   `(100, 0, 243350, 0, -100, 4508550)`, nodata `nan`, **5,167,373 finite** footprint cells,
   **7,111,787 NaN**, values `{0.0, 1.0}` with 60,988 ones. `labels.tif`'s `-1` mask is
   *exactly* the template's NaN mask and its `1` mask is *exactly* the template's `1` mask.

2. **The range-error root cause is measured, not inferred (IR-30-044).** `training_features.tif`
   declares nodata as the float32 sentinel `-3.4028234663852886e+38`. All 19 bands carry it on
   **3,061 pixels inside the scoring footprint** (band 6 `tc`: 3,073; **58,171** band-pixels
   total). Band 1 calls only **5,165,852** pixels valid against the template's **5,167,373**,
   and **3,061 template-valid pixels are sentinel in band 1** — so a footprint mask derived
   from a feature band strands exactly those 3,061 scored pixels as NaN. Either mechanism
   alone yields precisely the reported rejection. Record:
   [range-error root cause](docs/research/range-error-root-cause-2026-10-03.md).

3. **Zero-outside is now the default, reversing IR-30-038 (IR-30-045).** The organizer's own
   [reference solution](https://github.com/drivendataorg/gems-prize-reference-solution) writes
   its example prediction with `rasterio.open(..., "w", ...)` and **no `nodata` argument**, its
   sigmoid output finite everywhere. And `docs/score-ledger.csv` records
   `r7-nms3-dem10-scarp_0c9199f14e62` = **0.1294** beside `…_allfinite` = **0.1294** — the
   same score for both outside encodings, so outside cells carry no scoring weight.
   Zero-outside therefore cannot trip a whole-raster range check and costs nothing.

4. **`scripts/build_portal_submission.py`** takes the footprint **only** from
   `np.isfinite(sample_submission.tif)`, maps NaN→0.0 / +Inf→1.0 / −Inf→0.0, clips to `[0, 1]`,
   writes zero outside, **re-reads the bytes from disk**, and refuses exit 0 unless all
   12,279,160 cells are finite and in range. It writes to a `.partial` staging path and only
   publishes on success — a first version wrote straight to the output and left a rejected
   raster in `docs/downloads/`, which was caught and fixed. 7 tests in
   `tests/test_portal_submission.py` cover both mechanisms, both outside modes, bit
   preservation, staging cleanup, and fail-closed behaviour. Full suite: **99 passed,
   5 skipped** (torch absent), up from 92 passed.

5. **The metric's structure was reduced to a closed form and verified (knowledge base §7).**
   Substituting `FN_w = G − TP_w` gives `DTI = TP_w / (0.8·G + 0.2·(TP_w + FP_w))`, checked
   against `src/gemsdoe30/metric.py` to better than 1e-9 on both dotted artifacts. It implies a
   break-even — a dot pays iff its marginal TP per unit FP exceeds `0.2 × DTI` (≈0.052 at 0.26)
   — and because `TP_w` is a *max* per truth pixel, a redundant dot is strictly harmful. KD-tree
   spacing of the local artifacts then explains the portal ordering mechanically: 121,131 dots
   at 100 m → 0.1922; 60,069 at 200 m → 0.2477; 44,090 at 282.8 m (median NN 300 m) → 0.2600.
   The optimum lands on the kernel radius `R` itself. d2.8 fills only 0.85 % of the footprint
   against a ~15× denser 300 m hex packing, so it is **evidence-limited, not packing-limited**.

6. **Catalogue-proxy DTI is anti-correlated with portal score (IR-30-046).** It ranks the GBM
   artifact 0.19020 above d2.8 0.16177 — the reverse of the portal ordering — and is now
   explicitly barred from use as a holdout or promotion gate.

7. **The masking rule is verified from the organizer (IR-30-047).** DrivenData staff on
   [forum 11516](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516):
   known USGS/INGENIOUS pixels are masked out of evaluation in **both** rounds. Mass there
   earns no TP and no FP. The shipped file wastes 0 of 44,090; the OOF GBM artifact wastes
   2,517. New rule: every candidate must report `dots_on_catalogue`.

8. **The 0.2600 attribution conflict is logged, not papered over (IR-30-048).** The owner brief
   says D2.8 = 0.2600; `mirror-pins.json` annotates that same SHA-256 (`91eae1ca…`) as an
   "unscored alternate" and the d1.5 raster (`68d0e2e4…`) as "labelled 0.2477". Going-forward
   rule: record filename + SHA-256 + returned portal score as one triple at submission time.

## Current next steps and limits

1. **A submittable file now exists; nothing has been uploaded.** `index.html` and `executive-summary.html` lead with `gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif` — all 12,279,160 cells finite `float32` in `[0, 1]`, 0 NaN, exact template grid, 44,090 off-catalogue predictions — plus a paste-ready note, a d1.5 alternate, and a NaN-outside twin. The range-error cause is diagnosed (IR-30-044), not "undiagnosed". **Remaining limit:** local format validation is not organizer acceptance, and no score is claimed. The prediction content is the owner's best-reported artifact re-encoded without altering a single in-footprint value, so it cannot itself beat 0.2600; a slot spent on it re-tests a known file. The next lever is a better score field, per §7.3 of the knowledge base.
2. **H-31-02r is the strongest measured new feature signal, but not a submission candidate.** Its spatial evidence is split between the incomplete catalogue proxy and independent SGMC frames, and the SGMC calibration-ratio criterion misses its fold threshold in 2/4 folds. The predeclared dual-frame gate withholds promotion. Do not rerun or retune on the inspected SGMC labels. A future OOF model integration would need a frozen design and validation independent of those inspected labels; absent that, do not spend a slot. Full results: [placement/scarp holdout](docs/research/h33-01-placement-and-scarp-holdout.md) and [three-check review](docs/research/verification-checks-results.md).
3. **Boundary-loss line remains closed.** The 300 m geometry term remains paired with regional loss and changes near-miss allocation, but seed-31 and larger-budget confirmations do not establish a DTI gain; weight-sweep scoring criteria disagreed. Do not restart λ tuning without a materially new, preregistered mechanism and independent validation.
4. **Untried geology:** the five current candidates, exact layers/signatures, planning priors/costs, official source/access checks, and falsifiable gates are in [docs/hypotheses.md](docs/hypotheses.md) and [the bounded novelty audit](docs/research/untried-hypotheses-review-2026-10-03.md). H-31-04's GeoDAWN lineage/schema audit is the lowest-cost next *new-hypothesis* action; H-31-03 needs full-ROI NHD/DEM coverage; H-32-04 needs an independent inventory such as OSTI 1148722 or GDR 616, not Qfaults alone.
5. **Scores and sources:** the public snapshot showed DARD 0.3195 and `wbg1` 0.2600; no row identifies a TIFF hash, so D2.8's score attribution remains unresolved. The official data page is login-gated; pinned owner mirrors are not organizer-authenticated. No credentials, login bypass, or automated DrivenData monitoring are used.
6. **Rules:** eligibility, the 5:00 p.m. ET vs 11:59 p.m. UTC deadline discrepancy, and entrant-approved AI disclosure need authorized sign-off or organizer clarification. See [official-rules review](docs/research/official-rules-review-2026-10-03.md) and IR-30-008/020.
7. **Experiment integrity:** report global and active scored-domain counts separately; equal global counts are not active-count matched. Preflight realized capacity before freezing budgets; enforce 300 m spacing where needed; do not treat catalogue/SGMC proxy scores as private competition scores.
8. **Status:** `scripts/build_status.py` regenerates `docs/status.json`; refresh the public leaderboard only through a permitted, dated manual route (no scraper). Record the final test/link audit, current branch PR, and merge outcome in [the cumulative review checklist](docs/research/review-checklist-2026-10-03.md) after each is actually verified.


---

<a id="current-owner-prompt"></a>
## Current owner prompt — complete task text (formatting normalized)

**Requirements and owner-reported claims, not verified results.** Read this at the start of every session.
Whitespace and link formatting are normalized; repeated requests and the supplied submission list are retained.
The [current run card](docs/research/texture-displacement/run-card.json) and automated gates, not the quoted claims, determine readiness.

<details>
<summary>Expand the complete owner task text (2026-10-25)</summary>

```text
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

https://buffedlizard55-lab.github.io/8GEMSDOE/docs/index.html

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
wormrank-d28-20261003-59dcaf6dd11d-zeros:0.2560
wormsurv-filter-20261003-921f10960d6e-zeros: 0.0532
xfit-c0-habitat-20261003-ca879db0089a-zeros:0.0439
xfit-h41-union-qfaults-20261003-9edb34b99e3a-zeros:0.0356

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

h57r-joint-strata-38000-20261010T214547Z-00cf5b2066f1-zeros: 0.0254

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

h69-joint-relayramp-pullapart-38669-20261020T201504Z-f29b6df5:0.0053

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

This is the guidelines we need to follow.https://www.drivendata.org/competitions/306/competition-doe-gems/

Get familiar with the problem through the overview and problem description,https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/. You might also want to reference additional resources available on the about page,https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/.

Download the data from the data,https://www.drivendata.org/competitions/306/competition-doe-gems/data/, tab.

Create and train your own model. This reference solution,https://github.com/drivendataorg/gems-prize-reference-solution implements a simple approach.

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
```

</details>
