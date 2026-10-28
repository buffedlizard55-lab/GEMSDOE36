"""Archived release integrity and current fail-closed Pages regressions."""
from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_mto_site import (  # noqa: E402
    additional_archives,
    current_branch,
    ensure_parallel_dw,
    ensure_status,
    ensure_stop_card,
    parallel_dw_projection,
    site_table,
    update_readme,
)
from check_site import sha, validate_current  # noqa: E402
from verify_mto_release import verify_all  # noqa: E402


def load(name: str) -> dict:
    return json.loads((ROOT / name).read_text())


@pytest.mark.skipif(
    not (ROOT / "data/raw/sample_submission.tif").is_file(),
    reason="data/raw not restored",
)
def test_archived_negative_release_is_locally_valid_but_not_authorized() -> None:
    if not (ROOT / "data/raw/sample_submission.tif").is_file():
        pytest.skip("requires restored data/raw (run scripts/restore_data.py)")
    result = verify_all(ROOT)
    assert result["passed"], result["errors"]
    assert result["verdict"] == "negative"
    assert result["archived_not_current_candidate"] is True
    assert result["download_research"] is True
    assert result["download_and_submit"] is False


def test_generator_fails_closed_if_old_verdict_or_score_labels_forged() -> None:
    card = load("evidence/mto36_run_card_20261026.json")
    ledger = load("evidence/focus_sites_9repo_summary_20261026.json")
    ensure_status(card, ledger)
    promoted = deepcopy(card)
    promoted["submit_ok"] = True
    with pytest.raises(RuntimeError, match="research download"):
        ensure_status(promoted, ledger)
    fake_score = deepcopy(ledger)
    fake_score["focus_sites"][6]["highest_historical_submission"]["score_label"] = "ORGANIZER-CONFIRMED"
    with pytest.raises(RuntimeError, match="owner-reported"):
        ensure_status(card, fake_score)


def test_working_branch_is_read_from_checkout_not_a_historical_run_card(monkeypatch) -> None:
    class Result:
        stdout = "arena/test-branch\n"

    def fake_run(*args, **kwargs):
        assert args[0] == ["git", "branch", "--show-current"]
        return Result()

    monkeypatch.setattr("build_mto_site.subprocess.run", fake_run)
    assert current_branch() == "arena/test-branch"


def test_nine_pinned_links_labels_and_measured_lineage() -> None:
    ledger = load("evidence/focus_sites_9repo_summary_20261026.json")
    table = site_table(ledger)
    checked = load("evidence/mto36_ninesite_forensics.json")
    assert len(checked["sites"]) == 9
    for site in checked["sites"]:
        assert site["pinned_source_url"] in table
        assert site["sha256"][:12] in table
        label = "USER-REPORTED" if site["site"] == "GEMSDOE24" else "OWNER-REPORTED"
        assert f"{site['reported_score_not_organizer_authenticated']:.4f} {label}" in table
    assert "ORGANIZER-CONFIRMED" not in table
    assert checked["nested_family_crosschecks"]["b2_vs_d28_gt_2px_xor"] == 0
    assert checked["nested_family_crosschecks"]["d28_removed_to_b2"] == 6436
    assert checked["nested_family_crosschecks"]["solo_removed_to_b2"] == 2545


def test_table_does_not_call_estimates_holdouts_or_nine_sites_unique() -> None:
    ledger = load("evidence/focus_sites_9repo_summary_20261026.json")
    table = site_table(ledger)
    assert table.count("<strong>NO</strong>") == 9
    assert "Reported score, no receipt" in table
    assert "Uniqueness vs other 8 pinned sites" in table
    assert "Estimated Score" not in table
    for item in ledger["focus_sites"]:
        assert item["highest_historical_submission"]["name"] in table
    # The current executive table is the source-checked, more concise successor.
    from publish_current_review import build_focus_table

    summary = (ROOT / "docs/executive-summary.html").read_text()
    current_table = build_focus_table(
        load("evidence/focus9_decision_table_20261027.json"), ledger,
        load("evidence/focus_sites_pairwise_uniqueness_20261026.json"),
    )
    assert summary.count("<!-- FOCUS9_DECISION:START -->") == 1
    assert summary.count("<!-- FOCUS9_DECISION:END -->") == 1
    assert current_table in summary


def test_negative_preflight_cannot_be_forged_to_promote():
    stop = load("evidence/registry_preflight_run_card_20261026.json")
    gvsc = load("evidence/gvsc36_run_card_20261026.json")
    ensure_stop_card(stop, gvsc)
    for change in ("submit", "candidate", "score", "bound"):
        fake = deepcopy(stop)
        if change == "submit":
            fake["submit_ok"] = True
        elif change == "candidate":
            fake["candidate"]["raster_sha256"] = "0" * 64
        elif change == "score":
            fake["holdout"]["dti"] = 0.9
        else:
            fake["registry"]["literal_preflight"]["bound"]["minimum_overlapping_dots"] -= 1
        with pytest.raises(RuntimeError):
            ensure_stop_card(fake, gvsc)


