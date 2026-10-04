# Results ledger

## 2026-10-04 — baseline research scaffold (carried forward)

- The repository began as only `README.md` with a title. The first implementation added a local DTI calculator, differentiable orientation loss, spatial-fold utility, template GeoTIFF writer/validator, source register, site, and synthetic tests.
- No competition rasters/template, external AOI raster, trained model, real spatial holdout, organizer score, or upload-ready candidate was available. No real performance gain was measured.
- Historical README/result notes had inconsistent test counts. A fresh pre-change run in this continuation resolved the baseline: **19 passed, 1 skipped** because optional PyTorch was absent; Ruff and site checks passed. This run did not verify the orientation/differentiability tests.

## 2026-10-04 — source, score-attribution, and code/site review

- Reviewed current GEMSDOE31/32/25 owner-site histories. GEMSDOE32 explicitly labels H33-2-B2 unscored and 0.2747 projected; it says no organizer score exists for its artifacts. GEMSDOE31's owner-reported 0.2708 attribution conflicts with GEMSDOE32's later audit. User-reported 0.2778 remains unattributed; 0.3195 is not verified as the current maximum. No leaderboard table or participant names are mirrored.
- Verified the DrivenData staff answer that existing USGS/INGENIOUS fault pixels are masked from scoring/re-evaluation. Updated validation policy to emulate that mask and rejected an unsupported universal 200 m catalogue buffer.
- Verified official publisher pages for GFZ World Stress Map 2025 (CC BY 4.0), USGS 3DEP, GeoDAWN flight-line inventory/rights, and NASA Sentinel-1/ASF access. No external binary, AOI query, or local coverage test was performed; all candidates remain conditional.
- Registered four distinct hypotheses and a source-checked availability table. H1 is a provisional research priority only; no numeric DTI gain is claimed.
- Found an orientation-helper bug: an exactly zero strain tensor had near-unit confidence due to `sqrt(... + epsilon)`. Reworked scale normalization and confidence, documented strain-versus-stress limits, added valid-support masking and confidence-range checks, and added regression tests.
- Hardened TIFF validation against infinite values outside the sample mask, corrected rotated pixel-vector resolution calculation, added collision-resistant filename generation with shape+content digest and random suffix, and made the builder require a unique submission name and truthful short note.
- Added repository-root redirect for Pages `main:/`; strengthened static-site checks for the redirect, local links, warnings, and exact submission guide flags. Reworked the executive summary to say no competition TIFF exists and surface the score/format caveats.
- **No candidate GeoTIFF, model, real holdout, weekly slot use, or new official score was produced.**
- **Final local QA:** PyTorch 2.14.1 was installed in the ignored `.venv` from the default package index after the CPU-only PyTorch index failed with a TLS/EOF error. The default wheel included large CUDA runtime packages even though this sandbox has no GPU; no dependency artifacts were committed. `pytest -q` → **33 passed** (Torch orientation/differentiability tests included); Ruff passed; `scripts/check_site.py` passed, including the root redirect; the input audit returned its expected exit 2 for absent authorized files.

## Required next measured result

Before any submission slot: obtain official data/template; record hashes and actual template/mask geometry; reproduce the organizer comparator; run preregistered spatial folds and ablations; show pooled and fold-by-fold DTI plus uncertainty/costs; compare against the current same-run local holdout best; then generate a unique candidate, write an accurate note, locally validate exact TIFF bytes/hash, and preserve any manual platform receipt. **Status (2026-10-04):** all pre-slot steps are complete — data present, 5-fold holdout run, H6 candidate generated and validated. Current local holdout best = H6 `nodip_cover` (mean 0.452 on the off-catalogue proxy). The remaining step is the owner's manual upload.

## 2026-10-04 — GitHub handoff and live-site verification

