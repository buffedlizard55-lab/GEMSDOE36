"""SFD-36: Signed Fault-step Dipole features (lane SFD-36, 2026-10-27).

Hypothesis H-SFD-A: many uncatalogued normal faults have little or no ridge/scarp
*monopole* (the signal prior lanes integrate: worms, coherence, step maxima) but a
strong transverse *dipole*: elevation / RTP-magnetic / gravity values step from one
signed level to another across the fault. A lithologic or buried fault juxtaposing
different basement therefore appears as |f(+d) - f(-d)| sustained along strike,
even where no crest exists. Prior repo features use gradient magnitude, tilt,
coherence and along-strike integrals of a non-negative field; none computes an
antisymmetric transverse difference at fixed offsets (2 and 4 px = 200/400 m)
integrated along strike at 1.5 km and 3 km. Label-free: physical bands only.

Named non-fault mimic: lithologic contacts, Lahontan shoreline scarps, canal/road
embankments -- all are also dipoles; the HGB must separate them using the other
89 contextual features, and the holdout is the arbiter.
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import gaussian_filter
from scipy.ndimage import shift as nd_shift
from scipy.signal import fftconvolve

from gemsdoe36.kpl_features import _line_kernel

SFD_FEATURES: tuple[str, ...] = (
    "sfd_elev_dip7", "sfd_elev_dip15", "sfd_mag_dip7", "sfd_mag_dip15",
    "sfd_grav_dip7", "sfd_grav_dip15", "sfd_lid_dip7", "sfd_lid_dip15",
    "sfd_slope_dip7", "sfd_xdip_elev_mag", "sfd_xdip_all", "sfd_persist_mag",
)
SFD_LIDAR_FEATURES: frozenset[str] = frozenset({"sfd_lid_dip7", "sfd_lid_dip15", "sfd_xdip_all"})
N_ORIENT = 8


def _fill(a, fp):
    med = float(np.nanmedian(a[fp])) if np.isfinite(a[fp]).any() else 0.0
    return np.where(np.isfinite(a), a, med).astype(np.float32)


def _unit(a, fp):
    v = a[fp]
    v = v[np.isfinite(v)]
    lo, hi = np.nanpercentile(v, [1.0, 99.0]) if v.size else (0.0, 1.0)
    return np.clip((_fill(a, fp) - lo) / max(hi - lo, 1e-12), -1.0, 1.0).astype(np.float32)


def dipole(field_unit, half, offset):
    """Max-over-8-strikes of along-strike-integrated |f(+offset)-f(-offset)|."""
    mx = np.zeros(field_unit.shape, np.float32)
    acc = np.zeros(field_unit.shape, np.float32)
    for k in range(N_ORIENT):
        th = np.deg2rad(k * 180.0 / N_ORIENT)
        # strike direction (dy,dx); transverse is perpendicular
        ty, tx = np.sin(th), np.cos(th)  # transverse unit (image coords, approx axial)
        plus = nd_shift(field_unit, (offset * ty, offset * tx), order=1, mode="nearest")
        minus = nd_shift(field_unit, (-offset * ty, -offset * tx), order=1, mode="nearest")
        diff = np.abs(plus - minus).astype(np.float32)
        resp = fftconvolve(diff, _line_kernel(k * 180.0 / N_ORIENT, half), mode="same").astype(np.float32)
        acc += resp
        np.maximum(mx, resp, out=mx)
    return mx, (mx - acc / N_ORIENT).astype(np.float32)


def build_sfd_features(cols2d, fp):
    elev = gaussian_filter(_fill(cols2d["org_det_elev"], fp), 1.0)
    mag = gaussian_filter(_fill(cols2d["org_rtp"], fp), 1.0)
    grav = gaussian_filter(_fill(cols2d["org_iso_grav_anom"], fp), 1.0)
    slope = cols2d["org_det_elev_slope"]
    lid_ok = np.isfinite(cols2d["lid_valid"]) & (cols2d["lid_valid"] > 0.5) & np.isfinite(cols2d["lid_step_max"])
    lid = np.where(lid_ok, cols2d["lid_step_max"], 0.0)

    out = {}
    e7, _ = dipole(_unit(elev, fp), 7, 2)
    e15, _ = dipole(_unit(elev, fp), 15, 4)
    m7, _ = dipole(_unit(mag, fp), 7, 2)
    m15, _ = dipole(_unit(mag, fp), 15, 4)
    g7, _ = dipole(_unit(grav, fp), 7, 2)
    g15, _ = dipole(_unit(grav, fp), 15, 4)
    l7, _ = dipole(_unit(lid, fp), 7, 2)
    l15, _ = dipole(_unit(lid, fp), 15, 4)
    s7, _ = dipole(_unit(slope, fp), 7, 2)
    out["sfd_elev_dip7"], out["sfd_elev_dip15"] = e7, e15
    out["sfd_mag_dip7"], out["sfd_mag_dip15"] = m7, m15
    out["sfd_grav_dip7"], out["sfd_grav_dip15"] = g7, g15
    out["sfd_lid_dip7"] = np.where(lid_ok, l7, np.nan).astype(np.float32)
    out["sfd_lid_dip15"] = np.where(lid_ok, l15, np.nan).astype(np.float32)
    out["sfd_slope_dip7"] = s7
    # cross-channel: a true basement step should dipole in elevation AND magnetics
    out["sfd_xdip_elev_mag"] = np.minimum(e7, m7).astype(np.float32)
    out["sfd_xdip_all"] = np.where(lid_ok, np.minimum(np.minimum(e7, m7), l7), np.nan).astype(np.float32)
    out["sfd_persist_mag"] = (m15 / (m7 + 0.05)).astype(np.float32)
    assert tuple(out.keys()) == SFD_FEATURES, tuple(out.keys())
    return {k: np.asarray(v, dtype=np.float32) for k, v in out.items()}
