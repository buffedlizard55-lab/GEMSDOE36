# Repository review and decision record — 2026-10-26 UTC

**Scope:** GEMSDOE24/25/27/28/30/31/32/33/36 forensic review; MTO-36 / ATVR-36 evidence; format gate; reproducibility and restore-data behavior. This is a review of artifacts already present in the repository plus a restore-receipt bug fix. **No new experiment, candidate TIFF, portal upload, submission slot, or organizer score was created.** The existing research TIFFs remain downloadable for research only; the current verdict is **DO NOT SUBMIT**.

## Executive decision

- Highest historical figure among the nine focus sites is GEMSDOE32 B2, **0.2778 OWNER-REPORTED**, not ORGANIZER-CONFIRMED: no authenticated submission-page receipt is archived. This is the correct answer only within the supplied/archived nine-site claims, not an independently checked current leaderboard score.
- Byte-level cross-checking shows GEMSDOE32 B2 is not a novel model relative to the prior family: its in-footprint positive mask is exactly D2.8 with all cells at or within 2 px (200 m on this 100 m grid) of the known-fault catalogue removed; XOR = 0, 6,436 pixels removed. GEMSDOE25 and GEMSDOE30 D2.8 masks also have XOR = 0. Do not reuse these as a new submission.
- The MTO-36 research TIFF passes the local raster format/range gate, but its final dots trip the literal registry overlap stop and its holdout does not justify a live slot. ATVR-36 EXP-2 has the strongest recorded ATVR score, but remains below the archived group holdout best and fails the expanded registry blanket rule. **No current artifact is promoted.** A holdout metric is not a leaderboard projection.

## Nine-site verified file inventory

File bytes, SHA-256, template geometry and in-footprint positive counts were checked against pinned GitHub commit/file references by `scripts/audit_focus_sources.py`. I additionally compared all 72 directed site pairs on the 5,167,373-pixel footprint using `scripts/audit_focus_uniqueness.py`; detailed values are saved in [`focus_sites_pairwise_uniqueness_20261026.json`](../../evidence/focus_sites_pairwise_uniqueness_20261026.json). Each raster is binary 0/1 inside the footprint, so pairwise Spearman rank correlation equals binary-mask Pearson correlation. For every candidate, I measured the fraction of its positive dots within Euclidean distance ≤3 pixels of each of the other eight site masks. **All nine historical TIFFs exceed the protocol's 70% overlap ceiling against every other site** (lowest per-candidate minimum ranges from 86.72% to 99.88%). This is an all-nine historical-family comparison, not a leaderboard score test. The reported scores remain claims, as labeled. The detailed site table is in [the MTO executive report](mto36-evidence-and-nine-sites.md); the source-integrity ledger is [here](../../evidence/mto36_ninesite_forensics.json).

| Site | Highest historical file | Dots | Historical score / provenance | Unique under the stated 3-px overlap test? |
|---|---|---:|---|---|
| GEMSDOE24 | `gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif` | 60,069 | 0.2477 OWNER-REPORTED | **No**; all 8 peers overlap ≥88.48% of this mask within 3 px. |
| GEMSDOE25 | `gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif` | 44,090 | 0.2600 OWNER-REPORTED | **No**; all 8 peers overlap ≥88.17%; exact mask duplicate of GEMSDOE30 (XOR 0). |
| GEMSDOE27 | `gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif` | 61,328 | 0.2449 OWNER-REPORTED | **No**; all 8 peers overlap ≥86.72%; near-duplicate/subset of GEMSDOE24. |
| GEMSDOE28 | `gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif` | 37,660 | 0.2710 OWNER-REPORTED | **No**; all 8 peers overlap ≥95.47% within 3 px. |
| GEMSDOE30 | `gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif` | 44,090 | 0.2600 OWNER-REPORTED | **No**; all 8 peers overlap ≥88.17%; exact mask duplicate of GEMSDOE25 (XOR 0). |
| GEMSDOE31 | `gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif` | 40,199 | 0.2708 OWNER-REPORTED | **No**; all 8 peers overlap ≥95.39%; identical to GEMSDOE28 solo D2.8 mask (XOR 0). |
| GEMSDOE32 | `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` | 37,654 | **0.2778 OWNER-REPORTED (highest of these nine)** | **No**; all 8 peers overlap ≥99.88%; exact D2.8-with-2-px-catalogue-collar subset (XOR 0). |
| GEMSDOE33 | `GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif` | 41,865 | 0.2632 OWNER-REPORTED | **No**; all 8 peers overlap ≥92.64% within 3 px. |
| GEMSDOE36 | `gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif` | 38,854 | 0.2750 OWNER-REPORTED | **No**; all 8 peers overlap ≥97.31%; B2 positives plus 1,200 additional thermal dots (repo cross-check). |

