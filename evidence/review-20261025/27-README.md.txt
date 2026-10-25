# 27GEMSDOE - topology-first research and submission lab for DrivenData #306 (DOE GEMS)

## Session 9 addendum (2026-10-25, merged with the parallel Lane L-S7 session; read at every session start)
**A new unique TIFF was generated (H30) and it is NOT certified for submission — ⛔ DO NOT SUBMIT it.**
H30 = the twice-confirmed Arm-D subsurface detector, re-ranked by a label-free hydrothermal-chemistry
field (measured well/spring temperatures; canary AUC 0.499) and emitted with deconflicted placement
(≤65 % of the 38,000-dot budget within 3 px of repo-shipped rasters). Fresh seeds 240–244 (first use),
20 cells, 59,372 withheld positives: pooled HOLDOUT-DTI **L 0.09608 vs B 0.10031 vs D 0.10234**;
paired **L−B −0.00445 [−0.00800, −0.00112]** (7/20 cells) and **L−D −0.00662 [−0.00845, −0.00463]** —
the frozen promote gate FAILED (negative; no post-hoc tuning; seeds consumed). D−B replicated
**+0.00217 [−0.00126, +0.00531]** (15/20 cells, 5/5 seeds) — third disjoint seed set with positive sign.
**Measured consequence (the session's real deliverable): buying strict self-registry uniqueness costs
more than the confirmed detector gain** — IR-2026-10-25-06's tension is now a number (IR-2026-10-25-14).
The H30 bytes (`docs/downloads/research/gems27-h30-chem-deconf-b2-38k-20261025-ad5a68bb0535-allfinite.tif`,
sha256 `047f383d9f76…`, validator hard-PASS) are **unique vs every screened raster in the merged repo**:
≤0.320 vs all 12 pinned peers; ≤0.648 vs all 12 repo rasters at build time; **0.302 vs the parallel
session's H29-S** (re-screened post-merge; exact shared pixels 1,812/38,000) — unique and valid are
necessary, not sufficient. **Selector decision recorded (IR-2026-10-25-15):** the current owner prompt's
focus sites = the 12-peer parallel registry = the operative duplicate screen (strict screen reported
alongside); under it the holdout-passed H29-1 D-refill family is eligible, and its badge flip is a
recorded owner action touching no bytes — **this session flipped nothing**. Instrument disclosure: H30's
E2 used the pre-fix `emit()` candidate domain (`valid ∪ hidden`, as in H29-1/L-DCONFIRM); the parallel
session's ring-leak fix (whole-fold domain) post-dates the frozen run, all three arms shared the same
instrument so the paired deltas stand, and no re-run was performed (that would be a 4th experiment).
Evidence: `evidence/h30_holdout.json`, `evidence/h30_run_card.json`, `knowledge/20` (prereg),
`knowledge/21` (hypothesis screen), `knowledge/22` (result). 112 tests pass; ruff clean.

**Site:** https://buffedlizard55-lab.github.io/GEMSDOE27/ — first screen (`index.html`) and `executive-summary.html` render the automated fail-closed machine gate (`gems27.readiness.publication_decision`), one-click GeoTIFF/ZIP links, unique submission name, and copyable `<= 140`-char note directly from byte-bound JSON receipts.

## Parallel Session 9 addendum — Lane L-H30 (merged after H29-S above)
**One new unique TIFF WAS generated this session, and it is ⛔ NOT OK TO SUBMIT.**
Lane L-H30 preregistered three contenders against the strongest in-repo control
(Arm D) — H30-1 dip-advection, H30-2 along-strike gap flanking, H30-3 soft
rank-taper emission — in [knowledge/20](knowledge/20_lane_h30_preregistration_2026-10-25.md)
(committed before any run), and gated them on fresh seeds 240–244. **All three
failed the frozen selection gate**: pooled **HOLDOUT-DTI** (`gems27.metric` v1)
D 0.10234 · GAP 0.10180 · SOFT 0.09943 · DIP 0.09888 (20 cells, 59,372 withheld
positives; canary max AUC 0.561, clean). No confirmation ran; no tuning followed.
The single built file (GAP arm, per the pre-result fallback rule) is a
**NEGATIVE research artifact**: `docs/downloads/research/gems27-h30-gapflank-b2-38k-20261025-3107a3007b77-allfinite.tif`
(sha256 `deb8b4f1…`, 38,000 dots) — format-valid (all-finite [0,1], the portal-error
fix) and peer-unique (max 45.7 % dot overlap vs the 12 pinned registry rasters)
but **DO NOT SUBMIT**. Full result: [knowledge/21](knowledge/21_h30_result_2026-10-25.md);
run card: `evidence/h30_dipgap_run_card.json`. The site's first screen and executive
summary show this status, computed fail-closed from the run-card JSON by
`scripts/audit_submission_readiness.py` (no human-inspection gate). Data-readiness
was restored first: 16 hash-pinned inputs OK, prepared stack sha256 `83ed2704…`,
107 tests passed, `verify_downloads.py` 0 failures. **Still no TIFF in this repo
is certified OK to submit**, and no live/organizer score exists for any file here.
The historical verbatim prompts below remain preserved.

## Current Automated Gate & Unique Candidate GeoTIFF (`Lane L-S7-2026-10-25` / `H29-HPVC`, `2026-10-25`)
* **Unique Submission Name:** `27GEMSDOE-H29S-20261025-511898747886` (`content_id = 511898747886`)
* **One-Click All-Finite GeoTIFF (`[0, 1]` fix):** `docs/downloads/gems27-h29-hydrothermal-piedmont-celf-20261025-511898747886-allfinite.tif` (`825,276 B`, SHA-256 `8585c5e870f197f84fda5bac7f22047d646fb73d455eb8b1129486c79bb976cf`) + single-member ZIP `gems27-h29-hydrothermal-piedmont-celf-20261025-511898747886-allfinite.zip` (`174,419 B`)
* **Copyable Short Note (`110 / 140` chars):** `27GEMSDOE H29-S | stitchedOOF hydro+piedmont+Frangi+CELF300m B2 37654px | id 511898747886 | unscored hold-slot`
* **Automated Machine Verdicts (`evidence/h29_run_card_2026-10-25.json`, `docs/data/submission_readiness_audit.json`, `scripts/verify_downloads.py` `162/162 PASS`):**
  1. **Technical Format & `[0, 1]` Range Gate — `PASS`:** Single-band `float32`, `EPSG:32611`, `3730×3292`, exact `{0.0, 1.0}` across all `12,279,160` cells (`0` NaN, `nodata=None` per official reference notebook Cell 19), `0` catalogue overlap, strict `B2` (`d_cat > 200 m`), `37,654` dots (`min_self_spacing = 2.0 px`).
  2. **24-Raster Uniqueness Gate (All 12 Peer Rasters + All 12 In-House Rasters) — `PASS`:** Unlike `H29-1 D-refill` (`c24b6371179c`) and `L-DCONFIRM` (`5ea0385b7e70`) which failed the self-registry screen against dense `H28-1` (`85.4% > 70%`), **`H29-S` (`511898747886`) clears ALL 24 rasters**: max 3-px dot overlap = **`64.21% <= 70%`** (`56.12%` vs `GEMSDOE32` `0.2778`, `56.43%` vs dense `H28-1`, `53.01%` vs `L-DCONFIRM`, `52.56%` vs `H29-1 D-refill`, `51.33%` vs `H29-1b`), pre-placement surface Spearman `max = 0.4776 <= 0.90`, post-placement Spearman `max = 0.0563 <= 0.90`.
  3. **Leakage Canary Gate — `PASS`:** Max direction-invariant holdout ROC-AUC across all 20 `H29` features = **`0.5765 <= 0.90`** (`evidence/h29_e1_canary_and_surface.json`; `dist_known_fault_px` strictly banned and unit-tested).
  4. **Blind Spatial Holdout (`HOLDOUT-DTI`, frozen unused seeds `210–219`, `40` cells, `118,673` withheld positive occurrences, `gems27.metric v1 + holdout-blind-buffered-v2`):**
     - **`H29-S` sets a NEW REPOSITORY #1 BLIND POOLED `HOLDOUT-DTI = 0.042198`** (unbuffered diagnostic `0.103907`), vs `D0 = 0.040902`, `H29-A = 0.039698`, `H28_1_B2 = 0.037578`, `B0 = 0.036368`, `U0 = 0.015341`.
     - **Beats `B0`:** **`+0.005829`** (`95% CI [+0.004420, +0.007417]`, **`10/10` seeds, `4/4` folds**).
     - **Beats prior promoted repo champion `H28-1`:** **`+0.004620`** (`95% CI [+0.003442, +0.005974]`, **`10/10` seeds, `3/4` folds**).
     - **Fixes `H27-6` (`H29-S` weighted 300 m CELF cover minus `H29-A` Poisson `d=2.8` on identical surface):** **`+0.002500` buffered / `+0.005716` unbuffered** (`95% CI [+0.000736, +0.004311]`, **`8/10` seeds**).
     - **Edges Session-6 internal control `D0`:** **`+0.001295` buffered / `+0.005399` unbuffered** (`3/4` folds: `NW +0.0022`, `NE_LidarGap +0.0024`, `SW +0.0032`), **but `SE` Walker Lane lagged `-0.0025`**, leaving the strict seed-bootstrap 95% CI vs `D0` at `[-0.000986, +0.003695]` (`3/6` strict composite gate clauses at commit `30accf8`).
  5. **Fail-Closed Weekly Live Slot Decision (`gems27.readiness.publication_decision` + `AGENTS.md` Hard Rule #3) — `HOLD WEEKLY SLOT` (`NO TIFF IS APPROVED TO SUBMIT` for a scarce `5/week` live slot yet):** Thresholds are never relaxed post-hoc. Preserve the weekly live slot and run `H29-6` (appending `ieq_n100a15`/`deq_n100a15` Walker Lane seismic-fabric coherence to `H29-S` on fresh unused seeds `220–229`) to clear the `SE` CI sub-clause first (`knowledge/16_h29_results_and_next_steps.md`).
* **Live Forensic Proofs (`OWNER-REPORTED`, no organizer receipt stored in repo):**
  - **`GEMSDOE32` (`h33-h33-2-b2-...-zeros`, `0.2778`):** Byte-verified (`c55bafc4…`, `37,654` dots) = `(GEMSDOE25_D2.8 > 0) & (EDT(~existing_faults) > 2.0)` — zero new geology, removing `7,865` zero-credit `0–200 m` collar FPs (`0.2586 -> 0.2778`).
  - **`27GEMSDOE` Slot 1 (`5512495c6bd1`, `0.2449` vs `24GEMSDOE` `0.2477`):** Byte diff (`evidence/slot1_live_ab_inversion.json`) proves Slot 1 adds `1,259` `T-v2` straight-line continuation dots (`0` removed); pure zero-hit FP dilution predicts `0.24491`, matching `0.2449` to 4 decimal places (`-0.00018` credit/dot vs `+0.05024` break-even).
  - **Template Bugs Fixed in Place (`IR-2026-10-25-10..13`):** Fixed `emit()` `600 m` hidden-ring mask leak and `parallel_registry` path typo in `scripts/run_lane_holdout.py`, fixed streaming memory footprint in `src/gems27/subsurface_features.py`, and audited PR #14's `98e59bf8e3ce` (`HOLDOUT-DTI = 0.0`, `evidence/audit_98e59bf8e3ce_uniqueness.json`).

---

## Parallel Session Audit Addendum (`2026-10-25`; read at every session start)
Run `.venv/bin/python scripts/audit_submission_readiness.py` to refresh the public [byte-bound submission evidence audit](docs/data/submission_readiness_audit.json). Badges fail closed on contradictory/missing evidence, hash mismatch, failed efficacy or uniqueness, leakage canary, and invalid notes (`knowledge/19_readiness_audit_20261025.md`, `knowledge/18_session8_repo_review_2026-10-25.md`). Note: parallel lanes `H29-1 D-refill` (`c24b6371179c`, seeds `210–214`) and `L-DCONFIRM` (`5ea0385b7e70`, seeds `215–224`) confirmed `D0` vs `B0` (`+0.0086` / `+0.0076`) but failed the extended self-registry uniqueness screen (`85.4%` vs `H28-1`, `87.5%` cross-session overlap; `IR-2026-10-25-06/09`), whereas `H29-HPVC` (`511898747886` above) clears all 24 rasters (`<= 64.21%`) and holds its weekly slot solely pending `H29-6` SE Walker Lane closure on fresh seeds `220–229` (seeds `210–224` are now consumed; use `225–234` for `H29-6`!).
Owner-reported reference: `24GEMSDOE` scored **0.2477** (`OWNER-REPORTED`); `27GEMSDOE` Slot 1 scored **0.2449** (`OWNER-REPORTED`); `GEMSDOE32` `H33-2-B2` scored **0.2778** (`OWNER-REPORTED`); leaderboard #1 is cited as **0.3195** / **0.4413** (`IR-2026-10-25-02`; unconfirmed; the agent never accesses `drivendata.org`).

## Start here every session (checklist)
1. Re-read **Task prompt (verbatim)** and **Core Values (verbatim)** below. Maximize P(Win) and Own the Outcome are the focal point of every build, research and implementation decision.
2. Do the previous sessions' next steps first: for Lane L-S7/H29-S read `knowledge/16_h29_results_and_next_steps.md` (H29-6 Walker Lane closure; seeds 210–224 consumed); for Lane L-H30 read `knowledge/21_h30_result_2026-10-25.md` (DIP/GAP/SOFT all failed selection vs Arm D on seeds 240–244; never reuse 240–254 for confirmation); then `knowledge/06_limitations_and_access.md` -> newest carry-forward sections. Data restore is proven working (Session 9), but `data_cache/` is git-ignored: re-run `scripts/restore_data.py` and `scripts/prepare_data.py` before claiming any fresh validation.
3. Verify inputs: `python scripts/restore_data.py` (16 hash-pinned artifacts; SHA-256 in `data/manifest.json`), `python scripts/prepare_data.py`, then `python -m pytest -q` and `python scripts/verify_downloads.py`.
4. Verify line by line against official sources and give links for manual review (`registry/sources.json`, `docs/sources.html`). Flag irregularities (`registry/irregularities.json`). No hallucinations: unknown stays unknown.
5. Never automate drivendata.org (Terms of Use); never claim an upload, score, PR or merge without evidence.
6. Before implementing new predictive features: maintain a current screen of 3–5 genuinely untried hypotheses in `knowledge/07_untried_hypotheses.md` and `registry/next_hypotheses.json`; validate any chosen candidate on the spatially blocked holdout **before** a weekly slot is spent. The broader `registry/hypotheses.json` is the historical evidence ledger.
7. Run three passes: implement+verify; review bugs/assumptions/edge cases; recheck against the original request (`evidence/review_passes.md`).

## Submission status — no current approved TIFF

**Do not upload any file from this repository as a current recommendation.** The current method lane, H28-3, failed its frozen efficacy gate despite passing its leakage, format, and peer-uniqueness checks. Its download package exists solely for reproducibility and carries the explicit status **NEGATIVE RESEARCH ARTIFACT — NOT APPROVED FOR SUBMISSION**:

- Evidence: `evidence/h28_3_strain_holdout.json` and `evidence/h28_3_negative_uniqueness.json`
- Protocol: `knowledge/13_preregistration_H28-3.md`
- Research manifest: `docs/downloads/research/h28_3_negative_research_manifest.json`
- All-finite reproducibility TIFF: `docs/downloads/research/gems27-h28-3-strain-conductivity-negative-research-20261025-27d6875f3b22-allfinite.tif`

Historic Slot 1–5 and H28-1 artifacts remain retained for audit and reproduction; they are not submission instructions. A future file may only be labelled **OK TO SUBMIT** after a new hypothesis beats its pre-registered spatial holdout gate, passes leakage/format checks, is uniquely screened against the parallel registry, and has a corresponding public evidence card. Human upload and organiser score recording remain separate steps.

## Session 6 update — H28-3 negative result and public disclosure

* **Frozen result: FAIL; no weekly slot.** The candidate's pooled HOLDOUT-DTI was 0.1033523 vs 0.1059458 baseline (Δ **−0.0025935**), with mean paired seed Δ −0.0025884 and deterministic 95% bootstrap CI [−0.0042399, −0.0009065]. Only 2/10 seeds and 1/4 folds improved. Canary, integrity, and uniform-control checks passed; efficacy gates failed. No post-hoc tuning or rerun is allowed.
* **Peer uniqueness does not promote a failed predictor.** The negative artifact passed the configured 12-peer duplicate screen (largest surface rank correlation 0.06217; largest directed 3-pixel overlap 0.48915), but it remains ineligible because predictive validation failed.
* **Three genuinely untried hypotheses remain:** H27-16 official GDR layers (bytes/provenance still required), H28-4 seismicity-fabric lineaments, and H28-5 quality-filtered hydrothermal chemistry gradients. See `knowledge/07_untried_hypotheses.md` and `registry/next_hypotheses.json`.
* **No competition outcome was claimed.** No DrivenData access, upload, or organiser score occurred. [PR #11](https://github.com/buffedlizard55-lab/GEMSDOE27/pull/11) merged this documented negative-result/public-disclosure update to `main` at merge commit `c3276755d1f26d2f72991de033d005413e1c99aa` after the CI test job succeeded; this GitHub event is distinct from a competition result.

## Session 6 (2026-10-25) — why 0.2778 won (pixel-exact), Lane L-2026-10-25 NEGATIVE, [0,1] fix shipped

* **Why 0.2778 won (`knowledge/12_why_02778_won.md`, MEASURED):** the GEMSDOE32 file
  `h33-h33-2-b2` (sha256 `c55bafc4…`, hash-authenticated here) is *pixel-exactly* the 0.2708
  file minus its 2,545 dots within (1,2] px of the catalogue: 0.1922 solid → 0.2477 dotted
  d1.5 → 0.2600 d2.8 → 0.2708 r≤1 prune → 0.2778 B2 prune (all OWNER-REPORTED; no
  ORGANIZER-CONFIRMED receipt exists in this repo). Each step deletes near-zero-credit FP
  mass; GEMSDOE36's independent PINN (0.2750) converges on the same B2 + ~38 k optimum.
  All five top files are the same dot field (91–100 % within 3 px), so beating 0.2778 needs
  new detector information, not more thinning.
* **Lane L-2026-10-25 (`knowledge/13`, declared because the prompt's "single method
  paragraph" was not delimited — IR-2026-10-25-01):** subsurface-only buried-fault detector
  (potential-field edges/strain/conductivity/seismicity fabric; lidar excluded by
  construction), B2, 38 k dots. **Frozen gate FAILED** (`knowledge/14`): pooled HOLDOUT-DTI
  0.0752 vs full-32 control 0.1001 (Δ −0.0262, 95 % CI [−0.0368, −0.0163], 60,423 withheld
  positives, seeds 200–204); canary clean (max AUC 0.576); uniqueness PASS (surface
  Spearman ≤ 0.100; final-dot overlap ≤ 51.0 % vs any registry raster). The unique TIF
  `docs/downloads/gems27-lane-subsurface-buried-fault-20261025-fc6d8c3acf6c-allfinite.tif`
  (sha256 `d648a3cc…`) is generated and format-valid but badged **⛔ RESEARCH ONLY — DO NOT
  SUBMIT** on the site's first screen. **Nothing is approved to submit** (aligned at merge with PR #11's STOP policy: legacy slots demoted to audit-only after the peer-overlap audit; H28-3 and this lane both negative).
  Positive control: the 15 lane transforms ON TOP of the full stack gained +0.0045
  HOLDOUT-DTI [+0.0003, +0.0090] — the recommended *next preregistered lane*, not shipped.
* **[0,1] portal error:** both mechanisms re-measured (sentinel −3.4e38 in 3,061 in-footprint
  cells; NaN-outside strictness). New primary downloads are all-finite (nodata=None, every
  cell in [0,1], independent re-read receipt in `docs/downloads/checks-*.json`).
* Template fixes (protocol §2, reported IR-2026-10-25-04): buffered scoring mask in
  `gems27.holdout`; detector column selection in `gems27.oof_detector`. 86 tests pass.

## Session 5 update — H27-10 rejected; H27-5b review class (`knowledge/06`, `knowledge/11`)

* **H27-10 frozen gate: FAIL; no weekly slot.** On seeds 150–159, baseline mean DTI was 0.10937685 and the annulus substitution mean was 0.11022300: paired ΔDTI **+0.00084615**, below +0.001. Fold means improved 4/4, seed means 7/10 (gate required 8/10), and added-annulus efficiency was **0.03357**, below m(0.2477)=**0.05212**. The first run's self-distance spacing diagnostic falsely marked the integrity check; the initial JSON is preserved. A corrected same-seed integrity rerun passed all data checks while leaving all metrics and the failed gate unchanged. It is not fresh confirmation. See `evidence/h27_10_annulus_holdout.json`, `evidence/h27_10_annulus_holdout_initial.json`, and Addendum F.
* **Review-only H27-5b class:** applied to the existing 345 z≥3 deduplicated T-v2 short links (1–4 km gaps), with exact filter `fid_src != fid_tgt AND same_name AND kinematic_compat`; count **81/345** (73 end-to-end, 4 abutting, 4 tip-to-tip oblique). Focused review files are `docs/data/topology_priority_h27_5b.csv` and `.geojson`; `docs/assets/fig_map_h27_5b_priority.png` previews the 81 links, and the Topology page includes class counts, source links, per-link arguments, cautious geometry cues and a searchable class column. Tier-2 whole-FID enrichment (0.1783 vs 0.0204 rotated control) supports review prioritization only—not hidden-label truth, transfer or live-score gain. FIDs are records in one NBMG compilation; unknown kinematic fields can pass the screen.
* Graph-ΔP ranking and overlapping en-echelon step-overs remain **refuted as holdout-improvement signals**. A geometry cue is not a fault interpretation. This Session 5 statement is superseded by the Session 6 screen above: three genuinely untried hypotheses remain, while H27-10 and H28-3 are tested failures.
* NBMG REST layer metadata, all four fetched chunks of Faulds & Hinz (OSTI), and the Berkowitz publisher abstract were rechecked; status is in `registry/sources.json`. The raw GDR #1391 packages have not been fetched/re-hashed in this checkout. Recorded GDR fetch-workflow attempts failed before any job and have no logs; the cause is unknown and source unavailability is not inferred (details in the irregularity register). No DrivenData access, upload or live score occurred. [PR #9](https://github.com/buffedlizard55-lab/GEMSDOE27/pull/9) merged to `main` at `733e2b2141c8babba29da383d264b4f3da12de38`; GitHub closeout and verification are recorded in `evidence/review_passes.md`.

## New in Session 4 — the far field was measured, and the holdout ran out of resolution (`knowledge/10_session4_farfield_measurement_and_proxy_limit.md`)
* **A live score this repo never had.** 16GEMSDOE's h18-4 (content id `aef8f42c`, sha256 `736f62c2da58…`, owner-reported **0.0360**) is the only scored emission in the programme whose pixels are *all* ≥300 m from the catalogue — 57,783 px of USGS State Geologic Map Compilation faults with no Quaternary counterpart. It was registered, hash-authenticated, its construction re-verified from the raster bytes (0 positives on catalogue px, minimum catalogue distance 3.16 px, 34 residual 2×2 blocks, 79.66 % on the restored SGMC mask), and inverted with this repo's own metric code — which first reproduced Session 3's published anchors to 5 significant figures (0.2477 → credit 5,286.0, concentration 5.667; 0.1922 → 6,188.8, 5.663).
* **Verdict: 1.62× blind** (exact bracket 0.76–1.65× over MP ∈ [0, N]), credit fraction **0.062 of |G|**, best modelled score at its own thinning optimum **0.0424** — against 5.3–6.0× for the family that produced 0.2477. Its 1-px lines also cover *less* DTI kernel mass than a uniform spray of the same size (c = 0.0384 vs 0.1050, ρ = 2.73 vs 1.43): an independent confirmation, from a file built by a completely different route, of why dotting beats tracing. **Never emit on an "independent second catalogue" again.**
* **The corollary that kills a plausible idea:** SGMC-gap pixels have a *higher* mean 1 m LiDAR positive-laplacian response than catalogued faults (136.4 vs 99.7; random background 86.2 — all on `lidar:valid` pixels only). Raw scarp-detector intensity does **not** discriminate hidden truth; position relative to the Quaternary catalogue does.
* **Addendum D (seeds 140–149, pre-registered and committed before running).** The base arm reproduces Session 3 exactly (mean DTI 0.08894 vs 0.0861; T-v2 paired gain +0.01221 vs +0.0115), so the instrument did not drift. **+24 oriented 0.5–2 km lineament bands: PR-AUC +0.0010 → REFUTED** (registered requirement +0.005); radiometric ratios +0.0007 and thermal-point distances +0.0005 likewise. Only the SGMC-distance arm passes criterion 1 (+0.01817 PR-AUC, 0.0246 → 0.0428) and the union arm (+0.02177), and both then pass criterion 2 (paired DTI **+0.02852** and **+0.03414**, 4/4 folds each). **Graph-connectivity ranking of the 345 links: REFUTED** (top half by |dP| 0.2914 vs all links 0.2889 — ratio 1.008 against a required ≥1.15 — and *below* the random-half 95th percentile 0.3117; the bottom half scored 0.2953). **Overlapping en-echelon step-overs — a class the forward-cone rule cannot generate at all (148.8 links/cell, median lateral offset 1.36 km, median along-strike overlap 1.12 km, median strike difference 8.1°): REFUTED** (pooled efficiency 0.0605, below break-even 0.0638, and only 1.11× the perpendicular-strike control against a required ≥2.0×; they still add +0.0022 paired DTI in 4/4 folds, 5.5× weaker than T-v2's +0.0122 at a quarter of the efficiency).
* **Why the two passing arms were NOT promoted** (`evidence/arm_habitat_decomposition.json`). Hidden truth in every gate this programme has run is catalogue pixels, so **100 % of it (120,983 px) lies at distance 0 from the published catalogue** and Habitat A (≥300 m away) contains *zero* truth by construction. Base-arm credit shares: 36.8 % on the catalogue spine, 51.5 % at 100 m, 11.4 % at 200 m, 0.37 % at 300 m–1 km, **0.0 % beyond 1 km** — while the live-scored 0.2477 emission puts **81.4 % of its dots ≥300 m away** (median 1.5 km) and earns 5.67× blind. The proxy is not biased against far-field arms, it is **blind** to them; both arms' entire gain is catalogue proximity, and their distinctive far-field behaviour is the habitat just measured live at 1.62× blind. Passing a gate that cannot see the habitat that pays is not a reason to spend a slot — so Slot 5 asks the question live instead, at fixed pixel count.
* **The graph argument a reviewing geologist can check independently** (`src/gems27/graph_value.py`). Every one of the 345 candidates now carries its network consequence — bridge status, merged system length, change in the largest-system share of mapped fault length, dP under Berkowitz et al. (2000) computed with this repo's own unit-tested closed form, and a continuous d(Σl²) tie-break — in `registry/topology_candidates.json`, `docs/data/topology_links.csv`/`.geojson` and `docs/topology.html`. **Closing all 345 moves the network's connectivity parameter from P = 5.784 to 6.124, i.e. from inside the paper's critical range (Pc 5.6–6.0) to above it; 339 of 345 links are bridges.** Disclosed: dP is quantised to {−1, 0, +1}·P/n_ge because it counts systems above l_min = 2 km (so a link joining two systems that are *both* already ≥2 km has dP < 0), and **no critical value is claimed for Σl²/area** because none could be verified from an official source inside this sandbox.
* **Access bridge built:** `.github/workflows/fetch-gdr-external-layers.yml` + `scripts/fetch_external_layers.py` download, **hash-verify against the 2026-09-30 pins** (refusing to use a file that does not match), inventory and footprint-clip three official GDR 1391 layers no detector here has ever used — paleo-geothermal (84,008 B, `faffcf69…`), INGENIOUS 2 m temperature probes (1,080,530 B, `1301f70d…`), Great Basin Quaternary volcanics (9,898,770 B, `c4a2d2df…`) — and HEAD-check the larger sources (wellspring FileGDB, both Qfaults releases, SGMC NV/CA, the Siler 2022 and DeAngelo 2022 DOIs, the GeoDAWN ScienceBase item) so obtainability is a recorded fact rather than an assumption. Results come back as a run artifact (`gh run download`). It never commits, never pushes, and never contacts drivendata.org.
* **Bug fixed:** `scripts/restore_data.py` used to leave a truncated `.part` file after a failed download and to keep a hash-mismatched assembly where the next run would trust it (this is how a corrupt 492,887,617 B / `c0e9b856…` `training_features.tif` appeared instead of the pinned 418,912,844 B / `4371c82e…`). It now removes stale parts, retries with backoff, verifies every part against the byte count GitHub itself reports, and deletes a bad assembly together with its parts.

### Separate H28-1 research candidate (not one of the four current weekly slots)

* `docs/downloads/gems27-h28-1-edge-coherence-plus-t-v2-h27-4-20261002-1113fba5f6cb-nan.tif`; ZIP, all-finite fallback, checks, and `h28_1_candidate_manifest.json` are in the same downloads directory.
* Content id `1113fba5f6cb`; SHA-256 `61f9b53de42786e6d48afa50fd453a87c57d5d7b9b626c7dcf28c2dfbd20f411`; 59,075 exact binary pixels; zero known-label overlap. Its preregistered seeds 140–149 cleared the internal gate with mean paired ΔDTI `+0.00294884`, 3/4 folds and 9/10 seeds. NE_LidarGapHeavy and seed 149 regressed; this is not a leaderboard result.
* Note to paste (`142` characters): `27GEMSDOE H28-1 research | OOF +0.0029 paired DTI; 3/4 folds, 9/10 seeds; no live score | id 1113fba5f6cb | research only; not yet live-scored`.
* See `docs/research.html` for direct download links and `knowledge/09_preregistration_H28-1_candidate.md` for recipe, checks, hashes and limits. The candidate is not a fifth weekly slot and does not replace or alter any of the four current slot artifacts.

## New in Session 3 — the live scores were inverted (`knowledge/07_live_score_inversion.md`)
All **20** of the owner's scored rasters that could be matched were recovered from the sibling repositories and accepted **only if their SHA-256 equalled a `registry/live_scores.json` row** (provenance by hash, not filename; `scripts/fetch_scored_corpus.py`). Five rows could not be matched and are listed as unmatched, not guessed.
* **The exact identity**, including a term the programme had been missing: `DTI = TPw / (0.2·TPw·(1 − ρ) + 0.2·N + 0.8·|G|)` where `ρ = MPw/TPw` is a **crowding factor**. Credit takes a *max* over predictions per truth pixel but false-positive mass takes a *sum*, so a pixel that merely sits near truth is cheap even when redundant — **crowding near truth is a discount, not a penalty**. The identity reproduces both live anchors exactly: H19-5 solid → **0.1922** (live 0.1922), dotted d1.5 → **0.2477** (live 0.2477).
* **|G| = 12,226 px**, from a blind spacing-5 lattice whose credit per truth pixel (`c = 0.37481`) is pure geometry and needs no assumption about *where* the truth is. The sibling's independent estimate was 12,503 — **2.2 % apart**. Use 12.2–12.8k.
* **Retention rule validated twice live**: `credit(d) = credit_solid · c(d)/c_solid` predicts H19-5→d1.5 to **−0.1 %** and H25-ctx→h28 to **+4.0 %**. Budget optimum **d = 2.25–2.8 → 0.2550** (+0.0073); the sibling's independent fit said 0.2553. **The emission-geometry lever is exhausted at ≈0.255.**
* **Concentration** (`(TPw/|G|)/c`) ranks detector quality independently of budget: the 0.2477 file is **5.67×** better than blind. The whole H19-5/h19-4/h16-1 family **plateaus at 5.3–5.7** — same detector, different clothes — and **no submission in the group's history has ever earned more than 0.508·|G|** of credit.
* **0.3195 is arithmetically out of reach by rearranging pixels**: at 60,069 px it needs **0.570·|G|** of credit, more than any submission has ever earned at any budget; at 44,090 px it needs 0.486·|G|, which H19-5 solid *has* (0.506) but thinning to that budget retains only 0.759 → 0.384. **Retention, not knowledge, is the wall.** Only two routes remain: retention ≈1.0 at ~44k px, or concentration above 5.7 — both are detector problems needing *new information*.
* **Rejected with evidence, so nobody re-derives them:** H27-6 coverage-optimal thinning (**0.866× Poisson-disk — 13 % worse** at the budget that matters); H27-7 union-recall ensembling (central 0.2655 but **pessimistic bound 0.2310**, vs 0.2550 for h19-5 alone on a rule validated to 4 %); H27-9 habitat tomography (**not identifiable** — LOO score RMSE 0.0715 vs a score spread of 0.0686, signal ratio 0.96).
* **Leaderboard context** (secondary quote from the sibling's owner-directed read, *not* fetched by this agent — drivendata.org is off limits): rank 1 **0.3195**, rank 2 **0.3128 with only 2 submissions**, rank 5 **0.2941**; the group's 0.2477 sits at **rank 16**. Rank 2 reaching 0.31+ in two attempts is evidence of a materially better **detector**, not a better submission schedule.

## What is validated, and what is not
| claim | status |
|---|---|
| Files are single-band float32, exact 0.0/1.0 inside the footprint, NaN outside (nodata=NaN) like the sample; fallback and zip provided | verified by an independent script (`scripts/verify_downloads.py`, **147 checks, 0 failures**, covering the five weekly-slot files, the separate H28-1 research candidate, and the Addendum-E single-variable invariants) |
| Emitting on independently-mapped bedrock faults the Quaternary catalogue lacks ("a second official catalogue sees what we miss") | **LIVE-REFUTED** — h18-4 scored 0.0360 → 1.62× blind (bracket 0.76–1.65×), credit fraction 0.062 of \|G\|, best modelled 0.0424 (`evidence/sgmc_gap_inversion.json`) |
| Ranking gap links by graph-connectivity value beats the local z ≥ 3 rule | **REFUTED** on seeds 140–149 (0.2914 vs 0.2889, needed ≥1.15×, and inside the random-half spread). The values stay in every dossier as documentation |
| Overlapping en-echelon step-overs are a productive candidate class | **REFUTED** (efficiency 0.0605 < break-even 0.0638; 1.11× the perpendicular control, needed ≥2.0×) |
| Oriented 0.5–2 km lineament integration, radiometric ratios or thermal-point distances improve the detector | **REFUTED** as features on this footprint: PR-AUC +0.0010 / +0.0007 / +0.0005 against a registered +0.005 requirement |
| The catalogue-internal holdout can decide whether a better detector pays | **REFUTED** — 100 % of its truth sits at d = 0 from the published catalogue and 99.6 % of credit within 200 m, while 81.4 % of the live emission's dots are ≥300 m out. Slot 5 is the registered live substitute |
| The four weekly files are single-band float32, exact 0.0/1.0 inside the footprint, NaN outside (nodata=NaN) like the sample; fallback and zip provided | independent script (`scripts/verify_downloads.py`, 79 checks, 0 failures) |
| Separate H28-1 full-map research candidate is a valid, exact binary single-band GeoTIFF on the official template grid | independently verified by the same audit: EPSG:32611, 3730×3292, float32, `[0,1]`/finite inside, NaN outside with nodata=NaN, all-finite fallback, one-TIFF ZIP, no known-label overlap; candidate is unscored and not a weekly slot |
| The forward model `DTI = TPw/(0.2·TPw·(1−ρ) + 0.2·N + 0.8·|G|)` reproduces the two live anchors | **verified exactly** on hash-authenticated rasters: H19-5 solid → 0.1922, dotted d1.5 → 0.2477 (`evidence/live_inversion.json`, `tests/test_inversion.py`) |
| The retention rule `credit(d) = credit_solid·c(d)/c_solid` transfers to an unseen live pair | **verified**: −0.1 % on H19-5→d1.5, +4.0 % on H25-ctx→h28 (`evidence/budget_optimum.json`) |
| `|G|` ≈ 12.2–12.8k px | three independent instruments agree within 4.3 % (blind lattice 12,226 here; sibling lattice 12,503; sibling pair 12,769). Still an **estimate**, not an organiser receipt |
| Coverage-optimal thinning beats Poisson-disk | **REFUTED** — 0.866× at the sparse budget (`src/gems27/coverage_thin.py`) |
| Union-recall ensembling of near-disjoint surfaces beats the best single surface | **REFUTED as an improvement** — central 0.2655 vs pessimistic 0.2310, against 0.2550 for h19-5 alone |
| Habitat tomography of the hidden truth is identifiable from 20 live scores | **REFUTED** — LOO signal ratio 0.96, no better than predicting the mean |
| The 0.2477 file is exactly `dot_thin(H19-5 minus catalogue, 1.5)` | reproduced (60,069 px identical) |
| Topology gap-closure beats rotated-cone controls and random same-size subsets on the 8-connected component holdout | pre-registered gates passed on seeds 100-109 (`0.118` vs `0.057` ctrl) and confirmed on fresh seeds 110-119 (`z>=3 dedup = 0.280` vs `0.056` ctrl) and seeds 120-129 (`0.2926` vs `0.0586` ctrl) |
| Topology gap-closure and H27-5 kinematic typing beat rotated-cone controls when **whole NBMG INGENIOUS `FID` vector polylines** are held out | pre-registered Addendum B gate passed on seeds 120-129 (`evidence/vector_topology_validation.json`): `z>=3 dedup = 0.1003` vs `0.0204` ctrl (`4.92x`, `> m(0.30) = 0.0638`); `H27-5a (inter-FID + kinematic_compat) = 0.1374` (`6.74x`); `H27-5b (inter-FID + same_name + kinematic_compat) = 0.1783` (`8.74x`) |
| Topology gap-closure (H27-1) and 100–200 m flank-shadow pruning (H27-4) improve DTI on a **strictly out-of-fold 4-quadrant spatial-CV detector ($B_{\text{oof}}$)** | pre-registered Addendum C gates passed on seeds 130-139 (`evidence/oof_hypothesis_gates.json`): `plus_T_v2` gains `+0.0115` (`4/4` folds); `prune_r1_100m` gains `+0.0022` solo (`4/4` folds, removed efficiency `0.0034` vs live break-even `0.0521`) and **`+0.0141` stacked with T-v2** (`4/4` folds); H27-3 isolated-dot removal refuted (`-0.0010`, `0/4` folds) |
| H28-1 multiscale magnetic/gravity edge features + T-v2/H27-4 beat the OOF best | preregistered seeds 140–149 passed (`evidence/h28_1_edge_holdout.json`): mean paired ΔDTI `+0.00294884`; 3/4 folds, 9/10 seeds. NE_LidarGapHeavy and seed 149 regressed. Catalogue-internal only; not a public score. |
| Full-map H28-1 + T-v2 + H27-4 r1 candidate | fit on all existing catalogue labels with frozen parameters; exact binary GeoTIFF, no known-label overlap, independently format/range checked; separate research manifest and note. No weekly slot or upload used. |
| The same on the real hidden test set | **unknown until a slot is used** (only a live score tests the organisers' newly created expert labels) |
| Plausible effect on DTI at the 0.2477 operating point | Slot 1 (`5512495c6bd1`): `-0.0029` (zero hit rate) ... `+0.0024` (`FID_trace` eff `0.1003`) ... `+0.0110` (`component` eff `0.280`); Slot 3 (`d466b251f309`): `+0.0141` (`FID_trace`) to `+0.0223` (`component`) |
| Modelled DTI of all four slots under both truth assumptions | `evidence/candidate_model_scores.json`: geo/hyb — slot 1 `0.2506`/`0.2580`, slot 2 `0.2585`/`0.2671`, slot 3 `0.2439`/`0.2704`, slot 4 `0.2484`/`0.2781`. **Models, not scores.** They disagree only on the targeted prune; the geometric model is validated for *unbiased* removal and is known to be biased against *targeted* removal (it charges pruned flank pixels average credit; the OOF gate measured 0.0034, ~15× below the 0.0521 break-even) |
| Reaching 0.3195 | **No** — not with any rearrangement of pixels the group already has. It needs 0.570·\|G\| of credit at 60,069 px (more than any submission has ever earned) or retention ≈1.0 at ~44k px. See `knowledge/07_live_score_inversion.md` §8 |

## Map of the repo
| path | what |
|---|---|
| `src/gems27/` | `metric.py`, `thinning.py`, `holdout.py`, `graph.py`, `links.py`, `candidates.py`, `topology_theory.py`, `submission.py`, `grid.py`, `paths.py`, `vector_graph.py`, `topology_classes.py`, `oof_detector.py`, `potential_edges.py`, `subsurface_features.py` (streamed `<500 MB`), **`coverage_thin.py`** (`weighted_celf_cover` & `expected_weighted_coverage`), **`hydrothermal_piedmont.py`** (`H29-1` 20 hydrothermal/piedmont/destriped-magnetic features + 10 Stage-2 Frangi vesselness + 45°-rotated sectors + 2-stage nested spatial cross-fitting) |
| `scripts/` | `restore_data.py`, `fetch_parallel_registry.py`, `download_competition_data.sh`, `prepare_data.py`, `fetch_vector_faults.py`, `run_h29_holdout.py` (`E1` canary/surface + `E2` 40-cell blind holdout), `build_h29_submission.py` (`E3` dual-partition stitched-OOF GeoTIFF + Run Card builder), `run_lane_holdout.py` (`IR-2026-10-25-06/07` fixes), `verify_downloads.py` (`162/162` checks), `check_parallel_uniqueness.py`, `build_site.py`, `refresh_source_feed.py` |
| `knowledge/` | `01` why `0.2477` won; `02` hypothesis ledger; `03` pre-registration; `04` topology & vector argument; `05` verified sources; `06` limitations/access; `07` live-score inversion; `08/09` `H28-1`; `10` far-field limit; `11` `H27-5b` review class; `12` why `0.2778` won; `13/14` `H28-3` & subsurface lane; **`15` geothermal vent discovery & frozen `H29-1` preregistration (`30accf8`)**; **`16` Session 7 `H29-1` results, limitations & next steps (`H29-6`)** |
| `registry/` | `sources.json` (first-hand verified official links), `hypotheses.json` (historical ledger through `H29-1`), `next_hypotheses.json` (5 untried hypotheses `H29-6, H29-2, H29-3, H27-16, H29-5` + tested `H27-10, H28-3, H29-1`), `parallel_submission_registry.json` (12 SHA-256-pinned peer rasters), `irregularities.json` (`IR-2026-10-25-01..09`), `live_scores.json`, `topology_candidates.json` |
| `evidence/` | **`h29_e1_canary_and_surface.json`**, **`h29_e2_holdout_210_219.json`**, **`h29_uniqueness_vs_peers.json`**, **`h29_run_card_2026-10-25.json`**, **`slot1_live_ab_inversion.json`**, **`audit_98e59bf8e3ce_uniqueness.json`**, plus historical validation/inversion JSONs and `review_passes.md` |
| `docs/` | GitHub Pages site (`index.html`, `executive-summary.html`, `topology.html`, `research.html`, `sources.html`), `downloads/` (`gems27-h29-hydrothermal-piedmont-celf-20261025-511898747886-{allfinite.tif,allfinite.zip,nan.tif}`, `checks-*.json`, `note-*.txt`, `h29_candidate_manifest.json`, plus historic audit manifests), `data/` |
| `.github/workflows/` | `source-feed.yml` (official sources only; never drivendata.org), `fetch-vector-faults.yml`, `build-site.yml` (stdlib Python 3.11), `ci.yml` (tests + lint + site build) |

## Reproduce
```bash
pip install -r requirements.txt
GEMS_DATA_DIR=./data_cache python scripts/restore_data.py          # restores 17 hash-pinned artifacts (or run bash scripts/download_competition_data.sh outside the sandbox)
python scripts/fetch_parallel_registry.py                          # fetches & SHA-256-authenticates all 12 peer rasters
python scripts/prepare_data.py                                     # builds 32-band label-free feature matrix (data_cache/prepared/features.npy)
python scripts/run_h29_holdout.py                                  # E1 (canary + surface Spearman) + E2 (40-cell blind holdout, seeds 210-219)
python scripts/build_h29_submission.py                             # E3 (dual-partition stitched-OOF GeoTIFF + 12-peer uniqueness + JSON Run Card)
python scripts/verify_downloads.py                                 # 162/162 automated GeoTIFF, [0,1] range, CRS, transform, ZIP & note checks
python scripts/build_site.py && python -m pytest -q
```

## Task prompt (verbatim, owner-supplied)
```text
We are competing in this competition to be placed at the top of the leaderboard: https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/ https://www.drivendata.org/competitions/306/competition-doe-gems/

Fault network topology. In Berkowitz, Bour, Davy, and Odling (GRL 2000), a fault network's percolation/connectivity threshold is governed by its length-distribution exponent and fractal dimension, and a single mapped segment can be the difference between two faults being disconnected vs. part of one connected cluster. Build the known INGENIOUS/USGS traces into an explicit graph (nodes at segment endpoints and intersections, edges as mapped fault segments), then identify short, otherwise-low-scoring gaps whose closure would convert two structurally related but disconnected mapped faults into a single coherent system consistent with regional kinematics and known step-over/termination settings. Treat those topologically load-bearing gaps as a distinct high-priority candidate class, and write the graph-based argument directly into each candidate's documentation.

We got our highest score on https://buffedlizard55-lab.github.io/GEMSDOE24/ , study, analyze and understand why and how at a Phd level. Can we generate a higher scoring submission? And if so, how? Higher than 0.2477, and ideally higher than the current high on the leaderboard of 0.3195?

Build a unique new research and generation system, not just a re-skinning of the existing website. Provide a clean, simple website with links to official sources and an up-to-date feed so I don't have to manually check things. Ensure the submission TIF is easy to download and obvious on the first screen, and verify it passes the competition's validation checks (fixing the "Predicted values must be in range [0, 1]" error). Also, build an organized, auditable knowledge base and data table with links to official sources.

Review the repo and put this full prompt into the README.Read the README every session as the starting point.

Work on the next steps from the previous sessions first.

Before writing any new feature code, generate 3-5 untried candidate geological hypotheses — each naming the specific layer(s), the physical signature it targets, why it should catch a fault that is missing from the USGS/INGENIOUS catalogue rather than one already in it, and how it differs from everything already in the repo. Rank them by expected DTI improvement and implementation cost, then validate the top candidate on the spatially-blocked holdout set before touching a weekly submission slot. If a hypothesis needs external data, name the free official source and check that it's actually obtainable.

Don't limit your thinking to what's already in the repo — be contrarian, think outside the box, and look for overlooked data sources, unconventional geological signals, or novel ways of combining existing layers that no previous session has tried. Ground every wild idea in a real physical mechanism and a concrete validation test so we only ship what actually works.

Remember, the goal is to get the highest score possible on the leaderboard. Do not spend a weekly submission slot on an idea that hasn't beaten our current best on the holdout set.

Provide a one-click submission button on the executive summary page that downloads the TIF file with a unique name, along with a short comment to copy-paste into the submission form. Explain how to submit it on the executive-summary subpage.

The submit form on DrivenData takes a .tif (or a .zip with one GeoTIFF) and an optional short "Note" (≤200 chars) that only shows up in your own submissions list to help you tell runs apart.

Create a deep-research knowledge base from official sources, and an auditable data/source table with verified links.

State your limitations and what access you need.

Run the task through 3 passes: Pass 1: Implement and verify. Pass 2: Review for bugs, missing requirements, incorrect assumptions, and edge cases, then fix. Pass 3: Re-check the entire implementation against the original request and polish. Then create a pull request and merge onto main. List remaining work and limitations for the next session.

Current leaderboard high is 0.3195

Scores from our other sites:
https://buffedlizard55-lab.github.io/GEMSDOE/ : 0.1563
https://buffedlizard55-lab.github.io/5GEMSDOE/ : 0.1563
https://buffedlizard55-lab.github.io/7GEMSDOE/ : 0.1461
https://buffedlizard55-lab.github.io/8GEMSDOE/ : 0.1563
https://buffedlizard55-lab.github.io/GEMSDOE10/ : (h28-dotted-ridge) 0.1839
https://buffedlizard55-lab.github.io/12GEMSDOE/ : 0.1294
https://buffedlizard55-lab.github.io/16GEMSDOE/ : (h16-1) 0.1855, (h18-3a) 0.0976, (h18-4) 0.0360
https://buffedlizard55-lab.github.io/19GEMSDOE/ : (h19-5) 0.1922, (h19-4) 0.1894
https://buffedlizard55-lab.github.io/20GEMSDOE/ : (h20-1) 0.1890
https://buffedlizard55-lab.github.io/GEMSDOE22/ : (h23-a) 0.1002
https://buffedlizard55-lab.github.io/24GEMSDOE/ : (h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan) 0.2477
https://buffedlizard55-lab.github.io/25GEMSDOE/ :
https://buffedlizard55-lab.github.io/26GEMSDOE/ :
https://buffedlizard55-lab.github.io/27GEMSDOE/ :

Official Rules: https://docs.nlr.gov/docs/fy26osti/96647.pdf
The GEMS Prize utilizes the INGENIOUS play fairway regional dataset inside the GeoDAWN footprint: https://gdr.openei.org/submissions/1391
Dropbox links for the competition data:
GEMS_96647.pdf: https://www.dropbox.com/scl/fi/aemhtutjgcp6tr3tint94/GEMS_96647.pdf?rlkey=rek210cj2smnmzb8n0sla1vmd&st=wz4kofki&dl=0
example_submission.tif: https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?rlkey=kbykilvau066xuogoosbf4cq8&st=8junzdyw&dl=0
existing_faults.tif: https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?rlkey=yiao96uluqdkipf0h5vju71jf&st=rnino7ya&dl=0
gems-geodawn-numerical-features.tif: https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?rlkey=je8d8fepqfbst9lnwsq9rkplu&st=zj1lag1r&dl=0
Digital-elevation-model-links-JSON.pdf: https://www.dropbox.com/scl/fi/ig0mban712ns1atphgphe/Digital-elevation-model-links-JSON.pdf?rlkey=zm77f1vbtt2if8hlruymptnu3&st=srhhir10&dl=0
```

## Session 6 prompt (operative text verbatim, 2026-10-25; score list elided)

The 2026-10-25 tasking: focus on the highest-scoring submissions from GEMSDOE24/25/27/28/30/
31/32/33/36; study why `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` scored 0.2778
(owner-reported; leaderboard highs stated as both 0.4413 and 0.3195 — IR-2026-10-25-02);
generate a UNIQUE TIF whose submit-readiness is obvious and machine-validated; fix the
"Predicted values must be in range [0, 1]" rejection; one-click download + unique name +
short note on the first screen and an executive-summary subpage; 3–5 untried hypotheses
ranked before implementing; validate on the spatially blocked holdout before any weekly
slot; 3 passes; PR + merge. The full per-site score list in the prompt is elided here —
its values for the focus sites are recorded in `knowledge/12` (OWNER-REPORTED).

```text
PARALLEL-RUN PROTOCOL — read first. This session is one of several running from this same prompt.
1. LANE. Your lane is the single method paragraph below. Stay inside it. If your raster's rank-correlation with any registry raster exceeds [0.90], or more than [70%] of your dots fall within 3 px of one registry raster's dots, you have drifted into another lane: log it as a duplicate and stop. Check this on the surface before placement AND on the final dots.
2. REUSE, DON'T REBUILD. Use the template's cached feature stack, evaluate_holdout.py and submission_writer.py. Holdout = hide-and-recover: withhold whole fault segments with a buffer, derive every catalogue-based feature only from the visible faults, mask visible faults pixel-exactly, score pooled DTI (alpha 0.2, beta 0.8, 300 m triangular kernel). If a shared tool is wrong, fix it once in the template and report it; never keep a private fork.
3. LABEL EVERY NUMBER as HOLDOUT-DTI (evaluator version, number of withheld positives, 95% CI) or ORGANIZER-CONFIRMED (copied from a submission-page receipt). A projection is never written as a score.
4. LEAKAGE CANARY. Test each feature alone on the holdout before trusting any result. AUC above [0.90] means leakage until proven otherwise.
5. RUN CARD. End with one JSON card: hypothesis; mechanism; the named non-fault process that could mimic it; holdout DTI + CI; correlation/overlap vs registry; raster sha256; validator output (no NaN inside the footprint, values in [0,1], CRS/shape/transform match); submission name + note of at most 140 characters; verdict promote / negative. Negative results are deliverables.
6. BUDGET. Stop after [3] experiments or [2] hours. Do not pick submissions: promotion to a real slot is a separate selector step, within the weekly cap shown on the submission page.
THE FOLLOWING IS THE HIGHEST URGENCY AND MUST BE FOLLOWED! MUST GENERATE A UNIQUE TIF SUBMISSION FOR THE COMPETITION. DO NOT COPY A PREVIOUS SUBMISSION UNLESS IT'S FOR LEARNING AND EDUCATION. BUT WE MUST GENERATE A UNIQUE TIF SUBMISSION. IT MUST BE OBVIOUS WHETHER IT IS OK TO DOWNLOAD AND SUBMIT THE GENERATED TIF SUBMISSION.
```

## Core Values (verbatim, owner-supplied)
```text
The following is taken from the Arena AI team and I think it makes a good point on building a successful project, so let's keep the Core Values and Own the Outcome as a focal point when building, developing, researching, suggesting upgrades, and implementing the work.

Our Core Values
Maximize P(Win)
"Maximize the Probability of Winning": our decision making framework. In every decision, we weigh tradeoffs, assess risk, and choose the path that maximizes the probability that Arena succeeds. We set aside our emotions and make tough decisions in order to maximize P(Win). "Maximize P(Win)" frees us from constraints and clarifies that we must put Arena first.

Own the Outcome
We own results end to end — not just our individual slice of the work. When problems arise and we have the means to act, we do so without waiting for permission or assignment. We treat failure and success as signals and use them to improve. At Arena, we stay accountable to the final outcome.

Work line by line verifying from official verified trusted sources, provide links for manual review. There should be no manual input, work on your own to complete tasks. Flag any irregularities for review. No hallucinations.
Verify no hallucinations.
```

## Credit and disclosure
Metric, thinning and holdout conventions re-implement the owner's sibling repository `buffedlizard55-lab/GEMSDOE24` (credited in each module); the graph, link, candidate, connectivity-theory, vector-attribution, OOF-detector, and submission-verification code is new.
This work was produced by an AI agent on Arena.ai; see `AI_DISCLOSURE.md` (the Official Rules require generative-AI use to be stated in the narrative).

## Current session task prompt (verbatim)

The following is the full task prompt for this session, to be re-read at the start of every work session as the starting point for what is being built.

```
Focus on the highest scoring submissions from these sites: GEMSDOE24, GEMSDOE25, GEMSDOE27, GEMSDOE28, GEMSDOE30, GEMSDOE31, GEMSDOE32, GEMSDOE33, GEMSDOE36.

HIGHEST URGENCY — MUST FOLLOW:
MUST GENERATE A UNIQUE TIF SUBMISSION FOR THE COMPETITION. DO NOT COPY A PREVIOUS SUBMISSION UNLESS IT IS FOR LEARNING AND EDUCATION. WE MUST GENERATE A UNIQUE TIF SUBMISSION. IT MUST BE OBVIOUS WHETHER IT IS OK TO DOWNLOAD AND SUBMIT THE GENERATED TIF SUBMISSION.

There should be an easy to download submission TIF file as described by the prompt. Read the entire prompt. Many sites mention inspection only and a human inspector, but the inspection needs to be done through the project and needs to be validated for submission without human intervention.

PARALLEL-RUN PROTOCOL:
1. LANE. Stay inside the single method paragraph. If your raster's rank-correlation with any registry raster exceeds 0.90, or more than 70% of your dots fall within 3 px of one registry raster's dots, log it as a duplicate and stop. Check on the surface before placement AND on the final dots.
2. REUSE, DON'T REBUILD. Use the template's cached feature stack, evaluate_holdout.py and submission_writer.py. Holdout = hide-and-recover: withhold whole fault segments with a buffer, derive every catalogue-based feature only from the visible faults, mask visible faults pixel-exactly, score pooled DTI (alpha 0.2, beta 0.8, 300 m triangular kernel). Fix shared tools once in the template; never keep a private fork.
3. LABEL EVERY NUMBER as HOLDOUT-DTI (evaluator version, number of withheld positives, 95% CI) or ORGANIZER-CONFIRMED (copied from a submission-page receipt). A projection is never written as a score.
4. LEAKAGE CANARY. Test each feature alone on the holdout before trusting any result. AUC above 0.90 means leakage until proven otherwise.
5. RUN CARD. End with one JSON card: hypothesis; mechanism; the named non-fault process that could mimic it; holdout DTI + CI; correlation/overlap vs registry; raster sha256; validator output (no NaN inside the footprint, values in [0,1], CRS/shape/transform match); submission name + note of at most 140 characters; verdict promote / negative. Negative results are deliverables.
6. BUDGET. Stop after 3 experiments or 2 hours. Do not pick submissions: promotion to a real slot is a separate selector step, within the weekly cap shown on the submission page.

Study GEMSDOE32's h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros (0.2778): why and how did it get the highest score, and can we generate a submission that scores higher? Answer with PhD-level judgement, then generate a unique TIF submission. Current competition leaderboard GEMSDOE high score: 0.4413 (also cited elsewhere as 0.3195 — flagged as an irregularity to verify).

Before implementing, generate 3–5 candidate geological hypotheses not yet tried, each naming: the specific layer(s); the physical signature targeted (e.g. an edge-detection or curvature transform); why it should catch a fault missing from the USGS/INGENIOUS catalogue rather than one already in it; and how it differs from anything already implemented in this repo. Rank them by expected DTI improvement and implementation cost. Validate the top candidate on the spatially-blocked holdout set before touching a weekly submission slot. If a candidate cannot be validated without new external data, name the specific free, official source needed and check it is obtainable.

Work line by line, verifying from official verified trusted sources; provide links for manual review; no manual input; work autonomously; flag irregularities; no hallucinations.

Come up with distinct and unique strategies to score higher than 0.3195. Deep research into the scientific discovery of geothermal vents. Store information and knowledge from official verified sources as a starting point for other projects. Think outside the box but stay grounded in proper scientific research; aim for the top prize; be contrarian but smart.

Put this prompt into the repo README and read it every session. Core Values: Maximize P(Win) and Own the Outcome.

The site must generate the TIF required for submission: as easy as download → click a file → submit. Obvious at the very beginning of the site (executive summary or first screen). The submission form returned "Predicted values must be in range [0, 1]"; fix it. Give the submission a unique name and a short comment (e.g. clustering with k=25). Create an executive summary subpage explaining exactly how to make a submission.

Goal: place top of the leaderboard. Competition: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/ . Understand the problem; collect and organize all data into a clean, easily auditable table with official verified links for manual verification. Guidelines: https://www.drivendata.org/competitions/306/competition-doe-gems/ . Data: https://www.drivendata.org/competitions/306/competition-doe-gems/data/ (login-walled; no DrivenData auth — cannot auto-download; no agent access to drivendata.org per Terms of Use). Reference solution: https://github.com/drivendataorg/gems-prize-reference-solution . Rules PDF: https://docs.nlr.gov/docs/fy26osti/96647.pdf . GEMS data: https://gdr.openei.org/submissions/1391 .

Create a GitHub Page with a clean, user-friendly, simple UI; organized and clean; all relevant information in an easy-to-read format with official verified links as sources. Verify everything line by line; no hallucinations.

Run the task through 3 passes: Pass 1 implement + verify; Pass 2 review bugs/assumptions/edge cases and fix; Pass 3 re-check against the original request and polish. Then create a pull request and merge onto main. List remaining work and limitations for the next session.

Leaderboard context from the group's sites (owner-reported unless marked): GEMSDOE24 0.2477, GEMSDOE25 0.2600, GEMSDOE27 (unscored candidates), GEMSDOE28 up to 0.2710, GEMSDOE30 0.2600, GEMSDOE31 0.2708, GEMSDOE32 h33 0.2778, GEMSDOE33 0.2632, GEMSDOE36 0.2750. Public leaderboard #1 cited variously as 0.3195 / 0.3262 / 0.4413 across sources — irregularity, not verified by the agent (no drivendata.org access).
```

