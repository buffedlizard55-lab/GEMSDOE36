#!/usr/bin/env python3
"""Check Pages links, research artifact integrity, and the current negative stop.

No score receipt, official TIFF acceptance, or submission is inferred from this
static check. Raster-level archived checks live in the separate release scripts.
"""
from __future__ import annotations

import hashlib
import json
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
STOP = ROOT / "evidence/registry_preflight_run_card_20261026.json"
KPL_CARD_PATH = ROOT / "evidence/kpl36_run_card_20261026.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.blank_targets: list[tuple[str, str]] = []
        self.text: list[str] = []
        self.ids: set[str] = set()
        self.refresh_target: str | None = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        href = a.get("href") or (a.get("src") if tag in {"img", "script"} else None)
        if tag in {"a", "link", "img", "script"} and href:
            self.links.append(href)
            if tag == "a" and a.get("target") == "_blank":
                self.blank_targets.append((href, a.get("rel", "") or ""))
        if tag == "meta" and (a.get("http-equiv") or "").lower() == "refresh":
            match = re.search(r"url\s*=\s*['\"]?([^;'\"\s]+)", a.get("content") or "", flags=re.I)
            if match:
                self.refresh_target = match.group(1)

    def handle_data(self, data):
        self.text.append(data)


def parse(path: Path) -> LinkParser:
    parser = LinkParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


def _validate_current_v3(current: dict, stop: dict, stop_sha: str) -> list[str]:
    errors = []
    if (current.get("schema") != "gemsdoe36.current-run.v3"
            or current.get("lane_id") != stop.get("lane_id")
            or current.get("verdict") != "negative"
            or current.get("slot_approved") is not False
            or current.get("ok_to_download_and_submit") is not False
            or current.get("research_downloads_only") is not True
            or current.get("tif_path") is not None or current.get("tif_sha256") is not None
            or current.get("holdout_dti") is not None):
        errors.append("Current manifest must describe a negative preflight with no candidate or slot")
    if (current.get("run_card") != "downloads/registry-preflight-run-card.json"
            or current.get("run_card_sha256") != stop_sha
            or current.get("registry_preflight") != stop["registry"]["literal_preflight"]["bound"]):
        errors.append("Current manifest is not bound to the recorded preflight proof")
    return errors


def kpl_promote() -> tuple[bool, dict]:
    """KPL-36 promote iff its evidence run card says so and every gate is true."""
    try:
        card = json.loads(KPL_CARD_PATH.read_text())
    except (OSError, ValueError):
        return False, {}
    return bool(card.get("verdict") == "promote" and card.get("gates") and all(card["gates"].values())), card


