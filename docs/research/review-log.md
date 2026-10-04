# Three-pass review log

**This log covers the carried-forward scaffold and the current follow-up.** The fresh check count is the source of truth; older README claims of 26/28 passing tests were not supported by the test environment without optional Torch.

## Carried-forward scaffold review — 2026-10-04

### Pass 1 — requirements, repository, and rules

- Preserved the standing requirements: ranked hypotheses, exact DTI, stress in the differentiable loss, spatial holdout before slots, fail-closed GeoTIFF, easy-to-find site status, AI disclosure, source citations, three reviews, and PR/merge honesty.
- Confirmed the original checkout was README-only and official data access requires an enrolled DrivenData session.
- **Outcome:** no model score or guessed TIFF was claimed.

### Pass 2 — geology, target alignment, and validation

- Registered distinct fault-detection hypotheses and emphasized that scalar dilatation/shear/second-invariant layers do not determine a unique axis.
- Separated fault detection from geothermal favorability and documented public-source/AOI limitations.
- Specified contiguous spatial folds, collars, matched policy, stress ablations, and a stop gate. No real data were available to run it.
- **Outcome:** no numeric gain forecast was claimed.

### Pass 3 — code, edge cases, site, and handoff

- Added synthetic tests for metric arithmetic, orientation (optional Torch), spatial folds, and template-grid TIFF writing/validation.
- Added the source/result/site scaffold and clearly labelled the synthetic TIFF as not for submission.
- **Count correction:** earlier README/review text claimed 26/28 passing tests. A fresh run before this follow-up actually reported **19 passed, 1 skipped** because `torch` was not installed. Ruff and the old site check passed. The skipped orientation tests had not been run; no claim of differentiability-test success is retained from that run.

## Current follow-up review — 2026-10-04

### Pass 1 — source, score, and rule re-verification

- Reviewed the current GEMSDOE32 README and public histories of GEMSDOE31/GEMSDOE25. GEMSDOE32 calls H33-2-B2 unscored and 0.2747 projected; its own README says no organizer score exists for its artifacts. GEMSDOE31's owner-reported 0.2708 attribution conflicts with GEMSDOE32's later audit; no receipt resolves it. The reported 0.2778 remains unattributed; 0.3195 is not verified as the current maximum.
- Re-read the official DTI/format page and DrivenData Staff answer that existing USGS/INGENIOUS fault pixels are masked in scoring. The holdout plan now states that mask requirement and rejects an unsupported 200 m exclusion.
- Verified publisher pages for WSM 2025 (GFZ; CC BY 4.0), 3DEP, GeoDAWN raw flight lines/rights, Sentinel-1/ASF access, and Anderson's original faulting paper. No data files, AOI queries, or external coverages were acquired.
- Confirmed GitHub Pages uses `main:/` and added a root redirect rather than assuming `/docs/` is the entry URL.
- **Outcome:** score claims and data availability remain explicitly qualified; no copying or submission is authorized.

### Pass 2 — hypotheses, assumptions, and holdout design

- Re-ranked four distinct conditional candidates: WSM regime-aware stress orientation, high-resolution DEM geomorphology, raw GeoDAWN flight-line coherence, and Sentinel-1 InSAR.
- For each, recorded physical signature, off-catalogue rationale, difference from current code/prior-art history, qualitative DTI potential, cost, official/free source, license/access, and untested local AOI coverage.
- Tightened the top stress hypothesis: use WSM only after an AOI quality/regime count; transform to a normal-regime extension direction only where justified; give ambiguous regimes zero confidence unless a multi-modal loss is implemented. Documented that strain-derived principal axes are not direct stress observations.
- Defined exact spatial policy: 512 px contiguous tiles, 30 px training collar, 3 px metric support, held-out fault systems where possible, same-run reference/best comparison, masked known-fault pixels, and a paired spatial-block improvement gate.
- **Outcome:** no holdout has run; current local best is `NONE`; no weekly slot is eligible.

### Pass 3 — code, edge cases, public site, and handoff

- Fixed the zero-tensor orientation-confidence bug; normalized tensor magnitudes, rejected invalid confidence/mask ranges, added support-mask erosion around invalid boundaries, and added regression tests for zero tensors, scale changes, mask edges, and invalid confidence.
- Tightened GeoTIFF validation to reject infinity outside bounds and calculate rotated pixel-vector lengths correctly. Made filenames collision-resistant, added submission-name provenance to the manifest, and changed the builder to require an explicit unique name and short note.
- Added and tested the root Pages redirect, revised the landing download status and executive summary, and included a manual exact build/validate/upload sequence. The QA fixture remains explicitly not a submission.
- The CPU-only PyTorch index failed with a TLS/EOF error. PyPI installation succeeded but pulled a large CUDA-enabled wheel and runtime packages; the ignored local `.venv` was used only on CPU and no dependencies were committed.
- **Final QA:** `pytest -q` → 33 passed, including differentiability tests; Ruff and the strengthened site check passed. The input audit returned its expected exit 2 because the authorized competition files are missing.
- **Outcome:** no candidate TIFF, real holdout, official score, upload, PR, or merge exists yet for this follow-up. The final PR must be created from `arena/01a10801-gemsdoe36` and GitHub must confirm any merge.
