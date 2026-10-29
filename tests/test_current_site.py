"""Active site entrypoints must stay negative and preserve historical evidence."""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_kpl_site  # noqa: E402
import build_mto_site  # noqa: E402
import build_s2d_site  # noqa: E402
import build_site  # noqa: E402
import publish_current_review as publisher  # noqa: E402
import publish_literal_review  # noqa: E402
import publish_tcd36_site  # noqa: E402


def test_all_page_entrypoints_delegate_to_current_publisher(monkeypatch):
    for module in (build_site, build_kpl_site, build_s2d_site, publish_tcd36_site,
                   publish_literal_review):
        assert module.main is publisher.main
    assert publish_literal_review.publish is publisher.publish
    monkeypatch.setattr(publisher, "main", lambda: 17)
    assert build_mto_site.main() == 17


def _copy_publish_inputs(tmp_path):
    shutil.copytree(ROOT / "evidence", tmp_path / "evidence")
    shutil.copytree(ROOT / "docs", tmp_path / "docs")
    shutil.copytree(ROOT / "scripts", tmp_path / "scripts")
    shutil.copytree(ROOT / "src", tmp_path / "src")


def _published_digests(root):
    names = ("docs/index.html", "docs/executive-summary.html", "docs/current-run.json",
             "docs/downloads/submissions_manifest.json",
             "docs/downloads/session-review-20261029-run-card.json",
             "docs/downloads/focus9_content_checks_20261028.json",
             "docs/downloads/strict-download-validation-20261029.json",
             "docs/downloads/gsewc36-run-card.json",
             "docs/downloads/hypothesis-screen-20261029.json",
             "docs/downloads/gsewc36-prepared-manifest-20261029.json",
             "docs/downloads/gsewc36-restore-receipt-20261029.json",
             "docs/downloads/gsewc36-current-restore-receipt-20261029.json",
             "docs/downloads/registry-coverage-audit-20261028.json")
    return [hashlib.sha256((root / name).read_bytes()).hexdigest() for name in names]


def test_current_publisher_is_idempotent_and_preserves_archived_lanes(tmp_path):
    _copy_publish_inputs(tmp_path)
    publisher.publish(tmp_path)
    before = _published_digests(tmp_path)
    publisher.publish(tmp_path)
    assert _published_digests(tmp_path) == before
    current = json.loads((tmp_path / "docs/current-run.json").read_text())
    assert current["schema"] == "gemsdoe36.current-run.v6"
    assert current["run_card"] == "downloads/session-review-20261029-run-card.json"
    assert current["slot_approved"] is False and current["tif_path"] is None
    assert current["submission_name"] is None and current["note"] is None
    assert current["latest_research_lane_s2d36"]["verdict"] == "negative"
    assert current["latest_research_lane_tcd36"]["verdict"] == "negative"
    experiment = current["latest_unassigned_research_experiment"]
    assert experiment["experiment_id"] == "GSEWC36-EXP1"
    assert experiment["lane_assignment"] is None and experiment["verdict"] == "negative"
    assert experiment["candidate_dti"] == pytest.approx(0.039712)
    assert experiment["paired_delta_ci95"] == pytest.approx([-0.004191, 0.004111])
    assert experiment["oof_dot_gate_passed"] is False
    assert experiment["submission_tif_written"] is False and experiment["slot_selected"] is False
    card = json.loads((tmp_path / "evidence/session_review_20261029_run_card.json").read_text())
    cache = card["data_readiness"]["numeric_feature_cache"]
    gdr = card["data_readiness"]["gdr_working_csv"]
    assert cache["feature_band_arrays"] == 19 and cache["array_files"] == 21
    assert cache["bytes"] == 957_781_264
    assert gdr["data_rows"] == 27_092
    assert gdr["major_ion_or_trace_element_assays_present"] is False
    assert gdr["prohibited_label_derived_column"] == "dist_known_fault_px"
    strict_audit = json.loads((tmp_path / "evidence/downloads_validation_latest.json").read_text())
    s2d_row = next(row for row in strict_audit["artifacts"]
                   if row["validator"]["path"] == card["historical_archive_audit"]["s2d36_exp2_path"])
    assert card["historical_archive_audit"]["audited_historical_tiffs"] == 23
    assert card["historical_archive_audit"]["strict_format_passes"] == 5
    assert card["historical_archive_audit"]["strict_format_failures"] == 18
    assert card["historical_archive_audit"]["promoted"] == 0
    assert s2d_row["validator"]["passed"] is False
    assert s2d_row["validator"]["finite_outside_bounds"] == 7_111_787
    for name in ("index.html", "executive-summary.html"):
        text = (tmp_path / "docs" / name).read_text()
        assert text.index("DO NOT SUBMIT") < text.index("DOWNLOAD: YES")
        assert "0.205–0.238" not in text
        assert "NaN-outside files are what triggered" not in text
        assert "OK TO SUBMIT" not in text
        assert "the cause is unknown" in text
        assert "gate-design defect" in text
        assert "not proof of candidate duplication" in text
        assert "registry-coverage-audit-20261028.json" in text
        assert "10 comparison rasters from nine sites contain eight distinct" in text
        assert "gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif" in text
        assert "not</strong> GEMSDOE28's h36-1 historical-best (37,660 dots)" in text
        assert "research/review-20261029.md" in text
        assert "session-review-20261029-run-card.json" in text
        assert "7,111,787 finite values outside the template footprint" in text
        assert "0 are promoted" in text
        assert "strict-download-validation-20261029.json" in text
        assert "GSEWC36-EXP1" in text
        assert "GSEWC36 negative research run card" in text
        assert "0.039712" in text and "0.039523" in text
        assert "96.9645%" in text
        assert "pre-run status card" in text