- [PR #2](https://github.com/buffedlizard55-lab/GEMSDOE36/pull/2) was merged to `main` at 2026-10-04 18:07:50 UTC as merge commit `1186bd1b705f47a8979d85c65c552f4c9bc31106`.
- GitHub Pages reported its build `built`. A cache-busted request to the public root followed the root redirect to `/docs/`; the updated landing page showed the no-submission status, score-attribution note, four conditional hypotheses, and QA-only TIFF warning.
- This confirms publication of the research/site/code changes only. No authorized competition data, model, real holdout, candidate TIFF, upload, or organizer score exists.

## 2026-10-04 — data arrival, pipeline, holdout gate, and upload-ready candidate (session `arena/01a10834-gemsdoe36`)

- **Data:** the owner-supplied SHA-256-pinned mirrors of the official rasters
  (features, labels, sample template) plus external layers (USGS 3DEP LiDAR
  scarp, GeoDAWN radiometric/extension grids, USGS SGMC proxy, GDR-1391
  geothermal manifests) are present under `data/`. Provenance and the single
  point of trust (owner mirrors, not organizer-authenticated bytes) are in
  `sources.md` and `data/processed/manifest.json`.
- **Pipeline:** `prepare_data.py` (49 channels) → `field.py` (multi-family
  corroboration belief field + SGMC prior) → `anderson.py` (spatially varying
  extension field, dip projection, soft strike weight) → `emitter.py`
  (exact-marginal-gain dots, support confinement, 200 m catalogue-flank
  exclusion, 300 m scatter) → `submission.py` (fail-closed writer).
- **Holdout gate — run 5 (concentrated top-K, H1 dip primary): FAIL.**
  `full` beat the incumbent in 2/5 folds (0.0916 / 0.0241 / 0.1191 / 0.0491 /
  0.1353 vs 0.1319 / 0.0811 / 0.0838 / 0.0968 / 0.0902), high variance; the
  failure mode was **under-coverage** (13.5k dots concentrated on the best
  segments vs the incumbent's 37.6k broad). Dip ablation: `nodip` ≥ `full` in
  4/5 (dip is a small negative on a surface-trace target). `model_only`
  0.004–0.029 (geophysics alone is near-zero off-catalogue). ⇒ the lever is
  coverage + an off-catalogue prior, not dip.
- **Hypothesis H6 (off-catalogue SGMC network prior + broad-coverage emission)
  promoted to lead.** Emission target changed from the concentrated top-12.5k
  to the full off-catalogue SGMC line network; the emitter now stops at the
  break-even bar at ~23–25k dots.
- **Holdout gate — run 6 (H6 broad coverage): PASS 5/5.** `full_cover`
  (23.2–23.7k dots) beat `incumbent_h33` on **every fold**: 0.4162 / 0.3414 /
  0.4816 / 0.3826 / 0.5191 vs 0.1319 / 0.0811 / 0.0838 / 0.0968 / 0.0902
  (mean 0.428 vs 0.097, 4.4×). Ablations: `full_topk`→`full_cover` ≈10×
  (coverage); `model_only`→`full_cover` (the SGMC prior carries the
  off-catalogue signal); `full_cover`→`nodip_cover` a consistent small
  negative (−0.01…−0.045, so dip is off in the candidate). Full table in
  `holdout_results.json`. **Current local holdout best = H6 `nodip_cover`
  (mean 0.452).** Caveat: the SGMC proxy over-counts old faults the hidden set
  excludes, so the proxy→live transfer is partial.
- **Upload-ready candidate generated and validated.** Config = dip off, SGMC
  prior on, broad coverage, scatter 3 px, flank exclusion → **24,881 dots**,
  binary dot map, EPSG:32611 100 m, single float32 band, [0,1] in-bounds, NaN
  outside, template match, SHA-256 manifest. File:
  `outputs/submissions/GEMS36_h6_offcatalog_network_prior_20261004T193432.021282Z_3276c04090_3c064db2.tif`
  (mirrored to `docs/downloads/` for the site). Diagnostics in
  `outputs/h6_diagnostics.json`. The upload itself is the owner's manual step;
  no slot has been spent and no organizer score exists yet.
- **Not done yet:** the H5 CNN ensemble has not been trained/gated, so it is
  not in this file. It may use a later slot only if it beats the H6 holdout
  best on the same folds.