def test_current_manifest_binds_negative_card_and_rejects_positive_mutations():
    """Current v6 binds the negative no-candidate review and preserves BDC-36."""
    stop_path = ROOT / "evidence/registry_preflight_run_card_20261026.json"
    stop = json.loads(stop_path.read_text())
    current = load("docs/current-run.json")
    assert current["schema"] == "gemsdoe36.current-run.v6"
    assert validate_current(current, stop, sha(stop_path)) == []
    prev = current["previous_current_run_v4_BDC36"]
    assert prev["lane_id"] == "BDC-36" and prev["verdict"] == "negative"
    for key, value in (("slot_approved", not current["slot_approved"]), ("tif_sha256", "invented"),
                       ("ok_to_download_and_submit", not current["ok_to_download_and_submit"]), ("run_card_sha256", "bad")):
        fake = deepcopy(current)
        fake[key] = value
        assert validate_current(fake, stop, sha(stop_path))
    fake = deepcopy(current)
    fake["previous_current_run_v4_BDC36"]["slot_approved"] = True
    assert validate_current(fake, stop, sha(stop_path))
    fake = deepcopy(current)
    del fake["tif_path"]  # explicit null, not an absent/ambiguous field
    assert validate_current(fake, stop, sha(stop_path))


def test_lane36_self_promotion_cannot_bypass_expanded_registry():
    lane = load("docs/downloads/lane36_run_card.json")
    crosscheck = load("evidence/lane36_crosscheck.json")
    assert lane["verdict"] == "promote" and lane["ok_to_submit"] is True
    assert crosscheck["final_dot_uniqueness_passed"] is False
    assert crosscheck["max_competing_dot_overlap"] > 0.70
    rows = additional_archives()
    assert len(rows) == 6
    assert all(row["submit_ok"] is False for row in rows)
    assert next(row for row in rows if row["lane"] == "Lane36")["sha256"] == crosscheck["sha256"]


def test_builder_preserves_standing_owner_brief_verbatim(tmp_path, monkeypatch):
    import build_mto_site

    fake_readme = tmp_path / "README.md"
    standing = "## Full standing owner brief (historical wording)\n\nExact user text.\n- Preserve me.\n"
    fake_readme.write_text("old introductory status\n\n" + standing)
    monkeypatch.setattr(build_mto_site, "README", fake_readme)
    update_readme(load("evidence/registry_preflight_run_card_20261026.json"),
                  load("evidence/focus_sites_9repo_summary_20261026.json"))
    assert fake_readme.read_text().endswith(standing)


def test_newer_external_holdout_review_is_hash_pinned_and_qualified():
    provenance = load("evidence/gemsdoe24_current_best_review_provenance_20261026.json")
    snapshot = ROOT / provenance["snapshot_path"]
    assert sha(snapshot) == provenance["source_sha256"]
    reviewed = json.loads(snapshot.read_text())["current_recorded_point_best"]
    assert reviewed["holdout"]["label"] == "HOLDOUT-DTI"
    assert reviewed["holdout"]["dti"] == pytest.approx(0.1637924246971501)
    assert reviewed["holdout"]["n_withheld_positive_pixels"] == 60_988
    assert reviewed["holdout"]["evaluator_version"] == "gems-segment-pooled-v1"
    assert reviewed["holdout"]["ci95"]["interval"] == pytest.approx([0.15044621733051888, 0.1773903019943756])
    assert reviewed["verdict"] == "negative" and reviewed["ok_to_submit"] is False
    assert "no independent protocol/paired-gain/novelty certification" in reviewed["scope"]


def test_parallel_dw_remains_negative_and_separate_from_preflight():
    dw = load("evidence/dw36_run_card_20261026.json")
    ensure_parallel_dw(dw)
    current = load("docs/current-run.json")
    assert current["parallel_experiments"] == [parallel_dw_projection(dw)]
    # Current run has no candidate; historical lanes remain separately labeled.
    assert current["previous_current_run_v4_BDC36"]["lane_id"] == "BDC-36"
    assert current["holdout_dti"] is None
    assert current["latest_research_lane_tcd36"]["holdout_dti"] == pytest.approx(0.19416399564770398)
    assert current["latest_research_lane_s2d36"]["holdout_dti"] == pytest.approx(0.2007657135656901)
    assert dw["holdout_dti"]["pooled_candidate"] == pytest.approx(0.06605205634872657)
    fake = deepcopy(dw)
    fake["submit_ok"] = True
    with pytest.raises(RuntimeError, match="negative"):
        ensure_parallel_dw(fake)
    fake = deepcopy(dw)
    fake["registry"]["final"]["max_3px_overlap"] = 0.0
    with pytest.raises(RuntimeError, match="duplicate"):
        ensure_parallel_dw(fake)


def test_published_threshold_copy_includes_the_boundary():
    landing = (ROOT / "docs/index.html").read_text()
    assert "At or above this count the proof forces a stop" in landing
    assert "Above this count the proof forces a stop" not in landing
