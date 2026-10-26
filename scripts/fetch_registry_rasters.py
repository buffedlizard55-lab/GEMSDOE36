#!/usr/bin/env python3
"""Re-download the comparison-only registry rasters listed in registry/scored_registry.json and
registry/peer_downloads.json (GitHub repo/path rows) and verify each file's SHA-256.

Uses ``gh api`` (authenticated GitHub CLI). Files land in data/registry/ (git-ignored). Learning,
forensics and uniqueness checks only - nothing here is ever copied into a candidate.
Note: peer rows point at the branch HEAD of sibling repos on 2026-10-25; a file that has since
changed upstream fails the hash check and is reported, never silently accepted.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWNER = "buffedlizard55-lab"


def main() -> int:
    rows = []
    for reg in ("registry/scored_registry.json", "registry/peer_downloads.json"):
        rows += json.loads((ROOT / reg).read_text())["entries"]
    ok = bad = 0
    for r in rows:
        out = ROOT / r["local"]
        if out.exists() and hashlib.sha256(out.read_bytes()).hexdigest() == r["sha256"]:
            ok += 1
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        res = subprocess.run(
            ["gh", "api", f"repos/{OWNER}/{r['repo']}/contents/{r['path']}" +
             (f"?ref={r['ref']}" if r.get("ref") else ""),
             "-H", "Accept: application/vnd.github.raw"],
            capture_output=True,
        )
        if res.returncode or hashlib.sha256(res.stdout).hexdigest() != r["sha256"]:
            print(f"MISMATCH/FAIL {r['repo']}/{r['path']}")
            bad += 1
            continue
        out.write_bytes(res.stdout)
        ok += 1
    print(f"verified {ok} registry rasters; {bad} failed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
