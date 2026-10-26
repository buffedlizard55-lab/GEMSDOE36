#!/usr/bin/env python3
"""Recompute an exact literal-registry placement bound from pinned local inputs."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gemsdoe36.feasibility import PreflightError, inspect_registered_lattice  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dots", type=int, default=37_654, help="number of distinct footprint pixels")
    args = parser.parse_args()
    try:
        result = inspect_registered_lattice(ROOT, args.dots)
    except (ValueError, OSError, StopIteration, KeyError, PreflightError) as exc:
        print(f"Preflight error (fail closed): {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 2 if result["bound"]["guaranteed_duplicate"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