The table's scores are descriptive historical reports, not estimates for a new file. The current official leaderboard and competition rules are linked from the site; this sandbox did not authenticate a live leaderboard fetch or obtain an organizer receipt. No score was inferred as a leaderboard projection.

## Candidate hypotheses already ranked and tested

The five preregistered concepts are fully specified in [`evidence/atvr36_preregistration_20261026.json`](../../evidence/atvr36_preregistration_20261026.json). Rankings below summarize that protocol; “expected improvement” was a hypothesis ranking, not a calibrated numerical prediction.

| Rank | Layers and target signature | Why it might find uncatalogued faults / main mimic | Difference and status |
|---:|---|---|---|
| 1 | Magnetic/gravity derivatives (`tmi_vg`, `tmi_hg`, TMI/RTP, gravity VG/HG/slope) + elevation and 3DEP LiDAR scarp features; phase-equalized tilt, multi-scale curvature/ridge, relief correction and anisotropic variational diffusion. | Seek depth-persistent edges and concealed piedmont breaks, not catalogue buffers; mimics include paleo-shoreline benches and basaltic dikes. | New multi-physics combination; tested as ATVR-36 EXP-1/2/3. EXP-2 did best of the three recorded ATVR runs, but did not pass all promotion gates. |
| 2 | RTP/TMI, surface conductivity, depth-to-basement, K/Th and DOE GDR geothermometers; magnetite-destruction trough and depth-regressed clay-cap residual. | Hydrothermal alteration could mark blind upflow structures; playa brines and tuff contacts mimic it. | Adds geothermal alteration evidence to H36-A; included in EXP-2. It raised the internal holdout point estimate, not enough to clear the external gates. |
| 3 | Basement depth, gravity derivatives, detrended elevation; signed flexural hinge plus mountain/piedmont/basin calibration. | Concealed basin-fill faults; differential compaction over buried paleo-topography mimics it. | Distinct regime/horizon mechanism; EXP-3 added this and was lower than EXP-2 on the same evaluator. |
| 4 | USGS GeoDAWN raw line-located magnetic/radiometric profiles; tie-line crossover residuals. | Could resolve narrow offsets lost in gridded products; pipelines, powerlines and guardrails mimic them. | Requires raw survey lines; the preregistration records the official USGS DOI `10.5066/P93LGLVQ`, but it was not obtained in this restricted environment, so it is not a viable tested candidate here. |
| 5 | NASA/ASF OPERA InSAR displacement/coherence time series; persistent LOS velocity or seasonal phase-gradient discontinuity. | Fault-controlled aquifer barriers; pumping and stratigraphic pinch-outs mimic them. | Independent deformation/hydrology modality; requires Earthdata/ASF access not available in this environment, so not tested or scored. |

### HOLDOUT-DTI results (not leaderboard scores)

| Candidate | Evaluator / withheld positives | HOLDOUT-DTI and 95% CI | Result |
|---|---|---:|---|
| ATVR-36 EXP-1 / H36-A | `gems36-segment-audit-v1`; 60,988 withheld positives | 0.110598 [0.075495, 0.145617] | Lower point estimate than EXP-2; CI wide. |
| ATVR-36 EXP-2 / H36-A + H36-B | `gems36-segment-audit-v1`; 60,988 withheld positives | 0.114542 [0.078547, 0.151221] | Best ATVR point estimate; paired delta vs archived B1 is positive in recorded analysis, but below shared holdout baseline B0=0.133749 and group best=0.14876; final all-registry uniqueness failed. |
| ATVR-36 EXP-3 / H36-A + H36-B + H36-C | `gems36-segment-audit-v1`; 60,988 withheld positives | 0.113705 [0.078494, 0.148428] | Did not improve on EXP-2. |
| MTO-36 magnetic contact × gravity crosscut | `gems-segment-pooled-v1`; 60,988 withheld positives | 0.067611 [0.058449, 0.077867] | Paired CI vs matched control crosses zero; negative. |

These are blocked/recovery metrics under the named local evaluators, not public leaderboard score estimates. The ATVR report records 50 feature-alone canaries with max two-polarity AUC 0.58811; MTO-36 records nine with max two-polarity AUC 0.58778. Both are below the preregistered 0.90 leakage alarm. The per-experiment results and methodology are in the linked run cards and JSON evidence.

## Uniqueness and submission decision

