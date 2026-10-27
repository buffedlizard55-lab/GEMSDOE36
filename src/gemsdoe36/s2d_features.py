"""S2D-36: Seamless 10 m 3DEP scarp, survey/road deconfounding & Stage-2 corridor features.

Preregistered in ``evidence/s2d36_preregistration_20261027.json`` (SHA-256 locked).
Every Stage-1 feature in ``S2D_FEATURES`` and every Stage-2 operator in
``build_s2d_stage2_corridor_features`` is 100% label-free and 100% catalogue-free
(reads zero pixels of ``labels.tif``, ``existing_faults.tif``, or ``SGMC``).
"""

from __future__ import annotations

import gc
import hashlib
import tarfile
import urllib.request
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_erosion, distance_transform_edt, gaussian_filter
from scipy.signal import fftconvolve

from .kpl_features import N_ORIENT, _line_kernel, _robust_unit, line_anisotropy

DEM10_SHA256: dict[str, str] = {
    "dem10_slope_max": "fd46738e9a58a6f40c130c3c70f645525dbfc12d27b6ed149e596e6a379cbfaa",
    "dem10_slope_mean": "338b443c441db61120faf36437ec61dfcccaa569c41aa3099ed3accef5a35f95",
    "dem10_slope_std": "9c15e0e760d8255eb0473821a07cc09e4fe4b40746e6e37278e691f615c0f642",
    "dem10_hgm20_max": "f58df86b0be3b3dc54affc60dc7d77a95db3dafb9c1267eac4912c5d8e57526b",
    "dem10_hgm50_max": "1cca42538ec0c91951b578136893eb5d90cd1414c45257d2a72ebe80b29f0f40",
    "dem10_hgm200_mean": "9328f889f4d607f8530840da138741b7431da49d2432b0ab2da110a82984102b",
    "dem10_steep_ratio_max": "eaf3d5e24c6769ffb98665e75c9665dbaa16bdb79708900217dca955031e6828",
    "dem10_resid_std": "50db8caa815cb09cc695ec230f15f41e8e04cd9bef5fc09b07b06aeadd44a86e",
    "dem10_resid_range": "bbcf8a462ace31a80964ba8a7ab76fcbcb347deb4f4d2919166b3eda5c721b0c",
    "dem10_curv_absmax": "58e82f1301032b46b10344b9299b83e6ce5bed1ca83e320f078fa57321bff632",
    "dem10_onesided": "02d1d241de9534d307f314d0b2f8a857ceb1ce0d099fd7dee8872a83bd0271f8",
    "dem10_onesided3": "bca9faf8e0c572ecb1e77b6c94b0cb96c41e824873cb7747e0ece28b531598d2",
}

TIGER_ROAD_SHA256 = "e5350423508968fa2d32b0a6ae0d3fb4ae3ea645e3b8736f0c8e7ad9ff2f2988"
ACQ_BLOCK_SHA256 = "2c0785c4b3ec46c734d1be7a7aedbb3e816201100ab358033a3af074418c894a"

S2D_FEATURES: tuple[str, ...] = (
    "s2d_dem10_slope_max",
    "s2d_dem10_slope_mean",
    "s2d_dem10_slope_std",
    "s2d_dem10_hgm20_max",
    "s2d_dem10_hgm50_max",
    "s2d_dem10_hgm200_mean",
    "s2d_dem10_steep_ratio_max",
    "s2d_dem10_resid_std",
    "s2d_dem10_resid_range",
    "s2d_dem10_curv_absmax",
    "s2d_dem10_onesided",
    "s2d_dem10_onesided3",
    "s2d_dem10_scarp_sharpness",
    "s2d_dem10_asymm_scarp_idx",
    "s2d_dem10_onesided3_line15",
    "s2d_dem10_piedmont_inflection",
    "s2d_tiger_road_dist_log",
    "s2d_road_cut_mimic",
    "s2d_geodawn_seam_dist_km",
    "s2d_mag_hg_block_z",
    "s2d_rad_k_block_z",
)

