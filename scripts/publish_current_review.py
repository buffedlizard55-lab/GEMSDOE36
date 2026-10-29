#!/usr/bin/env python3
"""Publish the current negative release review and latest research-only result.

Historical TIFFs and evidence remain available, but no submission candidate or
slot is authorized. GSEWC36-EXP1 is exposed as an unassigned negative experiment;
all site entrypoints delegate here so rebuilding preserves it and the strict
archive checks rather than resurrecting an obsolete upload instruction.
"""
from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
from shutil import copyfile

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def build_focus_table(table: dict, historical: dict, pairs: dict) -> str:
    """Render exactly nine pinned historical rows, not a live leaderboard."""
    expected = {"GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
                "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"}
    entries = table["entries"]
    if (len(entries) != 9 or {x["site"] for x in entries} != expected
            or table["decision"] != "negative" or table["approved_submission"] is not None
            or table["leaderboard_estimate"] is not None):
        raise ValueError("Focus-9 decision table does not describe the required negative snapshot")
    by_site = {x["site"]: x["highest_historical_submission"] for x in historical["focus_sites"]}
    rows = []
    for entry in entries:
        site = entry["site"]
        best, source, pair = entry["historical_best"], by_site[site], pairs["site_summary"][site]
        if (entry["unique_vs_other_eight"] is not False
                or entry["estimated_leaderboard_score"] is not None
                or pair["unique_under_parallel_protocol_vs_all_eight"] is not False
                or best["file"] != source["name"] or best["url"] != source["pinned_raster_source_url"]
                or best["sha256"] != source["sha256_full"] or best["reported_score"] != source["score"]
                or best["max_overlap_3px_vs_other_eight"] != pair["max_overlap_vs_other_eight"]
                or best["max_abs_spearman_vs_other_eight"] != pair["max_abs_binary_surface_spearman"]):
            raise ValueError(f"Focus-9 source or uniqueness mismatch for {site}")
        label = best["score_label"].split(",", 1)[0]
        if label not in {"OWNER-REPORTED", "USER-REPORTED"} or not source["score_label"].startswith(label):
            raise ValueError(f"Unsupported score provenance for {site}: {label}")
        rows.append(
            f'<tr><th scope="row">{esc(site)}</th>'
            f'<td><a href="{esc(best["url"])}"><code>{esc(best["file"])}</code></a>'
            f'<br><small>SHA-256 {esc(best["sha256"][:12])}…</small></td>'
            f'<td>{best["reported_score"]:.4f} {esc(label)}<br><small>Estimate: Not estimable</small></td>'
            f'<td><strong>NO</strong> · max {best["max_overlap_3px_vs_other_eight"] * 100:.2f}% '
            f'within 3 px</td><td><strong>DO NOT SUBMIT</strong></td></tr>'
        )
    # Data-derived "at a glance" callout: the highest REPORTED score among the nine pinned
    # rows. It states the negative verdict only; it does not authorise upload or estimate.
    top_entry = max(entries, key=lambda x: x["historical_best"]["reported_score"])
    top = top_entry["historical_best"]
    top_label = top["score_label"].split(",", 1)[0]
    glance = (
        '<div class="callout warning" id="best-reported"><strong>Highest reported file (at a glance): '
        f'{esc(top_entry["site"])}</strong> · <code>{esc(top["file"])}</code> · '
        f'{top["reported_score"]:.4f} {esc(top_label)} · estimate: not estimable · '
        f'unique vs the other eight: <strong>NO</strong> (max {top["max_overlap_3px_vs_other_eight"] * 100:.2f}% '
        "of dots within 3 px) · <mark>DO NOT SUBMIT</mark>. The owner page reports this file as already "
        "submitted; no organizer receipt is archived here.</div>"
    )
    return '''<!-- FOCUS9_DECISION:START -->
<section class="section" id="focus9-decision" aria-labelledby="focus-title">
''' + glance + '''
<div class="section-head"><div><span class="eyebrow">Pinned snapshot · nine sites</span><h2 id="focus-title">Historical files, not submission choices</h2></div></div>
<p>These are the highest reported files in the pinned historical snapshot, not a live ranking. Each fails uniqueness against at least one of the other eight. A nine-site check alone cannot establish global registry uniqueness. Scores are owner/user-reported; no submission-page receipt is archived. Additional results transcribed from the owner-supplied prompt are in the evidence, not authenticated receipts.</p>
<div class="table-wrap"><table><caption class="small">Research and provenance links only; no new leaderboard estimate is defensible</caption>
<thead><tr><th>Site</th><th>Historical file &amp; SHA-256 prefix</th><th>Reported score / estimate</th><th>Unique vs 8?</th><th>Action</th></tr></thead><tbody>''' + "".join(rows) + '''</tbody></table></div>
<p class="small">Pinned-content audit (29 Oct 2026): 10 comparison rasters from nine sites contain eight distinct in-footprint prediction contents. GEMSDOE25 and GEMSDOE30 are identical in-footprint (44,090 dots; only outside encoding differs). A separate GEMSDOE28 alternate, <code>gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif</code> (40,199 dots), is identical to GEMSDOE31's h27-4 file; it is <strong>not</strong> GEMSDOE28's h36-1 historical-best (37,660 dots). GEMSDOE32 B2 is a strict subset of the 44,090-dot D2.8 raster with 6,436 catalogue-near dots removed. Evidence: <a href="downloads/focus9_content_checks_20261028.json">pinned content-check JSON</a>.</p>
<p class="small"><a href="downloads/focus9-decision-table-20261027.json">Full decision data</a> · <a href="downloads/focus-sites-pairwise-uniqueness.json">72 directed pairwise checks</a> · <a href="research/focus9-executive-summary-20261027.md">Historical audit and later updates</a></p>
</section><!-- FOCUS9_DECISION:END -->'''


