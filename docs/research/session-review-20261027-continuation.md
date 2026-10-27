# Continuation review — 27 October 2026

## Decision

**NEGATIVE — no new TIFF, model run, weekly slot, or score estimate was authorized.** This is a repo audit and candidate-screening pass, not a submission run. The user-supplied parallel-run instruction refers to a single method paragraph, but no such paragraph is present in the request. The branch has no authority to infer a lane. The existing S2D-36 GeoTIFF remains a research artifact only: its local format check passed historically, but its literal all-registry 3-pixel overlap is 99.48% against `reg-052`, above the stated 70% stop threshold. The fixed 37,654-dot budget also has a registry-derived lower bound of 82.34%. These are registry-overlap diagnostics, not scores.

The standing protocol requires a stop if a registry raster exceeds either the correlation or overlap limit, requires whole-segment buffered holdout and one-feature-at-a-time leakage canaries, limits experiments, and reserves slot selection to a separate selector. We did not relax any threshold or spend a slot. Existing downloadable research TIFFs are not thereby authorized for contest upload.

## What the nine-site record says

The executive guide already has the nine requested site rows and artifact names. The supplied site results are reports, not organizer receipts. Its current record identifies these highest user-supplied historical values: GEMSDOE24 0.2477; GEMSDOE25 0.2600; GEMSDOE27 0.2449 (with later H31 reported at 0.2250); GEMSDOE28 0.2710; GEMSDOE30 0.2600; GEMSDOE31 0.2708; GEMSDOE32 0.2778; GEMSDOE33 0.2632; GEMSDOE36 0.2750 (with later KPL-36 reported at 0.1647). All are **USER-REPORTED** unless a dated organizer receipt is archived; none in this record is upgraded to **ORGANIZER-CONFIRMED**.

The existing file audits indicate that the strongest reported files in the older H19-5 / D2.8 family are closely related or strict subsets. In particular, GEMSDOE32 B2 is a catalogue-near-pruned subset of D2.8, not evidence that a new independent geological signal caused the score increase. Pruning can improve a precision-sensitive metric by removing predictions with no known-fault recall credit, but this is a mechanism hypothesis, not a demonstrated explanation of the hidden-label result. There is no calibrated leaderboard score forecast for a new method. The historical 0.2778 result cannot be used as a forecast, and the conflicting 0.3195 / 0.4413 leaderboard figures cannot be resolved from this checkout.

## Repository review: novelty claims that must not be repeated

The previous `docs/research/new-hypotheses-20261027.md` was stale: it said candidate N2 was not yet tested and asserted that magnetic analytic signal, drainage routing, and seismicity were absent from the repository. The audit found:

- N1 and N2 have recorded negative holdout cards (`evidence/n1_holdout_run_card.json`, `evidence/n2_holdout_run_card.json`). N2 achieved **HOLDOUT-DTI 0.010285**, 95% CI **[0.007327, 0.013786]**, evaluator `gems36-segment-audit-v1`, 60,988 withheld positive pixels; the matched baseline was **HOLDOUT-DTI 0.021746**, 95% CI **[0.018991, 0.024228]**. These are internal holdout measurements, not leaderboard scores.
- Magnetic analytic-signal features exist in `src/gemsdoe36/ctrb.py` (Group A).
- Drainage / chi / knickpoint features have been tested in TCD-36; see `src/gemsdoe36/tcd_features.py`, `scripts/run_tcd36_experiment.py`, and the TCD-36 research report.
- Seismicity features are used in the WDP/GVSC feature paths (`src/gemsdoe36/wdp_features.py`, `src/gemsdoe36/gvsc_features.py`).
- Contact and fault-crosscut concepts have already been explored in MTO and related lanes.

Therefore, these cannot honestly be presented as new or untested ideas. A repository grep is not proof of novelty across every GEMSDOE repository, and the full external registry itself contains calibration rasters whose overlap creates a hard fail. The existing cross-site pairwise audit should remain the authority for claims about comparisons actually tested.

## Candidate screen (proposals, not experiments)

Ranking is qualitative: **expected DTI improvement is unknown** until the same buffered-segment holdout is run. No numerical prediction is supplied because historical uploads do not calibrate this transfer. "Not present in this repo" is not the same as "never tried anywhere".