def validate_current(current: dict, stop: dict, stop_sha: str) -> list[str]:
    """A missing or fabricated candidate cannot be made submit-ready by Pages.

    Schema v6 represents the current negative review and binds its run card;
    every candidate field must be explicitly null. Legacy v3/v5 validation is
    retained for archived manifests, but cannot grant a current v6 slot.
    """
    if current.get("schema") == "gemsdoe36.current-run.v6":
        from publish_current_review import gsewc_public_projection, validate_gsewc36_evidence

        try:
            gsewc_card = validate_gsewc36_evidence(ROOT)
            gsewc_path = ROOT / "evidence/gsewc36_run_card_20261029.json"
            gsewc_expected = gsewc_public_projection(gsewc_card, gsewc_path)
            if current.get("latest_unassigned_research_experiment") != gsewc_expected:
                return ["Current manifest does not match the latest unassigned GSEWC36 research result"]
        except (OSError, ValueError, KeyError, TypeError) as exc:
            return [f"GSEWC36 research evidence invalid: {exc}"]
        card_path = ROOT / "evidence/session_review_20261029_run_card.json"
        try:
            card = json.loads(card_path.read_text())
        except (OSError, ValueError):
            return ["Missing or invalid current negative run card"]
        null_fields = ("lane_id", "tif_path", "tif_sha256", "zip_path", "zip_sha256",
                       "holdout_dti", "ci95", "evaluator_version", "withheld_positives",
                       "submission_name", "note", "score_estimate_scenario_range")
        errors = []
        if (current.get("verdict") != "negative" or current.get("slot_approved") is not False
                or current.get("slot_selected") is not False
                or current.get("ok_to_download_and_submit") is not False
                or current.get("research_downloads_only") is not True
                or any(k not in current or current[k] is not None for k in null_fields)
                or current.get("run_card") != "downloads/session-review-20261029-run-card.json"
                or current.get("run_card_sha256") != sha(card_path)
                or current.get("review_date_utc") != card.get("review_date_utc")):
            errors.append("v6 current manifest must describe the hash-bound negative no-candidate review")
        card_nulls = ("raster_sha256", "submission_name", "submission_note")
        h = card.get("holdout") or {}
        v = card.get("validator_output") or {}
        r = card.get("registry") or {}
        if (card.get("verdict") != "negative" or card.get("slot_approved") is not False
                or card.get("slot_selected") is not False
                or any(k not in card or card[k] is not None for k in card_nulls)
                or any(k not in h or h[k] is not None for k in
                       ("evaluator_version", "withheld_positive_pixels", "dti", "ci95"))
                or any(k not in v or v[k] is not None for k in
                       ("no_nan_inside_footprint", "values_in_0_1", "crs_shape_transform_match"))
                or any(k not in r or r[k] is not None for k in
                       ("new_surface_rank_correlation", "new_candidate_final_dot_overlap"))
                or v.get("new_raster_generated") is not False):
            errors.append("Current run card must remain negative with no new raster or slot")
        previous_path = ROOT / "evidence/previous_current_run_bdc36_20261026.json"
        try:
            previous = json.loads(previous_path.read_text())
        except (OSError, ValueError):
            errors.append("Missing archived BDC-36 manifest")
        else:
            if current.get("previous_current_run_v4_BDC36") != previous:
                errors.append("Archived BDC-36 manifest was modified or lost")
        return errors
    if current.get("schema") != "gemsdoe36.current-run.v5":
        return _validate_current_v3(current, stop, stop_sha)
    errors = []
    promote, card = kpl_promote()
    sub = card.get("submission") or {}
    if (current.get("lane_id") != "KPL-36"
            or current.get("verdict") != card.get("verdict")
            or current.get("slot_approved") is not promote
            or current.get("ok_to_download_and_submit") is not promote
            or current.get("research_downloads_only") is not (not promote)
            or current.get("tif_path") != str(sub.get("file", "")).removeprefix("docs/")
            or current.get("tif_sha256") != sub.get("sha256")
            or current.get("run_card") != "downloads/kpl36-run-card.json"
            or current.get("run_card_sha256") != sha(KPL_CARD_PATH)
            or not isinstance(current.get("holdout_dti"), float)):
        errors.append("v5 current manifest is not bound to the KPL-36 run card / gates")
    prev = current.get("previous_current_run_v4_BDC36")
    if (not isinstance(prev, dict) or prev.get("lane_id") != "BDC-36"
            or prev.get("verdict") != "negative" or prev.get("slot_approved")
            or prev.get("ok_to_download_and_submit")):
        errors.append("v5 current manifest must preserve the negative BDC-36 v4 manifest")
    return errors