def historical_lane(card: dict, card_filename: str, root: Path) -> dict:
    sub, h, best = card["submission"], card["holdout"], card["best_arm"]
    if (card["verdict"] != "negative" or card.get("slot_approved", False) is not False
            or card.get("ok_to_download_and_submit", False) is not False
            or sub.get("slot_approved", False) is not False
            or sub.get("ok_to_download_and_submit", False) is not False):
        raise ValueError(f"Archived {card['lane_id']} is not explicitly negative")
    for key, digest in (("file", "sha256"), ("zip", "zip_sha256")):
        if sha(root / sub[key]) != sub[digest]:
            raise ValueError(f"Historical artifact hash mismatch: {sub[key]}")
    return {
        "lane_id": card["lane_id"], "best_arm": best, "verdict": "negative",
        "slot_approved": False, "ok_to_download_and_submit": False,
        "ok_to_download_for_research": True, "tif_path": sub["file"].removeprefix("docs/"),
        "tif_sha256": sub["sha256"], "zip_path": sub["zip"].removeprefix("docs/"),
        "zip_sha256": sub["zip_sha256"], "holdout_label": "HOLDOUT-DTI",
        "holdout_dti": h["arms"][best]["dti"], "ci95": h["arms"][best]["ci95"],
        "evaluator_version": h["evaluator_version"],
        "withheld_positives": h["n_withheld_positive_pixels"],
        "run_card": f"downloads/{card_filename}",
    }


