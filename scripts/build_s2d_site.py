#!/usr/bin/env python3
"""Update GitHub Pages, manifests, and README from verified S2D-36 evidence.

Fail-closed invariants enforced:
- Promotes ONLY if S2D-36 run card verdict == "promote" AND all 6 gates are True.
- Preserves LITERAL_REVIEW, FOCUS9_EXEC (single block in executive-summary.html),
  KPL36, KPL36_ARCHIVE, DW36, and archived research bundle identities.
- Preserves README's verbatim `## Full standing owner brief (historical wording)` suffix.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
sys.path.insert(0, str(ROOT / "scripts"))
from build_mto_site import parallel_dw_projection  # noqa: E402

S2D_CARD = ROOT / "evidence/s2d36_run_card_20261027.json"
S2D_CROSS = ROOT / "evidence/s2d36_crosscheck_20261027.json"
S2D_PEERS = ROOT / "evidence/s2d36_oct27_peer_audit_20261027.json"
KPL_CARD = ROOT / "evidence/kpl36_run_card_20261026.json"
DW_CARD = ROOT / "evidence/dw36_run_card_20261026.json"
FOCUS9_LEDGER = ROOT / "evidence/focus_sites_9repo_summary_20261026.json"

INDEX = DOCS / "index.html"
SUMMARY = DOCS / "executive-summary.html"
CURRENT = DOCS / "current-run.json"
MANIFEST = DOCS / "downloads/submissions_manifest.json"
README = ROOT / "README.md"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def upsert(text: str, start: str, end: str, block: str, anchor: str, where: str = "after") -> str:
    if start in text and end in text:
        return re.sub(re.escape(start) + r".*?" + re.escape(end), lambda _: block, text, flags=re.S)
    if anchor not in text:
        raise RuntimeError(f"anchor not found: {anchor[:80]}")
    return text.replace(anchor, (anchor + "\n" + block) if where == "after" else (block + "\n" + anchor), 1)


def build_s2d_section(card: dict, cross: dict, peers: dict) -> str:
    verdict = card["verdict"]
    gates = card["gates"]
    promote = verdict == "promote" and all(gates.values())
    if verdict == "promote" and not all(gates.values()):
        raise RuntimeError("FAIL-CLOSED: verdict=promote with failing gates")

    sub = card["submission"]
    tif_rel = sub["file"].removeprefix("docs/")
    zip_rel = sub["zip"].removeprefix("docs/")
    h = card["holdout"]
    best = card["best_arm"]
    scen = card["scenario_projection_not_a_score"]
    scen_lo, scen_hi = scen["peer_mechanism_matched_scenario_range"]
    scen_floor = scen["conservative_kpl_ratio_projection"]

    arms_rows = "".join(
        f"<tr><td><code>{a}</code></td>"
        f"<td><strong>{v['dti']:.6f}</strong> HOLDOUT-DTI</td>"
        f"<td>[{v['ci95'][0]:.4f}, {v['ci95'][1]:.4f}]</td></tr>"
        for a, v in h["arms"].items()
    )

    exec_rows = [
        (
            "GEMSDOE36 · S2D-36 EXP-2 (current research build)",
            f'<a href="{html.escape(tif_rel)}" download><code>{html.escape(Path(sub["file"]).name)}</code></a>'
            f'<br><small>SHA-256 <code>{sub["sha256"][:16]}…</code> · {sub["dots"]:,} dots · [0,1] zeros-outside</small>',
            f"<strong>HOLDOUT-DTI {h['arms'][best]['dti']:.6f}</strong> [{h['arms'][best]['ci95'][0]:.4f}, {h['arms'][best]['ci95'][1]:.4f}]<br>"
            f"<small>{h['evaluator_version']} · {h['n_withheld_positive_pixels']:,} withheld positives</small>",
            f"{scen_lo:.3f}–{scen_hi:.3f} peer-matched scenario (floor {scen_floor:.3f}; NOT A SCORE, no receipt)",
            f"<strong>PASS modern ≤45k peers</strong> (max {peers['max_oct25_27_peer_3px_overlap']*100:.2f}%; "
            f"vs B2 {cross['final_dots']['overlap_vs_GEMSDOE32_B2_3px']*100:.2f}%) · "
            f"<strong>FAIL literal 198</strong> ({cross['final_dots']['max_overlap_literal_all_198']*100:.2f}% reg-052; "
            f"70.96% vs 61k d1.5)",
            "<strong>DO NOT SUBMIT</strong> (fail-closed; human selector required)",
        ),
        (
            "GEMSDOE36 · KPL-36 EXP-3 (Oct 26)",
            '<a href="downloads/gemsdoe36-kpl36-exp3-20261026-fc869911e88c-zeros.tif" download>'
            "<code>gemsdoe36-kpl36-exp3-20261026-fc869911e88c-zeros.tif</code></a>"
            "<br><small>SHA-256 <code>86fc8243ad573bcd…</code> · 37,654 dots</small>",
            "HOLDOUT-DTI 0.170100 [0.1551, 0.1861]; <strong>0.1647 USER-REPORTED</strong> (no receipt)",
            "Observed 0.1647 USER-REPORTED (withdrawn prior range)",
            "PASS Focus-9 (61.6%) · FAIL literal reg-052 (99.17%)",
            "<strong>DO NOT SUBMIT</strong> (superseded)",
        ),
        (
            "GEMSDOE32 · Historical B2 (Focus-9 high)",
            '<a href="https://github.com/buffedlizard55-lab/GEMSDOE32/blob/5fc7792c5887735ecd3aa9a612787da588a7bf2c/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif">'
            "<code>gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif</code></a>"
            "<br><small>SHA-256 <code>c55bafc47005…</code> · 37,654 dots</small>",
            "<strong>0.2778 OWNER-REPORTED</strong> (no organizer receipt)",
            "Historical H19-5 subset (D2.8 minus ≤2 px catalogue collar)",
            "<strong>NO</strong> (100.00% subset of D2.8 / solo-d28)",
            "<strong>DO NOT COPY / SUBMIT</strong>",
        ),
        (
            "GEMSDOE70 · P5 Dual-Submod300 OOF38k (peer leader)",
            '<a href="https://github.com/buffedlizard55-lab/GEMSDOE70/blob/158aec19800d4c7b8ca9fb94b06567e2b7d61e8d/docs/downloads/gems70-p5-dual-submod300-oof38k-20261020.tif">'
            "<code>gems70-p5-dual-submod300-oof38k-20261020.tif</code></a>"
            "<br><small>SHA-256 <code>d0e41ce921af…</code> · 37,654 dots</small>",
            "<strong>0.2478 USER-REPORTED</strong> (no receipt)",
            "External peer benchmark (10 m DEM + road deconf + OOF CELF)",
            "S2D-36 overlap vs GEMSDOE70: <strong>54.23%</strong> (|ρ|=0.087)",
            "Peer reference only",
        ),
        (
            "GEMSDOE76 · PTCF Tilt-Worm Submod39k (peer)",
            '<a href="https://github.com/buffedlizard55-lab/GEMSDOE76/blob/97f3dd5a324e4c7af3355b0b6e2661bf76141986/docs/downloads/gems76-ptcf-tiltworm-submod39k-20261021T034000Z-6316481d-zeros.tif">'
            "<code>gems76-ptcf-tiltworm-submod39k-20261021T034000Z-6316481d-zeros.tif</code></a>"
            "<br><small>SHA-256 <code>b2369c25da2c…</code> · 39,200 dots</small>",
            "<strong>0.2343 USER-REPORTED</strong> (no receipt)",
            "External peer benchmark (2-stage U-GBDT + CELF)",
            "S2D-36 overlap vs GEMSDOE76: <strong>59.98%</strong> (|ρ|=0.091)",
            "Peer reference only",
        ),
        (
            "GEMSDOE27 · H31 DRCG-WL CELF28 (Oct 26 Focus-9 peer)",
            '<a href="https://github.com/buffedlizard55-lab/GEMSDOE27/blob/4f34228aa5c836922d46e81529f5fdceab90784e/docs/downloads/gems27-h31-drcg-wl-celf28-20261026-cf8e1bbef244-allfinite.tif">'
            "<code>gems27-h31-drcg-wl-celf28-20261026-cf8e1bbef244-allfinite.tif</code></a>"
            "<br><small>SHA-256 <code>a53e25f368eb…</code> · 37,654 dots</small>",
            "<strong>0.2250 USER-REPORTED</strong> (H29: 0.2190 USER-REPORTED)",
            "Best Oct 25–26 independent Focus-9 peer",
            "S2D-36 overlap vs H31: <strong>68.49%</strong> (vs H29: 55.25%)",
            "Peer reference only",
        ),
        (
            "Other Oct 25–26 Focus-9 peer runs (30 / 33 / 24 / 25 / 28)",
            "<code>MSDB1</code> · <code>s33</code> · <code>gvc1</code> · <code>h66</code> · <code>s21</code>",
            "0.1462 · 0.0963 · 0.0859 · 0.0742 · 0.0206 USER-REPORTED",
            "Observed peer runs (PU collapse on s21 at 0.0206)",
            "S2D-36 overlap: <strong>28.58%–56.75%</strong> (all ≤70%)",
            "Peer reference only",
        ),
    ]
    exec_html = "".join(
        f"<tr><td><strong>{a}</strong></td><td>{b}</td><td>{c}</td><td>{d}</td><td>{e}</td><td>{f}</td></tr>"
        for a, b, c, d, e, f in exec_rows
    )

    banner = (
        "✅ OK TO SUBMIT — passed every preregistered automated gate"
        if promote
        else "⛔ DO NOT SUBMIT — automated literal registry gate failed; research download only"
    )
    return f"""<!-- S2D36:START -->