def test_20261029_research_review_covers_scope_and_blockers():
    report = (ROOT / "docs/research/review-20261029.md").read_text()
    for site in ("GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
                 "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"):
        assert f"| {site} |" in report
    assert "10 reference rasters across nine sites and eight distinct in-footprint contents" in report
    assert "The GEMSDOE28 member is the **h27-4 alternate**, not GEMSDOE28's **h36-1 historical-best**" in report
    assert "Leading eligible hypothesis at this pre-run checkpoint:** none" in report
    assert "no new HOLDOUT-DTI was run at that checkpoint" in report
    assert "0.3195 USER-REPORTED" in report
    assert "DOE GDR 1391" in report
    assert "957,781,264 bytes" in report
    assert "27,092 rows" in report
    assert "200 passed, 1 skipped" in report
    assert "No new candidate TIFF" in report
    assert "Historical pre-experiment snapshot" in report
    assert "hypothesis-screen-20261029.md" in report


def test_publisher_rejects_changed_gsewc36_experiment_or_missing_prereg_hash(tmp_path):
    changed_result = tmp_path / "changed-result"
    _copy_publish_inputs(changed_result)
    card_path = changed_result / "evidence/gsewc36_run_card_20261029.json"
    card = json.loads(card_path.read_text())
    card["results"]["candidate"]["pooled_16block_dti"] = 0.9
    card_path.write_text(json.dumps(card))
    with pytest.raises(ValueError, match="HOLDOUT-DTI"):
        publisher.publish(changed_result)

    changed_prereg = tmp_path / "changed-prereg"
    _copy_publish_inputs(changed_prereg)
    card_path = changed_prereg / "evidence/gsewc36_run_card_20261029.json"
    card = json.loads(card_path.read_text())
    card["preregistration"]["sha256"] = "0" * 64
    card_path.write_text(json.dumps(card))
    with pytest.raises(ValueError, match="hash mismatch"):
        publisher.publish(changed_prereg)


def test_publisher_rejects_promoted_run_card_before_modifying_pages(tmp_path):
    _copy_publish_inputs(tmp_path)
    before = _published_digests(tmp_path)
    path = tmp_path / "evidence/session_review_20261029_run_card.json"
    card = json.loads(path.read_text())
    card["slot_approved"] = True
    path.write_text(json.dumps(card))
    with pytest.raises(ValueError, match="negative"):
        publisher.publish(tmp_path)
    assert _published_digests(tmp_path) == before


def test_publisher_rejects_forged_geometric_bound(tmp_path):
    _copy_publish_inputs(tmp_path)
    before = _published_digests(tmp_path)
    path = tmp_path / "evidence/session_review_20261029_run_card.json"
    card = json.loads(path.read_text())
    card["registry"]["reproduced_literal_preflight"]["minimum_overlapping_dots"] = 1
    path.write_text(json.dumps(card))
    with pytest.raises(ValueError, match="registry evidence"):
        publisher.publish(tmp_path)
    assert _published_digests(tmp_path) == before


def test_publisher_rejects_forged_registry_coverage_audit(tmp_path):
    _copy_publish_inputs(tmp_path)
    publisher.publish(tmp_path)
    before = _published_digests(tmp_path)
    path = tmp_path / "evidence/registry_coverage_audit_20261028.json"
    audit = json.loads(path.read_text())
    audit["rasters"][0]["coverage_share"] = 0.2
    path.write_text(json.dumps(audit))
    with pytest.raises(ValueError, match="coverage audit"):
        publisher.publish(tmp_path)
    assert _published_digests(tmp_path) == before


def test_publisher_rejects_fabricated_holdout(tmp_path):
    _copy_publish_inputs(tmp_path)
    path = tmp_path / "evidence/session_review_20261029_run_card.json"
    card = json.loads(path.read_text())
    card["holdout"]["dti"] = 0.9
    path.write_text(json.dumps(card))
    with pytest.raises(ValueError, match="no candidate"):
        publisher.publish(tmp_path)


def test_publisher_rejects_altered_research_tiff_before_modifying_pages(tmp_path):
    _copy_publish_inputs(tmp_path)
    before = _published_digests(tmp_path)
    card = json.loads((tmp_path / "evidence/s2d36_run_card_20261027.json").read_text())
    (tmp_path / card["submission"]["file"]).write_bytes(b"wrong")
    with pytest.raises(ValueError, match="artifact hash mismatch"):
        publisher.publish(tmp_path)
    assert _published_digests(tmp_path) == before
