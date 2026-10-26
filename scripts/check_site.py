#!/usr/bin/env python3
"""Fail-closed check of the GitHub Pages site against the machine-written JSON run cards
across all GEMSDOE36 lanes (H36-CTRB, H36-GPS, and Lane36).
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
CTRB_CARD = REPO_ROOT / "evidence/h36_ctrb_run_card_20261025.json"
GPS_CARD = REPO_ROOT / "evidence/h36_run_card.json"
LANE36_CARD = DOCS_ROOT / "downloads/lane36_run_card.json"
LANE36_CC = REPO_ROOT / "evidence/lane36_crosscheck.json"
BLOCKED_REVIEW = DOCS_ROOT / "current-run.json"
BOTH_PAGES = ("DO NOT SUBMIT", "Research downloads only", "HOLDOUT-DTI")
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
        if rp.refresh_target != "docs/":
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

    ctrb = json.loads(CTRB_CARD.read_text())
    gps = json.loads(GPS_CARD.read_text())
    landing = " ".join(parsers.get("index.html", LinkParser()).text_chunks)
    execp = " ".join(parsers.get("executive-summary.html", LinkParser()).text_chunks)

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

    any_ok = (ctrb["verdict"] == "promote") or (gps["verdict"] == "promote")
    must = [
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
    if ctrb_zeros.name not in first_screen or gps_zeros.name not in first_screen:
        errors.append("current downloads are not on the first screen of the landing page")

    for phrase in FORBIDDEN_COPY:
        if phrase.lower() in (landing + execp).lower():
            errors.append(f"stale/incorrect claim present: {phrase}")

    for phrase in EXECUTIVE_COPY + (
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

    if BLOCKED_REVIEW.exists():
        blocked = json.loads(BLOCKED_REVIEW.read_text())
        if blocked.get("slot_approved") or blocked.get("verdict") != "negative":
            errors.append("docs/current-run.json (blocked review) must not authorize a submission")

    if LANE36_CARD.exists():
        lc = json.loads(LANE36_CARD.read_text())
        lf = DOCS_ROOT / "downloads" / lc["raster"]["file"]
        if not lf.is_file() or _sha(lf) != lc["raster"]["sha256"]:
            errors.append("Lane36 download missing or SHA-256 mismatch")
        if lc["raster"]["file"] not in landing:
            errors.append("landing page does not list the Lane36 file")
        cc = json.loads(LANE36_CC.read_text()) if LANE36_CC.exists() else None
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
    print("SITE CHECK PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