<section class="hero compact-hero" id="s2d36-release" aria-label="S2D-36 27 October 2026 decision">
<div>
<span class="eyebrow">GEMS DOE 36 · S2D-36 current research candidate · 27 October 2026 · verdict: {verdict} · DOWNLOAD: YES</span>
<h1>S2D-36 EXP-2 (HOLDOUT-DTI 0.200766) — research download only</h1>
<p class="lede"><strong>{banner}.</strong> File <code>{html.escape(Path(sub['file']).name)}</code> · {sub['dots']:,} binary dots · single-band float32 GeoTIFF, EPSG:32611, 3730×3292 at 100 m, all 12,279,160 cells strictly in [0, 1] with 0 outside the footprint (0 NaN cells anywhere) · SHA-256 <code>{sub['sha256']}</code>. Automatic slot approval is <strong>NO</strong> (<code>slot_approved: false</code>).</p>
<div class="hero-actions">
<a class="button" href="{html.escape(tif_rel)}" download>⬇ Download S2D-36 GeoTIFF (.tif)</a>
<a class="button secondary" href="{html.escape(zip_rel)}" download>Download ZIP (.zip)</a>
<a class="button secondary" href="downloads/s2d36-run-card.json">S2D-36 JSON run card</a>
<a class="button secondary" href="research/s2d36-20261027.md">S2D-36 PhD monograph &amp; full audit →</a>
</div>
<p><strong>Unique submission name:</strong> <code>{html.escape(sub['name'])}</code><br>
<strong>Copy-paste Note</strong> ({sub['note_characters']}/140 chars, if selector overrides): <code>{html.escape(sub['note'])}</code></p>
</div>
<aside class="status-card" aria-label="S2D-36 gate summary"><span class="eyebrow">Automated 6-gate verdict: {verdict.upper()}</span>
<p style="font-size:.93rem"><strong>G1 Canary PASS:</strong> max single-feature symmetric AUC = {card['leakage_canary']['max_symmetric_auc']:.4f} (&le;0.90).<br>
<strong>G2 Holdout PASS:</strong> <strong>HOLDOUT-DTI {h['arms'][best]['dti']:.6f}</strong> [{h['arms'][best]['ci95'][0]:.4f}, {h['arms'][best]['ci95'][1]:.4f}] ({h['evaluator_version']}, {h['n_withheld_positive_pixels']:,} withheld positives) — beats C-KPL ({h['arms']['C-KPL']['dti']:.6f}) by <strong>+{h['paired_vs_C_KPL']['paired_delta_dti']:.4f}</strong> (4/4 folds) and KPL-36 EXP-3 (0.170100) by <strong>+0.0307</strong>.<br>
<strong>G3a Surface PASS:</strong> pre-placement max |Spearman| = {cross['surface_before_placement']['max_abs_rank_correlation_all_198']:.4f} (&le;0.90 across 198 rasters).<br>
<strong>G3b/G3c Overlap STOP:</strong> passes 18/18 local GEMSDOE36 files (&le;65.95%), 13/13 Oct 25–27 modern peers (&le;68.49%), and 7/9 Focus-9 champions (vs GEMSDOE32 B2 = <strong>65.49%</strong>), but wide &ge;60k blankets (GEMSDOE27 d1.5 = 70.96%, reg-062 = 96.23%) and the 5&times;5 calibration lattice reg-052 (99.48%) exceed 70%.<br>
<strong>G4 Format PASS:</strong> single-band float32, [0, 1] whole-grid finite, d_cat &gt; 2 px (min 2.236 px).</p>
</aside>
<div class="table-wrap"><table><caption>Executive summary ledger — downloadable files, measured provenance, scenario range (not a score), and uniqueness</caption>
<thead><tr><th>Site / Lane</th><th>File to download &amp; SHA-256</th><th>Measured metric &amp; provenance</th><th>Scenario range (not a score)</th><th>Uniqueness audit (3-px dot overlap)</th><th>Automated decision</th></tr></thead>
<tbody>{exec_html}</tbody></table></div>
<div class="table-wrap"><table><caption>S2D-36 4-quadrant buffered segment holdout — HOLDOUT-DTI ({h['evaluator_version']}, {h['n_withheld_positive_pixels']:,} withheld positives)</caption>
<thead><tr><th>Arm</th><th>Pooled Metric</th><th>95% Segment-Bootstrap CI</th></tr></thead><tbody>{arms_rows}</tbody></table></div>
<p style="font-size:.92rem"><strong>Why GEMSDOE32 B2 achieved 0.2778 OWNER-REPORTED &amp; how to score higher:</strong> B2 (37,654 dots) is the exact set difference <code>D2.8 \\ {{d_cat &le; 2 px}}</code> (removing 6,436 near-catalogue collar dots where organizer pixel-exact masking zeros out known-fault recall while leaving adjacent background pixels as 4&times;-weighted precision penalties under &alpha;=0.2, &beta;=0.8) on top of 19GEMSDOE H19-5's four-layer skeleton (L1 fault-tip Coulomb lobes + L2 GDR thermal/sinter + L3 3DEP scarps + L4 GeoDAWN worms). KPL-36 (0.1647 USER-REPORTED) trailed due to the 24.63% 1 m LiDAR gap, highway/survey-seam false positives (SW 90.6% FP), and 1-stage piedmont halo bleed. S2D-36 EXP-2 resolves those three physics/inference gaps (+0.0309 HOLDOUT-DTI to 0.200766; scenario range {scen_lo:.3f}–{scen_hi:.3f}, NOT A SCORE). Surpassing 0.2778 toward the 0.4413 / 0.4437 public leaderboard top requires adding Leave-Segment-Out explicit fault-tip &amp; relay-ramp continuation (L1) plus Sentinel-1 InSAR / raw 1-D flight-line wavelets (H-S2D-4); see the <a href="research/s2d36-20261027.md">S2D-36 monograph</a>.</p>
</section>
<!-- S2D36:END -->"""


def build_literal_block() -> str:
    return """<!-- LITERAL_REVIEW:START -->
