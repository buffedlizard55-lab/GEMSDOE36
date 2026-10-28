# Fresh-checkout review verification — 28 October 2026

This note records checks performed in the current Arena checkout, which is distinct from earlier review evidence in `review_passes_20261028.md`.

## Observed workspace state

- Branch: `arena/f17aba23-gemsdoe36`.
- The checkout contained `data/prepared/h36_ctrb_features.json`, `data/prepared_manifest.json` and `data/restore_receipt.json`, but no `data/raw`, training labels, official submission template, or cached numerical-feature raster. This prevents an independent fresh rerun of the full spatial holdout, leakage canaries, exact-template validation, and all-registry raster comparison.
- Existing TIFFs under `docs/downloads/` are historical/research artifacts. Their presence is not evidence that a fresh candidate was generated, passes the current literal all-registry gate, or is authorized to submit.
- No model experiment was run, no new TIFF was created, and no submission slot was selected or used.

## Verification commands and results

1. System Python initially lacked NumPy and pytest. To avoid changing the system environment, created the ignored project virtual environment and installed the declared `.[dev]` dependencies from PyPI.
2. `.venv/bin/pytest -q`: **186 passed, 6 skipped**. Skips were: optional PyTorch orientation test; incomplete CSDL inputs; absent raw data for CSDL/MTO/TCD integration; and absent restored core/scored mirrors for the registry-feasibility integration test.
3. `.venv/bin/ruff check src scripts tests`: passed (included through `scripts/run_checks.sh`).
4. `PATH="$PWD/.venv/bin:$PATH" bash scripts/run_checks.sh`: **186 passed, 6 skipped**; Ruff passed; site check passed for the negative no-candidate run card, nine-site evidence, local links and research bundles.
5. `python scripts/registry_feasibility.py` using system Python did not run because system NumPy is absent. No numeric conclusion is claimed from that invocation; the committed prior evidence records the earlier SHA-pinned calculation and explains its provenance.
6. An initial unqualified `bash scripts/run_checks.sh` also failed because it invoked system Python without pytest. The corrected PATH invocation above passed; this is an environment invocation issue, not a repository test failure.

## Decision

**Negative — do not submit.** There is no verified candidate in this checkout. The designated method paragraph is not unambiguous in the preserved brief, the literal registry rule already documented forces rejection at the historical 37,654-dot density, and the shared comparator's CRS/transform defect remains upstream. Do not substitute historical TIFFs, treat the historic 0.2778 report as a calibrated projection, or claim an organizer-confirmed result without the actual submission receipt.

A new experiment requires, in order: identify the assigned lane; restore and hash-check authorized inputs; resolve/re-pin the shared comparator fix; confirm that the selected idea's official data has adequate coverage and rights; run canaries and the required buffered whole-segment holdout; and pass both surface and final-dot novelty checks. No weekly slot should be considered until those gates pass, and slot selection remains separate.
