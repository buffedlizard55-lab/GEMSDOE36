#!/usr/bin/env python3
"""Check local Pages links, key warnings, and the downloadable QA fixture."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1] / "docs"
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

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        href = attributes.get("href")
        if tag in {"a", "link"} and href:
            self.links.append(href)
            if tag == "a" and attributes.get("target") == "_blank":
                self.blank_targets.append((href, attributes.get("rel", "") or ""))

    def handle_data(self, data: str) -> None:
        self.text_chunks.append(data)


def main() -> int:
    errors: list[str] = []
    parsers: dict[str, LinkParser] = {}
    for page in REQUIRED_PAGES:
        path = ROOT / page
        if not path.is_file():
            errors.append(f"missing page: {page}")
            continue
        parser = LinkParser()
        parser.feed(path.read_text(encoding="utf-8"))
        parsers[page] = parser
        for href in parser.links:
            parsed = urlsplit(href)
            if parsed.scheme or href.startswith(("//", "#")):
                continue
            target = (path.parent / parsed.path).resolve()
            if not target.is_file():
                errors.append(f"{page}: broken local link: {href}")
        for href, rel in parser.blank_targets:
            if "noopener" not in rel.split():
                errors.append(f"{page}: target=_blank link lacks rel=noopener: {href}")

    landing_text = " ".join(parsers.get("index.html", LinkParser()).text_chunks)
    for phrase in REQUIRED_COPY:
        if phrase.lower() not in landing_text.lower():
            errors.append(f"landing page missing required warning/status phrase: {phrase}")

    fixture = ROOT / "downloads" / "GEMS36_FORMAT_TEST_NOT_SUBMISSION.tif"
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
    print(f"Checked pages: {', '.join(REQUIRED_PAGES)}")
    print(f"Local page assets/links verified; QA TIFF bytes: {fixture.stat().st_size}")
    print("Upload warning/status copy verified; no external URLs were scraped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