<section aria-label="Superseding protocol review" style="padding:1.5rem;border:3px solid #ad3434;margin:1rem">
<h2>DO NOT SUBMIT — literal uniqueness gate failed</h2>
<p>27 October 2026: Both S2D-36 EXP-2 (<strong>HOLDOUT-DTI 0.200766</strong>, 99.48% vs reg-052; &le;68.49% vs all modern &le;45k peer detectors and 65.49% vs GEMSDOE32 B2) and KPL-36 EXP-3 (overlap with registry reg-052 is <strong>99.17%</strong>) exceed the literal unseparated 70% limit due to the 5&times;5 calibration lattice (reg-052) and &ge;60k wide blankets.
Every downloadable TIFF on this site is <strong>research only</strong> unless a human selector explicitly scopes uniqueness to deployed &le;45k detectors. No automatic weekly slot was authorized.</p>
<p>Latest KPL result: <strong>0.1647 USER-REPORTED</strong>, no organizer receipt.
No calibrated leaderboard estimate is available for KPL-36; the older KPL-36 scenario range is withdrawn as a forecast (S2D-36 empirical peer-transfer scenario is documented separately as a non-score scenario in the S2D-36 monograph).</p>
<p><a href="research/s2d36-20261027.md">S2D-36 monograph, 4 ranked hypotheses, 0.2778 forensic proof &amp; peer audit</a> ·
<a href="downloads/s2d36-run-card.json">S2D-36 JSON run card</a> ·
<a href="research/review-20261027.md">Prior literal review</a> ·
<a href="downloads/literal-release-review.json">Prior literal run card</a></p>
</section><!-- LITERAL_REVIEW:END -->"""


def build_guide_block(card: dict) -> str:
    sub = card["submission"]
    return f"""<!-- KPL36_GUIDE:START -->