S2D_STAGE2_FEATURES: tuple[str, ...] = (
    "s2_p1_raw",
    "s2_p1_logit",
    "s2_p1_g1p5",
    "s2_p1_g4",
    "s2_p1_g8",
    "s2_p1_g16",
    "s2_p1_halo_sharp4",
    "s2_p1_halo_sharp8",
    "s2_p1_line9_max",
    "s2_p1_line9_ortho_contrast",
    "s2_p1_line17_max",
    "s2_p1_line17_aniso",
    "s2_p1_hessian_ridge",
    "s2_corrob_surf_subsurf",
)

S2D_EXP3_AUX_FEATURES: tuple[str, ...] = (
    "s2_dual_raw",
    "s2_dual_g4",
    "s2_dual_line13_max",
    "s2_dual_corrob_quat",
)


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for ch in iter(lambda: fh.read(1 << 20), b""):
            h.update(ch)
    return h.hexdigest()


def _stream_codeload(repo: str, ref: str, wanted: dict[str, Path]) -> None:
    url = f"https://codeload.github.com/{repo}/tar.gz/{ref}"
    req = urllib.request.Request(url, headers={"User-Agent": "gemsdoe36-s2d36/1.0"})
    with urllib.request.urlopen(req, timeout=240) as resp:
        with tarfile.open(fileobj=resp, mode="r|gz") as tf:
            for member in tf:
                if not member.isfile():
                    continue
                rel = member.name.split("/", 1)[1]
                if rel in wanted:
                    out = wanted[rel]
                    out.parent.mkdir(parents=True, exist_ok=True)
                    src = tf.extractfile(member)
                    assert src is not None
                    with out.open("wb") as dst:
                        while True:
                            chunk = src.read(1 << 20)
                            if not chunk:
                                break
                            dst.write(chunk)


def ensure_s2d36_external_layers(data_raw_dir: Path) -> Path:
    """Verify or stream-restore SHA-256 pinned public-domain S2D-36 external rasters."""
    ext_dir = data_raw_dir / "external" / "s2d36"
    dem10_dir = ext_dir / "dem10"
    dem10_dir.mkdir(parents=True, exist_ok=True)

    missing_dem10 = {
        f"{ch}.f32.npy": dem10_dir / f"{ch}.f32.npy"
        for ch, sha in DEM10_SHA256.items()
        if not (dem10_dir / f"{ch}.f32.npy").is_file()
        or _sha256_file(dem10_dir / f"{ch}.f32.npy") != sha
    }
    if missing_dem10:
        _stream_codeload("buffedlizard55-lab/GEMSDOE10", "ext/dem10-36343078537", missing_dem10)
    for ch, sha in DEM10_SHA256.items():
        p = dem10_dir / f"{ch}.f32.npy"
        got = _sha256_file(p)
        if got != sha:
            raise RuntimeError(f"SHA-256 mismatch for {p}: {got} != {sha}")

    audit_wanted: dict[str, Path] = {}
    road_p = ext_dir / "tiger_road_distance_m.tif"
    block_p = ext_dir / "acquisition_block_id_100m.tif"
    if not road_p.is_file() or _sha256_file(road_p) != TIGER_ROAD_SHA256:
        audit_wanted["data/external/audit_sources/tiger_road_distance_m.tif"] = road_p
    if not block_p.is_file() or _sha256_file(block_p) != ACQ_BLOCK_SHA256:
        audit_wanted["data/external/audit_sources/acquisition_block_id_100m.tif"] = block_p
    if audit_wanted:
        _stream_codeload(
            "buffedlizard55-lab/GEMSDOE24",
            "07345ea0604953d7efb858d9cfbc21e20c7aca0b",
            audit_wanted,
        )
    if _sha256_file(road_p) != TIGER_ROAD_SHA256:
        raise RuntimeError(f"SHA-256 mismatch for {road_p}")
    if _sha256_file(block_p) != ACQ_BLOCK_SHA256:
        raise RuntimeError(f"SHA-256 mismatch for {block_p}")
    return ext_dir


