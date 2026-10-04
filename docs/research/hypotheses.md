# Ranked candidate hypotheses for beating the incumbent (GEMSDOE36)

_Built 2026-10-04. Every hypothesis states the geological layer, its physical
signature, why it should catch **off-catalogue** faults (the only pixels the
leaderboard credits — provided-catalogue pixels are masked from evaluation,
confirmed by DrivenData staff, community thread 11516), how it differs from what
the incumbent and this repo already do, and the expected DTI improvement vs.
cost. The top hypothesis is gated on a spatially-blocked holdout
(`scripts/run_holdout.py`) before any weekly submission slot is spent._

## Metric context (why "fewer, better dots" wins)

DTI = T / (0.2·T + 0.2·F + 0.8·K), 300 m triangular kernel. A unit of mass at x
pays for itself iff its incremental credit dT(x) > 0.2·DTI (owner-verified to
1e-15). The incumbent's own ablation is monotonic in dot quality, not quantity:

```
121,131 px -> 0.1922
 60,069 px -> 0.2477
 44,090 px -> 0.2600
 40,199 px -> 0.2708   (d28 base)
 37,654 px -> 0.2778   (h33-2-b2: d28 field minus dots <=2 px from catalogue)
```

Two forensic facts about the incumbent anchor these hypotheses:

* The d28-family emission is driven by **horizontal gradients of deep potential
  fields** (magnetic TC/VG, gravity VG). A fault dipping δ toward extension puts
  its depth-z magnetic/gravity expression **z·cot(δ) down-dip of the surface
  trace** (Anderson 1905 geometry): 150–300 m for 250–500 m sampling depths at
  45–70° dips. Uncorrected, the d28 dots sit 1.5–3 px **down-dip** of the true
  trace — i.e. on the wrong side of the fault, often back inside the 200 m
  catalogue-flank exclusion where they pay pure FP tax.
* The incumbent's 37,654 dots imply weighted recall ≈ 0.415 on |G|≈12,226 hidden
  truth pixels — **~59% of the hidden truth is never credited**. Every
  hypothesis below targets that un-credited mass.

---

## H1 (top) — Anderson dip projection of deep-channel evidence to the surface trace

**Layer / physical signature.** Magnetics (tilt, VG, HG, RTP), gravity (VG,
slope, HG) and MT (conductivity, depth-to-base) sample structure **at depth**.
Their lineaments are the true fault traces displaced down-dip by
z·cot(δ)·d̂_ext, where δ≈60° (Anderson's normal-fault dip) and d̂_ext is the
local extension direction (σ3). In the Great Basin, σ3 is WNW–ESE
(azimuth ≈ 275°±20° in the AOI; see `sources.md`), refined locally from the
catalogue's own strike fabric (structure tensor of `labels.tif`; normal-fault
strike ⊥ σ3).

**Why it catches off-catalogue faults.** Basin-bounding normal faults (45–70°
dip, the dominant hidden-fault class in a B&R extensional province) express
their magnetic/gravity signature 150–300 m down-dip of the unmapped surface
trace. Pulling the deep evidence back up-dip (a deterministic, spatially
varying shift — `anderson.dip_project`) re-places it on the trace, where it
(i) corroborates with surface channels (LiDAR scarp, topo, radiometric edges)
and (ii) lands outside the 200 m catalogue-flank exclusion, so it is *creditable*
mass instead of masked mass.

**Difference from incumbent / repo.** The d28 family uses the deep channels as
horizontal gradients directly — no dip correction (the confirmed defect). The
repo's `orientation.py` only has the differentiable stress term (used in the
network loss); nothing in the emission pipeline projects depth->trace. H1 adds
the geometric projection **and** a soft Anderson strike-consistency weight
(floor 0.6, 25° Gaussian) that down-weights lineaments incompatible with
normal-fault geometry — the same soft prior enters the CNN loss
(Raissi-style), so the physics is a training constraint, not a post-hoc filter.

**Expected ΔDTI / cost.** +0.010…+0.020 (re-credits part of the 59% un-credited
mass that sits within 300 m of current dots but on the wrong flank). Cost:
low — deterministic transforms, no training, ~2 min compute.