- MTO-36 pre-placement max absolute surface rank correlation: 0.4366 (below 0.90); final dots: literal 3-px overlap 1.0000 with a synthetic 5-pixel lattice and additional >0.70 masks, so duplicate-stop applies. Final-dot check is not waived because surface correlation is low.
- ATVR-36 maximum overlap across the expanded registry: 0.893637; literal registry gate fails despite the much lower overlap against the nine named focus sites. Dense blanket/control overlaps count under the protocol.
- Local MTO release validator verifies the exact template CRS/shape/transform, one-band float32, finite whole-array values in [0,1], the expected file SHA-256 and a one-TIFF ZIP. This verifies the local artifact only; it cannot guarantee portal acceptance.
- Current MTO-36 record: `gemsdoe36-mto36-ortho-contact-20261026-c41282e9da7a-zeros.tif`, SHA-256 `3e6594fe39facbffd433dc4500a7e8766fab2dd0d5089d2f591ed47713261607`. It is an existing research artifact, **not approved to download and submit**. The Pages front page and `docs/current-run.json` state that distinction.

## Three-pass code and repository review

1. **Evidence/method review:** checked README's requested research/protocol and core values; examined preregistration, 3 ATVR runs, MTO and WDP/MOE records, nine-site evidence, template and run cards. Found the score labels correctly cautious in the current summary: historical figures are owner-reported; no leaderboard projections are presented as scores.
2. **Reproducibility review:** initial clean workspace lacked ignored `data/raw` despite a tracked old restore receipt saying 23 files were restored. Restored core files and 12 scored manifest artifacts from pinned GitHub references and independently hash-verified the nine focus TIFFs plus GEMSDOE28 solo file. `scripts/audit_focus_sources.py` then verified all nine files and all eight nested-family XOR/count claims. External data not needed for this byte audit remains un-restored.
3. **Regression review:** found `scripts/restore_data.py` overwrote `data/restore_receipt.json` with only the most recently requested group, making the receipt misleading after a filtered restore. Fixed the writer to inventory all currently present files whose SHA-256 matches the manifest, mark earlier files as `present`, and exclude missing or changed files. Added `tests/test_restore_data.py` covering cross-group inventory, missing files, and hash mismatch. Also found that README and its generator hard-coded an earlier session's branch; README now records this session's fixed branch and the generator obtains the checked-out branch dynamically. Historical run cards retain the branch on which those runs were recorded; they are not rewritten to this review branch. No experiment or submission was run to test these utility changes.

## Commands and current verification

Executed from repository root after installing `.[dev]` into ignored `.venv` and restoring the necessary ignored assets:

- `python scripts/restore_data.py --group core` and `--group scored`: completed; final `data/restore_receipt.json` records 16 currently present/hash-verified manifest entries (4 core + 12 scored). Optional external group is not included.
- `python scripts/audit_focus_sources.py`: **PASS**, nine sites, all eight inherited family checks.
- `python scripts/verify_mto_release.py`: **PASS as a negative research release**, TIFF SHA matches, no errors, `download_and_submit=false`.
- `python scripts/check_site.py`: **PASS**.
- `.venv/bin/python -m pytest -q`: **108 passed, 1 skipped** (optional `torch` not installed; skip is in `tests/test_orientation.py`).
- `.venv/bin/ruff check src scripts tests`, Python `compileall`, `node --check docs/assets/live-feed.js`, `git diff --check`: **PASS** at final review.

The system's connected outbound host restrictions permit GitHub data restoration but not direct authentication to DrivenData or NASA/ASF portals. Competition data access was possible from the repository's pinned owner mirror; it is not an official-host download. Official competition/rules, USGS, USGS source and DOI, EPSG, reference solution, and scientific-source leads remain linked in `docs/research/sources.md` for external review. No statement here upgrades a mirror into an official authority.

## Items for the next session

1. Do not promote or upload any present TIFF. Start a distinct, pre-registered scientific lane only after confirming its available data, heldout split, feature canaries, experiment budget, and no reuse of a previously tested surface/placement.
2. Prioritize a validated source route for raw USGS GeoDAWN flight lines (or a truly independent, obtainable geological modality); do not claim H36-D/E viability until bytes are acquired, licensed, gridded/registered, and checked against official metadata.
3. Reduce area-blanket duplicate risk before dot placement using a source-independent spatial design or another approved selector policy—not by changing the 0.70 threshold after observing results. If the required protocol cannot be passed, emit a negative card and spend no slot.
4. Archive genuine organizer submission receipts if/when an authorized human chooses to submit a future promoted candidate; refresh the official leaderboard separately. Keep historical scores OWNER-REPORTED until then.
5. On a clean clone, restore data and rerun `python scripts/prepare_data.py` before research/evaluation; ignored rasters and the `.venv` are deliberately not versioned.
