#!/usr/bin/env python3
"""Build the derived feature set for GEMSDOE36 from the authorized competition rasters.

Memory-light design (2 vCPU, ~4 GB RAM):
  * every channel is stored as an individual float32 .npy file (48.6 MB each);
  * a compact *core* stack (the channels the field/emitter need) is also written
    as data/processed/core_stack.npz;
  * auxiliary channels (raw LiDAR bands, radiometric, extensions) live on disk and
    are loaded on demand by modules that need them.

Inputs (all on the official 3292x3730 EPSG:32611 100 m grid; SHA-256 pinned in
docs/research/sources.md and data/processed/manifest.json):

  data/raw/training_features.tif      19 float32 bands (official competition features)
  data/raw/labels.tif                 int8, existing USGS/INGENIOUS fault pixels
  data/raw/sample_submission.tif      float32 footprint template (valid mask)
  data/external/lidar_scarp_features_u8.tif   12 u8 1 m LiDAR scarp channels (0 = no LiDAR)
  data/external/geodawn_rad_u8.tif    4 u8  K/Th/U/TC (GeoDAWN, CC0)
  data/external/geodawn_extensions_u8.tif     4 u8  ThK/UK/UTh/TMI_up150 (GeoDAWN, CC0)
  data/external/derived_sgmc_faults_100m_u8.tif   1 u8 USGS SGMC faults (proxy/weak label)
  data/external/gdr_wellspring_in_footprint.csv   GDR 1391 wells/springs (CC BY 4.0)
  data/external/gdr_volcanic_vents_in_footprint.csv  GDR 1391 volcanic vents

Output:
  data/processed/channels/<name>.npy  all channels, float32, (3730, 3292)
  data/processed/core_stack.npz       {stack, names} for the core channel set
  data/processed/manifest.json        channel names, stats, source hashes, build metadata

This script only assembles and records data. No model or submission logic lives here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt, gaussian_filter

ROOT = Path(__file__).resolve().parents[1]

# Official 19-band names, verified from the embedded XML of training_features.tif
# (sample index 0 -> band 1). See docs/research/band_map.txt.
RAW_BAND_NAMES = [
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

LIDAR_BAND_NAMES = [
    "ex_max",
    "ex_mean",
    "step_max",
    "lapneg_max",
    "lappos_max",
    "downface_max",
    "upface_max",
    "cross_max",
    "relief",
    "coh100",
    "strike",
    "valid",
]
RAD_BAND_NAMES = ["rad_k", "rad_th", "rad_u", "rad_tc"]
EXT_BAND_NAMES = ["ext_thk", "ext_uk", "ext_uth", "ext_tmi_up150"]

# Core channel set written into core_stack.npz (the field/emitter working set).
CORE_CHANNELS = [
    f"raw_{n}" for n in RAW_BAND_NAMES
] + [
    "surface_scarp",
    "lidar_valid",
    "rad_composite",
    "ext_composite",
    "spring_ctx",
    "vent_ctx",
    "dist_catalogue_m",
    "sgmc_faults",
    "sgmc_off_catalogue",
    "footprint",
]


def sha256_of(path: Path, chunk: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            digest.update(block)
    return digest.hexdigest()


def percentile_clip_inplace(arr: np.ndarray, mask: np.ndarray, lo: float = 1.0,
                            hi: float = 99.5) -> None:
    """Clip a float32 band to its [lo, hi] percentiles (inside mask), in place."""
    v = arr[mask]
    if v.size == 0:
        return
    a, b = np.percentile(v, [lo, hi])
    if a < b:
        np.clip(arr, a, b, out=arr)


def read_single_band(path: Path, band: int = 1) -> np.ndarray:
    with rasterio.open(path) as ds:
        arr = ds.read(band).astype(np.float32)
        nodata = ds.nodata
    if nodata is not None and np.isfinite(nodata):
        arr = np.where(arr == nodata, 0.0, arr).astype(np.float32)
    return arr


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    args = parser.parse_args()
    data_dir = args.data_dir
    out_dir = data_dir / "processed"
    chan_dir = out_dir / "channels"
    chan_dir.mkdir(parents=True, exist_ok=True)

    raw_features = data_dir / "raw" / "training_features.tif"
    labels_path = data_dir / "raw" / "labels.tif"
    template_path = data_dir / "raw" / "sample_submission.tif"
    missing = [str(p) for p in (raw_features, labels_path, template_path) if not p.is_file()]
    if missing:
        print("Missing required inputs:")
        for item in missing:
            print(f"- {item}")
        return 2

    # --- Footprint and catalogue mask -------------------------------------------
    with rasterio.open(template_path) as ds:
        template = ds.read(1, masked=False)
        footprint = np.isfinite(template)
        template_crs = ds.crs.to_string()
        template_transform = list(ds.transform)
    if template_crs != "EPSG:32611":
        raise SystemExit(f"FAIL: template CRS is {template_crs}, expected EPSG:32611")
    with rasterio.open(labels_path) as ds:
        if (ds.width, ds.height) != (3292, 3730):
            raise SystemExit(f"FAIL: labels shape {(ds.width, ds.height)} != official grid")
        labels = ds.read(1, masked=True)
    catalogue = ((~labels.mask) & (labels == 1) & footprint).astype(np.float32)
    n_catalogue = int(catalogue.sum())
    if n_catalogue != 60988:
        print(f"NOTE: catalogue pixel count {n_catalogue} differs from the recorded 60988; "
              f"the grid is verified, the count is informational.")

    # Distance (m) from every pixel to the nearest provided-catalogue fault pixel.
    dist_catalogue_m = distance_transform_edt(catalogue == 0, sampling=(100.0, 100.0)).astype(
        np.float32
    )

    # RAM is tight (~4 GB): channels are written to disk and released immediately;
    # only names + stats are retained in memory.
    channel_names: list[str] = []
    stats: dict[str, dict] = {}

    def add_channel(name: str, arr: np.ndarray, note: str = "") -> None:
        arr = np.ascontiguousarray(arr, dtype=np.float32)
        np.save(chan_dir / f"{name}.npy", arr)
        v = arr[footprint]
        stats[name] = {
            "min": float(v.min()) if v.size else None,
            "max": float(v.max()) if v.size else None,
            "median": float(np.median(v)) if v.size else None,
            "note": note,
        }
        channel_names.append(name)
        del arr

    # --- Raw 19 bands (one band at a time to bound RAM) ---------------------------
    with rasterio.open(raw_features) as ds:
        if (ds.width, ds.height) != (3292, 3730) or ds.count != 19:
            raise SystemExit(
                f"FAIL: training_features grid/bands {(ds.width, ds.height, ds.count)}"
            )
        raw_nodata = ds.nodata
        for i, name in enumerate(RAW_BAND_NAMES):
            band = ds.read(i + 1).astype(np.float32)
            if raw_nodata is not None and np.isfinite(raw_nodata):
                band = np.where(band == raw_nodata, 0.0, band).astype(np.float32)
            percentile_clip_inplace(band, footprint)
            add_channel(f"raw_{name}", band, f"official band {i + 1}, p1-p99.5 clipped")

    # --- External layers ---------------------------------------------------------
    external = {
        "lidar": data_dir / "external" / "lidar_scarp_features_u8.tif",
        "rad": data_dir / "external" / "geodawn_rad_u8.tif",
        "ext": data_dir / "external" / "geodawn_extensions_u8.tif",
        "sgmc": data_dir / "external" / "derived_sgmc_faults_100m_u8.tif",
    }
    for path in external.values():
        if not path.is_file():
            print(f"NOTE: {path} missing; skipping its channels")

    lidar = None
    if external["lidar"].is_file():
        with rasterio.open(external["lidar"]) as ds:
            lidar = ds.read()
        for i, name in enumerate(LIDAR_BAND_NAMES):
            add_channel(f"lidar_{name}", lidar[i].astype(np.float32) / 255.0,
                        "1 m LiDAR scarp feature, u8/255; 0 = no LiDAR")
        valid = lidar[11].astype(bool)
        step = np.maximum.reduce(
            [
                lidar[2].astype(np.float32),  # step_max
                lidar[5].astype(np.float32),  # downface_max
                lidar[6].astype(np.float32),  # upface_max
                lidar[7].astype(np.float32),  # cross_max
            ]
        ) / 255.0
        curvature = np.maximum(lidar[3].astype(np.float32), lidar[4].astype(np.float32)) / 255.0
        surface_scarp = np.where(valid, np.maximum(step, curvature), 0.0).astype(np.float32)
        add_channel("surface_scarp", surface_scarp,
                    "max(step, curvature) * LiDAR-valid, u8/255; zero-depth channel")
        add_channel("lidar_valid", valid.astype(np.float32), "LiDAR tile coverage mask")

    if external["rad"].is_file():
        with rasterio.open(external["rad"]) as ds:
            rad = ds.read()
        for i, name in enumerate(RAD_BAND_NAMES):
            add_channel(name, rad[i].astype(np.float32) / 255.0,
                        "GeoDAWN radiometric, u8/255 (1st-99th pct quantised)")
        # Radiometric *contrast* composite: faults juxtapose lithologies, so the
        # spatial gradient of the elemental channels is the lineament signal.
        rad_grad = np.zeros(footprint.shape, dtype=np.float32)
        for i in range(4):
            g = gaussian_filter(rad[i].astype(np.float32) / 255.0, sigma=1.5)
            gy, gx = np.gradient(g)
            rad_grad = np.maximum(rad_grad, np.sqrt(gx * gx + gy * gy).astype(np.float32))
        rad_grad *= 6.0  # rescale the small gradient magnitudes to O(0.1-1)
        np.clip(rad_grad, 0.0, 1.0, out=rad_grad)
        add_channel("rad_composite", rad_grad, "max |grad| over K/Th/U/TC, x6, clipped to [0,1]")

    if external["ext"].is_file():
        with rasterio.open(external["ext"]) as ds:
            ext = ds.read()
        for i, name in enumerate(EXT_BAND_NAMES):
            add_channel(name, ext[i].astype(np.float32) / 255.0,
                        "GeoDAWN extension grid, u8/255 (1st-99th pct quantised)")
        ext_grad = np.zeros(footprint.shape, dtype=np.float32)
        for i in range(4):
            g = gaussian_filter(ext[i].astype(np.float32) / 255.0, sigma=1.5)
            gy, gx = np.gradient(g)
            ext_grad = np.maximum(ext_grad, np.sqrt(gx * gx + gy * gy).astype(np.float32))
        ext_grad *= 6.0
        np.clip(ext_grad, 0.0, 1.0, out=ext_grad)
        add_channel("ext_composite", ext_grad,
                    "max |grad| over ThK/UK/UTh/TMI_up150, x6, clipped to [0,1]")

    if external["sgmc"].is_file():
        with rasterio.open(external["sgmc"]) as ds:
            sgmc = ds.read(1)
        add_channel("sgmc_faults", sgmc.astype(np.float32),
                    "USGS SGMC faults rasterised at 100 m (proxy; includes pre-Quaternary)")
        sgmc_off = sgmc.astype(bool) & (dist_catalogue_m > 300.0)
        add_channel("sgmc_off_catalogue", sgmc_off.astype(np.float32),
                    "SGMC faults farther than 300 m from the provided catalogue")

    # --- Geothermal-manifest context (GDR 1391, CC BY 4.0) ------------------------
    spring_ctx = np.zeros(footprint.shape, dtype=np.float32)
    vents_ctx = np.zeros(footprint.shape, dtype=np.float32)
    spring_csv = data_dir / "external" / "gdr_wellspring_in_footprint.csv"
    vent_csv = data_dir / "external" / "gdr_volcanic_vents_in_footprint.csv"
    n_springs = n_vents = 0
    if spring_csv.is_file():
        h, w = footprint.shape
        with open(spring_csv) as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("row,"):
                    continue
                parts = line.split(",")
                if len(parts) < 9:
                    continue
                try:
                    row, col = int(float(parts[3])), int(float(parts[4]))
                except ValueError:
                    continue
                if not (0 <= row < h and 0 <= col < w) or not footprint[row, col]:
                    continue
                try:
                    temp = float(parts[8])
                except ValueError:
                    temp = 150.0
                weight = float(np.clip((temp - 20.0) / 180.0, 0.0, 1.0))
                if weight <= 0.0:
                    continue
                r0, r1 = max(0, row - 5), min(h, row + 6)
                c0, c1 = max(0, col - 5), min(w, col + 6)
                yr, xr = np.mgrid[r0:r1, c0:c1]
                d2 = (yr - row) ** 2 + (xr - col) ** 2
                spring_ctx[r0:r1, c0:c1] = np.maximum(
                    spring_ctx[r0:r1, c0:c1], weight * np.exp(-d2 / 18.0)
                )
                n_springs += 1
    if vent_csv.is_file():
        h, w = footprint.shape
        with open(vent_csv) as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("name,"):
                    continue
                parts = line.split(",")
                if len(parts) < 5:
                    continue
                try:
                    row, col = int(float(parts[3])), int(float(parts[4]))
                except ValueError:
                    continue
                if not (0 <= row < h and 0 <= col < w) or not footprint[row, col]:
                    continue
                r0, r1 = max(0, row - 5), min(h, row + 6)
                c0, c1 = max(0, col - 5), min(w, col + 6)
                yr, xr = np.mgrid[r0:r1, c0:c1]
                d2 = (yr - row) ** 2 + (xr - col) ** 2
                vents_ctx[r0:r1, c0:c1] = np.maximum(vents_ctx[r0:r1, c0:c1], np.exp(-d2 / 18.0))
                n_vents += 1
    add_channel("spring_ctx", spring_ctx, f"GDR 1391 wells/springs, T-weighted kernel (n={n_springs})")
    add_channel("vent_ctx", vents_ctx, f"GDR 1391 volcanic vents kernel (n={n_vents})")

    add_channel("dist_catalogue_m", dist_catalogue_m,
                "distance (m) to nearest provided-catalogue fault pixel")
    add_channel("footprint", footprint.astype(np.float32), "sample-submission valid mask")

    # --- Core stack + manifest ----------------------------------------------------
    names = list(CORE_CHANNELS)
    missing_core = [n for n in names if n not in channel_names]
    if missing_core:
        raise SystemExit(f"FAIL: missing core channels {missing_core}")
    # Rebuild the compact core stack from disk (channels were released to bound RAM).
    core = np.empty((len(names), 3730, 3292), dtype=np.float32)
    for i, n in enumerate(names):
        core[i] = np.load(chan_dir / f"{n}.npy")
    np.savez(out_dir / "core_stack.npz", stack=core, names=np.array(names))
    del core

    manifest = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "generated_by": "scripts/prepare_data_h6.py",
        "grid": {
            "width": 3292,
            "height": 3730,
            "crs": template_crs,
            "transform": template_transform,
            "resolution_m": 100.0,
        },
        "footprint_px": int(footprint.sum()),
        "catalogue_px": n_catalogue,
        "spring_sites": n_springs,
        "vent_sites": n_vents,
        "core_channels": names,
        "all_channels": sorted(channel_names),
        "stats": stats,
        "sources": {
            "training_features.tif": sha256_of(raw_features),
            "labels.tif": sha256_of(labels_path),
            "sample_submission.tif": sha256_of(template_path),
            **{key: sha256_of(path) for key, path in external.items() if path.is_file()},
        },
        "provenance": (
            "Owner-supplied mirrors of the official DrivenData competition files, "
            "SHA-256 pinned in the owner's data manifest (see docs/research/sources.md). "
            "External layers derived from USGS GeoDAWN (CC0), USGS 3DEP 1 m LiDAR, "
            "USGS SGMC (public domain), and GDR 1391 (CC BY 4.0)."
        ),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"PASS: {len(channel_names)} channels written to {chan_dir}")
    print(f"PASS: core_stack.npz with {len(names)} channels")
    print(f"PASS: footprint={int(footprint.sum())} px, catalogue={n_catalogue} px, "
          f"spring sites={n_springs}, vent sites={n_vents}")
    print("NOTE: the stack is a feature container, not a prediction; no model was trained here.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
