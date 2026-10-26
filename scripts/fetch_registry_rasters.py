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
import tarfile
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWNER = "buffedlizard55-lab"
SNAPSHOT_PATH = ROOT / "registry" / "priority_source_snapshot.json"


def _load_snapshot_commits() -> dict[str, str]:
    if not SNAPSHOT_PATH.exists():
        return {}
    payload = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    commits: dict[str, str] = {}
    for entry in payload.get("entries", []):
        repo = entry.get("repo")
        commit = entry.get("commit")
        if repo and commit and repo not in commits:
            commits[str(repo)] = str(commit)
    return commits


def _fallback_codeload_fetch(pending: list[dict]) -> tuple[int, list[dict]]:
    if not pending:
        return 0, []
    snap_commits = _load_snapshot_commits()
    by_repo_ref: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in pending:
        repo = str(row["repo"])
        ref = str(row.get("ref") or snap_commits.get(repo) or "main")
        by_repo_ref[(repo, ref)].append(row)

    recovered = 0
    still_missing: list[dict] = []
    for (repo, ref), items in sorted(by_repo_ref.items()):
        want = {str(it["path"]): it for it in items}
        refs_to_try = [ref]
        if ref != "main":
            refs_to_try.append("main")
        if repo in snap_commits and snap_commits[repo] not in refs_to_try:
            refs_to_try.insert(0, snap_commits[repo])
        for try_ref in refs_to_try:
            if not want:
                break
            url = f"https://codeload.github.com/{OWNER}/{repo}/tar.gz/{try_ref}"
            try:
                with urllib.request.urlopen(url, timeout=60) as resp:
                    with tarfile.open(fileobj=resp, mode="r|gz") as tf:
                        for member in tf:
                            if not member.isfile():
                                continue
                            parts = member.name.split("/", 1)
                            if len(parts) < 2:
                                continue
                            rel = parts[1]
                            if rel not in want:
                                continue
                            fobj = tf.extractfile(member)
                            if fobj is None:
                                continue
                            data = fobj.read()
                            target = want[rel]
                            if hashlib.sha256(data).hexdigest() == target["sha256"]:
                                out = ROOT / target["local"]
                                out.parent.mkdir(parents=True, exist_ok=True)
                                out.write_bytes(data)
                                recovered += 1
                                del want[rel]
            except Exception:
                continue
        still_missing.extend(want.values())
    return recovered, still_missing


def main() -> int:
    rows = []
    for reg in ("registry/scored_registry.json", "registry/peer_downloads.json"):
        rows += json.loads((ROOT / reg).read_text())["entries"]
    ok = 0
    pending: list[dict] = []
    for r in rows:
        out = ROOT / r["local"]
        if out.exists() and hashlib.sha256(out.read_bytes()).hexdigest() == r["sha256"]:
            ok += 1
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        res = subprocess.run(
            [
                "gh",
                "api",
                f"repos/{OWNER}/{r['repo']}/contents/{r['path']}"
                + (f"?ref={r['ref']}" if r.get("ref") else ""),
                "-H",
                "Accept: application/vnd.github.raw",
            ],
            capture_output=True,
        )
        if res.returncode == 0 and hashlib.sha256(res.stdout).hexdigest() == r["sha256"]:
            out.write_bytes(res.stdout)
            ok += 1
        else:
            pending.append(r)

    if pending:
        rec, failed = _fallback_codeload_fetch(pending)
        ok += rec
        for r in failed:
            print(f"MISMATCH/FAIL {r['repo']}/{r['path']}")
        bad = len(failed)
    else:
        bad = 0
    print(f"verified {ok} registry rasters; {bad} failed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