def validate_gsewc36_evidence(root: Path) -> dict:
    """Validate the latest unassigned research experiment without promoting it."""
    root = Path(root)
    card_path = root / "evidence/gsewc36_run_card_20261029.json"
    card = load(card_path)
    if (card.get("schema") != "gemsdoe36.experiment-run-card.v1"
            or card.get("experiment_id") != "GSEWC36-EXP1"
            or card.get("status") != "stopped_registry_dot_overlap"
            or card.get("verdict") != "negative"):
        raise ValueError("GSEWC36 run card is not the recorded negative research result")

    prereg = card.get("preregistration", {})
    prereg_path = root / prereg.get("path", "")
    inputs = card.get("inputs", {})
    manifest_snapshot = root / inputs.get("prepared_manifest_snapshot", "")
    restore_snapshot = root / inputs.get("restore_receipt_snapshot", "")
    current_restore_snapshot = root / inputs.get("current_restore_receipt_snapshot", "")
    checks = (
        (prereg_path, prereg.get("sha256")),
        (root / "scripts/run_gsewc36_experiment.py", prereg.get("runner_sha256")),
        (root / "src/gemsdoe36/scale_space.py", prereg.get("candidate_feature_source_sha256")),
        (manifest_snapshot, inputs.get("prepared_manifest_snapshot_sha256")),
        (restore_snapshot, inputs.get("restore_receipt_snapshot_sha256")),
        (current_restore_snapshot, inputs.get("current_restore_receipt_snapshot_sha256")),
    )
    for path, expected in checks:
        if not path.is_file() or not expected or sha(path) != expected:
            raise ValueError(f"GSEWC36 evidence hash mismatch or missing file: {path}")
    if (prereg.get("sha256") != prereg.get("expected_sha256")
            or inputs.get("prepared_manifest_sha256") != sha(manifest_snapshot)
            or inputs.get("restore_receipt_sha256") != sha(restore_snapshot)
            or inputs.get("current_restore_receipt_sha256") != sha(current_restore_snapshot)):
        raise ValueError("GSEWC36 preregistration or at-run inputs are not internally bound")
    prereg_doc = load(prereg_path)
    if (prereg_doc.get("schema") != "gemsdoe36.hypothesis-screen.v1"
            or prereg_doc.get("experiment", {}).get("id") != card["experiment_id"]):
        raise ValueError("GSEWC36 preregistration does not identify the run-card experiment")

    canary = card["feature_canary"]
    canary_gate = card["evaluator"]["feature_canary_gate"]
    if (not canary["features"] or not all(x.get("passed") is True for x in canary["features"])
            or canary_gate.get("all_passed") is not True
            or canary_gate.get("n_features_tested") != len(canary["features"])
            or canary_gate.get("max_two_polarity_auc_candidate", 1) > 0.90
            or canary_gate.get("max_two_polarity_auc_raw19", 1) > 0.90):
        raise ValueError("GSEWC36 feature-alone canary evidence does not pass the preregistered gate")

    results = card["results"]
    baseline, candidate = results["baseline"], results["candidate"]
    delta = results["paired_delta_vs_baseline"]
    if (baseline.get("label_tag") != "HOLDOUT-DTI"
            or candidate.get("label_tag") != "HOLDOUT-DTI"
            or baseline.get("evaluator_version") != card["evaluator"]["version"]
            or candidate.get("evaluator_version") != card["evaluator"]["version"]
            or candidate.get("withheld_positives_px") != card["holdout_plan"]["withheld_positive_pixels"]
            or candidate.get("withheld_positives_px") != 60988
            or abs((candidate["pooled_16block_dti"] - baseline["pooled_16block_dti"])
                   - delta["delta_point"]) > 1e-9
            or not (delta["delta_ci95_lo"] <= 0 <= delta["delta_ci95_hi"])
            or results.get("scientific_holdout_gate_passed") is not False
            or results.get("projection_or_leaderboard_score") is not None):
        raise ValueError("GSEWC36 HOLDOUT-DTI values or negative promotion gate are inconsistent")

    registry = card["registry_gate"]
    dots = registry["oof_dot_overlap_within_3px"]
    if (registry.get("surface_gate_passed") is not True
            or registry.get("dot_gate_passed_for_oof_diagnostic") is not False
            or registry.get("final_submission_dots_generated") is not False
            or registry.get("all_198_registry_rasters_checked") is not False
            or dots["overlap_dots"] / dots["candidate_oof_dots"] <= registry["literal_overlap_limit"]
            or registry.get("candidate_oof_surface_abs_spearman_rho", 1)
                >= registry.get("literal_abs_rank_correlation_limit", 0.90)):
        raise ValueError("GSEWC36 registry evidence does not preserve the literal early-stop result")
    submission = card["submission"]
    if (submission.get("submission_tif_written") is not False
            or submission.get("submission_zip_written") is not False
            or submission.get("writer_invoked") is not False
            or submission.get("validator_output") is not None
            or submission.get("raster_sha256") is not None
            or submission.get("name") is not None or submission.get("note") is not None
            or submission.get("weekly_slot_selected") is not False):
        raise ValueError("GSEWC36 evidence must remain research-only with no TIFF or slot")
    return card


def gsewc_public_projection(card: dict, card_path: Path) -> dict:
    """Small public projection: research result only, never a submission candidate."""
    baseline = card["results"]["baseline"]
    candidate = card["results"]["candidate"]
    delta = card["results"]["paired_delta_vs_baseline"]
    registry = card["registry_gate"]
    return {
        "experiment_id": card["experiment_id"], "lane_assignment": None,
        "verdict": card["verdict"], "holdout_label": candidate["label_tag"],
        "evaluator_version": candidate["evaluator_version"],
        "withheld_positives": candidate["withheld_positives_px"],
        "baseline_dti": baseline["pooled_16block_dti"],
        "baseline_ci95": baseline["pooled_16block_ci95"],
        "candidate_dti": candidate["pooled_16block_dti"],
        "candidate_ci95": candidate["pooled_16block_ci95"],
        "paired_delta": delta["delta_point"],
        "paired_delta_ci95": [delta["delta_ci95_lo"], delta["delta_ci95_hi"]],
        "registry_surface_abs_spearman": registry["candidate_oof_surface_abs_spearman_rho"],
        "registry_oof_dot_overlap_fraction": registry["oof_dot_overlap_within_3px"]["fraction"],
        "literal_dot_overlap_limit": registry["literal_overlap_limit"],
        "oof_dot_gate_passed": registry["dot_gate_passed_for_oof_diagnostic"],
        "submission_tif_written": card["submission"]["submission_tif_written"],
        "slot_selected": card["submission"]["weekly_slot_selected"],
        "run_card": "downloads/gsewc36-run-card.json", "run_card_sha256": sha(card_path),
    }


