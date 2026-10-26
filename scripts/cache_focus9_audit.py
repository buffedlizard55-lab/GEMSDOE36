#!/usr/bin/env python3
"""Fetch exactly ten historical comparison TIFFs by commit and SHA for the nine-site audits.

These ignored files are comparison-only, never model features or submissions.
Requires the GitHub CLI; no DrivenData authentication or downloads are involved.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
OWNER = "buffedlizard55-lab"
SOLO = "h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif"


def build_tasks(ledger: dict, registry: dict) -> list[dict]:
    tasks = []
    refs = {}
    if len(ledger["focus_sites"]) != 9:
        raise ValueError("Exactly nine historical sites are required")
    for site in ledger["focus_sites"]:
        repo = site["site"]
        h = site["highest_historical_submission"]
        source = urlsplit(h["pinned_raster_source_url"])
        parts = source.path.lstrip("/").split("/")
        if (source.scheme != "https" or source.netloc != "github.com" or len(parts) < 5
                or parts[:3] != [OWNER, repo, "blob"] or not re.fullmatch(r"[0-9a-f]{40}", parts[3])):
            raise ValueError(f"Invalid pinned source URL for {repo}")
        path = "/".join(parts[4:])
        rows = [r for r in registry["entries"] if r["repo"] == repo and r["sha256"] == h["sha256_full"]]
        if len(rows) != 1 or rows[0]["path"] != path or Path(path).name != h["name"]:
            raise ValueError(f"Ledger/registry mismatch for {repo}")
        refs[repo] = parts[3]
        tasks.append({**rows[0], "ref": parts[3]})
    if len(refs) != 9:
        raise ValueError("Duplicate historical sites")
    solo = [r for r in registry["entries"] if r["repo"] == "GEMSDOE28" and SOLO in r["path"]]
    if len(solo) != 1 or "GEMSDOE28" not in refs:
        raise ValueError("Missing pinned GEMSDOE28 solo comparator")
    tasks.append({**solo[0], "ref": refs["GEMSDOE28"]})
    return tasks


def main() -> int:
    try:
        ledger = json.loads((ROOT / "evidence/focus_sites_9repo_summary_20261026.json").read_text())
        registry = json.loads((ROOT / "registry/scored_registry.json").read_text())
        tasks = build_tasks(ledger, registry)
        for task in tasks:
            dest = ROOT / task["local"]
            # Do not write outside the ignored comparison cache even if registry data is corrupted.
            cache = (ROOT / "data/registry/scored").resolve()
            if cache not in dest.resolve().parents:
                raise ValueError(f"Unsafe comparison cache path: {dest}")
            if dest.is_file() and hashlib.sha256(dest.read_bytes()).hexdigest() == task["sha256"]:
                print(f"verified cached {task['repo']}/{Path(task['path']).name}")
                continue
            result = subprocess.run(
                ["gh", "api", f"repos/{OWNER}/{task['repo']}/contents/{task['path']}?ref={task['ref']}",
                 "-H", "Accept: application/vnd.github.raw"], capture_output=True, check=True,
            )
            if hashlib.sha256(result.stdout).hexdigest() != task["sha256"]:
                raise ValueError(f"Pinned SHA-256 mismatch: {task['repo']}/{task['path']}")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(result.stdout)
            print(f"downloaded and verified {task['repo']}/{Path(task['path']).name}")
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print(f"Focus-nine cache failed closed: {exc}", file=sys.stderr)
        return 1
    print("Ten pinned comparison TIFFs verified; no candidate data generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
