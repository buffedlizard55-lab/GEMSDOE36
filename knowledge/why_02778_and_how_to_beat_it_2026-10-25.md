# Why GEMSDOE32 `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` scored 0.2778, and what beating it requires

*GEMSDOE36 session 2026-10-25. Labels: **[official]** = competition page / rules PDF;
**[measured]** = computed here from the published bytes (`scripts/forensics_champion.py` →
`evidence/forensics_champion.json`, `scripts/analyze_scored_registry.py` →
`evidence/scored_registry_analysis.json`); **[owner-reported]** = scores from the owner brief
(not organizer receipts); **[inference]** = reasoning, not measurement. The rasters were opened for
learning only; no pixel of any of them is copied into the GEMSDOE36 candidate.*

## 1. The metric is a mass budget **[official → measured]**

From page 967: `TPw = Σ_g max_x p(x)k(d)`, `FPw = Σ_x p(x)[1 − max_g k]`, `FNw = Σ_g[1 − max_x p(x)k(d)]`,
`DTI = TPw / (TPw + 0.2 FPw + 0.8 FNw)`, `k(d) = max(1 − d/300 m, 0)`. Writing `T = TPw`,
`S = Σp` and `M = Σ_x p(x) max_g k`, one gets `FNw = N − T` and `FPw = S − M`, hence

```
DTI = T / (0.2 (T + S − M) + 0.8 N)                                   (1)
```

A unit of mass whose realised credit is `k` raises DTI iff `k > 0.2·DTI` — at 0.2778 the
break-even credit is **0.0556**. Binary values are optimal: (1) is linear-fractional in each
pixel's value, so every pixel is best at 0 or 1 **[inference, exact algebra]**.

## 2. Exact anatomy of the file **[measured]**

| member | owner-reported | positive px | construction (verified bit-exactly) |
|---|---|---|---|
| 19GEMSDOE H19-5 | 0.1922 | 121,131 | solid ridges of a 4-line corroborated field (LiDAR/10 m openness + thermal/geochem + power-law tip/step-over + geopotential worms) |
| GEMSDOE25 d2.8 | 0.2600 | 44,090 | strict subset of H19-5 (raster-order thinning, nearest-neighbour 3 px) |
| GEMSDOE30 poisson300m | 0.2600 | 44,090 | **identical** to d2.8 — same bytes in footprint, same score (scorer is deterministic) |
| GEMSDOE31/28 solo | 0.2708 | 40,199 | d2.8 minus the 3,891 dots ≤ 1 px from the catalogue (B = 1) |
| **GEMSDOE32 h33-2-b2** | **0.2778** | **37,654** | solo minus the 2,545 dots ≤ 2 px from the catalogue (B = 2) |
| GEMSDOE36 anderson | 0.2750 | 38,854 | h33-2-b2 **plus** 1,200 geothermal/relay dots (median 1.45 km from catalogue) |

No new prediction coordinate was ever added on the way from 0.2600 to 0.2778: the gain is pure
deletion of near-catalogue dots.

## 3. Why the deletions helped — the dead annulus **[measured + inference]**

Applying (1) with `T ≈ M` (thin dots; a 2:1 ratio changes T by only ~3 %) to the three nested
files gives the credit carried by the removed dots. The truth size `N` is unknown; the
13GEMSDOE blind 5-px lattice (206,895 dots, 0.0904) implies an effective `N' ≈ 12,541`
truth pixels (truth assumed uniform relative to the lattice; `N' = N_public / f_public` if
only public chunks are scored). At `N' = 12,541`:

| quantity | credit per dot |
|---|---|
| average dot of h33-2-b2 | **0.130** (coverage `T/N' ≈ 0.39`) |
| 3,891 dots ≤ 1 px from catalogue (B0→B1) | **0.0018** |
| 2,545 dots 1–2 px from catalogue (B1→B2) | **0.0059** |
| 1,200 Anderson dots added | **0.014** (< 0.0556 break-even ⇒ 0.2778 → 0.2750) |

Hidden test faults are, by construction, **new faults not in the USGS database**
**[official: page 967; rules PDF §2]** and the scorer masks known faults (organizer forum
clarification recorded as IR-07). Dots within ~200 m of a mapped fault are therefore almost
worthless: they pay the 0.2 FP tax and earn ~1–5 % of an average dot. The registry confirms it
independently: eight owner-scored rasters whose median distance to the catalogue is ≤ 3 px scored
**0.0005–0.0461** (`evidence/scored_registry_analysis.json`).

So 0.2778 = (the best field in the family) × (dot emission at ~3 px) × (denominator thrift from
removing the dead annulus). It is **not** evidence of new geology: the B-ladder changed only which
already-predicted dots were kept.

## 4. Why most later attempts scored lower **[measured]**

Across 118 owner-scored rasters, every file ≥ 0.2600 is a member or near-copy of the H19-5 dot
family. Other detectors placed 37–44 k dots but earned roughly 0.02–0.05 credit per dot (a
regression of score on distance bands is ill-conditioned — RMSE 0.047 DTI — so it is reported only
qualitatively). Lanes placing dots near the catalogue (tilt rings, collars, fault-zone buffers)
collapsed to ≤ 0.05.

## 5. Can we beat 0.2778? **[inference with explicit arithmetic]**

At the same 37,654 dots and `N' = 12,541`, `T` must rise from 4,879 to 5,269 (+8.0 %) for 0.30,
to 5,612 (+15 %) for 0.3195, and to 7,751 (+58.9 %) for the verified leaderboard top 0.4413
(xiaofanhu, read 2026-10-25). Removing a further dead annulus (2–3 px) could add at most a few
thousandths; anything larger needs a **better detector** — more of the dots on the experts' new
faults — not more emission tricks.

The owner brief's "0.3195 is the highest score right now" is stale: on 2026-10-25 the public
leaderboard shows 0.4413 at #1, 0.3916 #2, 0.3904 #3, 0.3724 #4, 0.3539 #5, 0.3379 #10,
0.3273 #20, 0.3051 #30 and 0.2818 #50 — 0.2778 is outside the top 50
(https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/).

## 6. What this session tried, and the result

The H36-GPS lane (`knowledge/h36_preregistration_2026-10-25.md`) added a new physical signature —
conjugate synthetic/antithetic LiDAR scarp pairs and strike-coherent scarp integrals — to a fold-safe
59-feature multi-sensor model. On the shared hide-and-recover evaluator (HOLDOUT-DTI,
`gems-segment-pooled-v1`, 60,988 withheld positives) it scored **0.13203** (95% CI [0.12053, 0.14433])
against **0.13375** ([0.12224, 0.14604]) for the matched baseline: paired Δ −0.00172
([−0.00667, +0.00319], 2/4 folds). The physics-only variant scored 0.05354, and the final dots fell > 70% within 3 px of seven
registry rasters (lane-duplicate rule; 36% vs the 0.2778 file). The lane is therefore **negative**:
its new GeoTIFF is published for research with an automatic **DO NOT SUBMIT** verdict
(`evidence/h36_run_card.json`, `knowledge/h36_findings_2026-10-25.md`). No organizer score exists.

The honest answer to "can we beat 0.2778?" is: not with anything validated today. The arithmetic in §5
says the lever is a materially better detector of the experts' new faults (+8 % credit per dot for 0.30),
most plausibly expert-scale scarp detection on the 1 m DEM itself, which needs a GitHub Actions data route.
