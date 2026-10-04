"""Hydrothermal Upflow Conduit Modeling from GDR 1391 Geothermometer Chemistry.

In the Great Basin extensional province, hydrothermal convection cells are channeled along
permeable fault zones. Deep reservoir temperatures estimated from silica (quartz/chalcedony)
and cation geothermometers reflect reservoir conditions (>130-200+ deg C).
When hot springs occur >1.5-3.0 km from any catalogued USGS fault, they indicate active,
permeable hidden fault conduits feeding fluid upflow.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter
from scipy.spatial import cKDTree


def load_gdr_spring_chemistry(data_dir: Path) -> pd.DataFrame:
    """Load and parse GDR 1391 wellspring chemistry table."""
    csv_path = data_dir / "external" / "gdr_wellspring_in_footprint.csv"
    if not csv_path.exists():
        csv_path = data_dir / "gdr_wellspring_in_footprint.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"GDR wellspring CSV not found under {data_dir}")

    df = pd.read_csv(csv_path)
    chem = df[df["layer"] == "spring_chemistry_20220808"].copy()
    for col in ("temp_c", "geothermquartz_c", "geothermchalc_c", "geothermcat_c"):
        if col in chem.columns:
            chem[col] = pd.to_numeric(chem[col], errors="coerce")
    chem = chem.dropna(subset=["row", "col"])
    return chem


def idw_surface_chunked(
    points_rc: np.ndarray,
    values: np.ndarray,
    shape: tuple[int, int],
    length_scale_px: float = 20.0,
    k: int = 8,
    sigma: float = 3.0,
    chunk_size: int = 400_000,
) -> np.ndarray:
    """Memory-bounded inverse-distance-weighted interpolation."""
    out = np.zeros(shape, dtype=np.float32)
    if points_rc.shape[0] == 0 or values.size == 0:
        return out
    tree = cKDTree(points_rc.astype(np.float64))
    yy, xx = np.mgrid[0 : shape[0], 0 : shape[1]]
    grid = np.column_stack([yy.ravel().astype(np.float64), xx.ravel().astype(np.float64)])
    acc = np.zeros(grid.shape[0], dtype=np.float64)
    wsum = np.zeros(grid.shape[0], dtype=np.float64)

    for s in range(0, grid.shape[0], chunk_size):
        chunk = grid[s : s + chunk_size]
        d, idx = tree.query(chunk, k=min(k, points_rc.shape[0]))
        d = np.atleast_2d(d.T).T if d.ndim == 1 else d
        idx = np.atleast_2d(idx.T).T if idx.ndim == 1 else idx
        w = 1.0 / (1.0 + (d / float(length_scale_px)) ** 2)
        acc[s : s + chunk_size] = (w * values[idx]).sum(axis=1)
        wsum[s : s + chunk_size] = w.sum(axis=1)

    vals = np.where(wsum > 0, acc / np.maximum(wsum, 1e-12), 0.0)
    out = vals.reshape(shape).astype(np.float32)
    if sigma > 0:
        out = gaussian_filter(out, sigma=sigma)
    return out


def compute_geothermal_reservoir_temperature_field(
    data_dir: Path,
    footprint: np.ndarray,
    length_scale_px: float = 20.0,
) -> tuple[np.ndarray, dict]:
    """Compute 2D continuous reservoir temperature field (deg C) and stats."""
    chem = load_gdr_spring_chemistry(data_dir)
    site = (
        chem.groupby(["row", "col"])
        .agg(
            T_q=("geothermquartz_c", "max"),
            T_c=("geothermchalc_c", "max"),
            T_k=("geothermcat_c", "max"),
            T_m=("temp_c", "max"),
            d_fault=("dist_known_fault_px", "min"),
        )
        .reset_index()
    )
    est = site[["T_q", "T_c", "T_k", "T_m"]]
    t_res_site = est.max(axis=1)

    m = t_res_site.notna()
    pts = site.loc[m, ["row", "col"]].to_numpy()
    vals = t_res_site[m].to_numpy(dtype=np.float64)

    t_field = idw_surface_chunked(
        pts, vals, footprint.shape, length_scale_px=length_scale_px, k=8, sigma=3.0
    )
    t_field[~footprint] = 0.0

    far = site["d_fault"] > 15.0  # > 1.5 km
    stats = {
        "n_spring_sites": int(m.sum()),
        "n_sites_gt130C": int((t_res_site >= 130).sum()),
        "n_sites_gt150C": int((t_res_site >= 150).sum()),
        "n_sites_gt130C_far_from_faults": int(((t_res_site >= 130) & far).sum()),
        "n_sites_gt150C_far_from_faults": int(((t_res_site >= 150) & far).sum()),
        "max_temp_c": float(np.nanmax(t_res_site)),
    }
    return t_field, stats
