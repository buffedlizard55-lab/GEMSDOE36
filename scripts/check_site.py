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


def validate_current(current: dict, stop: dict, stop_sha: str) -> list[str]:
    """A missing or fabricated candidate cannot be made submit-ready by Pages."""
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


def main() -> int:
    # Reuse the builder's independent card/proof contract rather than accepting a
    # self-consistent but fabricated positive manifest.
    from build_mto_site import (
        additional_archives,
        ensure_parallel_dw,
        ensure_status,
        ensure_stop_card,
        parallel_dw_projection,
        site_table,
    )

    errors: list[str] = []
    mto = json.loads((ROOT / "evidence/mto36_run_card_20261026.json").read_text())
    hvg = json.loads((ROOT / "evidence/hvg36_run_card_20261026.json").read_text())
    gvsc = json.loads((ROOT / "evidence/gvsc36_run_card_20261026.json").read_text())
    stop = json.loads(STOP.read_text())
    dw = json.loads((ROOT / "evidence/dw36_run_card_20261026.json").read_text())
    ledger = json.loads((ROOT / "evidence/focus_sites_9repo_summary_20261026.json").read_text())
    try:
        ensure_status(mto, ledger, hvg)
        ensure_stop_card(stop, gvsc)
        ensure_parallel_dw(dw)
    except (RuntimeError, OSError, KeyError, StopIteration, ValueError) as exc:
        errors.append(f"Release evidence invalid: {exc}")

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
                       "ORGANIZER-CONFIRMED", "0.158855", "0.135759", "0.1637924", "0.2778", "DW36", "0.066052"):
            if phrase not in text:
                errors.append(f"docs/{page}: missing {phrase}")
        first_screen = text[: max(1, len(text) // 4)]
        if "DO NOT SUBMIT" not in first_screen:
            errors.append(f"docs/{page}: negative verdict must lead the page")
        if site_table(ledger) not in path.read_text():
            errors.append(f"docs/{page}: pinned nine-site table differs from source")
        for forbidden in ("New GEMSDOE36 Holdout Record", "Highest Recorded Holdout across 9 repos",
                          "Estimated Score: HOLDOUT-DTI", "Projected live score", "OK TO SUBMIT"):
            if forbidden.lower() in text.lower():
                errors.append(f"docs/{page}: stale or unsafe claim: {forbidden}")
        if re.search(r"(?:0\.\d{3,4}).{0,25}ORGANIZER-CONFIRMED", text, re.I):
            errors.append(f"docs/{page}: numeric score incorrectly called organizer-confirmed")
        for fname, checksum in (
            (gvsc["submission"]["zeros_filename"], gvsc["submission"]["raster_sha256"]),
            (Path(hvg["artifact"]["tif_path"]).name, hvg["artifact"]["tif_sha256"]),
            (Path(mto["download"]["tif"]).name, mto["raster_sha256"]),
        ):
            if fname not in text or checksum not in text:
                errors.append(f"docs/{page}: missing archived artifact identity {fname}")

    exec_text = " ".join(parse(DOCS / "executive-summary.html").text).lower()
    for term in ("single-band geotiff (.tif)", ".zip file containing a single geotiff",
                 "crs, shape, and geotransform", "predicted values must be in range [0, 1]",
                 "three weekly slots", "one submission for both prize rounds", "nan"):
        if term not in exec_text:
            errors.append(f"executive submission guide missing: {term}")

    current_path = DOCS / "current-run.json"
    if current_path.is_file():
        current = json.loads(current_path.read_text())
        errors.extend(validate_current(current, stop, sha(STOP)))
        if current.get("parallel_experiments") != [parallel_dw_projection(dw)]:
            errors.append("Current manifest must preserve the separately run negative DW36 experiment")
    else:
        errors.append("Missing docs/current-run.json")
    for original, copy in (
        (STOP, DOCS / "downloads/registry-preflight-run-card.json"),
        (ROOT / "evidence/dw36_run_card_20261026.json", DOCS / "downloads/dw36-run-card.json"),
        (ROOT / "evidence/mto36_run_card_20261026.json", DOCS / "downloads/mto36-run-card.json"),
        (ROOT / "evidence/hvg36_run_card_20261026.json", DOCS / "downloads/hvg36-run-card.json"),
        (ROOT / "evidence/gvsc36_run_card_20261026.json", DOCS / "downloads/gvsc36-run-card.json"),
        (ROOT / "evidence/focus_sites_9repo_summary_20261026.json", DOCS / "downloads/focus9-verified-source-ledger.json"),
        (ROOT / "evidence/focus_sites_pairwise_uniqueness_20261026.json", DOCS / "downloads/focus-sites-pairwise-uniqueness.json"),
        (ROOT / "evidence/mto36_ninesite_forensics.json", DOCS / "downloads/focus9-source-integrity.json"),
        (ROOT / "evidence/lane36_crosscheck.json", DOCS / "downloads/lane36-crosscheck.json"),
        (ROOT / "evidence/moe36_run_card_20261026.json", DOCS / "downloads/moe36-run-card.json"),
        (ROOT / "evidence/atvr36_run_card_20261026.json", DOCS / "downloads/atvr36-run-card.json"),
    ):
        if not copy.is_file() or original.read_bytes() != copy.read_bytes():
            errors.append(f"Pages JSON mirror differs from evidence: {copy}")

    manifest = json.loads((DOCS / "downloads/submissions_manifest.json").read_text())
    if (manifest.get("slot_approved") is not False or manifest.get("current_candidate") is not None
            or len(manifest.get("archived_research_only", [])) != 9
            or any(x.get("submit_ok") is not False for x in manifest["archived_research_only"])):
        errors.append("Downloads manifest must only contain negative research artifacts")

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

    # Preserve hash/ZIP integrity checks for the three displayed research bundles.
    artifacts = [
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
    print("Site check passed: negative preflight, no candidate/slot, pinned links and research bundle integrity")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
