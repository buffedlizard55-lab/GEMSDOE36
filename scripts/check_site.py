#!/usr/bin/env python3
"""Check the GitHub Pages entry point, local links, key warnings, and QA download."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = REPO_ROOT / "docs"
REQUIRED_PAGES = ("index.html", "executive-summary.html")
REQUIRED_COPY = (
    "No upload-ready prediction yet",
    "NOT a competition submission",
    "never upload it",
)


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
            errors.append(f"{path.relative_to(REPO_ROOT)}: target=_blank link lacks rel=noopener: {href}")


def main() -> int:
    errors: list[str] = []
    parsers: dict[str, LinkParser] = {}

    root_entry = REPO_ROOT / "index.html"
    if not root_entry.is_file():
        errors.append("missing repository-root index.html; GitHub Pages root would not redirect")
    else:
        root_parser = _parse(root_entry)
        _check_local_links(root_entry, root_parser, errors)
        if root_parser.refresh_target != "docs/":
            errors.append("repository-root index.html must immediately redirect to docs/")
        if not any(href == "docs/" for href in root_parser.links):
            errors.append("repository-root entry point needs a working docs/ fallback link")

    for page in REQUIRED_PAGES:
        path = DOCS_ROOT / page
        if not path.is_file():
            errors.append(f"missing page: docs/{page}")
            continue
        parser = _parse(path)
        parsers[page] = parser
        _check_local_links(path, parser, errors)

    landing_text = " ".join(parsers.get("index.html", LinkParser()).text_chunks)
    for phrase in REQUIRED_COPY:
        if phrase.lower() not in landing_text.lower():
            errors.append(f"landing page missing required warning/status phrase: {phrase}")

    executive_text = " ".join(
        parsers.get("executive-summary.html", LinkParser()).text_chunks
    ).lower()
    for phrase in ("--submission-name", "--note", "spatial holdout"):
        if phrase.lower() not in executive_text:
            errors.append(f"executive summary is missing exact submission-guide item: {phrase}")

    fixture = DOCS_ROOT / "downloads" / "GEMS36_FORMAT_TEST_NOT_SUBMISSION.tif"
    if not fixture.is_file():
        errors.append("missing synthetic QA TIFF download")
    elif fixture.stat().st_size > 1_000_000:
        errors.append("synthetic QA TIFF should remain under 1 MB")

    if errors:
        print("SITE CHECK FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("SITE CHECK PASS")
    print(f"Checked Pages entry: {root_entry.relative_to(REPO_ROOT)} → docs/")
    print(f"Checked pages: {', '.join(f'docs/{page}' for page in REQUIRED_PAGES)}")
    print(f"Local page assets/links verified; QA TIFF bytes: {fixture.stat().st_size}")
    print("Submission-not-ready warning and exact guide flags verified; no external URLs were scraped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