| Rank | Candidate and named layers/source | Physical signature and why it might identify an unmapped fault | Difference from this repo; named non-fault mimic | Expected DTI / cost / data gate |
|---:|---|---|---|---|
| 1 | **Persistent hydraulic-head barrier** — USGS Water Data API / groundwater-level observations, plus the existing DEM and geophysical context for interpolation and terrain controls. Official source route: [USGS Water Data APIs](https://api.waterdata.usgs.gov/). | A laterally persistent water-level gradient break or head discontinuity, reproduced across seasons and independent wells, may indicate a low-permeability fault core or fault-controlled basin compartment even when no surface scarp is mapped. This targets hydraulic architecture, not catalogue proximity. | No sustained water-level surface is used by the current feature store. Mimics: pumping cones, recharge boundaries, lithologic contacts, seasonal measurement imbalance, and well-screen differences. | **Unknown; potentially useful but high uncertainty / high cost. Blocked.** This session did not query the API or establish local well density, temporal repeatability, license compatibility, or footprint coverage. Do not call viable until a small AOI query, metadata/rights check, and coverage audit succeed. |
| 2 | **Seasonal thermal phase-lag / persistence** — time-series surface-temperature observations from [USGS Landsat Collection 2](https://www.usgs.gov/landsat-missions/landsat-collection-2) or NASA LP DAAC, registered to the sample grid; compare repeated seasons rather than a single thermal image. | Persistent thermal inertia or seasonal phase anomalies can mark shallow fluid discharge or a permeable concealed structure. A line-shaped anomaly that survives season, illumination, and topographic normalization could point to a fault corridor not mapped by the USGS/INGENIOUS catalogue. | Existing thermal-probe/geothermometer inputs are point observations; the repo does not build a multi-date satellite phase-lag surface. Mimics: albedo, vegetation, soil moisture, irrigation, topographic illumination, and lithology. | **Unknown / high cost. Blocked.** No time-series scenes or AOI query were obtained here; NASA/USGS access, temporal coverage, sharing terms, and 100 m signal quality are unverified. A free catalog listing alone is not evidence that suitable imagery is obtainable. |
| 3 | **Mapped-unit offset consistency** — official USGS National Geologic Map Database / Nevada Bureau of Mines and Geology surficial-unit polygons and contacts, combined with cached magnetic/radiometric/DEM edges. Source starting points: [USGS NGMDB](https://ngmdb.usgs.gov/ngmdb/ngmdb_home.html) and [NBMG maps](https://www.nbmg.unr.edu/Maps/Maps.html). | Detect paired, geometrically consistent truncation or lateral offset of the same mapped contact on opposite sides of a corridor. Unlike a contact detector, require displacement geometry and corroboration across independent unit boundaries, which can expose concealed fault traces away from known catalogue lines. | MTO examined contact orientation/crosscuts, not this preregistered multi-contact displacement-consensus statistic. Mimics: depositional facies pinch-outs, map generalization, erosional unconformities, and registration errors. | **Unknown / medium-high cost. Blocked.** These official catalogs are identified as sources, but this session did not verify a downloadable, appropriately scaled map covering the competition footprint, its license for sponsor sharing, or registration accuracy. Do not treat as viable until those checks are complete. |

No candidate above has passed the local data gate. These are research leads, not recommendations to spend a submission slot. The highest-ranked candidate is not run because its required measurements are absent and the method paragraph assigning the lane is missing. The only acceptable top-candidate validation is the shared cached feature stack where applicable, shared `evaluate_holdout.py` / `submission_writer.py`, whole buffered fault-segment hide-and-recover, feature-alone canaries, and registry comparison before placement and on final dots. A method must beat the current same-design holdout best and pass literal uniqueness before a selector may consider it.

## Verification and limitations

- Read `README.md` standing brief and the current Pages executive summary; checked the latest review card, S2D/TCD run cards, N1/N2 cards, source ledger, feature implementations, and experiment drivers.
- `python -m pytest -q` could not start: this checkout's interpreter has no `pytest`; the review/gate scripts also could not start because `numpy` is not installed. No tests are claimed as passed in this session.
- No `data/raw` files or `.venv` were present in the working tree, so this session could not rerun TIFF validators, model code, or the holdout. Existing run-card evidence is reported as prior evidence, not a fresh rerun.
- DrivenData, USGS, NASA, and GDR hosts are not on this sandbox's outbound allowlist. Existing prior GitHub Actions endpoint checks are historical evidence, not current verification. The public source routes listed above are not asserted to be currently reachable or adequate for this AOI.
- The nine-site table is an auditable historical snapshot, not a live feed. No official score receipt, authenticated current leaderboard refresh, submission-page weekly cap, or upload acceptance was available in this session.
- The local `[0,1]` zero-outside TIFF format check is not proof of organizer acceptance. The one reported portal error cannot be diagnosed without the rejected TIFF and the exact contemporaneous organizer template.

## Three-pass review record

1. **Pass 1 — inspect:** located the current decision, executive table, source ledger, historic candidate register, run cards, shared evaluator/writer, tests, and generated research TIFFs. Confirmed that the latest intended action is negative, not an automatic upload.
2. **Pass 2 — check contradictions:** found stale novelty claims in the previous candidate register and reconciled them against actual source files and run cards. Found that test execution is blocked by missing Python dependencies and raw input data. Did not use a projection as a score or infer an official receipt.
3. **Pass 3 — final safety check:** preserved the stop conditions, did not alter any raster, model, validator, gate, registry threshold, or submission slot. Updated the living candidate record and added this continuation review. Final decision remains negative.

## Next session

1. Supply/identify the actual single method paragraph and permitted lane; do not infer it.
2. Restore the authorized/pinned dataset and dependencies; run the shared tests and report current results.
3. Query the official source for the highest-ranked external-data hypothesis; verify AOI coverage, license/sharing rights, temporal quality, and hashes before preregistration. If unavailable, record a negative result and move to the next candidate without treating the source as viable.
4. Refresh and hash the registry, then run at most three preregistered experiments within two hours. Do not touch a weekly slot unless the shared holdout improves over the current baseline and the surface plus final dots pass the literal uniqueness thresholds.
5. Keep every score provenance-labeled. A generated TIFF is either explicitly **research-only / DO NOT SUBMIT** or fully gate-passed with a separate selector decision; never imply local validation is organizer acceptance.

Core values: **Maximize P(Win)** by refusing uncalibrated leaderboard claims and invalid duplicates; **Own the Outcome** by documenting the blockers and making the next action reproducible.