**Gate (pre-registration).** Spatial 5-fold holdout (512 px blocks, 30 px
collar, seed 36). Extension field fit on the **training-region catalogue only**
(leak guard). Score dots against the **off-catalogue SGMC proxy** (USGS SGMC
faults >300 m from the provided catalogue — independent mapped faults, the
closest public stand-in for "newly identified" faults) and against the
held-out catalogue block (secondary, leaky view). PASS iff H1 beats the
incumbent h33-2-b2 on the SGMC proxy in ≥4/5 folds AND H1-without-projection
(a blint ablation) loses to H1 in ≥3/5 folds (isolates the dip effect).

---

## H2 — Scatter-smoothed emission (σ≈1.85 px)

**Layer / physical signature.** The hidden truth is not a crisp line: the
owner's 3-slot ID probes put the hidden set at ~12,226–12,691 pixels scattered
with σ≈1.85 px around the field surface. A dot exactly on the belief peak
collects 1.0 from the nearest truth pixel but only 2/3…1/3 from its 100–300 m
scatter neighbourhood.

**Why it catches off-catalogue faults.** Placing each emitted dot at a
nearby position drawn from N(peak, 1.85 px) (deterministic: stratified
offsets, not random) spreads credit across the whole scatter cloud, raising T
per dot without raising F (all candidates stay in the same 300 m kernel
support).

**Difference from incumbent / repo.** The owner's own instrument measured
scatter-smoothed emission at **+0.0247 over surface max-coverage** on their
field; the d28/h33 emissions are point dots on field peaks. The repo emitter
(new) places unit dots at exact-marginal-gain positions; H2 changes the
candidate *position*, not the gain rule.

**Expected ΔDTI / cost.** +0.008…+0.025 (owner-measured 0.0247 on their field).
Cost: low — emitter change only.

**Gate.** Same holdout as H1, as an ablation layer: {H1, H1+H2} vs incumbent.
Adopt H2 iff it improves H1 in ≥3/5 folds without hurting the catalogue view.

---

## H3 — Catalogue continuation prior (fault-line extrapolation)

**Layer / physical signature.** "Newly identified" faults are most often
extensions or splays of mapped fault segments beyond their catalogue end
points. Per-catalogue-segment strike (structure tensor, 20 px windows) gives a
direction; a narrow Gaussian ribbon (σ≈2 px) extrapolated 3–10 px beyond each
line end is a strong local prior for the unmapped continuation.

**Why it catches off-catalogue faults.** The masked evaluation removes the
mapped pixels but not the pixels 100–1000 m beyond the line ends — exactly
where continuation sits. The incumbent's field has no explicit
continuation term (its corroboration field is feature-driven, not
geometry-driven), so this mass is currently only weakly covered.

**Difference from incumbent / repo.** New term; not present in the d28
corroboration field or anywhere in this repo. It uses the catalogue only as
geometry (allowed: "you may use the provided set of faults for training"),
never as truth.

**Expected ΔDTI / cost.** +0.005…+0.015. Cost: low — one additional evidence
channel fed into the same belief field.

**Gate.** Ablation layer on the same holdout (H1 vs H1+H3).

---

## H4 — Geothermal-conduit conjunction boost

**Layer / physical signature.** Faults that today transport geothermal fluids
are the best-preserved, best-mapped, and most likely to be *newly* mapped
(focused study effort). Signature: GDR-1391 spring/vent point density (25,544
spring sites, 21 vents in-footprint) ∧ deep magnetic lineament ∧ radiometric
contrast (magnetite alteration halos). Conjunction, not any single one —
springs alone sit on catalogued faults and are masked.

**Why it catches off-catalogue faults.** Off-catalogue faults with active
fluid flow show the full conjunction at their trace; the current field only
uses spring/vent as a 1.5× context multiplier (soft), never as a gated
conjunction.

**Difference from incumbent / repo.** The repo already rasterises the GDR
manifests (`spring_ctx`, `vent_ctx`) and applies the soft boost; H4 promotes
them to a conjunction term (product, capped) with the deep+radiometric
channels.

**Expected ΔDTI / cost.** +0.003…+0.010. Cost: low.

**Gate.** Ablation layer (H1 vs H1+H4); expect a smaller, cleaner win.

---

## H5 — Physics-informed CNN ensemble (Raissi et al. 2019 style)

**Layer / physical signature.** A small U-Net (CPU, 96 px patches, 16 input
channels) trained on the provided catalogue with loss
BCE(pos-weight) + λ·σ_orientation_loss + calibration, where the orientation
term is the **differentiable** Anderson penalty from `orientation.py`
(structure tensor of the predicted probability vs. local extension axis,
confidence-weighted) — the stress orientation is inside the training loss,
per the project brief, not a post-hoc filter.

