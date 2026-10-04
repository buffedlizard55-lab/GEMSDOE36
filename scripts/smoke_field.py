#!/usr/bin/env python3
"""Smoke test: load stack, build Anderson field + belief field, emit a few dots."""
import sys
sys.path.insert(0, "src")
import numpy as np
import rasterio
from scipy.ndimage import binary_dilation

from gemsdoe36.anderson import local_extension_field
from gemsdoe36.field import build_belief_field, FieldConfig
from gemsdoe36.emitter import emit_dots

H, W = 3730, 3292
data = np.load("data/processed/core_stack.npz")
stack, names = data["stack"], [str(n) for n in data["names"]]
channels = {n: stack[i] for i, n in enumerate(names)}
print("channels:", len(names))

with rasterio.open("data/raw/sample_submission.tif") as ds:
    footprint = np.isfinite(ds.read(1, masked=False))
with rasterio.open("data/raw/labels.tif") as ds:
    lab = ds.read(1, masked=True)
catalogue = np.asarray((~lab.mask) & (lab == 1) & footprint, dtype=np.float32)
print("catalogue px:", int(catalogue.sum()))

# Anderson extension field (fit on full catalogue for the smoke test).
ext = local_extension_field(catalogue, tile_px=120)
print("extension conf: mean=%.3f max=%.3f" % (ext.confidence[footprint].mean(), ext.confidence.max()))

cfg = FieldConfig()
bf = build_belief_field(channels, footprint, catalogue, config=cfg, extension=ext)
print("belief: max=%.4f median=%.4f p99=%.4f" % (
    bf.belief.max(), np.median(bf.belief[footprint]), np.percentile(bf.belief[footprint], 99)))
print("diagnostics:", bf.diagnostics)

# Exclude the catalogue-flank (200 m) like the validated incumbent rule.
yy, xx = np.ogrid[-2:3, -2:3]
disk = (xx*xx + yy*yy) <= 4
exclude = binary_dilation(catalogue > 0, structure=disk)

# Binary truth proxy = top-K belief pixels (K ~ owner's hidden-truth estimate).
K_TARGET = 12500
b = bf.belief
bflat = b.ravel()
idx = np.argpartition(-bflat, K_TARGET)[:K_TARGET]
truth_proxy = np.zeros(b.shape, dtype=np.float32)
truth_proxy.ravel()[idx] = 1.0
print("truth_proxy px:", int(truth_proxy.sum()))

res = emit_dots(b, budget=40000, support_quantile=99.0, exclude_mask=exclude,
                truth_proxy=truth_proxy)
print("emitted dots:", len(res.dots), "stopped_by:", res.stopped_by,
      "dti_est=%.4f T=%.0f F=%.0f" % (res.dti_estimate, res.credit, res.fp_mass))
print("OK smoke")
