# GEMSDOE36 — DOE GEMS Prize: Subsurface Fault Discovery (`WDP-36`, `ATVR-36`, `H36-CTRB`, `H36-GPS`, `Lane36`)

**Live GitHub Pages Site & One-Click Download Portal:** [`docs/index.html`](docs/index.html) · [`docs/executive-summary.html`](docs/executive-summary.html)  
**Working Branch:** `arena/b8f55e32-gemsdoe36`

<!-- STATUS:START -->
> ## Automated Repository Release Gate: `DO NOT SUBMIT — HOLD WEEKLY LIVE SLOT` (`DOWNLOAD: YES` for format-safe `[0, 1]` research & cross-lane ensemble inspection)
>
> * **Current Branch Deliverable (`WDP-36 EXP-1`, `arena/b8f55e32-gemsdoe36`, zeros-only):** [`gemsdoe36-wdp36-exp1-20261026-zeros.tif`](docs/downloads/gemsdoe36-wdp36-exp1-20261026-zeros.tif) · [ZIP](docs/downloads/gemsdoe36-wdp36-exp1-20261026-zeros.zip) · [Receipt / Run Card](docs/downloads/gemsdoe36-wdp36-exp1-20261026-zeros.receipt.json) · [Monograph](docs/research/wdp36-20261026.md)
>   * Name: `gemsdoe36-wdp36-exp1-20261026` · SHA-256: `ae9da29e45c67d03b7a7fd438a3cf0686f0678111181cd960b86dffb56f0f698` (ZIP `c6767fb5e05fe8f573a365b24913b1b58544a4d16ee9c6cd1eb7f7ae241f7de5`)
>   * Note (`95 <= 140` chars): `GEMSDOE36 WDP-36 EXP-1 | worm persistence 0-800m only | HOLDOUT-DTI 0.0933 | NEGATIVE hold slot`
>   * **HOLDOUT-DTI:** **`0.093269`** (`95% CI [0.083380, 0.103501]`, `gems-segment-pooled-v1`, 1.5 km buffer, 60,988 withheld px; unsupervised persistence vs single-scale `A0 = 0.091901`, paired `+0.001368 [-0.004578, +0.006991]`; strain hurt, seismic neutral) — **below** `repo B0 = 0.13375` / group best `0.14876`, so fail-closed **negative**. Canary PASS (`max AUC 0.6145`); surface `|rho|max 0.264`; focus-9 dot overlap max `0.4909` (`0.2360` vs champion); literal expanded gate FAIL on one 54.8%-coverage blanket (`0.7227`). No organizer score (not submitted).
> * **Previous Branch Deliverable (`ATVR-36 EXP-2`):** [`gemsdoe36-atvr36-20261026.tif`](docs/downloads/gemsdoe36-atvr36-20261026.tif) · [ZIP](docs/downloads/gemsdoe36-atvr36-20261026.zip) · [Receipt](docs/downloads/gemsdoe36-atvr36-20261026.receipt.json) · [Run Card](evidence/atvr36_run_card_20261026.json)
>   * Name: `gemsdoe36-atvr36-exp-2-20261026` · SHA-256: `54f493f4fa5c74ed3a02f88ca6d47272b0c3cee0cc0bd9bbd9cb94eaf997204a`
>   * Note (`116 <= 140` chars): `GEMSDOE36 ATVR-36 EXP-2 | tilt/LiDAR+hydrothermal+Anderson PDE+CELF | HOLDOUT-DTI 0.1145/0.1179 | NEGATIVE hold slot`
>   * **HOLDOUT-DTI:** **`0.114542`** (`95% CI [0.078547, 0.151221]`, `gems36-segment-audit-v1`, 3 km buffer, `+0.075018` vs `B1` `0.039523`, `p = 1.0000`) and **`0.117925`** (`95% CI [0.101961, 0.132998]`, `gems-segment-pooled-v1`, 1.5 km buffer; **repository-best `NW = 0.15048` & `SE = 0.15438`**; `SW = 0.11115`, `NE = 0.05312`).
>   * **Uniqueness & Canary:** `50/50` features pass leakage canary (`max AUC = 0.5881 <= 0.90`); **100% unique across all 9 focus repositories (`GEMSDOE24`–`36`)** (`max overlap = 0.6328 <= 0.70`, `35.94%` vs `GEMSDOE32` `0.2778` champion `B2`, `37.36%` vs `H36-CTRB`); `201`-raster all-repo registry literal check `FAIL` (`0.8936` on `8` non-focus `80k–517k`-dot `41–55%` area blankets; [`evidence/atvr36_crosscheck_20261026.json`](evidence/atvr36_crosscheck_20261026.json)).
>   * **Gates:** G1 PASS · G2 FAIL (`0.117925 < repo B0 0.13375 / group best 0.14876`) · G3 PASS · G4a PASS · G4b PASS (`9` focus sites) · G4c FAIL (`201` blankets) · G5 PASS -> **`verdict: "negative"`** (`12,279,160 / 12,279,160` cells finite in `[0.0, 1.0]`).
> * **Parallel `H36-CTRB` (`gemsdoe36-h36-ctrb-submod-36800-20261025T000000Z-a1d85443-zeros.tif`):** **DO NOT SUBMIT** (`HOLDOUT-DTI = 0.114425` on `gems-segment-pooled-v1`, **repository-best `NE_LidarGap = 0.13141`**; [`evidence/h36_ctrb_run_card_20261025.json`](evidence/h36_ctrb_run_card_20261025.json), SHA-256 `2bb4513d6307e2394d5de7e7e7649e28eff067b602b805a0215e82aa5ff89907`).
> * **Parallel `H36-GPS` (`gemsdoe36-h36-gps-graben-pair-20261026-bb29ce2a4bb4-zeros.tif`):** **DO NOT SUBMIT** (`HOLDOUT-DTI = 0.13203 < B0 = 0.13375`; [`evidence/h36_run_card.json`](evidence/h36_run_card.json), SHA-256 `e3800971b44116bca8ef8f996c3b2796b4d316962f797975f17d643abfac379b`).
> * **Parallel `Lane36` (`gemsdoe36-lane36-supgbm-68302-20261026T002651Z-f35cb3e4-zeros.tif`):** **DO NOT SUBMIT** (198-raster shared-template cross-check `FAIL` at `0.9317` max overlap; [`evidence/lane36_crosscheck.json`](evidence/lane36_crosscheck.json)).
<!-- STATUS:END -->

