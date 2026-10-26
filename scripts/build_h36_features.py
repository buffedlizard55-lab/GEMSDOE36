#!/usr/bin/env python3
"""Build the label-free H36-GPS feature columns (footprint-only float32 .npy files)."""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gemsdoe36.h36_features import build_feature_stack  # noqa: E402

if __name__ == "__main__":
    t0 = time.time()
    store, grid = build_feature_stack(ROOT / ".cache" / "h36", force="--force" in sys.argv)
    print(f"{len(store.names)} features x {store.n_fp:,} footprint px in {time.time() - t0:.0f}s")
    print(store.names)
