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

Before any submission slot: obtain official data/template through an authorized session; record hashes and actual template/mask geometry; count WSM/DEM/flightline coverage in the AOI; reproduce the organizer comparator; implement/test the official known-fault evaluation mask; run preregistered spatial folds and H1 ablations; show pooled and fold-by-fold DTI plus uncertainty/costs; compare against the current same-run local holdout best; then generate a unique candidate, write an accurate note, locally validate exact TIFF bytes/hash, and preserve any manual platform receipt. Current local holdout best remains `NONE`.