<section class="section" id="how-to-submit" aria-label="How to submit">
<div class="section-head"><div><span class="eyebrow">Submission guide · automated gate: DO NOT SUBMIT</span><h2>How to submit (only if a human selector overrides the reg-052 / wide-blanket gate)</h2></div></div>
<p><strong>Automated status: DO NOT SUBMIT</strong> (<code>verdict: negative</code>, <code>slot_approved: false</code>). Because registry entry <code>reg-052</code> (5&times;5 calibration lattice covering 99.87% of the footprint within 3 px) forces &ge;82.34% overlap on every 37,654-dot file, automated release authorization remains locked off. If the human selector explicitly scopes uniqueness to deployed &le;45,000-dot detectors (where S2D-36 EXP-2 passes all 13 Oct 25–27 peers at &le;68.49% and GEMSDOE32 B2 at 65.49%), follow these exact steps:</p>
<ol>
<li>Download the S2D-36 <strong>single-band GeoTIFF (.tif)</strong> above (<code>{html.escape(Path(sub['file']).name)}</code>, SHA-256 <code>{sub['sha256']}</code>), or the <strong>.zip file containing a single GeoTIFF</strong> (<code>{html.escape(Path(sub['zip']).name)}</code>). It matches the template's <strong>CRS, shape, and geotransform</strong> (EPSG:32611, 3730&times;3292, 100 m) and every pixel satisfies the portal validator check <em>“Predicted values must be in range [0, 1]”</em> — outside-footprint cells are <code>0.0</code>, never <code>NaN</code> (outside-NaN files previously triggered that portal range rejection).</li>
<li>Open the <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/" target="_blank" rel="noopener">DrivenData DOE GEMS competition portal ↗</a>, click <em>Submit</em>, upload the <code>.tif</code> or <code>.zip</code>, and paste this exact &le;140-character Note ({sub['note_characters']}/140 chars): <code>{html.escape(sub['note'])}</code>.</li>
<li>Slot discipline: official rules cap teams at <strong>three weekly slots</strong> and require choosing <strong>one submission for both prize rounds</strong>. Do not spend a slot without recording the selector override; once scored on the portal, save the submission-page receipt in <code>evidence/</code> before labeling any number organizer-confirmed.</li>
</ol>
</section>
<!-- KPL36_GUIDE:END -->"""


def update_readme(card: dict, cross: dict, peers: dict) -> None:
    raw = README.read_text(encoding="utf-8")
    marker = "## Full standing owner brief (historical wording)"
    idx = raw.find(marker)
    if idx < 0:
        raise RuntimeError("Standing owner brief marker missing from README.md")
    standing_suffix = raw[idx:]

    # Extract existing FOCUS9_TABLE block verbatim so pinned SHA-12 table never drifts
    m_table = re.search(r"(<!-- FOCUS9_TABLE:START -->.*?<!-- FOCUS9_TABLE:END -->)", raw, flags=re.S)
    if not m_table:
        raise RuntimeError("FOCUS9_TABLE block missing from README.md")
    focus9_md_table = m_table.group(1)

    sub = card["submission"]
    h = card["holdout"]
    best = card["best_arm"]
    scen = card["scenario_projection_not_a_score"]

    prefix = f"""# GEMSDOE36 — current decision & reproducible research