def _within_block_robust_z(field_fp: np.ndarray, block_fp: np.ndarray) -> np.ndarray:
    """Label-free within-survey-block median/MAD standardization."""
    out = np.zeros_like(field_fp, dtype=np.float32)
    for b_id in (1, 2, 3, 4):
        m = block_fp == b_id
        if not np.any(m):
            continue
        vals = field_fp[m]
        finite = vals[np.isfinite(vals)]
        if finite.size == 0:
            continue
        med = float(np.median(finite))
        mad = float(np.median(np.abs(finite - med))) * 1.4826
        scale = mad if mad > 1e-6 else (float(np.std(finite)) or 1.0)
        out[m] = np.clip(( np.nan_to_num(vals, nan=med) - med ) / scale, -8.0, 8.0).astype(np.float32)
    # Any residual block==0 pixels outside blocks 1..4
    m0 = ~np.isin(block_fp, (1, 2, 3, 4))
    if np.any(m0):
        med = float(np.nanmedian(field_fp))
        scale = float(np.nanstd(field_fp)) or 1.0
        out[m0] = np.clip((np.nan_to_num(field_fp[m0], nan=med) - med) / scale, -8.0, 8.0).astype(
            np.float32
        )
    return out


def _compute_geodawn_seam_dist_km(block_2d: np.ndarray, fp: np.ndarray) -> np.ndarray:
    """Distance in km (capped at 15 km) to internal boundaries between GeoDAWN blocks 1..4."""
    seam = np.zeros(fp.shape, dtype=bool)
    for b_id in (1, 2, 3, 4):
        bm = fp & (block_2d == b_id)
        if not np.any(bm):
            continue
        interior = binary_erosion(bm, structure=np.ones((3, 3), dtype=bool), border_value=0)
        # Boundary pixel touching another valid footprint pixel in a DIFFERENT block
        border = bm & ~interior
        seam |= border
    # Exclude the outer footprint boundary itself so only INTER-BLOCK seams remain
    fp_interior = binary_erosion(fp, structure=np.ones((3, 3), dtype=bool), border_value=0)
    internal_seam = seam & fp_interior
    if not np.any(internal_seam):
        return np.full(int(fp.sum()), 15.0, dtype=np.float32)
    dist_km = distance_transform_edt(~internal_seam).astype(np.float32) * 0.1
    return np.minimum(dist_km[fp], 15.0).astype(np.float32)


def build_s2d_stage1_features(
    cols_fp: dict[str, np.ndarray],
    fp: np.ndarray,
    data_raw_dir: Path,
) -> dict[str, np.ndarray]:
    """Build 21 footprint-indexed (shape ``(n_fp,)``, ``float32``) label-free S2D features."""
    ext_dir = ensure_s2d36_external_layers(data_raw_dir)
    dem10_dir = ext_dir / "dem10"
    n_fp = int(fp.sum())
    out: dict[str, np.ndarray] = {}

    raw10: dict[str, np.ndarray] = {}
    for ch in DEM10_SHA256:
        arr = np.asarray(np.load(dem10_dir / f"{ch}.f32.npy"), dtype=np.float32)
        if arr.shape != (n_fp,):
            raise ValueError(f"Expected ({n_fp},) for {ch}, got {arr.shape}")
        arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)
        raw10[ch] = arr
        out[f"s2d_{ch}"] = arr

    hgm20 = np.maximum(raw10["dem10_hgm20_max"], 0.0)
    hgm200 = np.maximum(raw10["dem10_hgm200_mean"], 0.0)
    onesided3 = np.maximum(raw10["dem10_onesided3"], 0.0)
    steep_ratio = np.maximum(raw10["dem10_steep_ratio_max"], 0.0)
    slope_mean = np.maximum(raw10["dem10_slope_mean"], 0.0)

    out["s2d_dem10_scarp_sharpness"] = (hgm20 / (hgm200 + 0.02)).astype(np.float32)
    out["s2d_dem10_asymm_scarp_idx"] = (onesided3 * np.log1p(steep_ratio)).astype(np.float32)

    # 2D spatial transforms on seamless 10 m DEM channels
    os3_2d = np.zeros(fp.shape, dtype=np.float32)
    os3_2d[fp] = onesided3
    os3_unit = _robust_unit(os3_2d, fp)
    out["s2d_dem10_onesided3_line15"] = line_anisotropy(os3_unit, 15)[fp].astype(np.float32)
    del os3_2d, os3_unit

    slp_2d = np.zeros(fp.shape, dtype=np.float32)
    slp_2d[fp] = slope_mean
    fp_f = fp.astype(np.float32)
    w2 = np.maximum(gaussian_filter(fp_f, 2.0), 1e-6)
    w8 = np.maximum(gaussian_filter(fp_f, 8.0), 1e-6)
    g2 = gaussian_filter(slp_2d, 2.0) / w2
    g8 = gaussian_filter(slp_2d, 8.0) / w8
    out["s2d_dem10_piedmont_inflection"] = (g8[fp] - g2[fp]).astype(np.float32)
    del slp_2d, fp_f, w2, w8, g2, g8

    # Census TIGER/Line 2024 road distance deconfounding
    with rasterio.open(ext_dir / "tiger_road_distance_m.tif") as ds:
        road_2d = ds.read(1).astype(np.float32)
    road_fp = np.maximum(np.nan_to_num(road_2d[fp], nan=5000.0), 0.0).astype(np.float32)
    del road_2d
    out["s2d_tiger_road_dist_log"] = np.log1p(road_fp).astype(np.float32)
    out["s2d_road_cut_mimic"] = (np.exp(-road_fp / 120.0) * hgm20).astype(np.float32)
    del road_fp

    # GeoDAWN 4-block survey seam & inter-block calibration normalization
    with rasterio.open(ext_dir / "acquisition_block_id_100m.tif") as ds:
        block_2d = ds.read(1)
    block_fp = block_2d[fp].astype(np.int16)
    out["s2d_geodawn_seam_dist_km"] = _compute_geodawn_seam_dist_km(block_2d, fp)
    del block_2d

    mag_fp = np.log1p(np.maximum(np.nan_to_num(cols_fp["org_tmi_hg"], nan=0.0), 0.0)).astype(
        np.float32
    )
    rad_k_fp = np.nan_to_num(cols_fp["gd_K"], nan=float(np.nanmedian(cols_fp["gd_K"]))).astype(
        np.float32
    )
    out["s2d_mag_hg_block_z"] = _within_block_robust_z(mag_fp, block_fp)
    out["s2d_rad_k_block_z"] = _within_block_robust_z(rad_k_fp, block_fp)

    del raw10, mag_fp, rad_k_fp, block_fp
    gc.collect()
    assert tuple(out.keys()) == S2D_FEATURES
    return out


