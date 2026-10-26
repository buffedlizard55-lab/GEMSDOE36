#!/usr/bin/env python3
"""Fail-closed Pages link/status checks for MTO-36 and six archived lanes.

Does not claim organizer portal acceptance or authenticate historical score claims.
"""

from __future__ import annotations

import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = REPO_ROOT / "docs"
ATVR_CARD = REPO_ROOT / "evidence/atvr36_run_card_20261026.json"
CTRB_CARD = REPO_ROOT / "evidence/h36_ctrb_run_card_20261025.json"
GPS_CARD = REPO_ROOT / "evidence/h36_run_card.json"
LANE36_CARD = DOCS_ROOT / "downloads/lane36_run_card.json"
LANE36_CC = REPO_ROOT / "evidence/lane36_crosscheck.json"
MTO_CARD = REPO_ROOT / "evidence/mto36_run_card_20261026.json"
MOE_CARD = REPO_ROOT / "evidence/moe36_run_card_20261026.json"
WDP_CARD = REPO_ROOT / "evidence/wdp36_run_card_20261026.json"
HVG_CARD = REPO_ROOT / "evidence/hvg36_run_card_20261026.json"
DW_CARD = REPO_ROOT / "evidence/dw36_run_card_20261026.json"
CURRENT_RUN = DOCS_ROOT / "current-run.json"
BOTH_PAGES = ("DO NOT SUBMIT", "Research downloads only", "HOLDOUT-DTI", "ORGANIZER-CONFIRMED")
REQUIRED_PAGES = ("index.html", "executive-summary.html")
FORBIDDEN_COPY = (
    "Projected live score",
    "0.2798",
    "gate-passed candidate",
    "No upload-ready prediction yet",
    "Competition TIFF: not available",
)
EXECUTIVE_COPY = (
    "single-band GeoTIFF (.tif)",
    ".zip file containing a single GeoTIFF",
    "CRS, shape, and geotransform",
    "Predicted values must be in range [0, 1]",
    "three weekly slots",
    "one submission for both prize rounds",
)


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.text_chunks: list[str] = []
        self.blank_targets: list[tuple[str, str]] = []
        self.refresh_target: str | None = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        href = a.get("href") or (a.get("src") if tag in {"img", "script"} else None)
        if tag in {"a", "link", "img", "script"} and href:
            self.links.append(href)
            if tag == "a" and a.get("target") == "_blank":
                self.blank_targets.append((href, a.get("rel", "") or ""))
        if tag == "meta" and (a.get("http-equiv") or "").lower() == "refresh":
            m = re.search(r"url\s*=\s*['\"]?([^;'\"\s]+)", a.get("content") or "", flags=re.I)
            if m:
                self.refresh_target = m.group(1)

    def handle_data(self, data):
        self.text_chunks.append(data)


