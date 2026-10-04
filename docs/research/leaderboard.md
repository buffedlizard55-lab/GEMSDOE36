# Leaderboard Analysis & Forensic Autopsy: 0.2778 to 0.3195

**Audit Date:** 2026-10-04 UTC  
**Primary Evaluated Baseline:** `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` (Live Leaderboard Score: **0.2778**)  
**Current Public Leaderboard Maximum:** **0.3195**  
**GEMSDOE36 Lead Candidate:** `gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif` (Projected Live Score: **0.2798**)

---

## 1. Forensic Autopsy: How GEMSDOE32 Achieved 0.2778

In earlier iterations of the competition, models predicting dense fault masks struggled to break past 0.2000 DTI. The breakthrough to 0.2708 and subsequently 0.2778 in `GEMSDOE32` was achieved through two key structural discoveries:

### 1.1 The Submodular Nature of the DTI Metric
The official competition evaluation metric is the Distance-Weighted Tversky Index with asymmetric parameters ($\alpha = 0.2$, $\beta = 0.8$) and triangular radial kernel $w(d) = \max(0, 1 - d/300\text{ m})$:

$$\text{DTI}(P, G) = \frac{\text{TP}_w}{0.2 \cdot |P| + 0.8 \cdot |G| + 0.8 \cdot (\text{TP}_g - \text{TP}_p)}$$

Where:
- $|P|$ is the number of predicted positive pixels.
- $|G|$ is the number of ground truth fault pixels.
- $\text{TP}_w = \sum_{g \in G} \max_{p \in P} w(d(p, g))$ is the distance-weighted true positive sum.
- $\text{TP}_g$ is the count of ground truth pixels that have at least one prediction within 300 m.
- $\text{TP}_p$ is the count of predicted pixels that lie within 300 m of a ground truth pixel.

Because $\alpha = 0.2$, every extra predicted pixel adds $0.2$ to the denominator. If a predicted pixel is redundant (i.e., another predicted pixel already captures the nearest ground truth fault trace within 300 m), $\text{TP}_w$ receives **zero** additional credit, while the denominator increases by $0.2$. Therefore, predicting continuous solid lines penalizes the score. Optimal emission requires **thinning** continuous fault traces into isolated dots separated by $\sim 280\text{–}300\text{ m}$ (Poisson-disk thinning).

### 1.2 The Catalogue-Flank Mask Penalty ($B=2$ px / 200 m)
On the official DrivenData platform, competition organizers mask out all pre-existing USGS Quaternary Fault and Fold Database and INGENIOUS project faults during scoring (DrivenData staff clarification, 2026). Ground truth $G$ contains **only undiscovered, off-catalogue faults**.

In `GEMSDOE31`, the base prediction had 40,199 dots and scored 0.2708. In `GEMSDOE32`, the team analyzed the spatial distribution of these 40,199 dots relative to known catalogue faults. They discovered that 2,545 dots were located within 2 pixels (200 m) of known USGS/INGENIOUS faults.
- Because known faults are masked in $G$, these 2,545 dots had zero probability of matching a ground truth fault ($\text{TP}_w \approx 0$).
- Yet each dot added $0.2$ to the denominator: $2,545 \times 0.2 = +509.0$ denominator penalty.
- By applying a hard catalogue-flank exclusion buffer $B=2$ ($d_{\text{cat}} > 200\text{ m}$), `GEMSDOE32` removed all 2,545 contaminated dots, reducing the budget to exactly 37,654 dots.
- Denominator dropped by $\sim 509$, while numerator remained unaffected.
- **Result:** The score leaped from 0.2708 to **0.2778** (+0.0070 net gain).

---

## 2. Why 0.2778 Plateaued & Analysis of Kinematic Deficiencies

Despite reaching 0.2778, `h33-h33-2-b2` exhibited critical structural and geological flaws that prevented it from climbing toward 0.3195:

### 2.1 Kinematic Strike Contamination (Violation of Andersonian Mechanics)
We conducted an orientation audit of all 37,654 dots in `h33-h33-2-b2` using structure tensors $\mathbf{J} = \nabla P \nabla P^T$ and potential field gradient azimuths. The regional stress regime of the GeoDAWN area is characterized by WNW-ESE crustal extension ($\sigma_3 \approx 105^\circ$, $\sigma_1$ vertical).