def _norm_gauss(arr: np.ndarray, domain: np.ndarray, sigma: float) -> np.ndarray:
    dom_f = domain.astype(np.float32)
    num = gaussian_filter((arr * dom_f).astype(np.float32), sigma)
    den = np.maximum(gaussian_filter(dom_f, sigma), 1e-6)
    return (num / den).astype(np.float32)


def _norm_line_stats(
    arr: np.ndarray, domain: np.ndarray, half: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (max_along, ortho_contrast_at_argmax, aniso_ratio) over 8 orientations."""
    dom_f = domain.astype(np.float32)
    masked = (arr * dom_f).astype(np.float32)
    resps = np.empty((N_ORIENT, arr.shape[0], arr.shape[1]), dtype=np.float32)
    for k in range(N_ORIENT):
        kern = _line_kernel(k * 180.0 / N_ORIENT, half)
        num = fftconvolve(masked, kern, mode="same").astype(np.float32)
        den = np.maximum(fftconvolve(dom_f, kern, mode="same").astype(np.float32), 1e-5)
        resps[k] = np.clip(num / den, 0.0, 1.0)
    best_k = np.argmax(resps, axis=0)
    ortho_k = (best_k + (N_ORIENT // 2)) % N_ORIENT
    rr, cc = np.ogrid[: arr.shape[0], : arr.shape[1]]
    mx = resps[best_k, rr, cc]
    ortho = resps[ortho_k, rr, cc]
    mean = resps.mean(axis=0)
    del resps, best_k, ortho_k
    aniso = (mx - mean) / (mean + 1e-4)
    return mx.astype(np.float32), (mx - ortho).astype(np.float32), aniso.astype(np.float32)


def build_s2d_stage2_corridor_features(
    p1_2d: np.ndarray,
    domain_mask: np.ndarray,
    subsurf_support_2d: np.ndarray,
    eval_flat: np.ndarray,
) -> np.ndarray:
    """Build ``(len(eval_flat), 14)`` float32 Stage-2 corridor matrix on ``domain_mask``."""
    p = np.where(domain_mask, np.clip(p1_2d, 0.0, 1.0), 0.0).astype(np.float32)
    p_clip = np.clip(p, 1e-5, 1.0 - 1e-5)
    logit = np.log(p_clip / (1.0 - p_clip)).astype(np.float32)
    del p_clip

    g1p5 = _norm_gauss(p, domain_mask, 1.5)
    g2 = _norm_gauss(p, domain_mask, 2.0)
    g4 = _norm_gauss(p, domain_mask, 4.0)
    g8 = _norm_gauss(p, domain_mask, 8.0)
    g16 = _norm_gauss(p, domain_mask, 16.0)

    sharp4 = (p - g4).astype(np.float32)
    sharp8 = (g1p5 - g8).astype(np.float32)

    l9_max, l9_ortho, _l9_aniso = _norm_line_stats(p, domain_mask, 4)
    l17_max, _l17_ortho, l17_aniso = _norm_line_stats(p, domain_mask, 8)

    # 2D Hessian ridge crest strength max(0, -lambda_min) on smoothed surface g2
    gy, gx = np.gradient(g2)
    gyy, gyx = np.gradient(gy)
    _gxy, gxx = np.gradient(gx)
    del gx, gy
    tr = gxx + gyy
    det_disc = np.sqrt(np.maximum((gxx - gyy) ** 2 + 4.0 * (gyx**2), 0.0))
    lam_min = 0.5 * (tr - det_disc)
    hess_ridge = np.maximum(0.0, -lam_min).astype(np.float32)
    del gxx, gyy, gyx, tr, det_disc, lam_min

    corrob = np.sqrt(np.maximum(g2, 0.0) * np.clip(subsurf_support_2d, 0.0, 1.0)).astype(
        np.float32
    )

    cols = (
        p,
        logit,
        g1p5,
        g4,
        g8,
        g16,
        sharp4,
        sharp8,
        l9_max,
        l9_ortho,
        l17_max,
        l17_aniso,
        hess_ridge,
        corrob,
    )
    mat = np.empty((len(eval_flat), len(cols)), dtype=np.float32)
    for j, c in enumerate(cols):
        mat[:, j] = c.ravel()[eval_flat]
    del p, logit, g1p5, g2, g4, g8, g16, sharp4, sharp8, l9_max, l9_ortho, l17_max, l17_aniso
    del hess_ridge, corrob, cols
    gc.collect()
    return mat


def build_s2d_dual_aux_features(
    p_dual_2d: np.ndarray,
    p1_2d: np.ndarray,
    domain_mask: np.ndarray,
    eval_flat: np.ndarray,
) -> np.ndarray:
    """Build ``(len(eval_flat), 4)`` float32 EXP-3 OOF dual-population corridor features."""
    pd = np.where(domain_mask, np.clip(p_dual_2d, 0.0, 1.0), 0.0).astype(np.float32)
    p1 = np.where(domain_mask, np.clip(p1_2d, 0.0, 1.0), 0.0).astype(np.float32)
    gd4 = _norm_gauss(pd, domain_mask, 4.0)
    gd2 = _norm_gauss(pd, domain_mask, 2.0)
    gq2 = _norm_gauss(p1, domain_mask, 2.0)
    ld13_max, _, _ = _norm_line_stats(pd, domain_mask, 6)
    corrob = np.sqrt(np.maximum(gd2, 0.0) * np.maximum(gq2, 0.0)).astype(np.float32)

    cols = (pd, gd4, ld13_max, corrob)
    mat = np.empty((len(eval_flat), 4), dtype=np.float32)
    for j, c in enumerate(cols):
        mat[:, j] = c.ravel()[eval_flat]
    del pd, p1, gd4, gd2, gq2, ld13_max, corrob, cols
    gc.collect()
    return mat


def apply_halo_sharpening(
    p_blend_2d: np.ndarray,
    domain_mask: np.ndarray,
    gamma_halo: float = 0.18,
) -> np.ndarray:
    """Province-preserving 800 m vs 2.4 km piedmont halo subtraction."""
    p = np.where(domain_mask, np.clip(p_blend_2d, 0.0, 1.0), 0.0).astype(np.float32)
    g8 = _norm_gauss(p, domain_mask, 8.0)
    g24 = _norm_gauss(p, domain_mask, 24.0)
    overshoot = np.maximum(0.0, g8 - g24)
    sharpened = np.clip(p - gamma_halo * overshoot, 0.0, 1.0)
    return np.where(domain_mask, sharpened, 0.0).astype(np.float32)