def _parse(path: Path) -> LinkParser:
    p = LinkParser()
    p.feed(path.read_text(encoding="utf-8"))
    return p


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    errors: list[str] = []
    root = REPO_ROOT / "index.html"
    if not root.is_file():
        errors.append("missing repository-root index.html")
    else:
        rp = _parse(root)
        if rp.refresh_target not in {"docs/", "docs/index.html"}:
            errors.append("repository-root index.html must redirect to docs/")

    parsers = {}
    for page in REQUIRED_PAGES:
        path = DOCS_ROOT / page
        if not path.is_file():
            errors.append(f"missing page docs/{page}")
            continue
        p = _parse(path)
        parsers[page] = p
        for href in p.links:
            u = urlsplit(href)
            if u.scheme or href.startswith(("//", "#")):
                continue
            target = (path.parent / u.path).resolve()
            if target.is_dir():
                target = target / "index.html"
            if not target.is_file():
                errors.append(f"docs/{page}: broken local link {href}")
        for href, rel in p.blank_targets:
            if "noopener" not in rel.split():
                errors.append(f"docs/{page}: target=_blank without rel=noopener: {href}")

    mto = json.loads(MTO_CARD.read_text(encoding="utf-8"))
    moe = json.loads(MOE_CARD.read_text(encoding="utf-8"))
    wdp = json.loads(WDP_CARD.read_text(encoding="utf-8"))
    atvr = json.loads(ATVR_CARD.read_text(encoding="utf-8"))
    ctrb = json.loads(CTRB_CARD.read_text(encoding="utf-8"))
    gps = json.loads(GPS_CARD.read_text(encoding="utf-8"))
    landing = " ".join(parsers.get("index.html", LinkParser()).text_chunks)
    execp = " ".join(parsers.get("executive-summary.html", LinkParser()).text_chunks)
    if (DOCS_ROOT / "index.html").read_text().count('id="focus-sites-title"') != 1:
        errors.append("landing must contain exactly one current focus-site table")
    dw = json.loads(DW_CARD.read_text(encoding="utf-8"))
    if (dw.get("verdict") != "negative" or dw.get("duplicate_stop_stage") != "final"
            or dw.get("raster_sha256") is not None or dw.get("validator_output") is not None
            or dw.get("submit_ok") or dw["registry"]["missing"]
            or dw["registry"]["verified_count"] != dw["registry"]["pinned_count"]
            or not dw["registry"]["final"]["duplicates"]
            or dw["holdout_dti"]["evaluator_version"] != "gems-segment-pooled-v1"):
        errors.append("DW36 latest negative duplicate-stop evidence inconsistent")
    public_dw = DOCS_ROOT / "downloads/dw36-run-card.json"
    if not public_dw.is_file() or public_dw.read_bytes() != DW_CARD.read_bytes():
        errors.append("DW36 public card missing or not identical to run card")
    if list((DOCS_ROOT / "downloads").glob("gemsdoe36-dw36*.tif")):
        errors.append("DW36 duplicate stop must not publish TIFF")
    for page, text in (("index.html", landing), ("executive-summary.html", execp)):
        if "LATEST EXPERIMENT: NO NEW TIFF" not in text or "DW36" not in text:
            errors.append(f"docs/{page} missing DW36 duplicate stop")

    # Verify ATVR-36 bundle on disk & pages
    atvr_tif = DOCS_ROOT / "downloads/gemsdoe36-atvr36-20261026.tif"
    atvr_zip = DOCS_ROOT / "downloads/gemsdoe36-atvr36-20261026.zip"
    for f, exp_sha in (
        (atvr_tif, atvr["raster_sha256"]),
        (atvr_zip, atvr["zip_sha256"]),
    ):
        if not f.is_file():
            errors.append(f"missing ATVR-36 download {f.name}")
        elif _sha(f) != exp_sha:
            errors.append(f"SHA-256 mismatch for {f.name}")
    if len(atvr["submission_note"]) > 140:
        errors.append("ATVR-36 note exceeds 140 characters")

    # Verify H36-CTRB bundle on disk & pages
    ctrb_sub = ctrb["submission"]
    ctrb_zeros = DOCS_ROOT / "downloads" / ctrb_sub["zeros_filename"]
    ctrb_nan = DOCS_ROOT / "downloads" / ctrb_sub["companion_nan_name"]
    ctrb_zip = DOCS_ROOT / "downloads" / ctrb_sub["zip_archive_name"]
    for f, exp_sha in (
        (ctrb_zeros, ctrb_sub["raster_sha256"]),
        (ctrb_nan, ctrb_sub["companion_nan_sha256"]),
        (ctrb_zip, ctrb_sub["zip_sha256"]),
    ):
        if not f.is_file():
            errors.append(f"missing H36-CTRB download {f.name}")
        elif _sha(f) != exp_sha:
            errors.append(f"SHA-256 mismatch for {f.name}")
    if len(ctrb_sub["note"]) > 140:
        errors.append("H36-CTRB note exceeds 140 characters")

    # Verify H36-GPS bundle on disk & pages
    r = gps["raster"]
    gps_zeros = REPO_ROOT / r["zeros_tif"]
    for key, rel in (("zeros_sha256", "zeros_tif"), ("nan_sha256", "nan_tif"), ("zip_sha256", "zip")):
        f = REPO_ROOT / r[rel]
        if not f.is_file():
            errors.append(f"missing H36-GPS download {r[rel]}")
        elif _sha(f) != r[key]:
            errors.append(f"SHA-256 mismatch for {r[rel]}")
    if len(gps["submission"]["note"]) > 140:
        errors.append("H36-GPS note exceeds 140 characters")

    any_ok = (
        (wdp["verdict"] == "promote")
        or (atvr["verdict"] == "promote")
        or (ctrb["verdict"] == "promote")
        or (gps["verdict"] == "promote")
    )
    must = [
        wdp["submission_file"],
        wdp["raster_sha256"],
        wdp["submission_note"],
        Path(mto["download"]["tif"]).name,
        mto["raster_sha256"],
        mto["submission_note"],
        moe["submission_note"],
        moe["raster_sha256"],
        atvr_tif.name,
        atvr["raster_sha256"],
        atvr["submission_note"],
        ctrb_zeros.name,
        ctrb_sub["raster_sha256"],
        ctrb_sub["note"],
        gps_zeros.name,
        r["zeros_sha256"],
        gps["submission"]["note"],
        "DOWNLOAD: YES",
        "OK TO SUBMIT" if any_ok else "DO NOT SUBMIT",
    ]
    for phrase in must:
        if phrase not in landing:
            errors.append(f"landing page missing: {phrase[:80]}")

    first_screen = landing[: max(1, len(landing) // 4)]
    current_tif = Path(mto["download"]["tif"]).name
    if current_tif not in first_screen or "DO NOT SUBMIT" not in first_screen:
        errors.append(f"current research-only {current_tif} + negative verdict must lead the landing page")

    for phrase in FORBIDDEN_COPY:
        if phrase.lower() in (landing + execp).lower():
            errors.append(f"stale/incorrect claim present: {phrase}")

    for phrase in EXECUTIVE_COPY + (
        wdp["submission_note"],
        wdp["submission_file"],
        wdp["raster_sha256"],
        mto["submission_note"],
        Path(mto["download"]["tif"]).name,
        mto["raster_sha256"],
    ):
        if phrase.lower() not in execp.lower():
            errors.append(f"executive summary missing: {phrase[:80]}")

    for page, text in (("index.html", landing), ("executive-summary.html", execp)):
        for phrase in BOTH_PAGES:
            if phrase not in text:
                errors.append(f"docs/{page}: missing {phrase}")

    if CURRENT_RUN.exists():
        cur = json.loads(CURRENT_RUN.read_text(encoding="utf-8"))
        if (
            cur.get("slot_approved") or cur.get("ok_to_download_and_submit")
            or cur.get("verdict") != "negative" or cur.get("lane_id") != "MTO-36"
            or cur.get("tif_sha256") != mto["raster_sha256"]
            or cur.get("latest_experiment", {}).get("lane_id") != "DW36"
            or cur["latest_experiment"].get("raster_sha256") is not None
            or cur["latest_experiment"].get("ok_to_download_and_submit")
        ):
            errors.append("docs/current-run.json must reflect the MTO-36 negative verdict/hash")
    else:
        errors.append("missing docs/current-run.json")

    new_tif = REPO_ROOT / mto["download"]["tif"]
    new_zip = REPO_ROOT / mto["download"]["zip"]
    if mto["verdict"] != "negative" or mto["submit_ok"] or mto["registry"]["final_dots"]["all_entries_passed_literal"]:
        errors.append("MTO-36 run card must remain a research-only strict duplicate stop")
    for file, expected in ((new_tif, mto["raster_sha256"]), (new_zip, mto["download"]["zip_sha256"])):
        if not file.is_file() or _sha(file) != expected:
            errors.append(f"MTO-36 artifact missing / SHA-256 mismatch: {file.name}")
    if len(mto["submission_note"]) > 140:
        errors.append("MTO-36 submission note exceeds 140 characters")
    if (DOCS_ROOT / "downloads/mto36-run-card.json").read_bytes() != MTO_CARD.read_bytes():
        errors.append("public MTO-36 run-card mirror differs from evidence")
    for file, expected in (
        (DOCS_ROOT / "downloads/gemsdoe36-moe36-exp1-20261026-zeros.tif", moe["raster_sha256"]),
        (DOCS_ROOT / "downloads/gemsdoe36-moe36-exp1-20261026-zeros.zip", moe["zip_sha256"]),
    ):
        if not file.is_file() or _sha(file) != expected:
            errors.append(f"MOE36 artifact missing / SHA-256 mismatch: {file.name}")
    if moe["verdict"] != "negative" or moe["ok_to_download_and_submit"] or moe["registry_uniqueness"]["full_198_raster_crosscheck"]["passed"]:
        errors.append("Archived MOE36 must remain a negative duplicate-flag release")
    if len(moe["submission_note"]) > 140:
        errors.append("MOE36 submission note exceeds 140 characters")
    for file, expected in (
        (DOCS_ROOT / "downloads" / wdp["submission_file"], wdp["raster_sha256"]),
        (DOCS_ROOT / "downloads" / wdp["submission_zip"], wdp["zip_sha256"]),
    ):
        if not file.is_file() or _sha(file) != expected:
            errors.append(f"WDP-36 artifact missing / SHA-256 mismatch: {file.name}")
    if (
        wdp["verdict"] != "negative"
        or wdp["validator_output"]["safe_to_download_and_submit"]
        or wdp["registry_uniqueness"]["final_dots"]["competing_method_passed"]
    ):
        errors.append("Archived WDP-36 must remain a negative duplicate-flag release")
    if len(wdp["submission_note"]) > 140:
        errors.append("WDP-36 submission note exceeds 140 characters")
    wdp_receipt = DOCS_ROOT / "downloads" / (Path(wdp["submission_file"]).stem + ".receipt.json")
    if not wdp_receipt.is_file() or wdp_receipt.read_bytes() != WDP_CARD.read_bytes():
        errors.append("public WDP-36 receipt mirror differs from evidence")

    if not HVG_CARD.is_file():
        errors.append("missing HVG-36 run card in evidence/")
    else:
        hvg = json.loads(HVG_CARD.read_text(encoding="utf-8"))
        hvg_tif = REPO_ROOT / hvg["artifact"]["tif_path"]
        hvg_zip = REPO_ROOT / hvg["artifact"]["zip_path"]
        for file, expected in (
            (hvg_tif, hvg["artifact"]["tif_sha256"]),
            (hvg_zip, hvg["artifact"]["zip_sha256"]),
        ):
            if not file.is_file() or _sha(file) != expected:
                errors.append(f"HVG-36 artifact missing / SHA-256 mismatch: {file.name}")
        if (
            hvg["verdict"] != "negative"
            or hvg["submission"]["ok_to_submit_to_live_portal"]
            or hvg["registry_uniqueness"]["final_dots"]["literal_all_203_passed"]
        ):
            errors.append("HVG-36 must remain a negative research release")
        if len(hvg["submission"]["note"]) > 140:
            errors.append("HVG-36 submission note exceeds 140 characters")
        hvg_mirror = DOCS_ROOT / "downloads/hvg36-run-card.json"
        if not hvg_mirror.is_file() or hvg_mirror.read_bytes() != HVG_CARD.read_bytes():
            errors.append("public HVG-36 run-card mirror differs from evidence")
        for phrase in (hvg_tif.name, hvg["artifact"]["tif_sha256"], hvg["submission"]["note"]):
            if phrase not in landing:
                errors.append(f"landing page missing HVG-36: {phrase[:80]}")
            if phrase not in execp:
                errors.append(f"executive summary missing HVG-36: {phrase[:80]}")
    for page, text in (("index.html", landing), ("executive-summary.html", execp)):
        if re.search(r"(?:0\.\d{3,4}).{0,25}ORGANIZER-CONFIRMED", text, re.I):
            errors.append(f"docs/{page}: numeric historical score incorrectly called organizer-confirmed")

    if LANE36_CARD.exists():
        lc = json.loads(LANE36_CARD.read_text(encoding="utf-8"))
        lf = DOCS_ROOT / "downloads" / lc["raster"]["file"]
        if not lf.is_file() or _sha(lf) != lc["raster"]["sha256"]:
            errors.append("Lane36 download missing or SHA-256 mismatch")
        if lc["raster"]["file"] not in landing:
            errors.append("landing page does not list the Lane36 file")
        cc = json.loads(LANE36_CC.read_text(encoding="utf-8")) if LANE36_CC.exists() else None
        cc_ok = bool(
            cc
            and cc["template_format_valid"]
            and cc["strict_whole_array_0_1"]
            and cc["final_dot_uniqueness_passed"]
        )
        any_ok = any_ok or (lc.get("verdict") == "promote" and lc.get("ok_to_submit") and cc_ok)

    if not any_ok and "OK TO SUBMIT" in landing:
        errors.append("landing page shows OK TO SUBMIT although no file is cleared")

    if errors:
        print("SITE CHECK FAIL")
        for err in errors:
            print(f"- {err}")
        return 1
    print("SITE CHECK PASS — MTO-36 negative research release and 6 archived lanes verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
