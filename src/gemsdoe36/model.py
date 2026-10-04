"""Small physics-informed CNN for fault probability (Raissi-Perdikaris-Karniadakis 2019 style).

The model is deliberately small (CPU, 2 vCPU, ~4 GB RAM): 3-level U-Net, 96 px
patches, 16-48 channels. The defining property required by the project brief is
that the Anderson stress orientation enters the *training loss* as a
differentiable, confidence-weighted regulariser (``orientation.
stress_orientation_loss``), not as a post-hoc filter:

    L = BCE(pos-weight) + lambda_stress * stress_orientation_loss(p, theta_ext, conf_ext)

Training labels are the provided catalogue (the only ground truth); patches are
sampled from the spatial CV training region only (held-out blocks + collar are
excluded), so the physics term and the supervised term both generalise the same
way. Inference tiles the full raster at 50 % overlap and averages.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# Channels the network sees (line metrics + context; all robust-scored [0,1] or
# small-range in prepare_data). Kept small for CPU speed.
MODEL_CHANNELS = [
    "raw_tc",
    "raw_tmi_vg",
    "raw_tmi_hg",
    "raw_iso_grav_anom_vg",
    "raw_iso_grav_anom_hg",
    "raw_iso_grav_anom_slope",
    "raw_det_elev_slope",
    "surface_scarp",
    "rad_composite",
    "ext_composite",
    "raw_cond_surf",
    "raw_ieq_n100a15",
    "spring_ctx",
    "vent_ctx",
]
N_CHANNELS = len(MODEL_CHANNELS)
PATCH = 96
STRIDE = 64


@dataclass(frozen=True)
class TrainConfig:
    patch: int = PATCH
    stride: int = STRIDE
    n_patches_per_epoch: int = 9000
    epochs: int = 8
    batch: int = 8
    lr: float = 3e-4
    lambda_stress: float = 0.5
    seed: int = 36
    min_patch_fault_px: int = 4  # skip empty context patches for positive class


def build_unet(in_channels: int = N_CHANNELS, base: int = 16):
    """A small 3-level U-Net. Returns (module, n_params)."""
    import torch.nn as nn

    class Block(nn.Module):
        def __init__(self, c_in: int, c_out: int):
            super().__init__()
            self.net = nn.Sequential(
                nn.Conv2d(c_in, c_out, 3, padding=1),
                nn.BatchNorm2d(c_out),
                nn.ReLU(inplace=True),
                nn.Conv2d(c_out, c_out, 3, padding=1),
                nn.BatchNorm2d(c_out),
                nn.ReLU(inplace=True),
            )

        def forward(self, x):
            return self.net(x)

    class SmallUNet(nn.Module):
        def __init__(self):
            super().__init__()
            self.enc1 = Block(in_channels, base)
            self.enc2 = Block(base, 2 * base)
            self.enc3 = Block(2 * base, 4 * base)
            self.bottleneck = Block(4 * base, 4 * base)
            self.up2 = nn.ConvTranspose2d(4 * base, 2 * base, 2, stride=2)
            self.dec2 = Block(4 * base, 2 * base)
            self.up1 = nn.ConvTranspose2d(2 * base, base, 2, stride=2)
            self.dec1 = Block(2 * base, base)
            self.head = nn.Conv2d(base, 1, 1)

        def forward(self, x):
            e1 = self.enc1(x)
            e2 = self.enc2(e1)
            e3 = self.enc3(e2)
            b = self.bottleneck(e3)
            d2 = self.dec2(torch.cat([self.up2(b), e2], dim=1))
            d1 = self.dec1(torch.cat([self.up1(d2), e1], dim=1))
            return self.head(d1)

    import torch

    model = SmallUNet()
    n_params = int(sum(p.numel() for p in model.parameters()))
    return model, n_params


def sample_patches(
    channels: dict[str, np.ndarray],
    catalogue: np.ndarray,
    valid_area: np.ndarray,
    extension_angle: np.ndarray,
    extension_conf: np.ndarray,
    train_mask: np.ndarray,
    *,
    n_patches: int,
    patch: int = PATCH,
    seed: int = 36,
    fault_fraction: float = 0.5,
):
    """Sample training patches: half centred on catalogue faults (positive),
    half random inside the training region (negative context).

    Patches must lie entirely inside ``train_mask`` (held-out blocks + collar
    excluded) so the network never sees held-out labels.
    """
    import torch

    h, w = valid_area.shape
    # Precompute channel stack once (memory: N_CHANNELS * 48 MB).
    stack = np.stack([channels[n].astype(np.float32) for n in MODEL_CHANNELS], axis=0)
    # z-normalise per channel over the valid area (robust: p1-p99).
    for c in range(stack.shape[0]):
        v = stack[c][valid_area]
        lo, hi = np.percentile(v, [1.0, 99.0])
        if hi <= lo:
            hi = lo + 1.0
        stack[c] = np.clip((stack[c] - lo) / (hi - lo), 0.0, 1.0)

    catalogue = catalogue * train_mask
    fault_px = np.argwhere((catalogue > 0) & valid_area)
    valid_px = np.argwhere(train_mask & valid_area)
    rng = np.random.default_rng(seed)

    pos_idx = rng.integers(0, len(fault_px), size=n_patches // 2 + 1)
    neg_idx = rng.integers(0, len(valid_px), size=n_patches - n_patches // 2 - 1)

    xs = []
    labels = []
    angles = []
    confs = []
    for center in list(fault_px[pos_idx]) + list(valid_px[neg_idx]):
        cy, cx = int(center[0]), int(center[1])
        y0 = cy - patch // 2
        x0 = cx - patch // 2
        if y0 < 0 or x0 < 0 or y0 + patch > h or x0 + patch > w:
            continue
        if not train_mask[y0 : y0 + patch, x0 : x0 + patch].all():
            continue
        xs.append(stack[:, y0 : y0 + patch, x0 : x0 + patch])
        labels.append(catalogue[y0 : y0 + patch, x0 : x0 + patch])
        angles.append(extension_angle[y0 : y0 + patch, x0 : x0 + patch])
        confs.append(extension_conf[y0 : y0 + patch, x0 : x0 + patch])
        if len(xs) >= n_patches:
            break

    x = torch.tensor(np.stack(xs, axis=0), dtype=torch.float32)
    y = torch.tensor(np.stack(labels, axis=0).astype(np.float32), dtype=torch.float32)
    a = torch.tensor(np.stack(angles, axis=0), dtype=torch.float32)
    cf = torch.tensor(np.stack(confs, axis=0), dtype=torch.float32)
    return x, y, a, cf, stack


def train_model(
    channels: dict[str, np.ndarray],
    catalogue: np.ndarray,
    valid_area: np.ndarray,
    extension_angle: np.ndarray,
    extension_conf: np.ndarray,
    train_mask: np.ndarray,
    *,
    config: TrainConfig | None = None,
    out_path: str | None = None,
    log=print,
):
    """Train the physics-informed U-Net on the spatial CV training region.

    Returns the torch module (CPU). The stress-orientation loss is added in the
    loss (differentiable), per the project brief.
    """
    import torch
    import torch.nn.functional as F

    from .orientation import physics_informed_objective

    config = config or TrainConfig()
    torch.manual_seed(config.seed)
    np.random.seed(config.seed)

    model, n_params = build_unet(N_CHANNELS)
    log(f"PASS: U-Net built: {n_params/1e6:.2f} M params, CPU, patches {config.patch} px")

    x, y, a, cf, _stack = sample_patches(
        channels, catalogue, valid_area, extension_angle, extension_conf, train_mask,
        n_patches=config.n_patches_per_epoch, patch=config.patch, seed=config.seed,
    )
    pos = float(y.sum())
    log(f"PASS: sampled {x.shape[0]} patches; positive px {pos:.0f} "
        f"({100*pos/x.shape[1:].numel():.3f}%)")
    if pos < 100:
        raise RuntimeError("FAIL: too few positive pixels in the training region")

    # Class-imbalance weight: positive weight ~ (neg/pos) capped for stability.
    pos_weight = float(np.clip((x.shape[1:].numel() * x.shape[0] - pos) / max(pos, 1.0), 1.0, 30.0))
    log(f"NOTE: BCE pos_weight={pos_weight:.1f}, lambda_stress={config.lambda_stress}")

    opt = torch.optim.AdamW(model.parameters(), lr=config.lr, weight_decay=1e-4)
    idx = torch.arange(x.shape[0])
    for epoch in range(config.epochs):
        model.train()
        perm = idx[torch.randperm(len(idx))]
        tot_loss = tot_bce = tot_stress = 0.0
        nb = 0
        for i in range(0, len(perm), config.batch):
            b = perm[i : i + config.batch]
            xb, yb = x[b], y[b]
            if torch.rand(()) < 0.5:
                xb = torch.flip(xb, dims=[3])
                yb = torch.flip(yb, dims=[3])
            if torch.rand(()) < 0.5:
                xb = torch.flip(xb, dims=[2])
                yb = torch.flip(yb, dims=[2])
            p = torch.sigmoid(model(xb))
            bce = F.binary_cross_entropy_with_logits(
                model(xb), yb, pos_weight=torch.tensor(pos_weight)
            )
            total, stress = physics_informed_objective(
                bce, p, a[b], cf[b], lambda_stress=config.lambda_stress
            )
            opt.zero_grad()
            total.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            tot_loss += float(total)
            tot_bce += float(bce)
            tot_stress += float(stress)
            nb += 1
        log(
            f"epoch {epoch+1}/{config.epochs}: loss={tot_loss/nb:.4f} "
            f"bce={tot_bce/nb:.4f} stress={tot_stress/nb:.4f}"
        )

    if out_path:
        torch.save(model.state_dict(), out_path)
        log(f"PASS: saved state dict -> {out_path}")
    return model


def predict_full(
    model,
    channels: dict[str, np.ndarray],
    valid_area: np.ndarray,
    *,
    patch: int = PATCH,
    stride: int = STRIDE,
) -> np.ndarray:
    """Tile the full raster and return the averaged probability map (float32)."""
    import torch

    h, w = valid_area.shape
    stack = np.stack([channels[n].astype(np.float32) for n in MODEL_CHANNELS], axis=0)
    for c in range(stack.shape[0]):
        v = stack[c][valid_area]
        lo, hi = np.percentile(v, [1.0, 99.0])
        if hi <= lo:
            hi = lo + 1.0
        stack[c] = np.clip((stack[c] - lo) / (hi - lo), 0.0, 1.0)

    model.eval()
    acc = np.zeros((h, w), dtype=np.float64)
    cnt = np.zeros((h, w), dtype=np.float32)
    with torch.no_grad():
        for y0 in range(0, h - patch + 1, stride):
            for x0 in range(0, w - patch + 1, stride):
                x = torch.tensor(stack[:, y0 : y0 + patch, x0 : x0 + patch], dtype=torch.float32)
                p = torch.sigmoid(model(x[None])).numpy()[0, 0]
                acc[y0 : y0 + patch, x0 : x0 + patch] += p
                cnt[y0 : y0 + patch, x0 : x0 + patch] += 1.0
    out = np.zeros((h, w), dtype=np.float32)
    positive = cnt > 0
    out[positive] = (acc[positive] / cnt[positive]).astype(np.float32)
    return np.where(valid_area, out, 0.0).astype(np.float32)
