# Repository review — 2026-10-29 (earlier checkout snapshot)

> **Superseded as current status by [`docs/research/review-20261029.md`](../docs/research/review-20261029.md).** This checkout review preceded restoration of `data/raw/`; its missing-input statements are historical. The later review restored and grid-checked inputs, populated `.cache/gems_work/bands`, and reran the relevant tests.

## Scope and decision

Reviewed the active checkout, current decision pages, nine-site decision evidence, historical run cards, raster inventory, and available project checks. This is a documentation/status review, not a new scientific experiment. **Verdict remains negative: no new candidate was generated, validated, or authorized for upload.** No organizer score, live leaderboard value, or submission-page receipt was independently checked in this review.

## Findings

1. **No assigned experimental lane.** The standing parallel-run protocol requires a specific method paragraph. The current owner brief/review says it is absent. Running a different experiment or fabricating a TIFF would violate that constraint.
2. **Registry gate is blocking and known to be degenerate.** The pinned `reg-052` regular lattice causes overlap above the literal threshold for typical candidate sizes. Existing evidence explains why that is a limitation of the gate, not proof of duplicate geology. Do not unilaterally remove it or infer uniqueness.
3. **No competition-ready fresh data in this checkout.** `data/raw/` is absent. `data/prepared_manifest.json` and `data/restore_receipt.json` exist, but do not establish that raw template/labels are currently present. Tests depending on those inputs skipped. This corrects overly broad claims in older README/session history that could be read to mean raw inputs are available now.
4. **The nine-site table is useful for historical comparison, not submission selection.** Its scores are labelled owner/user-reported without archived organizer receipts; estimates are explicitly not estimable; the historical candidates fail pairwise uniqueness in the pinned nine-site set. The table and existing page checks pass.
5. **Older run cards and pages are historical snapshots.** They must not be treated as current live leaderboard data, current account quota, or current portal acceptance. A TIFF's presence in `docs/downloads/` does not imply it is approved to submit.

## Verification performed

- `python -m venv .venv && .venv/bin/pip install -e '.[dev]'` — succeeded.
- `.venv/bin/pytest -q` — **190 passed, 8 skipped**. Skips include optional PyTorch and missing raw/integration inputs; see test output in the review session. No claim that skipped data-dependent tests passed.
- `.venv/bin/ruff check src scripts tests` — passed.
- `.venv/bin/python scripts/check_site.py` — passed (negative run card, nine-site evidence, local links, research bundles).
- `python -m compileall -q src scripts tests` — passed.
- `git status` was clean before this review note; generated environment/cache artifacts are ignored.

## Three-pass assessment

### Pass 1 — inventory

The repository already contains a prominent negative decision, the nine-site historical table, research-only TIFF wording, hypothesis/research notes, provenance records, a run card, a format validator, and a site-check command. No missing TIFF should be manufactured to satisfy the word “generate” while the required lane and validation inputs are absent.

### Pass 2 — risks and inconsistencies

Found a material freshness issue: previous status text says restored/prepared data are available, while the actual checkout lacks `data/raw/`; test skips corroborate the missing inputs. The note now distinguishes the manifests/receipts from the absent raster inputs. Another key limitation is that user-supplied leaderboard numbers and scores are not receipts. The local site check verifies consistency, not external truth.

### Pass 3 — requirements and disposition

The project correctly avoids claiming a high-scoring new submission, a calibrated score estimate, or organizer approval. The existing executive summary clearly marks no-submit and has per-site historical information. The unique-TIFF request remains unfulfilled and should remain so until (a) an authorized lane is explicitly supplied, (b) official competition rasters are available and provenance is resolved, (c) shared comparison tool CRS/transform defect is addressed upstream, (d) candidate passes leakage-aware blocked holdout and both novelty checks, and (e) validator confirms organizer grid/range/mask. The weekly selector remains separate.

## Recommended next steps

1. Obtain an explicit single-method lane assignment; do not select one from the backlog implicitly.
2. Restore the official organizer data through an authorized account or obtain documented approval/provenance for mirrors; ensure the required template/labels are present, not just prepared manifests.
3. Resolve the shared comparator's CRS/transform validation defect upstream; do not patch a private vendored copy.
4. Reconcile the site's submission format and the reported `[0,1]` portal error against an actual accepted sample and official documentation. Local validation is not portal acceptance.
5. Only then run the assigned, preregistered candidate(s), max three experiments/two hours, with feature-alone leakage canaries, buffered whole-segment holdout and CI, surface correlation, final-dot overlap, exact-grid validation, and a negative-or-promote run card.
6. A separate authorized selector may consider a candidate only after all gates pass and current weekly cap/slot policy is verified on the submission page.

## Provenance

This is a repository-state report as of 2026-10-29 UTC. Local tests and source files were inspected; no outbound official source was freshly verified in this review. It does not assert current leaderboard rank, account quota, submission acceptance, or organizer confirmation.