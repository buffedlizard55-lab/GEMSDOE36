import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def test_focus9_decision_table_is_bound_to_pinned_source_evidence():
    table = load("evidence/focus9_decision_table_20261027.json")
    historical = load("evidence/focus_sites_9repo_summary_20261026.json")
    uniqueness = load("evidence/focus_sites_pairwise_uniqueness_20261026.json")

    expected_sites = {
        "GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
        "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36",
    }
    entries = {item["site"]: item for item in table["entries"]}
    assert set(entries) == expected_sites
    assert table["decision"] == "negative"
    assert table["approved_submission"] is None
    assert table["leaderboard_estimate"] is None
    assert table["generated_submission_this_session"] is False

    historical_by_site = {
        item["site"]: item["highest_historical_submission"]
        for item in historical["focus_sites"]
    }
    assert set(historical_by_site) == expected_sites
    for site, entry in entries.items():
        best = entry["historical_best"]
        source = historical_by_site[site]
        pair = uniqueness["site_summary"][site]
        assert best["file"] == source["name"]
        assert best["url"] == source["pinned_raster_source_url"]
        assert best["sha256"] == source["sha256_full"]
        assert best["reported_score"] == source["score"]
        assert best["max_overlap_3px_vs_other_eight"] == pair["max_overlap_vs_other_eight"]
        assert best["max_abs_spearman_vs_other_eight"] == pair["max_abs_binary_surface_spearman"]
        assert entry["unique_vs_other_eight"] is False
        assert entry["estimated_leaderboard_score"] is None
        assert entry["action"].startswith("DO NOT SUBMIT")
        assert pair["unique_under_parallel_protocol_vs_all_eight"] is False


def test_public_exec_table_is_cautious_and_has_all_nine_rows():
    page = (ROOT / "docs/executive-summary.html").read_text(encoding="utf-8")
    start_marker = "<!-- FOCUS9_DECISION:START -->"
    end_marker = "<!-- FOCUS9_DECISION:END -->"
    assert page.count(start_marker) == page.count(end_marker) == 1
    section = page.split(start_marker, 1)[1].split(end_marker, 1)[0]
    table = load("evidence/focus9_decision_table_20261027.json")
    for entry in table["entries"]:
        assert section.count(f"scope=\"row\">{entry['site']}</th>") == 1
    assert section.count("<strong>DO NOT SUBMIT</strong>") == 9
    assert "Not estimable" in section
    assert "0.2778 OWNER-REPORTED" in section
    assert "no submission-page receipt is archived" in section
    assert "owner-supplied prompt" in section
    assert "downloads/focus9-decision-table-20261027.json" in section
    assert "downloads/focus-sites-pairwise-uniqueness.json" in section
    assert "0.205–0.238" not in section


def test_public_machine_readable_mirrors_match_repo_evidence():
    for source, public_copy in (
        ("evidence/focus9_decision_table_20261027.json", "docs/downloads/focus9-decision-table-20261027.json"),
        ("evidence/focus_sites_9repo_summary_20261026.json", "docs/downloads/focus9-historical-summary-20261026.json"),
    ):
        assert load(source) == load(public_copy)


def test_content_audit_identifies_ten_artifacts_and_the_gemsdoe28_alternate():
    audit = load("evidence/focus9_content_checks_20261028.json")
    public = load("docs/downloads/focus9_content_checks_20261028.json")
    historical = load("evidence/focus_sites_9repo_summary_20261026.json")
    assert audit == public
    assert audit["audited_reference_raster_count"] == 10
    assert audit["distinct_in_footprint_contents"] == 8

    pairs = audit["content_duplicate_groups"]
    assert len(pairs) == 2
    by_sites = {frozenset(x["site"] for x in group["artifacts"]): group for group in pairs}
    assert set(by_sites) == {
        frozenset({"GEMSDOE25", "GEMSDOE30"}),
        frozenset({"GEMSDOE28", "GEMSDOE31"}),
    }
    group = by_sites[frozenset({"GEMSDOE28", "GEMSDOE31"})]
    artifacts = {x["site"]: x for x in group["artifacts"]}
    assert artifacts["GEMSDOE28"]["filename"] == (
        "gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif"
    )
    assert artifacts["GEMSDOE31"]["filename"] == (
        "gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif"
    )
    best = next(x["highest_historical_submission"] for x in historical["focus_sites"]
                if x["site"] == "GEMSDOE28")
    assert best["name"].startswith("gems28-h36-1-")
    assert best["dots"] == 37660
    assert best["name"] != artifacts["GEMSDOE28"]["filename"]
