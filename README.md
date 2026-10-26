# GEMSDOE36 — current decision & reproducible research

**Working branch:** `arena/20b1a132-gemsdoe36`. **Read this first** before starting work: the decision below is the current branch decision, alongside archived GVSC-36/HVG-36/MTO-36/WDP-36/MOE36/ATVR/CTRB/GPS/Lane36 research lanes. Core values: **Maximize P(Win)** and **Own the Outcome**. The [full standing owner brief](#full-standing-owner-brief-historical-wording) is preserved verbatim below; its historical leaderboard claims are not verified observations. Latest pass-by-pass repository reviews: [HVG-36](evidence/hvg36_review_passes_20261026.md), [GVSC-36](evidence/gvsc36_review_passes_20261026.md), and [nine-site uniqueness audit](docs/research/repo-review-20261026.md).

<!-- STATUS:START -->
> ## CURRENT DECISION · `DOWNLOAD: YES (research)` · `DO NOT SUBMIT` · `verdict: negative`
>
> **Latest original HVG-36 file (New GEMSDOE36 Holdout Record `0.135759`):** [`gemsdoe36-hvg36-vent-dipole-20261026-b3ee97873192-zeros.tif`](docs/downloads/gemsdoe36-hvg36-vent-dipole-20261026-b3ee97873192-zeros.tif) · [one-TIFF ZIP](docs/downloads/gemsdoe36-hvg36-vent-dipole-20261026-b3ee97873192-zeros.zip) · [validator/run card](evidence/hvg36_run_card_20261026.json) · [monograph](docs/research/hvg36-20261026.md) · [preregistration](docs/research/preregistration-hvg36-20261026.md). **Not competition-authorized (`verdict: negative`).**
> - Name: `gemsdoe36-hvg36-vent-dipole-20261026-b3ee97873192`. Note (106 / 140 characters): `HVG-36 EXP-1 vent-conduit + dipole OOF ensemble | HOLDOUT-DTI 0.1358 vs B0 0.1332 | NEGATIVE do not submit`.
> - SHA-256: `85d56b03aff18f72d85de9c1e1ca02a2274263fffcd95aa0a6edac7bc9a08596` (ZIP SHA-256: `2809617a47d4985311447ffa6c5b76dd7885fd6be887c197de8183d09a53ca61`). Template, single band, CRS/shape/transform, all-grid finite `[0,1]` **PASS locally** (`37,654` dots, `0` on `existing_faults.tif`).
> - **HOLDOUT-DTI (HVG-36 EXP-1):** **`0.135759`** (95% CI `[0.123271, 0.148461]`; `gems-segment-pooled-v1`, `60,988` withheld positives; 1.5 km buffer; `NW=0.14972`, `NE_LidarGapHeavy=0.17477`, `SW=0.08927`, `SE=0.15112`). Beats matched `B0_base59` (`0.133169`, delta `+0.002590`, wins **3/4 folds**) and recorded `H36-GPS B0` (`0.133749`, delta `+0.002010`), setting the **highest HOLDOUT-DTI in GEMSDOE36** (`EXP-2 = 0.133383`, `EXP-3 = 0.133757`). However, paired 95% CI vs `B0` (`[-0.003311, +0.008388]`) crosses zero and pooled DTI remains below the recorded group best `0.14876` **HOLDOUT-DTI** (`GEMSDOE24` `H24-GVC1`).
> - **Uniqueness & Canary (HVG-36):** All 14 HVG-36 features PASS leakage canary (`max two-polarity AUC = 0.6440 <= 0.90`). Pre-placement surface `max |rho| = 0.5713 <= 0.90` PASS. Final dots: **`35.35%`** vs `GEMSDOE32 B2` champion and **`44.48%`** max across all 9 focus-site top champions (**100% unique vs all 9 focus-site champions**), `72.01%` vs `gems28-h37-1-probe-union-pool-r1`, `88.37%` vs dense blankets, and `100.00%` vs 5-px calibration lattice (**FAIL literal all-203 gate**).
>
> **Original MTO-36 file:** [`gemsdoe36-mto36-ortho-contact-20261026-c41282e9da7a-zeros.tif`](docs/downloads/gemsdoe36-mto36-ortho-contact-20261026-c41282e9da7a-zeros.tif) · [one-TIFF ZIP](docs/downloads/gemsdoe36-mto36-ortho-contact-20261026-c41282e9da7a-zeros.zip) · [validator/run card](evidence/mto36_run_card_20261026.json). **Not competition-authorized.**
> - Name: `gemsdoe36-mto36-ortho-contact-20261026-c41282e9da7a-zeros`. Note (98 / 140 characters): `GEMSDOE36 MTO-36 contact-crosscut | HOLDOUT-DTI 0.0676 | NEGATIVE; research only | id c41282e9da7a`. SHA-256: `3e6594fe39facbffd433dc4500a7e8766fab2dd0d5089d2f591ed47713261607`.
> - **HOLDOUT-DTI (MTO-36):** `0.067611` (95% CI `[0.058449, 0.077867]`; `gems-segment-pooled-v1`, `60,988` withheld positives; 1.5 km buffer). Matched control `0.066923`; paired CI `[-0.003002, 0.004433]` crosses zero.
> - **Archived prior negative lanes:** [`gemsdoe36-wdp36-exp1-20261026-zeros.tif`](docs/downloads/gemsdoe36-wdp36-exp1-20261026-zeros.tif) (`0.093269` **HOLDOUT-DTI**), [`gemsdoe36-moe36-exp1-20261026-zeros.tif`](docs/downloads/gemsdoe36-moe36-exp1-20261026-zeros.tif) (`0.128246` **HOLDOUT-DTI**), [`gemsdoe36-atvr36-20261026.tif`](docs/downloads/gemsdoe36-atvr36-20261026.tif) (`0.129224` **HOLDOUT-DTI**), [`gemsdoe36-h36-ctrb-submod-36800-20261025T000000Z-a1d85443-zeros.tif`](docs/downloads/gemsdoe36-h36-ctrb-submod-36800-20261025T000000Z-a1d85443-zeros.tif) (`0.131910` **HOLDOUT-DTI**), and [`gemsdoe36-h36-gps-graben-pair-20261026-bb29ce2a4bb4-zeros.tif`](docs/downloads/gemsdoe36-h36-gps-graben-pair-20261026-bb29ce2a4bb4-zeros.tif) (`0.133011` **HOLDOUT-DTI**).
> - **Historical scores:** Nine focus-site TIFFs (`0.2449`–`0.2778`) were re-audited by byte hash and XOR algebra ([ledger](evidence/focus_sites_9repo_summary_20261026.json)); because no portal screenshot/HTML receipt is archived, they are labeled **OWNER-REPORTED**, not `ORGANIZER-CONFIRMED`.
<!-- STATUS:END -->

## Additional completed lane — GVSC-36 (research-only; negative)

The [GVSC-36 research TIFF](docs/downloads/gemsdoe36-gvsc36-exp3-20261026-5fb822bdfb60-zeros.tif) and [single-TIFF ZIP](docs/downloads/gemsdoe36-gvsc36-exp3-20261026-5fb822bdfb60-zeros.zip) are available for audit, **not upload**. Its **HOLDOUT-DTI** is `0.158855` (95% CI `[0.145456, 0.173084]`; `gems-segment-pooled-v1`, `60,988` withheld positives), but its 3 px dot overlap is `94.60%` vs GEMSDOE22 H23-B and `99.62%` maximum literal overlap across 206 comparators. Local format/range validation passes; the strict novelty and protocol audit fails. It was not submitted; there is no leaderboard estimate. See the [full report](docs/research/gvsc36-20261026.md), [run card](evidence/gvsc36_run_card_20261026.json) and [protocol caveats](docs/research/known_irregularities.md#gvsc-36-review-flags-2026-10-26-latest-lane-negative).

## Nine-site executive summary (pinned bytes, unverified scores)

Exactly nine owner-specified repositories were reviewed. Each linked TIFF below was retrieved from a pinned GitHub snapshot; its **full SHA-256, exact filename, shape and on-footprint dot count** were checked against cached bytes by [`scripts/audit_focus_sources.py`](scripts/audit_focus_sources.py), with the [machine-readable receipt](evidence/mto36_ninesite_forensics.json) and [historical ledger](evidence/focus_sites_9repo_summary_20261026.json). The reported scores are **OWNER-REPORTED, not `ORGANIZER-CONFIRMED`**: no original submission-page receipts are archived. A pinned raster link cannot prove what was actually uploaded. None of these old files is a new approved candidate.

<!-- FOCUS9_TABLE:START -->
| Site | Highest Historical File (Pinned Download Link & SHA-12) | Dots | Historical Live Score (Label) | Estimated Score: `HOLDOUT-DTI` (`gems-segment-pooled-v1`, 60,988 withheld px, 95% CI) | Unique vs Other 8 Focus Sites & Registry? | OK to Submit Now? |
|---|---|---:|---|---|---|---|
| `GEMSDOE24` | [`gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif`](https://github.com/buffedlizard55-lab/GEMSDOE24/blob/fc2bc6f350bf5c6ce8da5d7a2ab03578ea1259d1/docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif) (`68d0e2e4fcc5`) | `60,069` | **`0.2477` OWNER-REPORTED** | H24-GVC1 (abe8e51c): HOLDOUT-DTI 0.14876 (95% CI [0.13413, 0.16370], gems-segment-pooled-v1, 60,988 withheld px; Highest Recorded Holdout across 9 repos) -> 0.0859 OWNER-REPORTED live *(Hist. in-sample diag: `0.171825`)* | Historical H25-1: NO (97.95% Jaccard with GEMSDOE27). Recent GVC1: NO (76.82% 3-px overlap vs 10GEMSDOE). | **NO** (historical family / negative) |
| `GEMSDOE25` | [`gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif`](https://github.com/buffedlizard55-lab/GEMSDOE25/blob/e40b9b5e3871cb34d138f586bde97f5099658d01/docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif) (`91eae1ca42ec`) | `44,090` | **`0.2600` OWNER-REPORTED** | Recent H66 (da617550): 0.0742 OWNER-REPORTED live (no SegmentHoldout card published) *(Hist. in-sample diag: `0.161630`)* | NO — 0-XOR pixel-identical in footprint to GEMSDOE30 & superset of GEMSDOE31/32. | **NO** (historical family / negative) |
| `GEMSDOE27` | [`gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif`](https://github.com/buffedlizard55-lab/GEMSDOE27/blob/927322eadbde56be42ae129ccdfb9b37540d8e60/docs/downloads/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif) (`33003374335d`) | `61,328` | **`0.2449` OWNER-REPORTED** | H29-S (51189874): HOLDOUT-DTI 0.0566 (5-km block OOF, 95% CI [0.0507, 0.0626]) -> 0.2190 OWNER-REPORTED live *(Hist. in-sample diag: `0.172636`)* | Historical T-v2: NO (97.95% Jaccard with GEMSDOE24). Recent H29-S: YES vs 9 focus sites (max 3-px = 38.2%), FAIL vs dense blankets. | **NO** (historical family / negative) |
| `GEMSDOE28` | [`gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif`](https://github.com/buffedlizard55-lab/GEMSDOE28/blob/e6321461066f89080e3b1bb670d3951ab20d3638/docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif) (`5556aa1438fd`) | `37,660` | **`0.2710` OWNER-REPORTED** | No clean non-leaking SegmentHoldout card (D2.8/B2 derivative) *(Hist. in-sample diag: `0.046180`)* | NO — >93% 3-px dot overlap with GEMSDOE25/30/31/32/33/36. | **NO** (historical family / negative) |
| `GEMSDOE30` | [`gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif`](https://github.com/buffedlizard55-lab/GEMSDOE30/blob/760af3005dd40b9f36d8fef97d6dc384fd9f2a2f/docs/downloads/gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif) (`8cf893ead566`) | `44,090` | **`0.2600` OWNER-REPORTED** | Recent H30-2c: 0.0695 OWNER-REPORTED live (no SegmentHoldout card) *(Hist. in-sample diag: `0.161630`)* | NO — 0-XOR pixel-identical in footprint to GEMSDOE25 (91eae1ca42ec). | **NO** (historical family / negative) |
| `GEMSDOE31` | [`gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif`](https://github.com/buffedlizard55-lab/GEMSDOE31/blob/597b04cd1afb65d1ebbe3e9417fd952be48e3d74/docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif) (`07b6db440535`) | `40,199` | **`0.2708` OWNER-REPORTED** | Recent H27-5: 0.0725 OWNER-REPORTED live *(Hist. in-sample diag: `0.049061`)* | NO — exact 0-XOR subset D2.8 & (d_cat > 1 px) (100% inside GEMSDOE25/30). | **NO** (historical family / negative) |
| `GEMSDOE32` | [`gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif`](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/5fc7792c5887735ecd3aa9a612787da588a7bf2c/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif) (`c55bafc47005`) | `37,654` | **`0.2778` OWNER-REPORTED** | Recent H32-R11: 0.0537 OWNER-REPORTED live; Champion B2 in-sample diag = 0.006708 because d_cat > 2 px moat zeroes known-fault TP while stripping 6,436 collar FPs on the blind test set *(Hist. in-sample diag: `0.006708`)* | NO — exact 0-XOR subset D2.8 & (d_cat > 2 px) (100% inside GEMSDOE25/30/31; 96.91% inside GEMSDOE36 PINN). | **NO** (historical family / negative) |
| `GEMSDOE33` | [`GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif`](https://github.com/buffedlizard55-lab/GEMSDOE33/blob/f618cc54773bd9b4d6c2b3ebf78103a05cc10cb6/docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif) (`87f857d505e2`) | `41,865` | **`0.2632` OWNER-REPORTED** | No clean non-leaking SegmentHoldout card (D2.8/B2 derivative) *(Hist. in-sample diag: `0.086408`)* | NO — >90% 3-px dot overlap with GEMSDOE25/28/30/31/32/36. | **NO** (historical family / negative) |
| `GEMSDOE36` | [`gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif`](https://github.com/buffedlizard55-lab/GEMSDOE36/blob/c5a8ae7da3bd2fcff5aa5855afd44c7a3346c16f/docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif) (`e15891020b9c`) | `38,854` | **`0.2750` OWNER-REPORTED** | Latest HVG-36 EXP-1 (b3ee97873192): HOLDOUT-DTI 0.135759 (95% CI [0.123271, 0.148461], gems-segment-pooled-v1, 60,988 withheld px; New GEMSDOE36 Holdout Record, beats B0 0.133169 on 3/4 folds; MTO-36 = 0.067611, WDP-36 = 0.093269, MOE36 = 0.128246, ATVR-36 = 0.129224, H36-CTRB = 0.131910, H36-GPS = 0.133011) *(Hist. in-sample diag: `0.011051`)* | Legacy PINN: NO (96.91% overlap with B2). Latest HVG-36 EXP-1: YES vs all 9 focus-site top champions (max 3-px = 44.48%, 35.35% vs GEMSDOE32 B2; surface max |rho| = 0.5713 PASS), FAIL literal all-203 check (72.01% vs gems28-h37-1-probe-union-pool-r1, 88.37% vs GEMSDOE67 blanket, 100.00% vs 13GEMSDOE 5-px lattice). | **NO** (historical family / negative) |
<!-- FOCUS9_TABLE:END -->

**What GEMSDOE32's reported 0.2778 means—and does not mean.** Measured in the archived masks: GEMSDOE25 D2.8 and GEMSDOE30 D2.8 have zero in-footprint XOR; GEMSDOE31 solo equals D2.8 after deleting **3,891** predictions within 1 px of existing faults, and GEMSDOE32 B2 equals D2.8 after deleting **6,436** within 2 px. Both identities have **zero XOR**. The B2 README's **2,545** is the *additional* solo→B2 pruning (3,891+2,545=6,436), not a rival D2.8→B2 count. If the owner-reported progression 0.2600→0.2708→0.2778 accurately reflects those uploaded bytes, suppressing predicted old-fault halos plausibly lowers false-positive penalty while preserving off-catalogue recall. **The hidden test labels and organizer score receipts are unavailable; this is a conditional explanation, not a causal proof.** The legacy GEMSDOE36 raster is B2 +1,200 extra dots (reported 0.2750), so it is not a new winner. A genuinely independent geology signal might beat B2, but MTO-36 did **not** establish that. [Detailed review, four preregistered hypotheses, experiment, irregularities and source links](docs/research/mto36-evidence-and-nine-sites.md).

The owner's suggested public high-water marks **0.3195 and 0.4413** conflict and are undated; neither is a verified current leaderboard value. [Consult the DrivenData leaderboard directly](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/). No holdout DTI is a leaderboard projection.

## This session's method & automatic decision

**Latest Session Lane — HVG-36 (`arena/d98aabea-gemsdoe36`, New GEMSDOE36 Holdout Record `0.135759`, `verdict: negative`).** Executing the #1 next steps from prior sessions (`MTO-36` untested hypotheses `P-TMI`, `D-PAIR`, `RAD-ANISO` + `WDP-36` §5.3 & `ATVR-36` §4 cross-expert synthesis + geothermal-vent conduit physics), four candidate geological hypotheses were ranked **before any experiment** in [`docs/research/preregistration-hvg36-20261026.md`](docs/research/preregistration-hvg36-20261026.md) and [`evidence/hvg36_preregistration_20261026.json`](evidence/hvg36_preregistration_20261026.json):
1. **`HVG-36-A`** (*Anisotropic Hydrothermal-Vent & Upflow Structural-Conduit + Slope-Deconfounded Radiometric Metasomatism `RAD-ANISO`*; OpenEI GDR 1391 Quaternary volcanic vents + multi-geothermometer excess projected along potential-field strike minus normal; lateral gradient edge $\|\nabla r_{\text{cond}}\|$ of fold-regressed playa-deconfounded `17_cond_surf` clay-cap residual; directional strike-minus-isotropic `K/Th` and `U/Th` line integral; mimic: evaporite playa margins / lacustrine shorelines);
2. **`HVG-36-B`** (*Cross-Scale RTP-to-150m Magnetic Phase Persistence `P-TMI` & Paired Signed Basement-Flexure Dipole `D-PAIR`*; `02_rtp` to GeoDAWN `TMI_up150` phase alignment + Verduzco magnetic/gravity tilt + across-strike paired opposing signed curvature shoulders in `15_depth_to_base_surf` and `13_iso_grav_anom` at 300–600 m offset + relief-deconfounded piedmont scarp-toe curvature + Walker Lane seismic-strain corridor; mimic: differential sediment compaction over unfaulted buried paleotopographic highs);
3. **`HVG-36-C`** (*LiDAR-Regime Tail-Calibrated Probability Fusion of Multi-Sensor `E_BASE59` and 100% LiDAR-Free Subsurface-Geothermal `E_HVG_SUBSURF` Out-of-Fold Experts*; mimic: multi-sensor topographic co-variation on erosional range fronts);
4. **`HVG-36-D`** (*Deferred External-Data Route: Raw USGS GeoDAWN 1D Flight-Line Crossover Profiles [`doi:10.5066/P93LGLVQ`] & NASA OPERA Sentinel-1 InSAR Velocity Steps*; documented with official public-domain sources; deferred due to sandbox outbound network allowlist).

All **14 HVG-36 features** (`12` static + `2` fold-regressed residuals; `dist_known_fault_px` strictly banned and stripped on load) **passed the single-feature leakage canary** (`max two-polarity ROC-AUC = 0.6440 <= 0.90`, [`evidence/hvg36_leakage_canary_20261026.json`](evidence/hvg36_leakage_canary_20261026.json)). Three preregistered experiments (`EXP-1`, `EXP-2`, `EXP-3`) were evaluated against the matched 59-feature `B0` control on `gems.holdout.SegmentHoldout` (`gems-segment-pooled-v1`, 1,500 m buffer, `3,199` whole components, `60,988` withheld positives, [`evidence/hvg36_holdout_experiments_20261026.json`](evidence/hvg36_holdout_experiments_20261026.json)):
- **`EXP-1` (`HVG-Single-73`, Winner):** **`HOLDOUT-DTI = 0.135759`** (`95% CI [0.123271, 0.148461]`; `NW = 0.14972`, `NE_LidarGapHeavy = 0.17477`, `SW = 0.08927`, `SE = 0.15112`), beating matched `B0_base59` (`0.133169`, `delta = +0.002590`, winning **3/4 folds**: `NW`, `NE_LidarGapHeavy`, `SW`) and recorded `H36-GPS B0` (`0.133749`, `delta = +0.002010`) — **the highest `HOLDOUT-DTI` achieved by any lane in `GEMSDOE36`**.
- **`EXP-2` (`HVG-DualExpert-ProbFuse`):** `HOLDOUT-DTI = 0.133383` (`95% CI [0.121782, 0.145328]`, `NW = 0.15253`, `NE_LidarGapHeavy = 0.17360`, `delta = +0.000214` vs `B0`).
- **`EXP-3` (`HVG-TriExpert-B2-Collar`):** `HOLDOUT-DTI = 0.133757` (`95% CI [0.122248, 0.145445]`, `NW = 0.15210`, `NE_LidarGapHeavy = 0.17432`, `delta = +0.000588` vs `B0`).
- **Fail-Closed Gate Decision (`verdict = "negative"` — `DOWNLOAD: YES (research) · DO NOT SUBMIT`):** Although `HVG-36 EXP-1` (`0.135759`) set a new `GEMSDOE36` holdout record, its paired 95% CI vs `B0` (`[-0.003311, +0.008388]`) includes zero (`G1` fail), its pooled DTI remains below the recorded group best `0.14876` (`G2` fail), and while its pre-placement surface (`max |rho| = 0.5713 <= 0.90`) and final dots vs **all 9 focus-site top champions** (`max 3-px overlap = 44.48% <= 70%`, `35.35%` vs `GEMSDOE32 B2`) pass, it trips the literal 70% 3-px dot-overlap cap against dense union-pool/blanket rasters in the 203-raster registry (`72.01%` on `gems28-h37-1-probe-union-pool-r1`, `88.37%` on `GEMSDOE67 ovtr-ml-cover`, `100.00%` on `13GEMSDOE` 5-px calibration lattice). The verified whole-array `[0, 1]` GeoTIFF [`docs/downloads/gemsdoe36-hvg36-vent-dipole-20261026-b3ee97873192-zeros.tif`](docs/downloads/gemsdoe36-hvg36-vent-dipole-20261026-b3ee97873192-zeros.tif) (`85d56b03aff1...`), [ZIP](docs/downloads/gemsdoe36-hvg36-vent-dipole-20261026-b3ee97873192-zeros.zip), [run card](evidence/hvg36_run_card_20261026.json), and [monograph](docs/research/hvg36-20261026.md) are archived for research download only — **do not submit to DrivenData**.

**Prior lane MTO-36 (`arena/cee70ea1-gemsdoe36`, also negative).** Four geological hypotheses were ranked **before any experiment** in [`knowledge/mtop36_preregistration_2026-10-26.md`](knowledge/mtop36_preregistration_2026-10-26.md): (1) magnetic-contact termination × orthogonal gravity crossing (**MTO-36; tested once, negative; intrusive contact junction as mimic**); (2) RTP/TMI upward-continuation phase persistence (pluton/flight-line mimic, tested in HVG-36 above); (3) paired signed basement-offset shoulders (sediment compaction mimic, tested in HVG-36 above); and (4) slope-deconfounded directional K/Th/U anomaly (soil/playa mimic, tested in HVG-36 above). No unrelated lane was tuned to the registry after seeing a failure.

E1 reused the prepared owner-mirror band cache, `gems.holdout.SegmentHoldout`, `gems.submission.write_submission` and `gems.novelty.compare_registry` rather than private evaluator or writer forks. Whole fault components were hidden with a 1,500 m buffer, catalogue-derived features were visible-only (MTO uses none), visible faults were masked pixel-exactly, and pooled DTI used α=0.2, β=0.8, 300 m triangular kernel. **Nine single-feature AUC canaries passed** (maximum two-polarity AUC 0.5878). One E1 candidate/control experiment ran in 249.3 s (limit 3 experiments / 2 h); no more in this lane. The candidate's **HOLDOUT-DTI** 0.067611 [0.058449, 0.077867] (`gems-segment-pooled-v1`, 60,988 withheld positives) failed to significantly beat its paired control 0.066923 (paired 95% CI −0.003002 to +0.004433) or prior recorded group-best **HOLDOUT-DTI** 0.14876. Surface rank screening passed; after placing dots, 3-px directed overlap reached 100% against a five-pixel calibration lattice and >70% against four more registry rasters. Comparisons restricted to the nine focus repositories would miss this. **Literal duplicate-stop: negative; file is research-only.** A download does not authorize spending a weekly slot.

**Merged parallel lane WDP-36 (PR #19, `arena/b8f55e32-gemsdoe36`, also negative).** Preregistered ([`evidence/wdp36_preregistration_20261026.json`](evidence/wdp36_preregistration_20261026.json)) unsupervised 0–800 m upward-continuation worm persistence (TMI+gravity; EXP-2 strain, EXP-3 seismic add-ons). Winner EXP-1 **HOLDOUT-DTI** 0.093269 [0.083380, 0.103501] (`gems-segment-pooled-v1`, 60,988 withheld) vs single-scale 0.091901 (paired CI includes zero; strain hurt). Canary PASS (0.6145); focus-9 overlap max 0.4909; literal gate fails on one 54.8%-coverage blanket (0.7227); post-merge overlaps MOE36 0.289 / MTO-36 0.472 ([`evidence/wdp36_postmerge_overlap_20261026.json`](evidence/wdp36_postmerge_overlap_20261026.json)). Zeros-only GeoTIFF `gemsdoe36-wdp36-exp1-20261026-zeros.tif` (`ae9da29e45c6...`) is a research download — **DO NOT SUBMIT**. Note: historical live numbers in WDP-36 documents written as organizer-confirmed must be read as **OWNER-REPORTED** per the MTO-36 correction above (no receipts archived). Monograph: [`docs/research/wdp36-20261026.md`](docs/research/wdp36-20261026.md). Reproduce detector checks with `python scripts/run_wdp36.py --reuse-cache` only on a data-restored checkout; do not submit the file.

## Checks and links for reviewers

```bash
python scripts/restore_data.py --group core    # if pinned owner-mirror data are absent
python scripts/fetch_registry_rasters.py        # if registry refs are absent
python scripts/audit_focus_sources.py           # rehash nine TIFFs; recheck mask algebra
python scripts/build_site.py                    # safe updater: MTO card + focused Pages
python scripts/check_site.py                    # landing/links & fail-closed status
python scripts/verify_mto_release.py            # verify current negative research artifact
python scripts/verify_release_gate.py           # legacy CTRB negative gate
pytest -q
ruff check src scripts tests
```

Run the *checks* only; **do not rerun `scripts/run_mto_contact.py` or submit the negative file**. The original TIFF and ZIP are in [`docs/downloads/`](docs/downloads/); [latest site](docs/index.html), [executive submission guide](docs/executive-summary.html), [machine-readable status](docs/current-run.json), [run card](evidence/mto36_run_card_20261026.json), [irregularities](docs/research/mto36-evidence-and-nine-sites.md#irregularities-and-inference-boundaries), [three review passes](evidence/mto36_review_passes_20261026.md), [AI disclosure](docs/AI_DISCLOSURE.md). Format validation is local; the organizer may apply other checks. Historical competition/USGS inputs are SHA-pinned **owner mirrors**, not independently authenticated downloads from the authority.

**Official/manual-review source leads:** [DrivenData competition](https://www.drivendata.org/competitions/306/competition-doe-gems/), [problem and metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [data/format](https://www.drivendata.org/competitions/306/competition-doe-gems/data/), [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/), [DOE/NLR rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf), [official reference solution (GitHub)](https://github.com/drivendataorg/gems-prize-reference-solution), [USGS GeoDAWN DOI](https://doi.org/10.5066/P93LGLVQ). Only GitHub and owner mirrors were accessed here; external competition and USGS pages are *not* represented as fetched/verified in this session.

**Next decision:** Archive the negative result; leave the weekly live slot unused. A *different*, preregistered, independently sourced signal would need its own whole-segment test, paired improvement, strict **all-registry** uniqueness and format gate, *then* an independent slot selector. Never adjust this candidate to fill holes in the comparator lattice. To verify any historical score, archive an organizer submission-page receipt pairing that score with the uploaded file. The public source-activity feed is for repository commit freshness, **not score monitoring**.

---

## Full standing owner brief (historical wording)

<details>
<summary>Show full user brief saved 2026-10-25; historical score claims are unverified</summary>

The text below is preserved as supplied context (link markup normalized; Arena branch wrapper omitted). It is **not** an independent validation of the listed scores, live standings or source authenticity. Current negative verdict and stricter gate above take precedence when this historical text is ambiguous.

# Owner brief — 2026-10-25

The following preserves the current user brief (link markup normalized; the Arena branch-status wrapper is omitted). Read this and the latest README decision at the beginning of every session. Historical claims inside are requirements/context, not independently verified scores. This current brief supersedes historical requests to submit copied/thinned reference rasters or to seek a human inspection exception.

---

Review the repo.

I want to focus on the highest scoring submissions from the following sites, GEMSDOE24, GEMSDOE25, GEMSDOE27, GEMSDOE28, GEMSDOE30, GEMSDOE31, GEMSDOE32, GEMSDOE33, GEMSDOE36. I want an executive summary on every site that is clear and obvious which is the best submission to submit to obtain a high score on the leaderboard. It should also be unique and not an exact duplicate of any previous submission that is the same as below.

We should be able to estimate the score for a submission. I want a table in the executive summary that clearly lists what file to download, what the estimate score is, and whether it is a unique submission unlike any of the other GEMDOE sites listed below.

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