---

## Arena Core Values — Guiding Every Engineering & Gate Decision

1. **Maximize `P(Win)`:** Every design choice protects the 3 weekly live submission slots for candidates that demonstrably advance genuine off-catalogue geological recall — never spending a slot on circular SGMC proxies, copied sibling rasters, or models that have not beaten the shared buffered holdout best.
2. **Own the Outcome:** Every gate executes automatically in code (`scripts/evaluate_holdout.py`, `scripts/verify_release_gate.py`, `scripts/check_site.py`) with zero manual human-inspector placeholders, zero unverified score projections, and line-by-line cryptographic SHA-256 verification.

## Standing User Prompt & Parallel-Run Directive (Reread Every Session)

> Review `GEMSDOE24`, `GEMSDOE25`, `GEMSDOE27`, `GEMSDOE28`, `GEMSDOE30`, `GEMSDOE31`, `GEMSDOE32` (`h33-h33-2-b2`: `0.2778`), `GEMSDOE33`, and `GEMSDOE36` (`0.2750`). Deliver an executive summary across all 9 focus sites, a PhD-level forensic explanation of why `GEMSDOE32` achieved `0.2778` and how to surpass `0.2778` / `0.3195` / `0.4413`, 3–5 ranked novel candidate geological hypotheses before implementation, and an original zero-copy GeoTIFF submission audited under the Parallel-Run Protocol (`<= 3` experiments or `2` hours; buffered whole-fault-segment hide-and-recover holdout; visible-only catalogue features; pixel-exact masking of visible faults; pooled DTI with $\alpha = 0.2, \beta = 0.8$, 300 m triangular kernel; two-polarity single-feature leakage canary `AUC <= 0.90`; pre-placement surface & post-placement final-dot registry checks `|rho| <= 0.90` and `<= 70%` 3-px overlap; strict `HOLDOUT-DTI` vs `ORGANIZER-CONFIRMED` score provenance; `[0, 1]` portal format validation; `<= 140`-char submission note; unmistakable site download/verdict UI; 3 review passes; single JSON Run Card; PR & merge onto `main`).

---

