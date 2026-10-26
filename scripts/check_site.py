#!/usr/bin/env python3
"""Automated GitHub Pages, Download Artifact, and Run-Card Consistency Gate."""

from __future__ import annotations

import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = REPO_ROOT / "docs"
REQUIRED_PAGES = ("index.html", "executive-summary.html")


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.text_chunks: list[str] = []
        self.blank_targets: list[tuple[str, str]] = []
        self.refresh_target: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        href = attributes.get("href")
        if tag in {"a", "link"} and href:
            self.links.append(href)
            if tag == "a" and attributes.get("target") == "_blank":
                self.blank_targets.append((href, attributes.get("rel", "") or ""))
        if tag == "meta" and (attributes.get("http-equiv") or "").lower() == "refresh":
            content = attributes.get("content") or ""
            match = re.search(r"url\s*=\s*['\"]?([^;'\"\s]+)", content, flags=re.IGNORECASE)
            if match:
                self.refresh_target = match.group(1)

    def handle_data(self, data: str) -> None:
        self.text_chunks.append(data)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _parse(path: Path) -> LinkParser:
    parser = LinkParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


def _check_local_links(path: Path, parser: LinkParser, errors: list[str]) -> None:
    for href in parser.links:
        parsed = urlsplit(href)
        if parsed.scheme or href.startswith(("//", "#")):
            continue
        target = (path.parent / parsed.path).resolve()
        if target.is_dir():
            target = target / "index.html"
        if not target.is_file():
            errors.append(f"{path.relative_to(REPO_ROOT)}: broken local link: {href}")
    for href, rel in parser.blank_targets:
        if "noopener" not in rel.split():
            errors.append(
                f"{path.relative_to(REPO_ROOT)}: target=_blank link lacks rel=noopener: {href}"
            )


def main() -> int:
    errors: list[str] = []

    # Check root redirect page
    root_index = REPO_ROOT / "index.html"
    if not root_index.is_file():
        errors.append("missing root index.html redirect")
    else:
        rp = _parse(root_index)
        if rp.refresh_target not in {"docs/", "docs/index.html"}:
            errors.append(f"unexpected root redirect target: {rp.refresh_target}")

    card_path = DOCS_ROOT / "current-run.json"
    run_card_path = REPO_ROOT / "evidence" / "atvr36_run_card_20261026.json"
    manifest_path = DOCS_ROOT / "downloads" / "submissions_manifest.json"
    for req_file in (card_path, run_card_path, manifest_path):
        if not req_file.is_file():
            errors.append(f"missing required JSON artifact: {req_file.relative_to(REPO_ROOT)}")

    if errors:
        print("SITE CHECK FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    card = json.loads(card_path.read_text(encoding="utf-8"))
    run_card = json.loads(run_card_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    tif_path = DOCS_ROOT / card["download_tif_href"]
    zip_path = DOCS_ROOT / card["download_zip_href"]
    if not tif_path.is_file():
        errors.append(f"missing primary GeoTIFF: {tif_path}")
    else:
        actual_tif_sha = _sha256(tif_path)
        for src_name, expected in (
            ("current-run.json", card.get("tif_sha256")),
            ("atvr36_run_card", run_card.get("raster_sha256")),
            ("submissions_manifest.json", manifest.get("primary_sha256")),
        ):
            if actual_tif_sha != expected:
                errors.append(f"GeoTIFF SHA-256 mismatch in {src_name}: {expected} != {actual_tif_sha}")

    if not zip_path.is_file():
        errors.append(f"missing ZIP bundle: {zip_path}")
    else:
        actual_zip_sha = _sha256(zip_path)
        if actual_zip_sha != card.get("zip_sha256"):
            errors.append("ZIP SHA-256 mismatch in current-run.json")

    verdict = card.get("verdict")
    gates = card.get("automated_gates", {})
    if verdict == "promote":
        for g_name in (
            "leakage_canary_passed",
            "beats_C0_repo_field_95ci",
            "beats_B1_raw19_hgb_d28_95ci",
            "portal_geotiff_valid",
            "registry_uniqueness_passed",
            "all_passed",
        ):
            if not gates.get(g_name, False):
                errors.append(f"verdict=promote requires automated_gates[{g_name}]=True")
    elif verdict != "negative":
        errors.append(f"invalid verdict in current-run.json: {verdict}")

    if len(card.get("submission_note", "")) > 140:
        errors.append("submission_note exceeds 140 character cap")

    expected_banner = (
        "OK TO DOWNLOAD AND SUBMIT" if verdict == "promote" else "DO NOT SUBMIT"
    )
    for page in REQUIRED_PAGES:
        path = DOCS_ROOT / page
        parser = _parse(path)
        _check_local_links(path, parser, errors)
        text = " ".join(parser.text_chunks)
        for required in (expected_banner, "HOLDOUT-DTI", "ORGANIZER-CONFIRMED"):
            if required not in text:
                errors.append(f"{page}: missing required token '{required}'")
        if card["download_tif_href"] not in parser.links:
            errors.append(f"{page}: missing one-click download link to {card['download_tif_href']}")

    if errors:
        print("SITE CHECK FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print(
        f"SITE CHECK PASS — verdict={verdict.upper()} | "
        f"tif={tif_path.name} ({card['tif_sha256'][:12]})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
