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


def _published_digests(root):
    names = ("docs/index.html", "docs/executive-summary.html", "docs/current-run.json",
             "docs/downloads/submissions_manifest.json")
    return [hashlib.sha256((root / name).read_bytes()).hexdigest() for name in names]


def test_current_publisher_is_idempotent_and_preserves_archived_lanes(tmp_path):
    _copy_publish_inputs(tmp_path)
    publisher.publish(tmp_path)
    before = _published_digests(tmp_path)
    publisher.publish(tmp_path)
    assert _published_digests(tmp_path) == before
    current = json.loads((tmp_path / "docs/current-run.json").read_text())
    assert current["schema"] == "gemsdoe36.current-run.v6"
    assert current["slot_approved"] is False and current["tif_path"] is None
    assert current["submission_name"] is None and current["note"] is None
    assert current["latest_research_lane_s2d36"]["verdict"] == "negative"
    assert current["latest_research_lane_tcd36"]["verdict"] == "negative"
    for name in ("index.html", "executive-summary.html"):
        text = (tmp_path / "docs" / name).read_text()
        assert text.index("DO NOT SUBMIT") < text.index("DOWNLOAD: YES")
        assert "0.205–0.238" not in text
        assert "NaN-outside files are what triggered" not in text
        assert "OK TO SUBMIT" not in text
        assert "the cause is unknown" in text


def test_publisher_rejects_promoted_run_card_before_modifying_pages(tmp_path):
    _copy_publish_inputs(tmp_path)
    before = _published_digests(tmp_path)
    path = tmp_path / "evidence/session_review_20261028_audit_run_card.json"
    card = json.loads(path.read_text())
    card["slot_approved"] = True
    path.write_text(json.dumps(card))
    with pytest.raises(ValueError, match="negative"):
        publisher.publish(tmp_path)
    assert _published_digests(tmp_path) == before


def test_publisher_rejects_forged_geometric_bound(tmp_path):
    _copy_publish_inputs(tmp_path)
    before = _published_digests(tmp_path)
    path = tmp_path / "evidence/session_review_20261028_audit_run_card.json"
    card = json.loads(path.read_text())
    card["registry"]["reproduced_literal_preflight"]["minimum_overlapping_dots"] = 1
    path.write_text(json.dumps(card))
    with pytest.raises(ValueError, match="registry evidence"):
        publisher.publish(tmp_path)
    assert _published_digests(tmp_path) == before


def test_publisher_rejects_fabricated_holdout(tmp_path):
    _copy_publish_inputs(tmp_path)
    path = tmp_path / "evidence/session_review_20261028_audit_run_card.json"
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