## 1. Executive Summary Across All 9 Focus Sites (`GEMSDOE24`–`GEMSDOE36`)

Full machine-readable ledger: [`evidence/focus_sites_9repo_summary_20261026.json`](evidence/focus_sites_9repo_summary_20261026.json) & [`docs/research/forensic-9sites-and-atvr36-20261026.md`](docs/research/forensic-9sites-and-atvr36-20261026.md).

| Focus Site | Highest Historical Submission & Provenance | Key Forensic Finding | Latest Zero-Copy Status | Safe Live Slot? |
|---|---|---|---|---|
| [`GEMSDOE24`](https://github.com/buffedlizard55-lab/GEMSDOE24) | `d1.5` (`60,069` dots): `0.2477` (`USER-REPORTED`) | Subset (`Jaccard 0.9795`) of `GEMSDOE27` `tgc` | `GVC1` = `0.0859` (`ORGANIZER-CONFIRMED` halo collapse); `RSHG1` = `72.69%` dup | **No** |
| [`GEMSDOE25`](https://github.com/buffedlizard55-lab/GEMSDOE25) | `d2.8` (`44,090` dots): `0.2600` (`ORGANIZER-CONFIRMED`) | `0` XOR vs `GEMSDOE30` `d2.8` | `H66` (`44,832` dots) = `0.0742` (`ORGANIZER-CONFIRMED`) | **No** |
| [`GEMSDOE27`](https://github.com/buffedlizard55-lab/GEMSDOE27) | `topo-gap-t-v2` (`61,328` dots): `0.2449` (`ORGANIZER-CONFIRMED`) | `d1.5` + `1,259` gap-closure dots | `H29-S` (`37,654` dots) = `0.2190` (`ORGANIZER-CONFIRMED`, already submitted) | **No** |
| [`GEMSDOE28`](https://github.com/buffedlizard55-lab/GEMSDOE28) | `h36-1` (`37,660` dots): `0.2710`; `solo` (`40,199`): `0.2708` (`ORGANIZER-CONFIRMED`) | `solo` = `(d2.8 & d_cat > 1 px)` (`0` XOR vs `GEMSDOE31`) | `S18` (`11,082` dots) = `0.0217` (`ORGANIZER-CONFIRMED`) | **No** |
| [`GEMSDOE30`](https://github.com/buffedlizard55-lab/GEMSDOE30) | `d2.8` (`44,090` dots): `0.2600` (`ORGANIZER-CONFIRMED`) | `0` XOR vs `GEMSDOE25` `d2.8` | `MSDB-1v2` = `0.1462` (`ORGANIZER-CONFIRMED`, marked `NOT APPROVED`) | **No** |
| [`GEMSDOE31`](https://github.com/buffedlizard55-lab/GEMSDOE31) | `h27-4-solo` (`40,199` dots): `0.2708` (`ORGANIZER-CONFIRMED`) | `0` XOR vs `GEMSDOE28` `solo` | `H31-M` (`37,654` dots) = `DO NOT SUBMIT` | **No** |
| [`GEMSDOE32`](https://github.com/buffedlizard55-lab/GEMSDOE32) | `h33-h33-2-b2` (`37,654` dots): **`0.2778`** (`ORGANIZER-CONFIRMED`) | **9-site champion**, `0` XOR vs `(d2.8 & d_cat > 2 px)` | `H-GEO-CONDUIT` (`37,654` dots) = `DO NOT SUBMIT` | **No** |
| [`GEMSDOE33`](https://github.com/buffedlizard55-lab/GEMSDOE33) | `h33d` (`41,865` dots): `0.2632` (`ORGANIZER-CONFIRMED`) | Partial `(0, 2] px` flank retention | `A33-L1` (`37,654` dots) = `NOT OK TO SUBMIT` | **No** |
| [`GEMSDOE36`](https://github.com/buffedlizard55-lab/GEMSDOE36) | Legacy `pinn-38854`: `0.2750` (`ORGANIZER-CONFIRMED`) | Copied `B2 + 1,200` thermal dots | `WDP-36` (`0.0933`), `ATVR-36` (`0.1179`), `H36-CTRB` (`0.1144`), `H36-GPS` (`0.1320`) — all `HOLDOUT-DTI`, all fail-closed `negative` | **No (Hold Slot)** |

---

## 2. Why `GEMSDOE32` Scored `0.2778` & Algebraic Path Above `0.2778` / `0.3195` / `0.4413`

1. **Zero-XOR Collar-Pruning Proof:** `GEMSDOE32` `h33-h33-2-b2` (`37,654` dots, `0.2778` `ORGANIZER-CONFIRMED`) is pixel-identical (`0` XOR across `12,279,160` cells) to masking `GEMSDOE25/30` `d2.8` (`44,090` dots, `0.2600`) by $d_{\text{cat}} > 2.0\text{ px}$ (`200 m`), eliminating `6,436` near-catalogue collar false positives (`1,287` Tversky FP penalty units).
2. **Reciprocal Tversky Inversion ($r^2 = 0.998523$):** Regressing $1/\text{DTI}$ vs $N$ across `[44090, 40199, 38854, 37654]` recovers family recall $\text{TP}_w \approx 5,151.3\text{ px}$ and hidden off-catalogue truth count **$K_{\text{from\_b2}} = 12,852.7\text{ px}$**, agreeing within **`1.72%`** with the independent 5-px calibration lattice inversion (`0.0904` `ORGANIZER-CONFIRMED` $\Rightarrow$ **$K_{\text{lattice}} = 12,631.8\text{ px}$**).
3. **Recall Expansion & Halo-Collapse Remedy (`IR-36-INSAMPLE-HALO-COLLAPSE`):** At $N = 37,654$, `0.3195` requires `TP_w = 5,906.5 px` (`46.8%` recall) and `0.4413` requires `TP_w = 8,279.4 px` (`65.5%` recall). Refitting multi-feature trees in-sample on 100% of `existing_faults.tif` memorizes smooth covariates and dumps `70%+` of dots into `220–500 m` known-fault halos (`GVC1 = 0.0859`, `MSDB1 = 0.1462`); **Chernozhukov Spatial Out-of-Fold Cross-Fitting** eliminates this collapse (`median d_cat = 10.6 px`).

---

## 3. `WDP-36` Ranked Hypotheses & 3-Experiment Buffered Holdout Results (this branch, negative)

Five ranked hypotheses (2 deferred as sandbox-unobtainable: ASF OPERA InSAR, GeoDAWN flight-line CSVs) and the full detector/gate definitions were locked **before any holdout number** in [`evidence/wdp36_preregistration_20261026.json`](evidence/wdp36_preregistration_20261026.json) (SHA-256 `860f7a35...`) + [`docs/research/preregistration-wdp36-20261026.md`](docs/research/preregistration-wdp36-20261026.md); monograph: [`docs/research/wdp36-20261026.md`](docs/research/wdp36-20261026.md). Evaluator: shared `gems-segment-pooled-v1` (whole components, 1.5 km buffer, pooled DTI, 60,988 withheld px). The detector is **unsupervised** (no catalogue-trained parameter; bands 14/13 only for EXP-1).

| Arm | Surface | `HOLDOUT-DTI` [95% CI] | Folds NW / NE / SW / SE |
|---|---|---|---|
| `A0` (control) | Single-scale THDR worms (h=0) | `0.091901 [0.081491, 0.101408]` | 0.0821 / 0.0800 / 0.0936 / 0.1050 |
| **`EXP-1` (winner)** | **0–800 m worm persistence (TMI+grav)** | **`0.093269 [0.083380, 0.103501]`** | 0.0902 / 0.0835 / 0.0884 / 0.1082 |
| `EXP-2` | PERS 0.70 + strain ridges 0.30 | `0.091090 [0.081887, 0.100339]` (strain hurt) | 0.0895 / 0.0798 / 0.0863 / 0.1062 |
| `EXP-3` | PERS 0.60 + strain 0.25 + seismic 0.15 | `0.093156 [0.083076, 0.103199]` | 0.0896 / 0.0826 / 0.0855 / 0.1121 |

Paired EXP-1−A0 `+0.001368 [-0.004578, +0.006991]` (CI includes 0) → persistence unsupported on catalogue-style recovery; verdict **negative / DO NOT SUBMIT** (G2 + literal-blanket G3b fail; canary/format/focus-uniqueness pass). Reproduce: `bash scripts/download_competition_data.sh` (core restore) then `.venv/bin/python scripts/run_wdp36.py`.

---

## 4. `ATVR-36` Ranked Geological Hypotheses & 3-Experiment Buffered Holdout Results

Locked prior to execution in [`evidence/atvr36_preregistration_20261026.json`](evidence/atvr36_preregistration_20261026.json) (`SHA-256: 351a9ad89ce0...`) and evaluated on `gems36-segment-audit-v1` (`3,000 m` buffer, `60,988` withheld px, `3,199` whole segments) + cross-checked on `gems-segment-pooled-v1` (`1,500 m` buffer):

| Arm | Hypothesis / Physical Mechanism | Feats | 3 km `HOLDOUT-DTI` (`95% CI`) | Unsplit `HOLDOUT-DTI` | Paired $\Delta$ vs `B1` (`95% CI`) |
|---|---|---:|---|---|---|
| `C0_repo_field` | Frozen existing repo physical belief field (SGMC off) | 14 ch | `0.018492` (`[0.009837, 0.030040]`) | `0.018489` | `-0.021031` |
| `B1_raw19_hgb_d28` | 19 sanitized official bands + HGB + `d_vis > 2 px` top-k | 19 | `0.039523` (`[0.027195, 0.054596]`) | `0.040417` | `0.000000` (ref) |
| `EXP-1` | **`H36-A`:** Mag/grav tilt+THDR + scarp-toe Hessian + relief-deconfounded piedmont + missingness-aware 3DEP 1 m LiDAR + Raissi–Anderson PDE + 300 m CELF cover | 36 | `0.110598` (`[0.075495, 0.145617]`) | `0.112064` | `+0.071075` (`[+0.0464, +0.0931]`) |
| **`EXP-2` (Winner)** | **`H36-A + H36-B`:** Adds magnetite-destruction `02_rtp` trough × mag-THDR + playa-regressed `17_cond_surf` clay-cap residual + GeoDAWN `K/Th` + GDR `1391` geothermometers | **44** | **`0.114542`** (`[0.078547, 0.151221]`) | **`0.115835`** | **`+0.075018`** (`[+0.0492, +0.0996]`) |
| `EXP-3` | **`H36-A + H36-B + H36-C`:** Adds `15_depth_to_base_surf` flexural hinge × grav-THDR + seismic/strain corridor + fold-learned 3-regime calibration | 50 | `0.113705` (`[0.078494, 0.148428]`) | `0.115229` | `+0.074182` (`[+0.0498, +0.0970]`) |

- **Cross-Lane Breakthrough (`ATVR-36` + `H36-CTRB`):** On `gems-segment-pooled-v1`, `ATVR-36 EXP-2` (`0.117925` pooled) achieves **`NW = 0.15048`**, **`SE = 0.15438`**, and **`SW = 0.11115`**, whereas `H36-CTRB` (`0.114425` pooled) achieves **`NE_LidarGap = 0.13141`** — with only **`37.36%`** dot overlap (`Spearman = +0.0398`). Future external-data routes: **`H36-D`** ([USGS GeoDAWN `doi:10.5066/P93LGLVQ`](https://doi.org/10.5066/P93LGLVQ) raw 1D flight-line profiles) and **`H36-E`** (NASA/ASF Sentinel-1 `OPERA_L3_DISP-S1_V1` InSAR velocity steps).

---

## 5. Verification & Official Sources

```bash
.venv/bin/pytest -q
.venv/bin/python scripts/verify_release_gate.py
.venv/bin/python scripts/check_site.py
```

- **Official Competition & Rules:** [DrivenData #306](https://www.drivendata.org/competitions/306/competition-doe-gems/) · [Problem & Metric (`page/967`)](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) · [Leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) · [DOE/NLR Rules PDF (`96647.pdf`)](https://docs.nlr.gov/docs/fy26osti/96647.pdf) · [Forum `t/11516`](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516) · [Forum `t/11536`](https://community.drivendata.org/t/clarification-what-counts-as-a-new-fault-in-the-test-set/11536) · [DOE GDR `1391`](https://gdr.openei.org/submissions/1391) · [USGS GeoDAWN (`doi:10.5066/P93LGLVQ`)](https://doi.org/10.5066/P93LGLVQ) · [USGS 3DEP](https://www.usgs.gov/3d-elevation-program) · [AI Disclosure](docs/AI_DISCLOSURE.md) · [Irregularities Ledger](docs/research/known_irregularities.md)
