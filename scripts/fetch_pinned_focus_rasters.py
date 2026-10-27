#!/usr/bin/env python3
"""Download pinned focus-site comparison TIFFs from GitHub at their archived commits.

Source URLs are the raw.githubusercontent.com links cited in docs/executive-summary.html
(GEMSDOE24/25/27/28/30/31/32/33/36 pinned forensic snapshot). raw.githubusercontent.com
is a GitHub host and is in the sandbox allow-list. Each file is SHA-256 checked against
the pinned executive-summary table where a SHA-12 prefix is recorded.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

# (site, commit, filename, expected sha-12 prefix from the pinned table, or None)
PINNED = [
    ("GEMSDOE24", "fc2bc6f350bf5c6ce8da5d7a2ab03578ea1259d1",
     "gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif",
     "68d0e2e4fcc5"),
    ("GEMSDOE25", "e40b9b5e3871cb34d138f586bde97f5099658d01",
     "gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif",
     "91eae1ca42ec"),
    ("GEMSDOE27", "927322eadbde56be42ae129ccdfb9b37540d8e60",
     "gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif",
     "33003374335d"),
    ("GEMSDOE28", "e6321461066f89080e3b1bb670d3951ab20d3638",
     "gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif",
     "5556aa1438fd"),
    ("GEMSDOE30", "760af3005dd40b9f36d8fef97d6dc384fd9f2a2f",
     "gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif",
     "8cf893ead566"),
    ("GEMSDOE31", "597b04cd1afb65d1ebbe3e9417fd952be48e3d74",
     "gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif",
     "07b6db440535"),
    ("GEMSDOE32", "5fc7792c5887735ecd3aa9a612787da588a7bf2c",
     "gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
     "c55bafc47005"),
    ("GEMSDOE33", "f618cc54773bd9b4d6c2b3ebf78103a05cc10cb6",
     "GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif",
     "87f857d505e2"),
    ("GEMSDOE36", "c5a8ae7da3bd2fcff5aa5855afd44c7a3346c16f",
     "gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif",
     "e15891020b9c"),
]

OUT = ROOT / ".cache" / "focus_registry"
OUT.mkdir(parents=True, exist_ok=True)


def fetch(site: str, commit: str, fname: str) -> Path:
    dest = OUT / f"{site}__{fname}"
    repo = "buffedlizard55-lab/" + site
    path = f"docs/downloads/{fname}"
    tmp = dest.with_suffix(dest.suffix + ".partial")
    try:
        with tmp.open("wb") as out:
            subprocess.run(
                ["gh", "api", f"repos/{repo}/contents/{path}?ref={commit}",
                 "-H", "Accept: application/vnd.github.raw"],
                stdout=out, check=True, timeout=300,
            )
        tmp.replace(dest)
    finally:
        tmp.unlink(missing_ok=True)
    return dest


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    results = []
    for site, commit, fname, sha12 in PINNED:
        dest = OUT / f"{site}__{fname}"
        try:
            if dest.exists() and sha256_file(dest)[:12] == sha12:
                print(f"[pinned] {site}: already present, sha256 {sha12} OK")
                results.append({"site": site, "file": fname, "path": str(dest), "status": "cached",
                                "sha256": sha256_file(dest), "commit": commit})
                continue
            fetch(site, commit, fname)
            digest = sha256_file(dest)
            ok = digest[:12] == sha12 if sha12 else None
            print(f"[pinned] {site}: fetched {dest.name} sha256={digest[:12]} prefix_match={ok}")
            results.append({"site": site, "file": fname, "path": str(dest), "status": "fetched",
                            "sha256": digest, "prefix_match": ok, "commit": commit})
        except Exception as exc:  # noqa: BLE001
            print(f"[pinned] {site}: FAILED {exc!r}")
            results.append({"site": site, "file": fname, "status": "failed", "error": str(exc)})
    (ROOT / "evidence" / "pinned_focus_fetch.json").write_text(
        json.dumps({"fetched_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
                    "items": results}, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