<!-- LITERAL_REVIEW:START -->
> **27 October 2026 superseding decision: DO NOT SUBMIT (automated fail-closed gate; research download ready).**
> - **New research candidate (`S2D-36 EXP-2`):** [`{Path(sub['file']).name}`]({sub['file']}) ([ZIP]({sub['zip']}), [run card](evidence/s2d36_run_card_20261027.json), [monograph](docs/research/s2d36-20261027.md), [preregistration](evidence/s2d36_preregistration_20261027.json)) achieved **`HOLDOUT-DTI = {h['arms'][best]['dti']:.6f}`** (`95% CI [{h['arms'][best]['ci95'][0]:.4f}, {h['arms'][best]['ci95'][1]:.4f}]`, `gems-segment-pooled-v1`, `60,988` withheld positives), beating `C-KPL` (`0.169892`) and recorded `KPL-36 EXP-3` (`0.170100`, **`0.1647 USER-REPORTED`** live) by **`+0.0307`–`+0.0309`** across **`4/4` spatial folds**, and passing `<= 70%` 3-px dot overlap against **18/18 local `GEMSDOE36` candidates** (`<= 65.95%`), **13/13 Oct 25–27 modern peer detectors** (`<= 68.49%`; `54.23%` vs `GEMSDOE70 0.2478`, `59.98%` vs `GEMSDOE76 0.2343`, `68.49%` vs `GEMSDOE27 H31 0.2250`), and **7/9 Focus-9 champions** (`65.49%` vs `GEMSDOE32 B2 0.2778`).
> - **Why automated submission remains locked off (`verdict: "negative"`, `slot_approved: false`):** Registry entry `reg-052` (`5x5` calibration lattice covering `99.87%` of the footprint within `3 px`) forces `>= 82.34%` overlap on every `37,654`-dot subset (`S2D-36 EXP-2 = 99.48%`, `KPL-36 = 99.17%`), and legacy `>= 60k`-dot blankets (`GEMSDOE27 d1.5 = 70.96%`, `reg-062 = 96.23%`) exceed `70%`. Per anti-gaming rules, dots were not perturbed to evade `reg-052`; spending one of the three weekly DrivenData slots requires an explicit human selector override.
<!-- LITERAL_REVIEW:END -->

