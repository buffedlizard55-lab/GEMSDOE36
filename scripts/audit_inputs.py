#!/usr/bin/env python3
"""Inventory and compare competition rasters after authorized local placement."""

from __future__ import annotations

import argparse
from pathlib import Path

import rasterio


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--features", type=Path, required=True)
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--template", type=Path, required=True)
    args = parser.parse_args()
    paths = {"features": args.features, "labels": args.labels, "template": args.template}
    missing = [f"{name}: {path}" for name, path in paths.items() if not path.is_file()]
    if missing:
        print("Missing required files (obtain through the official competition data page):")
        for item in missing:
            print(f"- {item}")
        return 2

    with rasterio.open(args.template) as template:
        print(
            f"template: {template.width}x{template.height}, bands={template.count}, "
            f"dtype={template.dtypes}, CRS={template.crs}, transform={template.transform}, "
            f"nodata={template.nodata}"
        )
        grid = (template.width, template.height, template.crs, template.transform)
        for name, path in (("features", args.features), ("labels", args.labels)):
            with rasterio.open(path) as dataset:
                print(
                    f"{name}: {dataset.width}x{dataset.height}, bands={dataset.count}, "
                    f"dtype={dataset.dtypes}, CRS={dataset.crs}, transform={dataset.transform}, "
                    f"nodata={dataset.nodata}"
                )
                candidate = (dataset.width, dataset.height, dataset.crs, dataset.transform)
                if candidate != grid:
                    raise SystemExit(f"FAIL: {name} grid differs from the official template")
    print(
        "PASS: all three rasters share an identical grid. Inspect band-level masks before training."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
