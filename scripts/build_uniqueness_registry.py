#!/usr/bin/env python3
"""Assemble the uniqueness registry consumed by the template's ``gems.novelty.compare_registry``.

Entries = every owner-scored GEMSDOE raster located on GitHub (registry/scored_registry.json) +
every current docs/downloads raster of the priority sites (parallel-session lanes). Rasters are
cached under data/registry/ (git-ignored) and pinned by file SHA-256 and footprint-content SHA-256.
Duplicate footprint contents are kept once (first occurrence) and their aliases recorded.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    with rasterio.open(ROOT / "data/raw/labels.tif") as s:
        fp = s.read(1) >= 0
    scored = json.loads((ROOT / "registry/scored_registry.json").read_text())["entries"]
    peers_p = ROOT / "registry/peer_downloads.json"
    peers = json.loads(peers_p.read_text())["entries"] if peers_p.exists() else []
    seen: dict[str, dict] = {}
    entries = []
    for src, rows in (("owner-scored", scored), ("priority-site-download", peers)):
        for r in rows:
            p = ROOT / r["local"]
            if not p.exists():
                continue
            with rasterio.open(p) as ds:
                if ds.shape != fp.shape:
                    continue
                a = ds.read(1)
            content = hashlib.sha256(np.asarray(a[fp], dtype="<f4").tobytes()).hexdigest()
            label = r.get("name") or Path(r["path"]).name
            if content in seen:
                seen[content]["aliases"].append(f'{r.get("site", r.get("repo"))}:{label}')
                continue
            e = {
                "id": f"reg-{len(entries) + 1:03d}",
                "file": f'{r.get("repo")}/{r["path"]}',
                "cache_path": r["local"],
                "footprint_sha256": content,
                "file_sha256": r["sha256"],
                "source": src,
                "site": r.get("site", r.get("repo")),
                "owner_reported_score": r.get("score"),
                "aliases": [],
            }
            seen[content] = e
            entries.append(e)
    out = {
        "description": "Uniqueness registry for the parallel-run lane rule (|rho| <= 0.90; <= 70% of dots within 3 px).",
        "n_entries": len(entries),
        "entries": entries,
    }
    (ROOT / "registry/uniqueness_registry.json").write_text(json.dumps(out, indent=1) + "\n")
    print(len(entries), "unique registry rasters")
    return 0


if __name__ == "__main__":
    sys.exit(main())
