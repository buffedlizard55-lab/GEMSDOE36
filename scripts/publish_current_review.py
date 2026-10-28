#!/usr/bin/env python3
"""Publish the current negative review. Never authorize a submission slot.

Historical TIFFs and evidence remain available, but the only current run is the
no-candidate 28 October review. All site entrypoints delegate here so rebuilding
cannot resurrect an obsolete upload instruction or overwrite a later lane.
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
    return '''<!-- FOCUS9_DECISION:START -->
<section class="section" id="focus9-decision" aria-labelledby="focus-title">
<div class="section-head"><div><span class="eyebrow">Pinned snapshot · nine sites</span><h2 id="focus-title">Historical files, not submission choices</h2></div></div>
<p>These are the highest reported files in the pinned historical snapshot, not a live ranking. Each fails uniqueness against at least one of the other eight. A nine-site check alone cannot establish global registry uniqueness. Scores are owner/user-reported; no submission-page receipt is archived. Additional results transcribed from the owner-supplied prompt are in the evidence, not authenticated receipts.</p>
<div class="table-wrap"><table><caption class="small">Research and provenance links only; no new leaderboard estimate is defensible</caption>
<thead><tr><th>Site</th><th>Historical file &amp; SHA-256 prefix</th><th>Reported score / estimate</th><th>Unique vs 8?</th><th>Action</th></tr></thead><tbody>''' + "".join(rows) + '''</tbody></table></div>
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


def render_page(table_html: str, card: dict, s2d: dict, *, title: str) -> str:
    h = card["holdout"]["historical_reference_not_rerun"]
    b = card["registry"]["reproduced_literal_preflight"]
    tif = s2d["tif_path"]
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="GEMSDOE36: negative competition decision, research downloads and evidence.">
<title>{esc(title)} · GEMS DOE 36</title><link rel="stylesheet" href="assets/site.css"></head>
<body><a class="skip-link" href="#main">Skip to main content</a>
<header class="site-header"><a class="brand" href="index.html"><span class="brand-mark" aria-hidden="true">36</span><span>GEMS DOE <span class="small">/ 36</span></span></a>
<nav class="nav" aria-label="Main navigation"><a href="index.html">Decision</a><a href="executive-summary.html">Executive guide</a><a href="research/review-20261028.md">Research &amp; sources</a><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/" target="_blank" rel="noopener">Official leaderboard ↗</a></nav></header>
<main id="main" class="wrap">
<!-- LITERAL_REVIEW:START -->
<section class="verdict verdict-bad" aria-labelledby="decision-title"><span class="eyebrow">Current decision · 28 October 2026</span>
<h1 id="decision-title">DO NOT SUBMIT — no candidate is authorized</h1>
<p class="verdict-sub"><strong>No new candidate TIFF, submission name, note, or approved slot.</strong> The designated method paragraph is missing. The literal 70% check is degenerate against reg-052's near-regular 5-pixel lattice; it blocks candidates at the historical density but does not prove an untested candidate is a duplicate. The current run is <strong>negative</strong>; a future selector is separate from validation.</p>
<div class="hero-actions"><a class="button warning" href="downloads/session-review-20261028-audit-run-card.json">Current negative JSON run card →</a><a class="button secondary" href="research/review-20261028.md">Audit, hypotheses &amp; sources →</a><a class="button secondary" href="#focus9-decision">Nine-site table ↓</a></div>
<p class="small">Historical KPL: <strong>0.1647 USER-REPORTED</strong>, without a receipt; 99.17% of its dots overlap reg-052 within 3 px. See the <a href="downloads/literal-release-review.json">literal-release review</a>.</p>
</section><!-- LITERAL_REVIEW:END -->
<section class="download-strip" aria-label="Research download, not submission"><div><strong>DOWNLOAD: YES · Research downloads only · SUBMIT: NO</strong>
<p>Historical S2D-36 EXP-2: <strong>HOLDOUT-DTI {h['dti']:.6f}</strong>, 95% CI [{h['ci95'][0]:.4f}, {h['ci95'][1]:.4f}], {esc(h['evaluator_version'])}, {h['withheld_positive_pixels']:,} withheld positives. This is prior internal validation, not rerun here or an organizer score. Its reg-052 overlap was 99.48%. SHA-256 <code>{esc(s2d['tif_sha256'])}</code>.</p></div>
<a class="button secondary" href="{esc(tif)}" download>Download historical research TIFF</a></section>
{table_html}
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
    card_path = evidence / "session_review_20261028_audit_run_card.json"
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
        "score_estimate_scenario_range": None, "run_card": "downloads/session-review-20261028-audit-run-card.json",
        "run_card_sha256": sha(card_path), "superseding_review": "downloads/literal-release-review.json",
        "latest_research_lane_s2d36": s2d, "latest_research_lane_tcd36": tcd,
    })
    current.pop("kpl36_run_card", None)
    # The predecessor's precise timestamp described its old run, not this review.
    current.pop("updated_utc", None)
    current_path.write_text(json.dumps(current, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    manifest_path = docs / "downloads/submissions_manifest.json"
    manifest = load(manifest_path)
    manifest.update({"slot_approved": False, "current_candidate": None,
                     "run_card": "session-review-20261028-audit-run-card.json"})
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
        (card_path, docs / "downloads/session-review-20261028-audit-run-card.json"),
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
        (docs / name).write_text(render_page(table_html, card, s2d, title=title), encoding="utf-8")
    print("Built current Pages: NEGATIVE; no candidate TIFF, submission name, or slot")


def main() -> int:
    publish()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
