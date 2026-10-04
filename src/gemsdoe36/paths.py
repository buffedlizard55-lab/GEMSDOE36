"""Path resolution for GEMSDOE36."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def repo_root() -> Path:
    """Return the repository root."""
    return ROOT


def data_dir() -> Path:
    """Resolve the directory holding competition inputs (checks GEMS_DATA_DIR, data/raw, data/)."""
    env = os.environ.get("GEMS_DATA_DIR")
    if env:
        return Path(env).expanduser()
    for cand in (ROOT / "data" / "raw", ROOT / "data", ROOT / ".cache" / "gems_data"):
        if (cand / "training_features.tif").exists():
            return cand
    return ROOT / "data" / "raw"


def work_dir() -> Path:
    """Scratch directory for regenerable numpy caches."""
    env = os.environ.get("GEMS_WORK_DIR")
    if env:
        return Path(env).expanduser()
    return ROOT / ".cache" / "gems_work"


def docs_dir() -> Path:
    """Directory holding GitHub Pages site, figures, and downloadable submissions."""
    d = ROOT / "docs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def downloads_dir() -> Path:
    """Directory holding downloadable submission GeoTIFFs and verification sidecars."""
    d = ROOT / "docs" / "downloads"
    d.mkdir(parents=True, exist_ok=True)
    return d


def evidence_dir() -> Path:
    """Directory holding machine-readable experimental receipts."""
    d = ROOT / "evidence"
    d.mkdir(parents=True, exist_ok=True)
    return d


def registry_dir() -> Path:
    """Directory holding the auditable registries (sources, manifests, irregularities)."""
    d = ROOT / "registry"
    d.mkdir(parents=True, exist_ok=True)
    return d