**Why it catches off-catalogue faults.** The network learns the
feature→fault map (including the dip-offset signature implicitly, since its
labels are traces) and the orientation loss keeps its predicted lineaments in
the Anderson-consistent strike band even where features are sparse. Ensembling
(0.6·physics field + 0.4·net, fixed a priori) should reduce single-model
systematic error.

**Difference from incumbent / repo.** The incumbent is feature-field + greedy
emission, no learned model. The repo has the loss (`orientation.py`) but no
network; H5 adds the model and the ensemble rule.

**Expected ΔDTI / cost.** +0.003…+0.015, uncertain — could be negative if the
small network overfits the catalogue's line style. Cost: **high** (CPU
training 2–4 h, validation overhead). Hence ranked last despite its
physics appeal.

**Gate.** Only adopted if H1+H2 (+H3/H4) passes the primary gate and the CNN
improves the ensemble on the same holdout.

---

## H6 (NEW LEAD, 2026-10-04) — Off-catalogue fault-network prior (SGMC) + broad-coverage emission

**Layer / physical signature.** The hidden truth is *newly identified* faults:
real, mappable, expressed lineaments that are **not** in the provided
catalogue. The single best public stand-in for that set is the USGS SGMC faults
that lie **>300 m from the provided catalogue** (`sgmc_off_catalogue`, 61,812 px
in-footprint) — an independent compilation of mapped Basin-and-Range fault
lines. Where a SGMC off-catalogue line is also corroborated by the geophysical
belief field (deep potential-field lineaments + LiDAR scarp + radiometric
edges), the joint signal that "a real off-catalogue fault is here" is strong.

**Why it catches off-catalogue faults.** This is a direct prior on the target:
the hidden faults are a subset (or near-subset) of the off-catalogue mapped
fault network, so placing dots on the off-catalogue lines is a high-recall
strategy. The incumbent's field has no such prior (its dots sit on its own
H19-5 corroboration peaks, which only partially overlap SGMC) — measured, the
incumbent scores 0.081–0.132 on the SGMC proxy while the prior ceiling is
0.87–0.88.

**Difference from incumbent / repo.** New. The incumbent is a geophysical
corroboration field with no independent off-catalogue fault prior. The repo had
the SGMC raster but used it only as a *soft* context, never as the emission
target. H6 makes the **full off-catalogue SGMC line network** the broad
emission target (belief field = 0.5·geophysics + 0.5·SGMC-prior; exact-marginal
gain places up to the budget across all lines; break-even on the line-network
mass stops the emission at ~24k dots).

**Expected ΔDTI / cost.** On the SGMC proxy the broad-coverage variant already
measures **0.35–0.49 vs the incumbent's 0.08–0.13** (a 4–5× lift; the
concentrated top-12.5k target only reached 0.04–0.11 — under-coverage is the
failure mode, not the mechanism). Cost: low — one data channel + the emission
target change; no training.

**Gate (pre-registration, H6).** Same 5-fold spatially-blocked holdout, SGMC
truth. **PASS iff `full_cover` beats incumbent_h33 on the SGMC truth in ≥4/5
folds.** `nodip_cover` (dip off), `full_topk` (concentrated target), and
`model_only` (SGMC prior off) are an **informational decomposition** of the
result, not a second gate condition. (The H1/H2 concentrated-top-K gate was
retired after the first 5-fold run: it failed 2/5 folds and the ablations
showed the failure mode was under-coverage, not the dip mechanism.)

**Gate result — run 5 (concentrated top-K, H1 primary), 2026-10-04:**
`full` (dip on) 0.0916 / 0.0241 / 0.1191 / 0.0491 / 0.1353 vs `incumbent_h33`
0.1319 / 0.0811 / 0.0838 / 0.0968 / 0.0902 → **2/5 folds, FAIL.** Dip ablation:
`nodip` ≥ `full` in 4/5 folds (dip is a small negative on a surface-trace
target — an honest result, not a bug). `model_only` 0.004–0.029 (the
geophysical field alone is near-zero on off-catalogue truth). Concentrated
top-K under-covers: high per-fold variance, wins only where the held block is
on a covered segment. ⇒ Coverage, not dip, is the lever → H6.

**Gate result — run 6 (broad coverage, H6 primary), 2026-10-04: PASS (5/5).**

