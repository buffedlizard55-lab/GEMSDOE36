"""Anderson's Theory of Faulting (1905) & Physics-Informed Kinematic Constraints.

In Anderson's (1905) standard structural geology framework, fault type and orientation are
governed by which principal stress axis is vertical:
- In the Great Basin's extensional / transtensional tectonic regime, maximum principal compressive
  stress sigma_1 is vertical (sigma_v = sigma_1).
- Minimum principal compressive stress sigma_3 is horizontal and defines the regional extension
  direction (T-axis, oriented ~105-115 deg azimuth / WNW-ESE across the GeoDAWN footprint).
- Coulomb failure criterion predicts conjugate normal faults dipping at theta = 45 deg + phi/2 ~ 60 deg
  and striking perpendicular to sigma_3: azimuth 015-025 deg (NNE-SSW) with allowed conjugate splays
  345-045 deg (NNW to NE) and Walker Lane strike-slip faults at ~135-155 deg (NW-SE).
- Candidate faults striking E-W to WNW (75-105 deg) are parallel to sigma_3 and are mechanically
  forbidden from forming as normal faults under vertical sigma_1.

Following Raissi, Perdikaris, and Karniadakis (J. Comp. Phys., 2019), this module provides both:
1. Continuous 2D Anderson kinematic favorability fields Phi_Anderson(x) based on local lineament strike.
2. Differentiable physics-informed orientation penalty terms regularizing neural / gradient models.
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import gaussian_filter


def compute_lineament_strike_azimuth(
    field: np.ndarray,
    sigma: float = 1.5,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute local lineament strike azimuth (0 to 180 deg from North) and gradient magnitude.

    In standard raster conventions:
    - x is column (+East)
    - y is row (+South)
    Normal azimuth is measured clockwise from North.
    Fault strike is perpendicular to the normal (normal_azimuth + 90 deg) mod 180.
    """
    smooth = gaussian_filter(np.nan_to_num(field, nan=0.0).astype(np.float32), sigma=sigma)
    gy, gx = np.gradient(smooth)
    grad_mag = np.hypot(gy, gx)

    # In math/polar: angle from +x (East) counterclockwise toward -y (North)
    # theta_math = arctan2(-gy, gx)
    # Azimuth from North clockwise: az = 90 - deg(theta_math) = 90 - arctan2(-gy, gx)
    normal_az = (np.rad2deg(np.arctan2(gx, -gy)) + 360.0) % 180.0
    strike_az = (normal_az + 90.0) % 180.0
    return strike_az.astype(np.float32), grad_mag.astype(np.float32)


def anderson_kinematic_consistency(
    strike_azimuth_deg: np.ndarray,
    extension_azimuth_deg: float = 108.0,
    optimal_normal_strike_deg: float = 18.0,
    transtension_strike_deg: float = 145.0,
) -> np.ndarray:
    """Return continuous Andersonian kinematic favorability score in [-1.0, 1.0].

    +1.0: perfectly aligned with Anderson normal fault strike (~018 deg NNE) or Walker Lane
          dextral strike-slip strike (~145 deg NW).
    -1.0: kinematically forbidden strike parallel to regional extension (~108 deg WNW).
    """
    az = np.asarray(strike_azimuth_deg, dtype=np.float32) % 180.0

    # Angular deviation from optimal normal fault strike
    diff_normal = np.minimum(
        np.abs(az - optimal_normal_strike_deg),
        180.0 - np.abs(az - optimal_normal_strike_deg),
    )
    score_normal = np.cos(np.deg2rad(2.0 * diff_normal))

    # Angular deviation from Walker Lane transtension strike
    diff_trans = np.minimum(
        np.abs(az - transtension_strike_deg),
        180.0 - np.abs(az - transtension_strike_deg),
    )
    score_trans = np.cos(np.deg2rad(2.0 * diff_trans))

    # Kinematically forbidden penalty for strikes parallel to extension
    diff_ext = np.minimum(
        np.abs(az - extension_azimuth_deg),
        180.0 - np.abs(az - extension_azimuth_deg),
    )
    ext_penalty = np.cos(np.deg2rad(2.0 * diff_ext))  # +1 when parallel to extension

    # Combined Anderson score: maximum of permitted normal/strike-slip modes, penalized by extension parallelism
    score = np.maximum(score_normal, 0.75 * score_trans) - 0.25 * np.maximum(ext_penalty, 0.0)
    return np.clip(score, -1.0, 1.0).astype(np.float32)


def filter_non_andersonian_candidates(
    candidate_mask: np.ndarray,
    strike_azimuth_deg: np.ndarray,
    forbidden_az_min: float = 75.0,
    forbidden_az_max: float = 105.0,
) -> np.ndarray:
    """Identify candidate dots whose strike falls within the kinematically forbidden extensional envelope."""
    az = strike_azimuth_deg % 180.0
    is_forbidden = (az >= forbidden_az_min) & (az <= forbidden_az_max)
    return candidate_mask & is_forbidden
