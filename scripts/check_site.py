#!/usr/bin/env python3
"""Check the GitHub Pages entry point, local links, submission downloads, and metadata.

GEMSDOE36 carries two independent candidate lines, kept side by side by a
non-destructive merge of two parallel research sessions:

  1. Anderson-PINN multi-physics (Anderson 1905 kinematics + Raissi et al. 2019
     structure-tensor loss + GDR 1391 blind geothermal conduits) — the primary
     download established on main (LM-calibrated 4-quadrant mirror).
  2. Off-catalogue fault-network prior (H6) — the 5-fold spatially-blocked
     holdout gate-passed candidate from the off-catalogue session.

The two lines used different holdout protocols, so this check does NOT claim a
head-to-head winner; it only verifies that BOTH candidate TIFs are present on the
served tree and that both lines are referenced on the landing/executive pages.
The owner selects the single final competition file to upload (a manual step).
"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = REPO_ROOT / "docs"
REQUIRED_PAGES = ("index.html", "executive-summary.html")

# Main's Anderson-PINN deliverable bundle (the established primary on main).
PRIMARY_TIF = "gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif"
NAN_TIF = "gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-nan.tif"
ZIP_FILE = "gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.zip"
MANIFEST_FILE = "submissions_manifest.json"

# The landing page must reference BOTH candidate lines and current honest status.
REQUIRED_COPY = (
    "GEMSDOE36",
    "Anderson",
    PRIMARY_TIF,            # main's PINN primary is referenced
    "off-catalogue",        # the H6 off-catalogue candidate line is referenced
    "holdout",              # spatial-holdout validation is described
)
# The landing page must NOT regress to the pre-gate "no prediction" framing.
FORBIDDEN_COPY = (
    "No upload-ready prediction yet",
    "Competition TIFF: not available",
)
# Executive page must keep the exact submission-guide items and describe both lines.
EXECUTIVE_COPY = (
    "--submission-name",
    "--note",
    "spatial holdout",
    "0.2778",
    PRIMARY_TIF.lower(),
    "off-catalogue",
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


def _h6_candidate() -> Path | None:
    """Return the H6 gate-passed candidate TIF (off-catalogue line) in docs/downloads/."""
    downloads = DOCS_ROOT / "downloads"
    if not downloads.is_dir():
        return None
    candidates = [
        p for p in downloads.glob("GEMS36_h6_*.tif")
        if p.name != "GEMS36_FORMAT_TEST_NOT_SUBMISSION.tif"
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_size)


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

    landing_lower = " ".join(parsers.get("index.html", LinkParser()).text_chunks).lower()
    for phrase in REQUIRED_COPY:
        if phrase.lower() not in landing_lower:
            errors.append(f"landing page missing required status phrase: {phrase}")
    for phrase in FORBIDDEN_COPY:
        if phrase.lower() in landing_lower:
            errors.append(f"landing page regressed to stale pre-gate copy: {phrase}")

    executive_lower = " ".join(
        parsers.get("executive-summary.html", LinkParser()).text_chunks
    ).lower()
    for phrase in EXECUTIVE_COPY:
        if phrase.lower() not in executive_lower:
            errors.append(f"executive summary is missing required submission-guide item: {phrase}")

    # Verify main's Anderson-PINN deliverable bundle is present.
    downloads_dir = DOCS_ROOT / "downloads"
    for label, name in (
        ("primary submission file", PRIMARY_TIF),
        ("nan companion submission file", NAN_TIF),
        ("zip bundle file", ZIP_FILE),
        ("submissions manifest", MANIFEST_FILE),
    ):
        if not (downloads_dir / name).is_file():
            errors.append(f"missing {label}: {name}")

    # Verify the H6 gate-passed candidate (off-catalogue line) is present.
    candidate = _h6_candidate()
    if candidate is None:
        errors.append("missing H6 gate-passed candidate TIFF (GEMS36_h6_*) in docs/downloads/")
    elif candidate.stat().st_size < 10_000:
        errors.append("H6 gate-passed candidate TIFF is suspiciously small")

    if errors:
        print("SITE CHECK FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("SITE CHECK PASS")
    print(f"Checked Pages entry: {root_entry.relative_to(REPO_ROOT)} -> docs/")
    print(f"Checked pages: {', '.join(f'docs/{page}' for page in REQUIRED_PAGES)}")
    print(f"Verified main deliverables: {PRIMARY_TIF}, {NAN_TIF}, {ZIP_FILE}, {MANIFEST_FILE}")
    if candidate is not None:
        print(f"H6 gate-passed candidate present: docs/downloads/{candidate.name} ({candidate.stat().st_size} bytes)")
    print("Both candidate lines referenced and verified; no external URLs were scraped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
