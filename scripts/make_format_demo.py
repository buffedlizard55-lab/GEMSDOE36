#!/usr/bin/env python3
"""Create a tiny synthetic QA GeoTIFF for the site; it is NOT a competition submission."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from affine import Affine

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "downloads" / "GEMS36_FORMAT_TEST_NOT_SUBMISSION.tif"
MANIFEST = OUTPUT.with_suffix(".json")


def main() -> int:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    # Intentionally tiny, synthetic raster. Its geometry is deliberately not the official
    # competition grid; it must never be uploaded or described as a candidate prediction.
    data = np.zeros((32, 48), dtype=np.float32)
    data[4:28, 16] = 0.75
    data[16, 8:40] = 0.35
    data[20:23, 24:29] = 1.0
    data[:2, :] = np.nan  # synthetic outside area to exercise a NaN NoData encoding
    profile = {
        "driver": "GTiff",
        "height": data.shape[0],
        "width": data.shape[1],
        "count": 1,
        "dtype": "float32",
        "crs": "EPSG:32611",
        "transform": Affine(100.0, 0.0, 400_000.0, 0.0, -100.0, 4_400_000.0),
        "nodata": float("nan"),
        "compress": "deflate",
        "predictor": 1,
        "tiled": False,
    }
    with rasterio.open(OUTPUT, "w", **profile) as dst:
        dst.write(data, 1)
        dst.update_tags(
            ARTIFACT_KIND="synthetic format QA fixture",
            WARNING="NOT_FOR_COMPETITION_UPLOAD: wrong dimensions/bounds; no contest data used",
            GEMS36_GENERATOR="scripts/make_format_demo.py",
        )

    with rasterio.open(OUTPUT) as ds:
        reread = ds.read(1)
        valid = np.isfinite(reread)
        if ds.count != 1 or ds.dtypes != ("float32",) or ds.crs.to_string() != "EPSG:32611":
            raise RuntimeError("synthetic QA GeoTIFF metadata read-back failed")
        if not valid.any() or float(reread[valid].min()) < 0 or float(reread[valid].max()) > 1:
            raise RuntimeError("synthetic QA GeoTIFF values failed the [0, 1] check")
        if valid[:2].any() or not valid[2:].all():
            raise RuntimeError("synthetic QA NoData placement failed read-back")
        metadata = {
            "file": OUTPUT.name,
            "sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
            "bytes": OUTPUT.stat().st_size,
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "purpose": "synthetic format QA only; do not upload to the competition",
            "official_submission": False,
            "width": ds.width,
            "height": ds.height,
            "count": ds.count,
            "dtype": ds.dtypes[0],
            "crs": ds.crs.to_string(),
            "resolution_m": [abs(ds.transform.a), abs(ds.transform.e)],
            "finite_value_range": [float(reread[valid].min()), float(reread[valid].max())],
            "finite_cells": int(valid.sum()),
            "nan_cells": int((~valid).sum()),
            "warning": "This raster does not use the official template shape/bounds and is not a prediction.",
        }
    MANIFEST.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote synthetic QA-only fixture: {OUTPUT}")
    print(f"SHA-256: {metadata['sha256']}")
    print("NOT FOR COMPETITION UPLOAD")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
