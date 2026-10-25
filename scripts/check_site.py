#!/usr/bin/env python3
"""Check current fail-closed status, research download links, and run-card policy."""

from __future__ import annotations

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
    import json

    errors: list[str] = []
    for page in REQUIRED_PAGES:
        path = DOCS_ROOT / page
        parser = _parse(path)
        _check_local_links(path, parser, errors)
        text = " ".join(parser.text_chunks)
        for required in ("DO NOT SUBMIT", "Research downloads only", "HOLDOUT-DTI"):
            if required not in text:
                errors.append(f"{page}: missing {required}")
    card = json.loads((DOCS_ROOT / "current-run.json").read_text())
    if card["slot_approved"] or card["verdict"] != "negative":
        errors.append("blocked review must not authorize a submission")
    print("SITE CHECK FAIL" if errors else "SITE CHECK PASS — research only; no upload approval")
    for error in errors:
        print(f"- {error}")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