**Read this decision and the [standing owner brief](#full-standing-owner-brief-historical-wording) at the start of every session.** Core values: **Maximize P(Win)** and **Own the Outcome**.

> ## CURRENT RESEARCH CANDIDATE · `S2D-36 EXP-2` · DOWNLOAD: YES · DO NOT SUBMIT · `verdict: negative`
>
> - **Downloadable GeoTIFF (portal-safe `[0, 1]`, zeros-outside, `0` `NaN`s):** [`{Path(sub['file']).name}`]({sub['file']}) | [ZIP]({sub['zip']}) | [Run card](evidence/s2d36_run_card_20261027.json) | [Monograph](docs/research/s2d36-20261027.md)
> - **SHA-256:** `{sub['sha256']}` (`{sub['dots']:,}` binary dots, `EPSG:32611`, `3730 x 3292` at `100 m`, `min(d_cat) = 2.236 px`)
> - **Unique submission name:** `{sub['name']}`
> - **Copy-paste Note (`{sub['note_characters']}/140` chars):** `{sub['note']}`
> - **Measured Holdout (`gems-segment-pooled-v1`, `60,988` withheld positives):**
>   - `B0` (59-col baseline): `HOLDOUT-DTI 0.132760` `[0.1205, 0.1449]`
>   - `C-KPL` (101-col KPL control): `HOLDOUT-DTI 0.169892` `[0.1553, 0.1850]` (prior `KPL-36 EXP-3`: `0.170100`, **`0.1647 USER-REPORTED`**)
>   - `EXP-1` (`H-S2D-1`: 10 m 3DEP scarp + TIGER road + GeoDAWN block-seam deconf): `HOLDOUT-DTI 0.184769` `[0.1702, 0.2002]`
>   - **`EXP-2` (`H-S2D-1 + H-S2D-2`: Stage-2 8-azimuth Corridor U-GBDT + 800 m halo sharpening):** **`HOLDOUT-DTI 0.200766` `[0.1865, 0.2153]`** (`+0.0309` vs `C-KPL`, `95% CI [+0.0231, +0.0387]`, `4/4` folds: `NW 0.2125`, `NE_LidarGap 0.2672`, `SW 0.1374`, `SE 0.2160`)
>   - `EXP-3` (`+ H-S2D-3` fold-safe SGMC Dual-Population auxiliary): `HOLDOUT-DTI 0.200593` `[0.1860, 0.2152]`
> - **Scenario Projection (`NOT A SCORE`, no organizer receipt):** `{scen['peer_mechanism_matched_scenario_range'][0]:.3f}–{scen['peer_mechanism_matched_scenario_range'][1]:.3f}` peer-mechanism transfer range (conservative KPL-ratio floor `{scen['conservative_kpl_ratio_projection']:.3f}`; full derivation in [monograph §2.4](docs/research/s2d36-20261027.md)).
> - **Uniqueness Summary:** Pre-placement surface `max |Spearman| = {cross['surface_before_placement']['max_abs_rank_correlation_all_198']:.4f} <= 0.90` across all 198 registry rasters; final 3-px dot overlap `<= 65.95%` vs all 18 local `GEMSDOE36` files, `<= 68.49%` vs all 13 Oct 25–27 modern peer files (`evidence/s2d36_oct27_peer_audit_20261027.json`), `65.49%` vs `GEMSDOE32 B2`, `70.96%` vs `61k`-dot `GEMSDOE27 d1.5`, and `99.48%` vs `reg-052` (`5x5` calibration lattice).

## Why `GEMSDOE32` `B2` Scored `0.2778` (`OWNER-REPORTED`), Why `KPL-36` Scored `0.1647` (`USER-REPORTED`), and How to Score Higher

1. **Exact `GEMSDOE32 B2` mechanism (`0.2778 OWNER-REPORTED`):** Pixel-exact forensics (`evidence/mto36_ninesite_forensics.json`) prove `B2` (`37,654` dots) is `D2.8` (`44,090` dots, `0.2600`) minus the `6,436` pixels within `d_cat <= 2 px` (`200 m`) of `existing_faults.tif` (`XOR = 0`), distilled from `19GEMSDOE H19-5` (`121,131` px, `0.1922`: `L1` fault-tip Coulomb shear lobes & relay bridges + `L2` GDR thermal/sinter + `L3` 3DEP scarps + `L4` GeoDAWN worms). Because organizer scoring masks `existing_faults.tif` pixel-exactly while weighting precision `4x` recall (`alpha = 0.2, beta = 0.8`), stripping `d_cat <= 2 px` collar dots removes unrewarded false-positive exposure.
2. **Why `KPL-36` scored `0.1647 USER-REPORTED` (`0.1701` holdout):** (i) `24.63%` 1 m LiDAR missingness fell back to `100 m` smoothed DEM; (ii) `3–5 km` slope coherence fired on I-80/US-95/US-395 road-cuts and GeoDAWN tie-line block seams (`SW` fold `90.6%` FP); (iii) 1-stage pixelwise GBDT bled across `1–2 km` piedmont aprons; and (iv) quadrant holdout omitted explicit `L1` catalogue tip/relay features.
3. **How `S2D-36` advances `+0.0307` on holdout (`0.200766`) & how to surpass `0.2778` toward `0.4413` / `0.4437`:** `S2D-36 EXP-2` fixes (i)–(iii) via seamless `10 m` 3DEP scarp asymmetry, TIGER road + GeoDAWN 4-block MAD deconfounding, and a zero-leakage Stage-2 8-azimuth Corridor U-GBDT + `800 m` halo sharpener. Surpassing `0.2778` toward leaderboard `#1` (`0.4413` in brief / `0.4437` on 2026-10-26 manual read) requires combining `S2D-36` with **Leave-Segment-Out explicit Mode-II/III fault-tip & relay-ramp continuation (`L1`, `d_cat > 2 px`)** and **Sentinel-1 InSAR phase-gradient / raw 1-D flight-line wavelets (`H-S2D-4`)**; see [`docs/research/s2d36-20261027.md`](docs/research/s2d36-20261027.md).

## Nine-site executive summary — pinned historical snapshot

The TIFF links and masks are rehashed; no historical score has an archived organizer receipt and pinned bytes do not prove which file was uploaded. All nine main refs changed since the snapshot ([freshness receipt](evidence/source_freshness_20261026.json)); newer Oct 25–27 peer submissions across `GEMSDOE24..33`, `GEMSDOE70` (`0.2478 USER-REPORTED`), and `GEMSDOE76` (`0.2343 USER-REPORTED`) are audited in [`evidence/s2d36_oct27_peer_audit_20261027.json`](evidence/s2d36_oct27_peer_audit_20261027.json) and [`docs/research/s2d36-20261027.md`](docs/research/s2d36-20261027.md). All nine historical masks fail the literal pairwise rule against at least one other pinned site.

{focus9_md_table}

The public [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) showed **0.4437** on a manual 2026-10-26 read (`0.4413` in the standing brief below), not a team receipt. Never call a score `ORGANIZER-CONFIRMED` without its archived submission-page receipt.

## Reproduce and verify

```bash
.venv/bin/python scripts/restore_data.py --group all
.venv/bin/python scripts/fetch_registry_rasters.py
.venv/bin/python scripts/run_s2d36_experiment.py --stage canary
.venv/bin/python scripts/run_s2d36_experiment.py --stage all
.venv/bin/python scripts/build_s2d_site.py
.venv/bin/python scripts/check_site.py
.venv/bin/pytest -q
.venv/bin/ruff check src scripts tests
```

The [GitHub Pages decision site](docs/index.html) and [executive submission guide](docs/executive-summary.html) display the fail-closed automated status, downloadable research GeoTIFF/ZIP, and auditable peer tables.

---

"""
    new_readme = prefix + standing_suffix
    assert new_readme.endswith(standing_suffix)
    README.write_text(new_readme, encoding="utf-8")


def main() -> int:
    s2d_card = load(S2D_CARD)
    s2d_cross = load(S2D_CROSS)
    s2d_peers = load(S2D_PEERS)
    kpl_card = load(KPL_CARD)
    dw_card = load(DW_CARD)
    existing_current = load(CURRENT)
    prev_bdc = existing_current["previous_current_run_v4_BDC36"]

    verdict = s2d_card["verdict"]
    gates = s2d_card["gates"]
    promote = verdict == "promote" and all(gates.values())
    if verdict == "promote" and not all(gates.values()):
        raise RuntimeError("FAIL-CLOSED: verdict=promote with failing gates")

    sub = s2d_card["submission"]
    tif_path = ROOT / sub["file"]
    zip_path = ROOT / sub["zip"]
    if sha(tif_path) != sub["sha256"] or sha(zip_path) != sub["zip_sha256"]:
        raise RuntimeError("Artifact SHA-256 mismatch vs S2D-36 run card")
    if len(sub["note"]) > 140:
        raise RuntimeError("Submission note exceeds 140 characters")

    # Mirror S2D-36 run card to docs/downloads/s2d36-run-card.json
    (DOCS / "downloads/s2d36-run-card.json").write_bytes(S2D_CARD.read_bytes())

    best = s2d_card["best_arm"]
    h = s2d_card["holdout"]

    # Update docs/current-run.json (schema v5 bound to S2D-36, preserving KPL-36 & BDC-36)
    current_doc = {
        "schema": "gemsdoe36.current-run.v5",
        "updated_utc": datetime.now(timezone.utc).isoformat(),
        "lane_id": "S2D-36",
        "verdict": verdict,
        "slot_approved": bool(promote),
        "ok_to_download_and_submit": bool(promote),
        "ok_to_download_for_research": True,
        "research_downloads_only": bool(not promote),
        "tif_path": sub["file"].removeprefix("docs/"),
        "tif_sha256": sub["sha256"],
        "zip_path": sub["zip"].removeprefix("docs/"),
        "zip_sha256": sub["zip_sha256"],
        "holdout_dti": h["arms"][best]["dti"],
        "ci95": h["arms"][best]["ci95"],
        "evaluator_version": h["evaluator_version"],
        "withheld_positives": h["n_withheld_positive_pixels"],
        "run_card": "downloads/s2d36-run-card.json",
        "run_card_sha256": sha(S2D_CARD),
        "note": sub["note"],
        "submission_name": sub["name"],
        "gates": gates,
        "score_estimate_scenario_range": None,
        "scenario_projection_not_a_score": s2d_card["scenario_projection_not_a_score"],
        "parallel_experiments": [parallel_dw_projection(dw_card)],
        "previous_current_run_v4_BDC36": prev_bdc,
        "kpl36_run_card": kpl_card,
        "s2d36_run_card": s2d_card,
    }
    CURRENT.write_text(json.dumps(current_doc, indent=2) + "\n", encoding="utf-8")

    # Update docs/downloads/submissions_manifest.json keeping archived_research_only (len 9) untouched
    manifest = load(MANIFEST)
    manifest["slot_approved"] = bool(promote)
    manifest["current_candidate"] = (
        {
            "lane": "S2D-36",
            "file": Path(sub["file"]).name,
            "sha256": sub["sha256"],
            "zip": Path(sub["zip"]).name,
            "zip_sha256": sub["zip_sha256"],
            "card": "s2d36-run-card.json",
            "submit_ok": True,
            "note": sub["note"],
        }
        if promote
        else None
    )
    manifest["run_card"] = "s2d36-run-card.json"
    kpl_sub = kpl_card["submission"]
    manifest["previous_research_candidates"] = [
        {
            "lane": "KPL-36",
            "file": Path(kpl_sub["file"]).name,
            "sha256": kpl_sub["sha256"],
            "zip": Path(kpl_sub["zip"]).name,
            "zip_sha256": kpl_sub["zip_sha256"],
            "card": "kpl36-run-card.json",
            "submit_ok": False,
            "holdout_dti_LABEL": "HOLDOUT-DTI",
            "holdout_dti": kpl_card["holdout"]["arms"]["EXP-3"]["dti"],
            "user_reported_score_no_receipt": 0.1647,
            "organizer_score": None,
        }
    ]
    manifest["research_candidate"] = {
        "lane": "S2D-36",
        "file": Path(sub["file"]).name,
        "sha256": sub["sha256"],
        "zip": Path(sub["zip"]).name,
        "zip_sha256": sub["zip_sha256"],
        "card": "s2d36-run-card.json",
        "submit_ok": bool(promote),
        "note": sub["note"],
        "holdout_dti_LABEL": "HOLDOUT-DTI",
        "holdout_dti": h["arms"][best]["dti"],
        "organizer_score": None,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    lit_block = build_literal_block()
    s2d_block = build_s2d_section(s2d_card, s2d_cross, s2d_peers)
    guide_block = build_guide_block(s2d_card)

    for page in (INDEX, SUMMARY):
        txt = page.read_text(encoding="utf-8")
        txt = txt.replace(
            '<a href="research/registry-preflight-20261026.md">Evidence &amp; research</a>',
            '<a href="research/s2d36-20261027.md">Evidence &amp; research</a>',
        )
        txt = upsert(txt, "<!-- LITERAL_REVIEW:START -->", "<!-- LITERAL_REVIEW:END -->", lit_block, '<main id="main" class="wrap">')
        txt = upsert(txt, "<!-- S2D36:START -->", "<!-- S2D36:END -->", s2d_block, "<!-- LITERAL_REVIEW:END -->", where="after")
        if page == SUMMARY:
            txt = upsert(txt, "<!-- KPL36_GUIDE:START -->", "<!-- KPL36_GUIDE:END -->", guide_block, "<!-- KPL36_ARCHIVE:END -->", where="after")
        page.write_text(txt, encoding="utf-8")

    update_readme(s2d_card, s2d_cross, s2d_peers)
    print(f"[build_s2d_site] updated Pages, manifests, and README (verdict={verdict}, promote={promote})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
