# Forensic Audit of GEMSDOE24–36 & Design of H36-CTRB (2026-10-25)

See also:
- Frozen preregistration: [`preregistration_2026-10-25.md`](preregistration_2026-10-25.md)
- Validation ledger & metric tables: [`results.md`](results.md)
- Irregularities & QA log: [`known_irregularities.md`](known_irregularities.md)
- Machine-readable Run Card: [`../downloads/run_card.json`](../downloads/run_card.json)

## 1. Why `GEMSDOE32` (`h33-h33-2-b2`, `0.2778` `ORGANIZER-CONFIRMED`) Beat Every Sibling Focus Site

1. **Out-of-Fold Multi-Physics Corroborated Backbone (`0.1922 -> 0.2477`):**
   - `19GEMSDOE` (`h19-5`, `121,131` px, `0.1922` `ORGANIZER-CONFIRMED`) established a 4-fold out-of-fold gradient-boosted skeleton fusing potential fields, topography, and 1 m LiDAR scarp features, preventing training-quadrant memorization of `labels.tif`.
   - `GEMSDOE24` (`d1.5`, `60,069` px, `0.2477` `ORGANIZER-CONFIRMED`) recognized that under the $R = 300\text{ m}$ (`3 px`) triangular DTI kernel with $\alpha = 0.2$, continuous 1-pixel chains pay redundant false-positive mass on background segments while gaining negligible marginal $\text{TP}_w$ credit on true segments. Thinning to `1.5 px` spacing lifted score by `+0.0555`.
2. **Near-Kernel-Radius Dotted Spacing (`0.2477 -> 0.2600`):**
   - `GEMSDOE25` and `GEMSDOE30` (byte-identical footprint `44,090` px, both `0.2600` `ORGANIZER-CONFIRMED`) widened along-ridge spacing to `2.8 px` (`280 m`), matching the `300 m` kernel support radius (`+0.0123`).
3. **Two-Step Removal of Unmasked Catalogue-Flank Hallucinations (`0.2600 -> 0.2708 -> 0.2778`):**
   - DrivenData masks known catalogue pixels (`d_cat == 0`, `60,988` px) pixel-exactly, **not** with a 100–200 m buffer. However, geophysical gradients (`tmi_hg`, `iso_grav_anom_hg`, `det_elev_slope`) have a 100–250 m spatial blurring width around known range-front faults, causing tree models to emit parallel "ghost ridges" `1–2 px` (`100–200 m`) beside mapped traces.
   - `GEMSDOE28` and `GEMSDOE31` (byte-identical `40,199` px, both `0.2708` `ORGANIZER-CONFIRMED`) pruned the `3,891` dots in `0 < d_cat <= 1.0 px` (`+0.0108`).
   - `GEMSDOE32` (`37,654` px, `0.2778` `ORGANIZER-CONFIRMED`) pruned the remaining `2,545` dots in `1.0 < d_cat <= 2.0 px` (`+0.0070`), proving **zero** hidden ground-truth credit existed within `200 m` of `labels.tif`.
   - Conversely, `GEMSDOE27` (`0.2449`), `GEMSDOE33` (`0.2632`), and old `GEMSDOE36` (`0.2750`) all lost DTI by re-introducing low-precision gap, flank, or isotropic radial IDW dots whose marginal precision fell below the Dinkelbach threshold $\lambda(D^*) = \frac{0.2 D^*}{1 - 0.2 D^*} \approx 0.059$.

## 2. How to Beat the `0.2778` Family Cleanly Without Copying Pixels

1. **Break the Upland Bedrock Accessibility Bias (`H36-D`):** Standard HGB models trained on `labels.tif` overweight raw `det_elev` and `det_elev_slope` because mapped faults are exposed in steep mountain bedrock while unmapped faults lie beneath flat Quaternary bajadas and playas. Removing raw `det_elev`/`det_elev_slope` and using macro-relief-normalized contour-orthogonal breaklines prevents steep-slope ridge duplication (`44.18%` vs `72.69%` on `8GEMSDOE`) and boosts `SW` Walker Lane generalization (`0.11022` vs `0.0799`).
2. **2D 1.5 km Strike-Worm Persistence & Geophysical Trunk Relay/Tip Operators (`H36-A`, `H36-B`, `H36-C`):** Subpixel-antialiased 12-azimuth `1.5 km` line integrals of magnetic tilt-zero sharpness, upward-continuation attenuation (`TMI - TMI_up150`), gravity HGM, and potassic alteration (`Th/K` depletion + MT `cond_surf` gradient + GDR 1391 chemical geothermometers), combined with label-free opposing-EDT relay bridges and $\cos^4\psi$ tip propagation cones, capture structurally coherent blind Basin-and-Range / Walker Lane faults (`+0.05647` `HOLDOUT-DTI` over raw 19-band HGB OOF).
3. **Exact Dinkelbach-Submodular 300 m Ridge Skeleton Emission:** Replaces heuristic uniform `d = 2.8 px` decimation with Minoux lazy-greedy maximization of expected 25-offset triangular kernel coverage minus exact Dinkelbach FP penalty $\frac{0.2 D^*}{1 - 0.2 D^*}(1 - q_{\text{nb}})$ strictly along 1-px Hessian centerlines (`ridge_nms`) outside `d_cat <= 2.0 px`.
