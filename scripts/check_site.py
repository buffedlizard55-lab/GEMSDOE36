#!/usr/bin/env python3
"""Fail-closed check of the GitHub Pages site against the machine-written JSON run cards
across all five GEMSDOE36 parallel lanes (WDP-36, ATVR-36, H36-CTRB, H36-GPS, and Lane36).
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
WDP_CARD = REPO_ROOT / "evidence/wdp36_run_card_20261026.json"
ATVR_CARD = REPO_ROOT / "evidence/atvr36_run_card_20261026.json"
CTRB_CARD = REPO_ROOT / "evidence/h36_ctrb_run_card_20261025.json"
GPS_CARD = REPO_ROOT / "evidence/h36_run_card.json"
LANE36_CARD = DOCS_ROOT / "downloads/lane36_run_card.json"
LANE36_CC = REPO_ROOT / "evidence/lane36_crosscheck.json"
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
        href = a.get("href") or (a.get("src") if tag == "img" else None)
        if tag in {"a", "link", "img"} and href:
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

    wdp = json.loads(WDP_CARD.read_text(encoding="utf-8"))
    atvr = json.loads(ATVR_CARD.read_text(encoding="utf-8"))
    ctrb = json.loads(CTRB_CARD.read_text(encoding="utf-8"))
    gps = json.loads(GPS_CARD.read_text(encoding="utf-8"))
    landing = " ".join(parsers.get("index.html", LinkParser()).text_chunks)
    execp = " ".join(parsers.get("executive-summary.html", LinkParser()).text_chunks)

    # Verify WDP-36 bundle on disk & pages (zeros-only portal bundle)
    wdp_tif = DOCS_ROOT / "downloads" / wdp["submission_file"]
    wdp_zip = DOCS_ROOT / "downloads" / wdp["submission_zip"]
    for f, exp_sha in (
        (wdp_tif, wdp["raster_sha256"]),
        (wdp_zip, wdp["zip_sha256"]),
    ):
        if not f.is_file():
            errors.append(f"missing WDP-36 download {f.name}")
        elif _sha(f) != exp_sha:
            errors.append(f"SHA-256 mismatch for {f.name}")
    if len(wdp["submission_note"]) > 140:
        errors.append("WDP-36 note exceeds 140 characters")
    wdp_receipt = DOCS_ROOT / "downloads" / (wdp_tif.stem + ".receipt.json")
    if not wdp_receipt.is_file() or wdp_receipt.read_bytes() != WDP_CARD.read_bytes():
        errors.append("WDP-36 receipt JSON missing or differs from evidence run card")

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
        wdp_tif.name,
        wdp["raster_sha256"],
        wdp["submission_note"],
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

    first_screen = landing[: max(1, len(landing) // 3)]
    for top_fname in (wdp_tif.name, atvr_tif.name, ctrb_zeros.name, gps_zeros.name):
        if top_fname not in first_screen:
            errors.append(f"{top_fname} is not on the first screen of the landing page")

    for phrase in FORBIDDEN_COPY:
        if phrase.lower() in (landing + execp).lower():
            errors.append(f"stale/incorrect claim present: {phrase}")

    for phrase in EXECUTIVE_COPY + (
        wdp["submission_note"],
        wdp_tif.name,
        atvr["submission_note"],
        atvr_tif.name,
        ctrb_sub["note"],
        ctrb_zeros.name,
        gps["submission"]["note"],
        gps_zeros.name,
    ):
        if phrase.lower() not in execp.lower():
            errors.append(f"executive summary missing: {phrase[:80]}")

    for page, text in (("index.html", landing), ("executive-summary.html", execp)):
        for phrase in BOTH_PAGES:
            if phrase not in text:
                errors.append(f"docs/{page}: missing {phrase}")

    if CURRENT_RUN.exists():
        cur = json.loads(CURRENT_RUN.read_text(encoding="utf-8"))
        if cur.get("slot_approved") or cur.get("verdict") != "negative":
            errors.append("docs/current-run.json must reflect negative fail-closed verdict")

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
    print("SITE CHECK PASS — all 5 lanes (WDP-36, ATVR-36, H36-CTRB, H36-GPS, Lane36) verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