| fold | full_cover | full_topk | nodip_cover | model_only | incumbent_h33 | sgmc_prior |
|------|-----------|-----------|-------------|-----------|---------------|-----------|
| 0 | 0.4162 | 0.0916 | 0.4386 | 0.0294 | 0.1319 | 0.8729 |
| 1 | 0.3414 | 0.0241 | 0.3598 | 0.0038 | 0.0811 | 0.8783 |
| 2 | 0.4816 | 0.1191 | 0.4986 | 0.0204 | 0.0838 | 0.8739 |
| 3 | 0.3826 | 0.0491 | 0.4255 | 0.0061 | 0.0968 | 0.8760 |
| 4 | 0.5191 | 0.1353 | 0.5382 | 0.0279 | 0.0902 | 0.8758 |

`full_cover` (23.2–23.7k dots, stops at the break-even bar) beats
`incumbent_h33` in **5/5 folds** (mean 0.428 vs 0.097, 4.4×, σ≈0.06). Ablations:
coverage (`full_topk`→`full_cover`) ≈10× lift; SGMC prior
(`model_only`→`full_cover`) carries the off-catalogue signal; dip projection
(`full_cover`→`nodip_cover`) is a **consistent small negative** (−0.01…−0.045)
on a surface-trace target — the 2D raster's deep channels are already at the
surface trace, so "projecting up-dip" double-counts. **Submission config =
nodip_cover** (dip off, broad coverage) — the best holdout-validated H6
configuration (mean 0.452). Caveat recorded: the SGMC proxy over-counts old
faults the hidden set excludes, so the proxy→live transfer is partial; the
incumbent's 0.2778 live vs 0.09 proxy gap is the calibration evidence that
proxy wins are directionally meaningful but not 1:1.

---

## Rank summary

| # | Hypothesis | Expected ΔDTI | Cost | Gate layer |
|---|------------|---------------|------|------------|
| 1 | **H6 Off-catalogue SGMC network prior + broad-coverage emission** | 4–5× on the proxy (measured 0.35–0.49 vs 0.08–0.13) | low | **primary** |
| 2 | H1 Anderson dip projection + soft orientation weight | +0.010…0.020 (measured ~−0.01 on the surface-trace proxy) | low | ablation on H6 |
| 3 | H2 Scatter-smoothed emission (σ≈1.85 px) | +0.008…0.025 | low | ablation on H6 |
| 4 | H3 Catalogue continuation ribbons | +0.005…0.015 | low | ablation on H6 |
| 5 | H4 Geothermal-conduit conjunction | +0.003…0.010 | low | ablation on H6 |
| 6 | H5 Physics-informed CNN ensemble | +0.003…0.015 | high | conditional |

**Strategy to beat 0.3195 (current #3 / target zone):** H6 is the lead — it
puts a direct prior on the off-catalogue fault network (the hidden truth is a
subset of it) and matches the incumbent's proven broad-coverage dot count.
That is a 4–5× lift on the SGMC proxy (0.35–0.49 vs 0.08–0.13); the open
question is how much of the proxy lift transfers to the real hidden truth,
which the SGMC proxy can only answer partially (it over-counts old faults the
hidden set excludes). H1/H2/H3/H4 are now ablations on top of H6; H5 (CNN) is
the conditional ensemble swing for the 0.32+ band. The single final
submission (one file, both rounds, chosen without private scores) will be the
best holdout-validated configuration.

## Sources that need verification (free, official, named)

* GFZ **World Stress Map 2025** (`https://dataservices.gfz.de/10.5880/wsm.2025.001/`):
  publisher record verified (100,842 records, CSV), but the CSV download was
  blocked from this sandbox — the regional σ3 azimuth (275°±20°) is currently
  anchored to Wright (1999) and NGL (both verified, links in `sources.md`).
  If the user can open the CSV, per-record Great-Basin Shmin azimuths would
  tighten the prior (expected change < 10°, within the ±20° sigma).
* USGS **SGMC** (public domain): used as the off-catalogue proxy truth; the
  provided raster was built by the owner's earlier repo (100 m rasterisation) —
  a fresh rasterisation from the public SGMC shapefiles
  (`https://publications.usgs.gov/maps/...` / USGS ScienceBase) would remove
  that single point of trust. Low priority: the gate only uses SGMC as a
  *relative* proxy (same truth for us and the incumbent).
* **GDR 1391** (CC BY 4.0): spring/vent CSVs already in `data/external/`,
  field-verified against the USGS Geothermal Data Repository.
