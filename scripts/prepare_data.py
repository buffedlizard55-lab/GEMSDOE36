#!/usr/bin/env python3
"""Prepare and audit the competition rasters for GEMSDOE36.

Reads training_features.tif (19 bands), labels.tif, and sample_submission.tif from data_dir(),
audits CRS (EPSG:32611), shape (3730x3292), 100 m geotransform, and sentinel pixels (-3.4028235e+38)
inside the 5,167,373-pixel footprint, writes fast per-band .npy arrays to work_dir()/bands, and saves
the full audit receipt to data/prepared_manifest.json.
"""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems.submission import EXPECTED
from gemsdoe36.paths import data_dir, work_dir

BASE_NAMES = [
    "mag_anom",
    "rtp",
    "tmi_hg",
    "geod_2ndinv",
    "iso_grav_anom_slope",
    "tc",
    "geod_shearrate",
    "geod_dilaterate",
    "tmi_vg",
    "deq_n100a15",
    "iso_grav_anom_vg",
    "det_elev",
    "iso_grav_anom",
    "tmi",
    "depth_to_base_surf",
    "ieq_n100a15",
    "cond_surf",
    "iso_grav_anom_hg",
    "det_elev_slope",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def inspect_core_inputs(
    template_path: Path,
    labels_path: Path,
    features_path: Path,
    *,
    expected_shape: tuple[int, int] = EXPECTED["shape"],
    expected_transform: tuple[float, ...] = EXPECTED["transform"],
    expected_footprint_pixels: int = EXPECTED["footprint_pixels"],
    expected_names: list[str] = BASE_NAMES,
) -> tuple[np.ndarray, np.ndarray, tuple[float, ...]]:
    """Verify all core grids before writing any cache files.

    The template is an integrity-pinned owner mirror, not proof of organizer
    authentication. Matching shape alone does not establish pixel alignment.
    """
    for path in (template_path, labels_path, features_path):
        if not path.is_file():
            raise FileNotFoundError(
                f"Missing required competition file {path}. "
                "Run `bash scripts/download_competition_data.sh` first."
            )
    with rasterio.open(template_path) as template:
        grid = (template.shape, template.crs, template.transform)
        transform = tuple(float(v) for v in template.transform)[:6]
        if template.count != 1 or template.dtypes != ("float32",):
            raise ValueError("Template must be a single-band float32 raster")
        if template.crs is None or template.crs.to_epsg() != 32611:
            raise ValueError(f"Expected EPSG:32611 template, got {template.crs}")
        if template.shape != expected_shape or transform != expected_transform:
            raise ValueError("Template shape or geotransform does not match the pinned grid")
        foot = np.isfinite(template.read(1)) & (template.read_masks(1) > 0)
        if int(foot.sum()) != expected_footprint_pixels:
            raise ValueError("Template valid-footprint count does not match the pinned grid")

    def aligned(ds: rasterio.io.DatasetReader, name: str) -> None:
        if (ds.shape, ds.crs, ds.transform) != grid:
            raise ValueError(f"{name} shape/CRS/geotransform differs from template")

    with rasterio.open(labels_path) as labels:
        aligned(labels, "labels.tif")
        if labels.count != 1:
            raise ValueError("labels.tif must have exactly one band")
        values = labels.read(1)
        if not (labels.read_masks(1)[foot] > 0).all() or not np.isin(values[foot], [0, 1]).all():
            raise ValueError("labels.tif must contain unmasked binary values inside the footprint")
        lab = (values == 1) & foot

    with rasterio.open(features_path) as features:
        aligned(features, "training_features.tif")
        names = [features.tags(i).get("band_name", f"band_{i}") for i in range(1, features.count + 1)]
        if names != expected_names:
            raise ValueError(f"Unexpected feature band order: {names}")
    return foot, lab, transform


def prepare() -> dict:
    ddir = data_dir()
    wdir = work_dir()
    wdir.mkdir(parents=True, exist_ok=True)
    bands_dir = wdir / "bands"

    feat_path = ddir / "training_features.tif"
    lab_path = ddir / "labels.tif"
    tmpl_path = ddir / "sample_submission.tif"
    foot, lab, transform_tuple = inspect_core_inputs(tmpl_path, lab_path, feat_path)
    shape_hw = foot.shape
    epsg = 32611

    band_stats = []
    total_sentinel_in_foot = 0
    any_sentinel_in_foot = np.zeros(shape_hw, dtype=bool)

    # Build a complete replacement before touching any existing cache. A failed
    # read/percentile calculation therefore leaves the previous cache intact.
    with tempfile.TemporaryDirectory(prefix=".bands-staging-", dir=wdir) as tmp:
        stage = Path(tmp) / "bands"
        stage.mkdir()
        np.save(stage / "_footprint.npy", foot)
        np.save(stage / "_labels.npy", lab)
        with rasterio.open(feat_path) as feat_src:
            nd = feat_src.nodata
            for idx, bname in enumerate(BASE_NAMES, 1):
                arr = feat_src.read(idx).astype(np.float32)
                is_sentinel = (~np.isfinite(arr)) | (arr < -1e38)
                if nd is not None and not np.isnan(nd):
                    is_sentinel |= arr == nd
                sentinel_in_foot = int(np.sum(is_sentinel & foot))
                total_sentinel_in_foot += sentinel_in_foot
                any_sentinel_in_foot |= is_sentinel & foot

                arr[is_sentinel] = np.nan
                arr[~foot] = np.nan
                valid_vals = arr[foot & np.isfinite(arr)]
                if not valid_vals.size:
                    raise ValueError(f"No valid values for feature band {bname} inside footprint")
                np.save(stage / f"{idx:02d}_{bname}.npy", arr)
                band_stats.append(
                    {
                        "index": idx,
                        "name": bname,
                        "finite_in_footprint": int(valid_vals.size),
                        "sentinel_in_footprint": sentinel_in_foot,
                        "min": float(np.min(valid_vals)),
                        "p05": float(np.percentile(valid_vals, 5)),
                        "median": float(np.median(valid_vals)),
                        "p95": float(np.percentile(valid_vals, 95)),
                        "max": float(np.max(valid_vals)),
                    }
                )

        manifest = {
            "schema_version": 1,
            "prepared_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "grid": {
                "epsg": epsg,
                "height": shape_hw[0],
                "width": shape_hw[1],
                "total_cells": int(shape_hw[0] * shape_hw[1]),
                "transform": list(transform_tuple),
                "pixel_size_m": [100.0, 100.0],
            },
            "counts": {
                "footprint_valid_pixels": int(foot.sum()),
                "outside_footprint_pixels": int((~foot).sum()),
                "positive_catalogue_label_pixels": int(lab.sum()),
                "negative_in_footprint_pixels": int(foot.sum() - lab.sum()),
                "total_sentinel_band_pixels_inside_footprint": total_sentinel_in_foot,
                "unique_footprint_pixels_with_any_sentinel": int(any_sentinel_in_foot.sum()),
            },
            "source_hashes": {
                "training_features.tif": sha256_file(feat_path),
                "labels.tif": sha256_file(lab_path),
                "sample_submission.tif": sha256_file(tmpl_path),
            },
            "input_grid_checks": {
                "template_pinned_grid": True,
                "labels_and_features_match_template_shape_crs_transform": True,
                "labels_binary_and_unmasked_inside_footprint": True,
                "organizer_authentication": "not established by local grid or hash checks",
            },
            "bands": band_stats,
        }

        # Stage the manifest on its destination filesystem before swapping the
        # cache; if either rename fails, restore the previous cache and leave
        # the previous manifest untouched. This is not crash-atomic across two
        # filesystems, but handled errors never knowingly retain a partial set.
        out_path = ROOT / "data" / "prepared_manifest.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=out_path.parent, suffix=".tmp", delete=False
            ) as file:
                temporary = Path(file.name)
                json.dump(manifest, file, indent=2, allow_nan=False)
                file.write("\n")

            previous = Path(tmp) / "previous-bands"
            if bands_dir.exists():
                bands_dir.rename(previous)
            try:
                stage.rename(bands_dir)
                temporary.replace(out_path)
            except Exception:
                if bands_dir.exists():
                    bands_dir.rename(stage)
                if previous.exists():
                    previous.rename(bands_dir)
                raise
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    return manifest


def main() -> None:
    manifest = prepare()
    print(
        f"[GEMSDOE36] Prepared {len(manifest['bands'])} bands | "
        f"Footprint={manifest['counts']['footprint_valid_pixels']:,} px | "
        f"Catalogue positives={manifest['counts']['positive_catalogue_label_pixels']:,} px | "
        f"Sanitized {manifest['counts']['total_sentinel_band_pixels_inside_footprint']:,} sentinel band-pixels."
    )


if __name__ == "__main__":
    main()