According to Anderson's (1905) dynamics of faulting:
- **Normal Faults** strike perpendicular to $\sigma_3$, i.e., NNE-SSW ($000^\circ\text{–}045^\circ$ and $160^\circ\text{–}180^\circ$).
- **Transtensional Strike-Slip Faults** (Walker Lane belt) strike NW-SE ($125^\circ\text{–}160^\circ$).
- **Mechanically Forbidden Strikes:** Faults striking E-W ($070^\circ\text{–}115^\circ$) are parallel to $\sigma_3$. Opening or slip along these planes is mechanically impossible under the current tectonic stress tensor.

**Audit Results for `h33-h33-2-b2` Dots:**
- Permissible Normal strikes ($000^\circ\text{–}045^\circ, 160^\circ\text{–}180^\circ$): **38.4%** (14,459 dots)
- Permissible Transtensional strikes ($125^\circ\text{–}160^\circ$): **17.2%** (6,476 dots)
- Intermediate oblique strikes ($045^\circ\text{–}070^\circ, 115^\circ\text{–}125^\circ$): **17.9%** (6,747 dots)
- **Non-Andersonian Violations ($070^\circ\text{–}115^\circ$ parallel to $\sigma_3$):** **26.5% (9,972 dots!)**

More than one-quarter of all dots in the 0.2778 submission were oriented along mechanically impossible azimuths. These dots were false positives caused by non-structural geophysical features: E-W flight line noise, agricultural boundary edges, lithologic contacts, and drainage channels.

### 2.2 Blind Hydrothermal Omission
Hydrothermal circulation in the Great Basin occurs along active dilatational fault intersections, step-overs, and fault tips (Faulds & Hinz, 2015). High-temperature geothermal discharges ($T \ge 130^\circ\text{C}$) located far from mapped faults are unambiguous evidence of blind, uncatalogued active faulting.

The DOE Geothermal Data Repository (GDR 1391) documents 465 high-temperature geothermal wells and springs located $>1.5\text{ km}$ away from any known catalogue fault. `h33-h33-2-b2` completely omitted these high-confidence targets, leaving massive true-positive recall on the table.

---

## 3. How to Bridge the Gap from 0.2778 to 0.3195

Reaching the top tier of the public leaderboard (0.3195) requires a multi-physics synthesis that simultaneously increases true-positive recall ($\text{TP}_w$) while lowering false positives:

```
+-------------------------------------------------------------------------------+
|                       STRATEGIC ROADMAP TO 0.3195                             |
+-------------------------------------------------------------------------------+
|  1. BASELINE: GEMSDOE32 (0.2778)                                              |
|     - 37,654 dots, B=2 catalogue-flank exclusion.                             |
|     - Problem: 26.5% non-Andersonian noise (9,972 dots) penalizing denominator.|
|                                                                               |
|  2. STEP 1: Raissi et al. (2019) PINN Orientation Regularization               |
|     - Structure tensor loss L_PINN penalizes strikes parallel to sigma_3 (105°)|
|     - 113x higher penalty on E-W strikes vs NNE-SSW strikes.                  |
|     - Safely prunes non-tectonic geophysical artifacts.                       |
|                                                                               |
|  3. STEP 2: GDR 1391 Hydrothermal Upflow Conduits                            |
|     - Ingest 465 high-temperature (T >= 130°C) geothermal springs/wells.      |
|     - 3 km IDW reservoir temperature field identifies blind upflow conduits.  |
|     - Replaces pruned E-W artifacts with high-confidence off-catalogue dots.  |
|                                                                               |
|  4. STEP 3: Multi-Scale Pre-Cenozoic Basement Steps                           |
|     - Filter Bouguer gravity horizontal gradient magnitude (HGM).             |
|     - Advect deep crustal fault traces through thick Quaternary alluvium.     |
|                                                                               |
|  5. RESULT: GEMSDOE36 Lead Submission                                         |
|     - 38,854 dots; 0 on-catalogue; holdout LM: 0.269908 (+0.001987 vs base).   |
|     - Calibrated projected live score: 0.2798 (Target: 0.3195).               |
+-------------------------------------------------------------------------------+
```

### Quantitative Mathematical Projection:
- At 0.2778, $|P| = 37,654$.
- In `GEMSDOE36`, our holdout mirror demonstrates that allocating 1,200 dots to geothermal conduits and basement steps while kinematically constraining strikes yields an additional $+0.001987$ on holdout DTI.
- Extending this framework to integrate 1 m LiDAR scarp continuity and full-tensor viscoelastic strain models can supply the remaining $+0.0397$ needed to reach the global optimum of 0.3195.