def render_page(table_html: str, card: dict, s2d: dict, archive_audit: dict,
                gsewc: dict, *, title: str) -> str:
    h = card["holdout"]["historical_reference_not_rerun"]
    b = card["registry"]["reproduced_literal_preflight"]
    s2d_format = next(
        row["validator"] for row in archive_audit["artifacts"]
        if row["validator"]["path"] == card["historical_archive_audit"]["s2d36_exp2_path"]
    )
    tif = s2d["tif_path"]
    gbase = gsewc["results"]["baseline"]
    gcandidate = gsewc["results"]["candidate"]
    gdelta = gsewc["results"]["paired_delta_vs_baseline"]
    greg = gsewc["registry_gate"]
    gcanary = gsewc["evaluator"]["feature_canary_gate"]
    oof_overlap = greg["oof_dot_overlap_within_3px"]
    gsewc_section = f'''<section class="section" id="gsewc36-exp1"><span class="eyebrow">29 October · preregistered research-only test</span><h2>GSEWC36-EXP1: negative; no submission file</h2>
<p>The cross-sensor Gaussian scale-space edge-width feature passed its feature-alone canary (maximum two-polarity AUC {gcanary["max_two_polarity_auc_candidate"]:.6f}; highest raw feature {gcanary["max_two_polarity_auc_raw19"]:.6f}). On the buffered whole-segment holdout ({gsewc["holdout_plan"]["n_segments"]:,} segments, {gcandidate["withheld_positives_px"]:,} withheld positives, <code>{esc(gcandidate["evaluator_version"])}</code>), it measured <strong>HOLDOUT-DTI {gcandidate["pooled_16block_dti"]:.6f}</strong> (95% CI [{gcandidate["pooled_16block_ci95"][0]:.6f}, {gcandidate["pooled_16block_ci95"][1]:.6f}]) versus matched raw-19 B1 at <strong>{gbase["pooled_16block_dti"]:.6f}</strong> (95% CI [{gbase["pooled_16block_ci95"][0]:.6f}, {gbase["pooled_16block_ci95"][1]:.6f}]); paired delta {gdelta["delta_point"]:+.6f} (95% CI [{gdelta["delta_ci95_lo"]:+.6f}, {gdelta["delta_ci95_hi"]:+.6f}]). It did not beat the baseline or same-evaluator best ({gsewc["results"]["same_evaluator_historical_best"]["dti"]:.6f}). These are internal measurements, never leaderboard scores.</p>
<p>The OOF prediction surface passed the first registry comparison (<code>|rho|={greg["candidate_oof_surface_abs_spearman_rho"]:.6f}</code> against reg-052). Its {oof_overlap["overlap_dots"]:,}/{oof_overlap["candidate_oof_dots"]:,} OOF dots ({oof_overlap["fraction"] * 100:.4f}%) were within 3 px of the five-pixel lattice, above the binding 70% limit. This is an OOF diagnostic, not a final-map result; the lattice's geometric lower bound is {greg["mathematical_lower_bound_overlap_at_37654_dots"] * 100:.4f}% at this dot budget. The literal gate is degenerate but remains binding. The scan stopped at reg-052; no full-map fit, final dots, TIFF, ZIP, or validator output exists, and no slot was selected. See the <a href="research/hypothesis-screen-20261029.md">five-hypothesis screen/result</a>, <a href="downloads/gsewc36-run-card.json">machine-readable run card</a>, and <a href="downloads/hypothesis-screen-20261029.json">preregistration JSON</a>.</p>
<p class="small">This user-directed research run did not assign the missing method lane. The earlier pre-run review's “no holdout” statement is a historical snapshot: <a href="research/review-20261029.md">pre-run review</a> · <a href="downloads/session-review-20261029-run-card.json">pre-run status card</a>.</p>
<p class="small">Exact at-run provenance snapshots: <a href="downloads/gsewc36-prepared-manifest-20261029.json">prepared manifest</a> · <a href="downloads/gsewc36-restore-receipt-20261029.json">restore receipt</a> · <a href="downloads/gsewc36-current-restore-receipt-20261029.json">current restore receipt at run time</a>.</p></section>'''
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="GEMSDOE36: negative competition decision, research downloads and evidence.">
<title>{esc(title)} · GEMS DOE 36</title><link rel="stylesheet" href="assets/site.css"></head>
<body><a class="skip-link" href="#main">Skip to main content</a>
<header class="site-header"><a class="brand" href="index.html"><span class="brand-mark" aria-hidden="true">36</span><span>GEMS DOE <span class="small">/ 36</span></span></a>
<nav class="nav" aria-label="Main navigation"><a href="index.html">Decision</a><a href="executive-summary.html">Executive guide</a><a href="research/hypothesis-screen-20261029.md">Current research &amp; result</a><a href="research/review-20261029.md">Earlier audit snapshot</a><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/" target="_blank" rel="noopener">Official leaderboard ↗</a></nav></header>
<main id="main" class="wrap">
<!-- LITERAL_REVIEW:START -->
<section class="verdict verdict-bad" aria-labelledby="decision-title"><span class="eyebrow">Current decision · 29 October 2026</span>
<h1 id="decision-title">DO NOT SUBMIT — no candidate is authorized</h1>
<p class="verdict-sub"><strong>No new candidate TIFF, submission name, note, or approved slot.</strong> GSEWC36-EXP1 was a negative, preregistered research test: HOLDOUT-DTI {gcandidate["pooled_16block_dti"]:.6f} (95% CI [{gcandidate["pooled_16block_ci95"][0]:.6f}, {gcandidate["pooled_16block_ci95"][1]:.6f}]) versus matched B1 {gbase["pooled_16block_dti"]:.6f} (95% CI [{gbase["pooled_16block_ci95"][0]:.6f}, {gbase["pooled_16block_ci95"][1]:.6f}]); paired delta {gdelta["delta_point"]:+.6f} (95% CI [{gdelta["delta_ci95_lo"]:+.6f}, {gdelta["delta_ci95_hi"]:+.6f}]). It did not beat the baseline or same-evaluator best. The OOF surface passed reg-052 rank correlation, but {oof_overlap["fraction"] * 100:.4f}% of OOF dots were within 3 px of its calibration lattice, failing the literal 70% gate. No final map/TIFF or leaderboard score was made. The method paragraph remains unassigned; no lane or slot was selected.</p>
<div class="hero-actions"><a class="button warning" href="downloads/gsewc36-run-card.json">GSEWC36 negative research run card →</a><a class="button secondary" href="research/hypothesis-screen-20261029.md">Hypothesis screen &amp; result →</a><a class="button secondary" href="#focus9-decision">Nine-site table ↓</a></div>
<p class="small">All HOLDOUT-DTI values are internal measurements, not organizer scores. Historical KPL: <strong>0.1647 USER-REPORTED</strong>, without a receipt; 99.17% of its dots overlap reg-052 within 3 px. The lattice makes the literal overlap gate non-discriminating, but the threshold remains binding. See the <a href="downloads/literal-release-review.json">literal-release review</a>.</p>
</section><!-- LITERAL_REVIEW:END -->
<section class="download-strip" aria-label="Research download, not submission"><div><strong>DOWNLOAD: YES · Research downloads only · SUBMIT: NO</strong>
<p>Historical S2D-36 EXP-2: <strong>HOLDOUT-DTI {h['dti']:.6f}</strong>, 95% CI [{h['ci95'][0]:.4f}, {h['ci95'][1]:.4f}], {esc(h['evaluator_version'])}, {h['withheld_positive_pixels']:,} withheld positives. This is prior internal validation, not rerun here or an organizer score. Its reg-052 overlap was 99.48%. SHA-256 <code>{esc(s2d['tif_sha256'])}</code>.</p>
<p><strong>Strict archive-format audit:</strong> this historical zeros-outside TIFF has {s2d_format['finite_outside_bounds']:,} finite values outside the template footprint and fails the strict outside-footprint check. The audit found {sum(bool(row['validator']['passed']) for row in archive_audit['artifacts'])} format-passing and {sum(not bool(row['validator']['passed']) for row in archive_audit['artifacts'])} format-failing historical TIFFs; <strong>0 are promoted</strong>. All remain research-only. <a href="downloads/strict-download-validation-20261029.json">Audit JSON</a>.</p></div>
<a class="button secondary" href="{esc(tif)}" download>Download historical research TIFF</a></section>
{table_html}
{gsewc_section}
<section class="section" id="why-b2"><span class="eyebrow">The reported 0.2778</span><h2>What the raster can—and cannot—tell us</h2>
<p>GEMSDOE32 B2 is the 44,090-dot D2.8 raster with 6,436 catalogue-near dots removed and no dots added. This lineage was reproduced from pinned comparison files; the reported <strong>0.2778 OWNER-REPORTED</strong> has no organizer receipt. Pruning changes spatial coverage and may reduce unsupported positives, but hidden labels and scorer details are not available to attribute the result. It may be beatable, but neither the method nor a score above it is established.</p>
<p>The official 300 m triangular-distance Tversky metric weights false positives at 0.2 and false negatives at 0.8; it does not establish the previously claimed organizer masking mechanism. <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Official problem and metric</a>.</p>
</section>
<section class="section" id="novelty"><span class="eyebrow">Literal registry protocol · fail closed</span><h2>The overlap check is degenerate against reg-052</h2>
<p>The SHA-pinned reg-052 comparison is a regular 5-pixel lattice covering 99.8713% of footprint cells within 3 pixels ({b['covered_pixels_within_3px']:,} of {b['footprint_pixels']:,}). It forces at least {b['minimum_overlapping_dots']:,}/{b['candidate_distinct_dots']:,} candidate dots ({b['minimum_overlap_fraction'] * 100:.2f}%) within 3 px, above the literal 70% limit; the forced-stop count is {b['first_dot_count_forced_over_70_percent']:,} dots. Because it tiles almost the whole footprint, this criterion cannot distinguish a duplicate from a different in-footprint detector. It is a gate-design defect, <strong>not proof of candidate duplication</strong>. Under the current protocol no candidate is authorized until this issue is resolved without unilateral threshold changes. The other 11 rasters in the local registry coverage audit cover 6–28% within 3 px. Hash-pinned owner mirrors are not organizer-authenticated. <a href="downloads/registry-coverage-audit-20261028.json">Download coverage audit</a>.</p>
<p>The shared novelty comparison also accepts a same-shaped raster with wrong CRS/transform; <a href="https://github.com/buffedlizard55-lab/GEMSDOE24/issues/77">reported upstream</a>. The shared template has not been privately patched; do not treat its output as promotion proof until fixed.</p>
</section>
<section class="section" id="how-to-submit"><span class="eyebrow">Future only · no slot selected</span><h2>Conditional submission guide</h2>
<ol class="steps"><li><div><h3>Prove eligibility first</h3><p>For a future assigned lane, run per-feature leakage canaries, whole buffered-segment holdout, and the literal surface and final-dot registry tests using the repaired shared template. Beat the comparable holdout best. A separate selector—not this site—must choose a slot.</p></div></li>
<li><div><h3>Validate the actual file</h3><p>Only after all gates pass, check a single-band float32 GeoTIFF (.tif), or a .zip file containing a single GeoTIFF: CRS, shape, and geotransform must match the sample; finite values inside the footprint must be in [0, 1]. The official sample uses NaN outside the footprint. Record both the NaN-aware and whole-array diagnostics and verify the current portal instructions; a local check is not portal acceptance.</p></div></li>
<li><div><h3>Investigate the reported range error</h3><p>For “Predicted values must be in range [0, 1]”, inspect finite minimum/maximum, non-finite values and nodata separately inside and outside the footprint with the shared writer/validator. The rejected file and portal validation trace are unavailable, so the cause is unknown. Do not assume zero outside fixes it.</p></div></li>
<li><div><h3>Selector and receipt</h3><p>After promotion and a separate selection, check the submission-page cap (official rules: three weekly slots), use the selected candidate's unique name and ≤140-character note, and archive the submission-page receipt. The rules select one submission for both prize rounds; a report without that receipt is not ORGANIZER-CONFIRMED.</p></div></li></ol>
<p><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">Competition</a> · <a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">Official rules</a> · <a href="https://github.com/drivendataorg/gems-prize-reference-solution">Reference solution</a></p>
</section>
</main><footer class="site-footer wrap"><p>Core Values: <strong>Maximize P(Win)</strong> &amp; <strong>Own the Outcome</strong>. No score projection is presented as a score. <a href="AI_DISCLOSURE.md">AI disclosure</a>.</p></footer></body></html>'''


def publish(root: Path = ROOT) -> None:
    root = Path(root)
    docs, evidence = root / "docs", root / "evidence"
    gsewc_path = evidence / "gsewc36_run_card_20261029.json"
    gsewc_card = validate_gsewc36_evidence(root)
    gsewc_projection = gsewc_public_projection(gsewc_card, gsewc_path)
    card_path = evidence / "session_review_20261029_run_card.json"
    card = load(card_path)
    nulls = ("raster_sha256", "submission_name", "submission_note")
    holdout_nulls = ("evaluator_version", "withheld_positive_pixels", "dti", "ci95")
    validator_nulls = ("no_nan_inside_footprint", "values_in_0_1", "crs_shape_transform_match")
    if (card.get("verdict") != "negative" or card.get("slot_approved") is not False
            or card.get("slot_selected") is not False
            or any(k not in card or card[k] is not None for k in nulls)
            or any(k not in card["holdout"] or card["holdout"][k] is not None for k in holdout_nulls)
            or any(k not in card["validator_output"] or card["validator_output"][k] is not None
                   for k in validator_nulls)
            or card["registry"]["new_surface_rank_correlation"] is not None
            or card["registry"]["new_candidate_final_dot_overlap"] is not None
            or card["validator_output"]["new_raster_generated"] is not False):
        raise ValueError("The current review must be negative with no candidate or selected slot")
    archive_audit = load(evidence / "downloads_validation_latest.json")
    archive_status = card.get("historical_archive_audit", {})
    s2d_audit = next((row for row in archive_audit.get("artifacts", [])
                      if row.get("validator", {}).get("path") == archive_status.get("s2d36_exp2_path")), None)
    passes = sum(bool(row.get("validator", {}).get("passed")) for row in archive_audit.get("artifacts", []))
    failures = len(archive_audit.get("artifacts", [])) - passes
    if (s2d_audit is None or archive_status.get("strict_outside_footprint_required") is not True
            or archive_status.get("audited_utc") != archive_audit.get("audited_utc")
            or archive_status.get("template_sha256") != archive_audit.get("template_sha256")
            or archive_status.get("audited_historical_tiffs") != len(archive_audit["artifacts"])
            or archive_status.get("strict_format_passes") != passes
            or archive_status.get("strict_format_failures") != failures
            or archive_status.get("promoted") != 0 or archive_audit.get("promoted_count") != 0
            or any(row.get("submit_ready") is not False for row in archive_audit["artifacts"])
            or s2d_audit["validator"].get("passed") is not False
            or archive_status.get("s2d36_exp2_strict_format_passed") is not False
            or archive_status.get("s2d36_exp2_finite_outside_footprint")
                != s2d_audit["validator"].get("finite_outside_bounds")
            or archive_status.get("s2d36_exp2_reason") != s2d_audit["validator"].get("errors")):
        raise ValueError("Strict historical archive-format audit does not match the current run card")
    literal = load(evidence / "literal_release_review_20261027.json")
    bound_doc = load(evidence / "literal_bound_20261027.json")
    coverage = load(evidence / "registry_coverage_audit_20261028.json")
    bound = bound_doc["bound"]
    proof = card["registry"]["reproduced_literal_preflight"]
    reg052 = next((row for row in coverage["rasters"]
                   if row["file"] == Path(bound_doc["reference_registry_path"]).name), None)
    if (coverage.get("schema_version") != "gemsdoe36.registry-coverage-audit.v1"
            or coverage.get("threshold") != 0.70 or coverage.get("radius_px") != 3
            or coverage.get("template_sha256") != bound_doc["template_sha256"]
            or reg052 is None or reg052.get("sha256") != bound_doc["reference_sha256"]
            or reg052.get("gate_degenerate") is not True
            or reg052.get("coverage_share", 0) < 0.99):
        raise ValueError("Registry coverage audit does not substantiate the current gate caveat")
    fields = {
        "candidate_distinct_dots": "candidate_distinct_dots",
        "footprint_pixels": "footprint_pixels",
        "covered_pixels_within_3px": "covered_pixels",
        "uncovered_pixels": "uncovered_pixels",
        "minimum_overlapping_dots": "minimum_overlapping_dots",
        "minimum_overlap_fraction": "minimum_overlap_fraction",
        "first_dot_count_forced_over_70_percent": "first_dot_count_forced_over_threshold",
    }
    if (literal["verdict"] != "negative" or literal["registry"]["dot_overlap_3px"] <= 0.70
            or card["registry"]["historical_kpl_rechecked_dot_overlap"] != literal["registry"]["dot_overlap_3px"]
            or proof["reference_id"] != bound_doc["reference_id"]
            or proof["reference_sha256"] != bound_doc["reference_sha256"]
            or any(proof[ours] != bound[ref] for ours, ref in fields.items())):
        raise ValueError("Negative literal registry evidence does not match the run card")
    table = load(evidence / "focus9_decision_table_20261027.json")
    historical = load(evidence / "focus_sites_9repo_summary_20261026.json")
    pairs = load(evidence / "focus_sites_pairwise_uniqueness_20261026.json")
    table_html = build_focus_table(table, historical, pairs)
    s2d_card = load(evidence / "s2d36_run_card_20261027.json")
    tcd_card = load(evidence / "tcd36_run_card_20261027.json")
    s2d = historical_lane(s2d_card, "s2d36-run-card.json", root)
    tcd = historical_lane(tcd_card, "tcd36-run-card.json", root)
    h = card["holdout"]["historical_reference_not_rerun"]
    if (s2d["holdout_dti"] != h["dti"] or s2d["ci95"] != h["ci95"]
            or s2d["evaluator_version"] != h["evaluator_version"]
            or s2d["withheld_positives"] != h["withheld_positive_pixels"]):
        raise ValueError("Historical holdout mismatch")

    # Retain historical data, but make every top-level field describe this review.
    current_path = docs / "current-run.json"
    current = load(current_path)
    current.update({
        "schema": "gemsdoe36.current-run.v6", "review_date_utc": card["review_date_utc"],
        "lane_id": None, "verdict": "negative",
        "slot_approved": False, "slot_selected": False, "ok_to_download_and_submit": False,
        "ok_to_download_for_research": True, "research_downloads_only": True,
        "tif_path": None, "tif_sha256": None, "zip_path": None, "zip_sha256": None,
        "holdout_dti": None, "ci95": None, "evaluator_version": None, "withheld_positives": None,
        "submission_name": None, "note": None, "gates": None,
        "score_estimate_scenario_range": None, "run_card": "downloads/session-review-20261029-run-card.json",
        "run_card_sha256": sha(card_path), "superseding_review": "downloads/literal-release-review.json",
        "latest_research_lane_s2d36": s2d, "latest_research_lane_tcd36": tcd,
        "latest_unassigned_research_experiment": gsewc_projection,
    })
    current.pop("kpl36_run_card", None)
    # The predecessor's precise timestamp described its old run, not this review.
    current.pop("updated_utc", None)
    current_path.write_text(json.dumps(current, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    manifest_path = docs / "downloads/submissions_manifest.json"
    manifest = load(manifest_path)
    manifest.update({"slot_approved": False, "current_candidate": None,
                     "run_card": "session-review-20261029-run-card.json"})
    old_kpl = manifest.get("superseded_kpl36_research_candidate")
    if old_kpl is not None:
        old_kpl["submit_ok"] = False
        # The historical note said PROMOTE before literal-registry review.
        # Keep the original in its immutable evidence card, not the live index.
        old_kpl["note"] = "Research only: literal registry overlap fails; no slot authorized."
    # This is explicitly historical; its presence cannot authorize upload.
    manifest["research_candidate"] = {
        "lane": s2d["lane_id"], "file": Path(s2d["tif_path"]).name, "sha256": s2d["tif_sha256"],
        "zip": Path(s2d["zip_path"]).name, "zip_sha256": s2d["zip_sha256"],
        "card": "s2d36-run-card.json", "submit_ok": False, "holdout_dti_LABEL": "HOLDOUT-DTI",
        "holdout_dti": s2d["holdout_dti"], "organizer_score": None,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    for source, target in (
        (gsewc_path, docs / "downloads/gsewc36-run-card.json"),
        (evidence / "hypothesis_screen_20261029.json",
         docs / "downloads/hypothesis-screen-20261029.json"),
        (evidence / "gsewc36_prepared_manifest_at_run_20261029.json",
         docs / "downloads/gsewc36-prepared-manifest-20261029.json"),
        (evidence / "gsewc36_restore_receipt_at_run_20261029.json",
         docs / "downloads/gsewc36-restore-receipt-20261029.json"),
        (evidence / "gsewc36_current_restore_receipt_at_run_20261029.json",
         docs / "downloads/gsewc36-current-restore-receipt-20261029.json"),
        (card_path, docs / "downloads/session-review-20261029-run-card.json"),
        (evidence / "focus9_content_checks_20261028.json",
         docs / "downloads/focus9_content_checks_20261028.json"),
        (evidence / "downloads_validation_latest.json",
         docs / "downloads/strict-download-validation-20261029.json"),
        (evidence / "literal_release_review_20261027.json", docs / "downloads/literal-release-review.json"),
        (evidence / "focus9_decision_table_20261027.json", docs / "downloads/focus9-decision-table-20261027.json"),
        (evidence / "focus_sites_9repo_summary_20261026.json", docs / "downloads/focus9-historical-summary-20261026.json"),
        (evidence / "focus_sites_pairwise_uniqueness_20261026.json", docs / "downloads/focus-sites-pairwise-uniqueness.json"),
        (evidence / "mto36_ninesite_forensics.json", docs / "downloads/focus9-source-integrity.json"),
        (evidence / "s2d36_run_card_20261027.json", docs / "downloads/s2d36-run-card.json"),
        (evidence / "tcd36_run_card_20261027.json", docs / "downloads/tcd36-run-card.json"),
        (evidence / "registry_coverage_audit_20261028.json",
         docs / "downloads/registry-coverage-audit-20261028.json"),
    ):
        copyfile(source, target)
    for name, title in (("index.html", "Decision and evidence"), ("executive-summary.html", "Executive guide")):
        (docs / name).write_text(
            render_page(table_html, card, s2d, archive_audit, gsewc_card, title=title),
            encoding="utf-8",
        )
    print("Built current Pages: GSEWC36 research negative; no candidate TIFF or slot")


def main() -> int:
    publish()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