def main() -> int:
    # Reuse the builder's independent card/proof contract rather than accepting a
    # self-consistent but fabricated positive manifest.
    from build_mto_site import (
        additional_archives,
        ensure_csdl_card,
        ensure_parallel_dw,
        ensure_status,
        ensure_stop_card,
        parallel_dw_projection,
    )
    from publish_current_review import (
        build_focus_table,
        historical_lane,
        validate_gsewc36_evidence,
    )

    errors: list[str] = []
    mto = json.loads((ROOT / "evidence/mto36_run_card_20261026.json").read_text())
    hvg = json.loads((ROOT / "evidence/hvg36_run_card_20261026.json").read_text())
    gvsc = json.loads((ROOT / "evidence/gvsc36_run_card_20261026.json").read_text())
    csdl = json.loads((ROOT / "evidence/csdl36_run_card_20261026.json").read_text())
    stop = json.loads(STOP.read_text())
    dw = json.loads((ROOT / "evidence/dw36_run_card_20261026.json").read_text())
    ledger = json.loads((ROOT / "evidence/focus_sites_9repo_summary_20261026.json").read_text())
    try:
        ensure_status(mto, ledger, hvg)
        ensure_stop_card(stop, gvsc)
        ensure_csdl_card(csdl)
        ensure_parallel_dw(dw)
    except (RuntimeError, OSError, KeyError, StopIteration, ValueError) as exc:
        errors.append(f"Release evidence invalid: {exc}")

    try:
        validate_gsewc36_evidence(ROOT)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        errors.append(f"GSEWC36 research evidence invalid: {exc}")

    try:
        focus_table = build_focus_table(
            json.loads((ROOT / "evidence/focus9_decision_table_20261027.json").read_text()),
            ledger,
            json.loads((ROOT / "evidence/focus_sites_pairwise_uniqueness_20261026.json").read_text()),
        )
    except (OSError, ValueError, KeyError) as exc:
        errors.append(f"Focus-9 evidence invalid: {exc}")
        focus_table = None

    root_page = parse(ROOT / "index.html")
    if root_page.refresh_target not in {"docs/", "docs/index.html"}:
        errors.append("Repository root must redirect to docs/")
    for page in ("index.html", "executive-summary.html"):
        path = DOCS / page
        p = parse(path)
        text = " ".join(p.text)
        for href in p.links:
            u = urlsplit(href)
            if href.startswith("#"):
                if u.fragment not in p.ids:
                    errors.append(f"docs/{page}: broken local anchor {href}")
                continue
            if u.scheme or href.startswith("//"):
                continue
            target = (path.parent / u.path).resolve()
            if target.is_dir():
                target /= "index.html"
            if not target.is_file():
                errors.append(f"docs/{page}: broken local link {href}")
        for href, rel in p.blank_targets:
            if "noopener" not in rel.split():
                errors.append(f"docs/{page}: target=_blank without rel=noopener: {href}")
        for phrase in ("DO NOT SUBMIT", "DOWNLOAD: YES", "Research downloads only", "HOLDOUT-DTI",
                       "ORGANIZER-CONFIRMED", "0.2778", "0.1647 USER-REPORTED", "82.34%",
                       "GSEWC36-EXP1", "0.039712", "0.039523", "0.000189", "96.9645%",
                       "GSEWC36 negative research run card"):
            if phrase not in text:
                errors.append(f"docs/{page}: missing {phrase}")
        first_screen = text[: max(1, len(text) // 4)]
        if "DO NOT SUBMIT" not in first_screen:
            errors.append(f"docs/{page}: negative verdict must lead the page")
        if focus_table is None or focus_table not in path.read_text():
            errors.append(f"docs/{page}: pinned nine-site decision table differs from source")
        forbidden_phrases = (
            "OK TO SUBMIT", "Projected live score", "0.205–0.238",
            "NaN-outside files are what triggered", "fixes prior portal error",
            "recommended spend of one slot", "4× precision penalty", "portal-safe",
        )
        for forbidden in forbidden_phrases:
            if forbidden.lower() in text.lower():
                errors.append(f"docs/{page}: stale or unsafe claim: {forbidden}")
        if re.search(r"(?:0\.\d{3,4}).{0,25}ORGANIZER-CONFIRMED", text, re.I):
            errors.append(f"docs/{page}: numeric score incorrectly called organizer-confirmed")

    exec_text = " ".join(parse(DOCS / "executive-summary.html").text).lower()
    for term in ("single-band float32 geotiff (.tif)", ".zip file containing a single geotiff",
                 "crs, shape, and geotransform", "predicted values must be in range [0, 1]",
                 "three weekly slots", "one submission for both prize rounds", "nan"):
        if term not in exec_text:
            errors.append(f"executive submission guide missing: {term}")

    current_path = DOCS / "current-run.json"
    if current_path.is_file():
        current = json.loads(current_path.read_text())
        if current.get("schema") != "gemsdoe36.current-run.v6":
            errors.append("Active Pages must use the current negative v6 manifest")
        errors.extend(validate_current(current, stop, sha(STOP)))
        if current.get("parallel_experiments") != [parallel_dw_projection(dw)]:
            errors.append("Current manifest must preserve the separately run negative DW36 experiment")
        for lane, evidence_path, public_name in (
            ("latest_research_lane_s2d36", "evidence/s2d36_run_card_20261027.json", "s2d36-run-card.json"),
            ("latest_research_lane_tcd36", "evidence/tcd36_run_card_20261027.json", "tcd36-run-card.json"),
        ):
            try:
                expected = historical_lane(json.loads((ROOT / evidence_path).read_text()), public_name, ROOT)
                if current.get(lane) != expected:
                    errors.append(f"Historical research summary does not match its card: {lane}")
            except (OSError, ValueError, KeyError) as exc:
                errors.append(f"Historical research summary invalid: {lane}: {exc}")
    else:
        errors.append("Missing docs/current-run.json")
    for original, copy in (
        (ROOT / "evidence/gsewc36_run_card_20261029.json", DOCS / "downloads/gsewc36-run-card.json"),
        (ROOT / "evidence/hypothesis_screen_20261029.json", DOCS / "downloads/hypothesis-screen-20261029.json"),
        (ROOT / "evidence/gsewc36_prepared_manifest_at_run_20261029.json",
         DOCS / "downloads/gsewc36-prepared-manifest-20261029.json"),
        (ROOT / "evidence/gsewc36_restore_receipt_at_run_20261029.json",
         DOCS / "downloads/gsewc36-restore-receipt-20261029.json"),
        (ROOT / "evidence/gsewc36_current_restore_receipt_at_run_20261029.json",
         DOCS / "downloads/gsewc36-current-restore-receipt-20261029.json"),
        (ROOT / "evidence/session_review_20261028_audit_run_card.json", DOCS / "downloads/session-review-20261028-audit-run-card.json"),
        (ROOT / "evidence/session_review_20261029_run_card.json", DOCS / "downloads/session-review-20261029-run-card.json"),
        (ROOT / "evidence/focus9_content_checks_20261028.json", DOCS / "downloads/focus9_content_checks_20261028.json"),
        (ROOT / "evidence/downloads_validation_latest.json", DOCS / "downloads/strict-download-validation-20261029.json"),
        (ROOT / "evidence/focus9_decision_table_20261027.json", DOCS / "downloads/focus9-decision-table-20261027.json"),
        (STOP, DOCS / "downloads/registry-preflight-run-card.json"),
        (ROOT / "evidence/dw36_run_card_20261026.json", DOCS / "downloads/dw36-run-card.json"),
        (ROOT / "evidence/mto36_run_card_20261026.json", DOCS / "downloads/mto36-run-card.json"),
        (ROOT / "evidence/hvg36_run_card_20261026.json", DOCS / "downloads/hvg36-run-card.json"),
        (ROOT / "evidence/gvsc36_run_card_20261026.json", DOCS / "downloads/gvsc36-run-card.json"),
        (ROOT / "evidence/csdl36_run_card_20261026.json", DOCS / "downloads/csdl36-run-card.json"),
        (ROOT / "evidence/focus_sites_9repo_summary_20261026.json", DOCS / "downloads/focus9-verified-source-ledger.json"),
        (ROOT / "evidence/focus_sites_pairwise_uniqueness_20261026.json", DOCS / "downloads/focus-sites-pairwise-uniqueness.json"),
        (ROOT / "evidence/mto36_ninesite_forensics.json", DOCS / "downloads/focus9-source-integrity.json"),
        (ROOT / "evidence/lane36_crosscheck.json", DOCS / "downloads/lane36-crosscheck.json"),
        (ROOT / "evidence/moe36_run_card_20261026.json", DOCS / "downloads/moe36-run-card.json"),
        (ROOT / "evidence/atvr36_run_card_20261026.json", DOCS / "downloads/atvr36-run-card.json"),
        (KPL_CARD_PATH, DOCS / "downloads/kpl36-run-card.json"),
        (ROOT / "evidence/tcd36_run_card_20261027.json", DOCS / "downloads/tcd36-run-card.json"),
        (ROOT / "evidence/s2d36_run_card_20261027.json", DOCS / "downloads/s2d36-run-card.json"),
    ):
        if not copy.is_file() or original.read_bytes() != copy.read_bytes():
            errors.append(f"Pages JSON mirror differs from evidence: {copy}")

    manifest = json.loads((DOCS / "downloads/submissions_manifest.json").read_text())
    if (manifest.get("current_candidate") is not None or manifest.get("slot_approved") is not False
            or manifest.get("research_candidate", {}).get("submit_ok") is not False
            or len(manifest.get("archived_research_only", [])) != 9
            or any(x.get("submit_ok") is not False for x in manifest["archived_research_only"])):
        errors.append("Downloads manifest must be negative with no current candidate")

    try:
        older = additional_archives()  # verifies all legacy TIFF/ZIP/NaN hashes and Lane36 conflict
        if manifest["archived_research_only"][3:] != older:
            errors.append("Downloads manifest differs from the verified archived lanes")
        for item in older:
            if item["zip"] is not None:
                with zipfile.ZipFile(DOCS / "downloads" / item["zip"]) as zf:
                    if (zf.namelist() != [item["file"]]
                            or hashlib.sha256(zf.read(item["file"])).hexdigest() != item["sha256"]):
                        errors.append(f"Archived ZIP does not match TIFF: {item['zip']}")
    except (RuntimeError, OSError, KeyError, ValueError) as exc:
        errors.append(f"Archived research evidence invalid: {exc}")

    # Preserve hash/ZIP integrity checks for the displayed research bundles.
    tcd = json.loads((ROOT / "evidence/tcd36_run_card_20261027.json").read_text())
    s2d = json.loads((ROOT / "evidence/s2d36_run_card_20261027.json").read_text())
    artifacts = [
        (ROOT / s2d["submission"]["file"], ROOT / s2d["submission"]["zip"], s2d["submission"]["sha256"]),
        (ROOT / tcd["submission"]["file"], ROOT / tcd["submission"]["zip"], tcd["submission"]["sha256"]),
        (DOCS / "downloads" / csdl["submission"]["zeros_filename"],
         DOCS / "downloads" / csdl["submission"]["zip_archive_name"], csdl["submission"]["raster_sha256"]),
        (DOCS / "downloads" / gvsc["submission"]["zeros_filename"],
         DOCS / "downloads" / gvsc["submission"]["zip_archive_name"], gvsc["submission"]["raster_sha256"]),
        (ROOT / hvg["artifact"]["tif_path"], ROOT / hvg["artifact"]["zip_path"], hvg["artifact"]["tif_sha256"]),
        (ROOT / mto["download"]["tif"], ROOT / mto["download"]["zip"], mto["raster_sha256"]),
    ]
    for tif, archive, expected in artifacts:
        if not tif.is_file() or sha(tif) != expected or not archive.is_file():
            errors.append(f"Missing/mismatched research bundle: {tif.name}")
            continue
        with zipfile.ZipFile(archive) as zf:
            if zf.namelist() != [tif.name] or hashlib.sha256(zf.read(tif.name)).hexdigest() != expected:
                errors.append(f"Research ZIP does not contain the exact TIFF: {archive.name}")

    for card_rel, files in (
        ("evidence/wdp36_run_card_20261026.json", (("gemsdoe36-wdp36-exp1-20261026-zeros.tif", "raster_sha256"), ("gemsdoe36-wdp36-exp1-20261026-zeros.zip", "zip_sha256"))),
        ("evidence/moe36_run_card_20261026.json", (("gemsdoe36-moe36-exp1-20261026-zeros.tif", "raster_sha256"), ("gemsdoe36-moe36-exp1-20261026-zeros.zip", "zip_sha256"))),
    ):
        card = json.loads((ROOT / card_rel).read_text())
        if card["verdict"] != "negative":
            errors.append(f"Archived card unexpectedly promoted: {card_rel}")
        for filename, hashkey in files:
            path = DOCS / "downloads" / filename
            if not path.is_file() or sha(path) != card[hashkey]:
                errors.append(f"Archived artifact SHA mismatch: {path}")

    snapshot = json.loads((ROOT / "registry/priority_source_snapshot.json").read_text())
    expected_refs = {x["repo"].split("/")[-1]: x["ref"] for x in snapshot["sources"]}
    if json.loads((DOCS / "data/focus-refs.json").read_text()) != expected_refs:
        errors.append("Source-feed pinned refs differ from audited snapshot")
    js = (DOCS / "assets/live-feed.js").read_text()
    if "api.github.com" not in js or "data/focus-refs.json" not in js or "drivendata.org" in js:
        errors.append("Source feed must check GitHub freshness only, not scrape the leaderboard")

    if errors:
        print("Site check FAILED:\n- " + "\n- ".join(errors))
        return 1
    print("Site check passed: negative release status, GSEWC36 result, nine-site evidence, links and research bundles verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
