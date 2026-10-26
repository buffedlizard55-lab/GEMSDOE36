#!/usr/bin/env python3
"""Fail-closed check of the GitHub Pages site against the machine-written run card.

Verifies: root redirect; required pages; every local link resolves; target=_blank links carry
rel=noopener; the first screen shows the current file, its verdict, SHA-256 and note; the
downloads exist and match the run-card hashes; the executive page carries the exact submission
guide; and no stale/incorrect historical claims reappear.
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
CARD = REPO_ROOT / "evidence/h36_run_card.json"
REQUIRED_PAGES = ("index.html", "executive-summary.html")
FORBIDDEN_COPY = (
    "Projected live score",
    "0.2798",
    "gate-passed candidate",
    "No upload-ready prediction yet",
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
        href = a.get("href")
        if tag in {"a", "link"} and href:
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
    card = json.loads(CARD.read_text())
    r = card["raster"]
    landing = " ".join(parsers.get("index.html", LinkParser()).text_chunks)
    execp = " ".join(parsers.get("executive-summary.html", LinkParser()).text_chunks)
    zeros = REPO_ROOT / r["zeros_tif"]
    for key, rel in (("zeros_sha256", "zeros_tif"), ("nan_sha256", "nan_tif"), ("zip_sha256", "zip")):
        f = REPO_ROOT / r[rel]
        if not f.is_file():
            errors.append(f"missing download {r[rel]}")
        elif _sha(f) != r[key]:
            errors.append(f"SHA-256 mismatch for {r[rel]}")
    must = [zeros.name, r["zeros_sha256"], card["submission"]["note"], "DOWNLOAD: YES"]
    must.append("OK TO SUBMIT" if card["verdict"] == "promote" else "DO NOT SUBMIT")
    for phrase in must:
        if phrase not in landing:
            errors.append(f"landing page missing: {phrase[:80]}")
    first_screen = landing[: max(1, len(landing) // 3)]
    if zeros.name not in first_screen:
        errors.append("current download is not on the first screen of the landing page")
    if card["verdict"] != "promote" and "OK TO SUBMIT" in landing:
        errors.append("landing page shows OK TO SUBMIT for a negative verdict")
    for phrase in FORBIDDEN_COPY:
        if phrase.lower() in (landing + execp).lower():
            errors.append(f"stale/incorrect claim present: {phrase}")
    for phrase in EXECUTIVE_COPY + (card["submission"]["note"], zeros.name):
        if phrase.lower() not in execp.lower():
            errors.append(f"executive summary missing: {phrase[:80]}")
    if len(card["submission"]["note"]) > 140:
        errors.append("note exceeds 140 characters")
    if errors:
        print("SITE CHECK FAIL")
        for err in errors:
            print(f"- {err}")
        return 1
    print("SITE CHECK PASS")
    print(f"verdict={card['verdict']} file={zeros.name} sha256={r['zeros_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
