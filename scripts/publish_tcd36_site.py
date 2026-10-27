#!/usr/bin/env python3
"""Deterministic publisher for TCD-36 research artifacts, 9-site executive table, and Pages.

Preserves all PR #31 fail-closed invariants (``LITERAL_REVIEW`` banner, ``verdict == 'negative'``,
``slot_approved == False``, ``current_candidate is None``, ``FOCUS9_EXEC`` table, and all legacy
archived bundle hashes) while surfacing the newly generated and validated ``TCD-36`` GeoTIFF,
JSON Run Card, 9-focus-site uniqueness & score-provenance audit, and PhD synthesis of ``0.2778``.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _replace_or_insert_after(text: str, marker_name: str, block_html: str, anchor: str) -> str:
    start_tag = f"<!-- {marker_name}:START -->"
    end_tag = f"<!-- {marker_name}:END -->"
    wrapped = f"{start_tag}\n{block_html}\n{end_tag}"
    pat = re.compile(re.escape(start_tag) + r".*?" + re.escape(end_tag), flags=re.S)
    if pat.search(text):
        return pat.sub(lambda _m: wrapped, text, count=1)
    if anchor not in text:
        raise RuntimeError(f"Anchor {anchor!r} missing when inserting {marker_name}")
    return text.replace(anchor, f"{anchor}\n{wrapped}", 1)


def build_tcd36_html_section(card: dict, focus_ov: dict) -> str:
    sub = card["submission"]
    h = card["holdout"]
    arms = h["arms"]
    uniq = card["registry_uniqueness"]
    crowd = card["crowding_forensics"]
    tif_rel = sub["file"].removeprefix("docs/")
    nan_rel = sub["companion_nan_file"].removeprefix("docs/")
    zip_rel = sub["zip"].removeprefix("docs/")

    focus_rows_meta = [
        ("GEMSDOE24", "gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif", "68d0e2e4fcc5", "n/a (upstream H19-5 re-thin)", "0.2477 USER-REPORTED", "NO (100.0% vs 8 sites)"),
        ("GEMSDOE25", "gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif", "91eae1ca42ec", "n/a (upstream H19-5 re-thin)", "0.2600 OWNER-REPORTED", "NO (100.0% vs 8 sites)"),
        ("GEMSDOE27", "gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif", "33003374335d", "n/a (H19-5 + gap closure; newer H31-1 = 0.2250 USER-REPORTED)", "0.2449 OWNER-REPORTED", "NO (98.02% vs 8 sites)"),
        ("GEMSDOE28", "gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif", "5556aa1438fd", "n/a (B2 + 6 probe dots)", "0.2710 OWNER-REPORTED", "NO (100.0% vs 8 sites)"),
        ("GEMSDOE30", "gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif", "8cf893ead566", "n/a (identical in-fp to D2.8)", "0.2600 OWNER-REPORTED", "NO (100.0% vs 8 sites)"),
        ("GEMSDOE31", "gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif", "07b6db440535", "n/a (D2.8 minus 2,545 solos)", "0.2708 OWNER-REPORTED", "NO (100.0% vs 8 sites)"),
        ("GEMSDOE32", "gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif", "c55bafc47005", "n/a (D2.8 minus 6,436 d_cat<=2)", "0.2778 OWNER-REPORTED (9-site high)", "NO (100.0% vs 8 sites)"),
        ("GEMSDOE33", "GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif", "87f857d505e2", "n/a (B2 + tip/stepover)", "0.2632 OWNER-REPORTED", "NO (99.71% vs 8 sites)"),
        ("GEMSDOE36 (hist.)", "gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif", "e15891020b9c", "n/a (B2 + 1,200 dots)", "0.2750 OWNER-REPORTED", "NO (97.58% vs 8 sites)"),
    ]

    tr_list = []
    for site_key, fname, sha12, hold_txt, live_txt, hist_u in focus_rows_meta:
        lookup = "GEMSDOE36" if site_key.startswith("GEMSDOE36") else site_key
        ov = focus_ov[lookup]["tcd36_fwd_3px_overlap"]
        tr_list.append(
            f"<tr><th scope=\"row\">{site_key}</th>"
            f"<td><code>{fname}</code><br><small>SHA-12 <code>{sha12}</code> · {focus_ov[lookup]['n_ref_dots']:,} dots</small></td>"
            f"<td>{hold_txt}</td>"
            f"<td><strong>{live_txt}</strong></td>"
            f"<td>{hist_u} · vs TCD-36: <strong>{ov*100:.2f}% (UNIQUE &le;70%)</strong></td>"
            f"<td><strong>DO NOT SUBMIT</strong> (already scored / duplicate family)</td></tr>"
        )

    kpl_ov = focus_ov["GEMSDOE36_KPL36"]["tcd36_fwd_3px_overlap"]
    tr_list.append(
        f"<tr><th scope=\"row\">GEMSDOE36 · KPL-36</th>"
        f"<td><a href=\"downloads/gemsdoe36-kpl36-exp3-20261026-fc869911e88c-zeros.tif\" download>"
        f"<code>gemsdoe36-kpl36-exp3-20261026-fc869911e88c-zeros.tif</code></a><br>"
        f"<small>SHA-12 <code>86fc8243ad57</code> · 37,654 dots · 42.57% 300 m crowding</small></td>"
        f"<td><code>HOLDOUT-DTI 0.170100</code><br><small>[0.1551, 0.1861]</small></td>"
        f"<td><strong>0.1647 USER-REPORTED</strong></td>"
        f"<td>Focus-9 &le;61.6% · reg-052 99.17% · vs TCD-36: <strong>{kpl_ov*100:.2f}%</strong></td>"
        f"<td><strong>DO NOT SUBMIT</strong> (already tested; literal reg-052 fail)</td></tr>"
    )
    tr_list.append(
        f"<tr style=\"background:rgba(25,115,232,0.06)\"><th scope=\"row\">GEMSDOE36 · TCD-36 (NEW 2026-10-27)</th>"
        f"<td><a href=\"{tif_rel}\" download><code>{Path(tif_rel).name}</code></a><br>"
        f"<small>SHA-12 <code>{sub['sha256'][:12]}</code> · {sub['dots']:,} dots · [0, 1] finite · 4.54% crowding</small></td>"
        f"<td><strong><code>HOLDOUT-DTI {arms['EXP-2']['dti']:.6f}</code></strong><br>"
        f"<small>[{arms['EXP-2']['ci95'][0]:.4f}, {arms['EXP-2']['ci95'][1]:.4f}] (+0.0241 vs KPL-36)</small></td>"
        f"<td><em>Unscored (no organizer receipt; no forecast claimed)</em></td>"
        f"<td>Surface |&rho;|=0.4254 &le;0.90 · Focus-9 max <strong>66.82% &le;70%</strong> (vs B2 <strong>56.99%</strong>) · Mutual max <strong>56.72% &le;70%</strong> · Literal reg-052 lattice <strong>99.35% &gt;70%</strong></td>"
        f"<td><strong>DOWNLOAD: YES · DO NOT SUBMIT automatically</strong> (human selector review required for reg-052 calibration-lattice gate per Rule 6)</td></tr>"
    )

    return f"""<section class="hero compact-hero" id="tcd36-release" aria-label="TCD-36 latest research candidate">
<div>
<span class="eyebrow">NEW 27 October 2026 · Lane TCD-36 ({card['best_arm']}) · Automated Validation Complete · verdict: {card['verdict']} · DOWNLOAD: YES</span>
<h1>TCD-36 Two-Stage 10 m 3DEP + Fluvial-&chi; Ridge Detector — Highest Holdout in Repo (+0.0241 over KPL-36), Fail-Closed on Literal Lattice Gate</h1>
<p class="lede"><strong>DOWNLOAD: YES (strict [0, 1] whole-array GeoTIFF verified automatically) · ⛔ DO NOT SUBMIT automatically (literal reg-052 5-px calibration lattice overlap = 99.35% &gt; 70%; human selector review required under Protocol Rule 6).</strong><br>
Primary file: <code>{Path(tif_rel).name}</code> · {sub['dots']:,} binary dots · single-band <code>float32</code> GeoTIFF, <code>EPSG:32611</code>, <code>3730&times;3292</code> at 100 m, all 12,279,160 pixels finite in <code>[0.0, 1.0]</code> (fixes prior portal error <em>&ldquo;Predicted values must be in range [0, 1]&rdquo;</em>), zero NaN inside or outside footprint, zero dots within 200 m of <code>labels.tif</code> · SHA-256 <code>{sub['sha256']}</code>.</p>
<div class="hero-actions">
<a class="button" href="{tif_rel}" download>⬇ Download TCD-36 GeoTIFF (-zeros.tif)</a>
<a class="button secondary" href="{zip_rel}" download>⬇ Download Single-TIFF ZIP</a>
<a class="button secondary" href="{nan_rel}" download>Companion outside-NaN TIFF</a>
<a class="button secondary" href="downloads/tcd36-run-card.json">TCD-36 JSON Run Card</a>
<a class="button secondary" href="research/tcd36-20261027.md">TCD-36 Monograph &amp; PhD 0.2778 Synthesis &rarr;</a>
</div>
<p><strong>Unique submission identifier:</strong> <code>{sub['name']}</code><br>
<strong>Copy-paste Note ({sub['note_characters']}/140 chars):</strong> <code>{sub['note']}</code></p>
</div>
<aside class="status-card" aria-label="TCD-36 automated gate scorecard"><span class="eyebrow">Automated Validation Scorecard (Zero Human Inspector Needed)</span>
<p style="font-size:.92rem">
<strong>G1 Leakage Canary:</strong> PASS &mdash; Stage-1 max AUC <code>{card['leakage_canary']['stage1_max_symmetric_auc']:.4f}</code>, Stage-2 OOF max AUC <code>{card['leakage_canary']['stage2_max_symmetric_auc']:.4f}</code> (&le;0.90).<br>
<strong>G2 Holdout Gate:</strong> PASS &mdash; <strong><code>HOLDOUT-DTI {arms['EXP-2']['dti']:.6f}</code></strong> [{arms['EXP-2']['ci95'][0]:.4f}, {arms['EXP-2']['ci95'][1]:.4f}] (<code>gems-segment-pooled-v1</code>, 60,988 withheld positives), beating KPL-36 (<code>0.170100</code>) by <strong><code>+0.024064</code></strong> across <strong>4/4 spatial folds</strong> (SW Walker Lane <code>0.13911</code> vs KPL <code>0.10470</code>; NE LiDAR Gap <code>0.25694</code> vs <code>0.24466</code>).<br>
<strong>Crowding Cure:</strong> 300 m &ge;3-neighbor dot crowding reduced from <strong>42.57%</strong> (KPL-36, <code>0.1647 USER-REPORTED</code>) to <strong>{crowd['frac_ge3_neighbors_within_300m']*100:.2f}%</strong>; blind 300 m kernel coverage raised <strong>+23.3%</strong> (<code>{crowd['blind_mean_300m_kernel_credit']:.5f}</code> vs <code>0.04210</code>).<br>
<strong>G3a Pre-Placement Surface:</strong> PASS &mdash; max |Spearman &rho;| = <code>{uniq['surface_before_placement']['max_abs_rank_correlation']:.4f}</code> &le; 0.90 across 198 registry rasters (checked strictly before dot placement).<br>
<strong>G3b Focus-9 &amp; Mutual Uniqueness:</strong> PASS &mdash; max 3-px overlap vs all 9 focus-site competing rasters = <code>{uniq['focus9_and_mutual_uniqueness']['focus9_max_competing_3px_dot_overlap']:.4f}</code> &le; 0.70 (vs GEMSDOE32-B2 = <code>0.5699</code>); max mutual overlap across all 215 rasters = <code>{uniq['focus9_and_mutual_uniqueness']['max_mutual_3px_dot_overlap']:.4f}</code> &le; 0.70.<br>
<strong>G3c Literal Unseparated Gate:</strong> FAIL (<code>{uniq['literal_unseparated_a_gt_0']['max_3px_dot_overlap']:.4f}</code> vs <code>reg-052</code> 5-px calibration lattice; mathematical pigeonhole minimum = <code>0.8234</code> for any 37,654 dots). Automatic slot spend stays <strong>DO NOT SUBMIT</strong>.</p>
</aside>
<table><caption>TCD-36 Preregistered Holdout Factorial &mdash; <code>HOLDOUT-DTI</code> (<code>gems-segment-pooled-v1</code>, 60,988 withheld positives; internal validation, not a live leaderboard forecast)</caption>
<thead><tr><th>Arm</th><th>NW</th><th>NE (LiDAR Gap)</th><th>SW (Walker Ln)</th><th>SE</th><th>Pooled HOLDOUT-DTI</th><th>95% Spatial Block CI</th><th>Paired &Delta; vs B0</th></tr></thead>
<tbody>
<tr><td><code>B0</code> (59-col control)</td><td>0.14992</td><td>0.17014</td><td>0.08607</td><td>0.15264</td><td>0.134184</td><td>[0.1223, 0.1464]</td><td>reference</td></tr>
<tr><td><em><code>KPL-36 EXP-3</code> (prior best)</em></td><td><em>0.19581</em></td><td><em>0.24466</em></td><td><em>0.10470</em></td><td><em>0.17285</em></td><td><em>0.170100</em></td><td><em>[0.1537, 0.1846]</em></td><td><em>+0.036166</em></td></tr>
<tr><td><code>TCD-36 EXP-1</code> (10m-3DEP + &chi; + TIGER/Lahontan)</td><td>0.19687</td><td>0.25613</td><td>0.12060</td><td>0.19859</td><td>0.185269</td><td>[0.1701, 0.2009]</td><td>+0.051085 [+0.0390, +0.0627]</td></tr>
<tr><td><strong><code>TCD-36 EXP-2</code> (Stage-2 U-GBDT, sp=2.50)</strong></td><td><strong>0.19700</strong></td><td><strong>0.25694</strong></td><td>0.13911</td><td><strong>0.20817</strong></td><td><strong>0.194164</strong></td><td><strong>[0.1803, 0.2083]</strong></td><td><strong>+0.059980 [+0.0478, +0.0719]</strong></td></tr>
<tr><td><code>TCD-36 EXP-3</code> (Stage-2 + sp=2.85 + echo taper)</td><td>0.19537</td><td>0.25239</td><td><strong>0.13990</strong></td><td>0.20572</td><td>0.192469</td><td>[0.1790, 0.2066]</td><td>+0.058285 [+0.0463, +0.0702]</td></tr>
</tbody></table>
<div class="table-wrap"><table><caption>Executive Comparison Across All 9 Focus Sites + GEMSDOE36 KPL-36 &amp; TCD-36 (Reported live scores have no archived organizer receipt; HOLDOUT-DTI is internal validation, never a forecast)</caption>
<thead><tr><th>Site / Lane</th><th>Artifact &amp; SHA-12</th><th>Internal Validation (<code>HOLDOUT-DTI</code>)</th><th>Reported Live Score (No Receipt)</th><th>Uniqueness Status (&le;70% 3-px Rule)</th><th>Automated Action Status</th></tr></thead>
<tbody>
{"".join(tr_list)}
</tbody></table></div>
<p class="fine-print"><strong>PhD synthesis of why GEMSDOE32 B2 achieved <code>0.2778 OWNER-REPORTED</code> &amp; how to bridge toward <code>0.3195</code> / <code>0.4413</code>:</strong> Under DTI (&alpha;=0.2, &beta;=0.8, 300 m kernel), a dot improves DTI iff marginal weighted recall &Delta;TP<sub>w</sub> &gt; 0.2&middot;DTI (&approx;0.0556 at 0.2778). Every focus-9 leader (0.2449&ndash;0.2778) re-thins a single upstream ridge skeleton (<code>19GEMSDOE H19-5</code>, 0.1922 OWNER-REPORTED): <code>d=2.8</code> dotting cut false positives 3&times; while preserving ~74% along-trace kernel bridge credit (+0.0678), and <code>B2</code> excised 6,436 near-catalogue detector-echo dots at 0 &lt; d<sub>cat</sub> &le; 2 px (+0.0178). Because <code>H19-5</code> covers only ~30&ndash;36% of hidden faults, re-thinning it asymptotes below ~0.295. Surpassing 0.2778 toward non-B2 ML peers (<code>GEMSDOE70</code> 0.2478 USER-REPORTED, <code>GEMSDOE76</code> 0.2343 USER-REPORTED) and public leaders (0.3195 / 0.4413 / 0.4437 manual read) requires closing the 24.63% 1 m LiDAR gap (10 m 3DEP), detecting blind range-front uplift via fluvial &chi;/k<sub>sn</sub> + hydrothermal upflow, consolidating 2D halos via Stage-2 spatial context (implemented here in <code>TCD-36</code>; paired Stage-2 gain +0.008895 [+0.0034, +0.0141]), and adding off-catalogue 1:24k&ndash;1:100k pre-Quaternary bedrock fault/ASTER TIR alteration layers (<a href="research/tcd36-20261027.md">full mathematical derivation &amp; 4 ranked hypotheses &rarr;</a>).<br>
<strong>Official Verified Sources:</strong> <a href="https://www.drivendata.org/competitions/311/competition-doe-gems/page/982/" target="_blank" rel="noopener">DrivenData Problem Description</a> &middot; <a href="https://www.drivendata.org/competitions/311/competition-doe-gems/page/983/" target="_blank" rel="noopener">Submission Format</a> &middot; <a href="https://community.drivendata.org/t/clarification-of-edge-cases-in-metric-calculation/11516/4" target="_blank" rel="noopener">DrivenData Forum DTI Clarification (11516/4)</a> &middot; <a href="https://gdr.openei.org/submissions/1391" target="_blank" rel="noopener">OpenEI GDR #1391 (INGENIOUS)</a> &middot; <a href="https://www.usgs.gov/3d-elevation-program" target="_blank" rel="noopener">USGS 3DEP 10 m DEM</a> &middot; <a href="https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html" target="_blank" rel="noopener">US Census TIGER/Line</a> &middot; <a href="https://www.usgs.gov/programs/earthquake-hazards/faults" target="_blank" rel="noopener">USGS QFaults</a>.</p>
</section>"""


def build_tcd36_readme_block(card: dict) -> str:
    sub = card["submission"]
    arms = card["holdout"]["arms"]
    crowd = card["crowding_forensics"]
    uniq = card["registry_uniqueness"]
    return f"""> ## LATEST RESEARCH CANDIDATE (2026-10-27) · `TCD-36` (`{card['best_arm']}`) · DOWNLOAD: YES · DO NOT SUBMIT AUTOMATICALLY (`verdict: {card['verdict']}`)
>
> - **Validated `[0, 1]` GeoTIFF:** [`{Path(sub['file']).name}`]({sub['file']}) ([Single-TIFF ZIP]({sub['zip']}), [Companion `-nan.tif`]({sub['companion_nan_file']}), [Run Card JSON](evidence/tcd36_run_card_20261027.json), [Monograph & PhD `0.2778` Synthesis](docs/research/tcd36-20261027.md), [Frozen Preregistration](docs/research/tcd36-preregistration-20261027.md)).
> - **SHA-256 (`-zeros.tif`):** `{sub['sha256']}` · **Dots:** `{sub['dots']:,}` · **Grid:** `EPSG:32611`, `3730×3292` at `100 m`, all `12,279,160` cells finite in `[0.0, 1.0]` (`0` NaN/Inf, `0` dots within `200 m` of `labels.tif`).
> - **Unique Name:** `{sub['name']}` · **Copy-Paste Note (`{sub['note_characters']}/140` chars):** `{sub['note']}`
> - **Spatially-Blocked Holdout (`gems-segment-pooled-v1`, `60,988` withheld positives):** **`HOLDOUT-DTI = {arms['EXP-2']['dti']:.6f}`** (95% CI `[{arms['EXP-2']['ci95'][0]:.6f}, {arms['EXP-2']['ci95'][1]:.6f}]`), beating `KPL-36 EXP-3` (`0.170100`) by **`+0.024064`** across **all 4/4 spatial folds** (`NW 0.19700`, `NE_LidarGapHeavy 0.25694`, `SW 0.13911`, `SE 0.20817`) and `B0` (`0.134184`) by **`+0.059980`** (`EXP-1 = {arms['EXP-1']['dti']:.6f}`, `EXP-3 = {arms['EXP-3']['dti']:.6f}`). Internal hide-and-recover metric — not a live leaderboard forecast.
> - **Crowding Collapse Fixed:** Cuts `KPL-36`'s `>=3`-neighbor 300 m blob crowding from **`42.57%`** (`0.1647 USER-REPORTED`) to **`{crowd['frac_ge3_neighbors_within_300m']*100:.2f}%`** (`9.4×` reduction) and expands blind 300 m kernel coverage by **`+23.3%`** (`{crowd['blind_mean_300m_kernel_credit']:.5f}` vs `0.04210`).
> - **Leakage Canary & Multi-Regime Uniqueness:** Stage-1 canary max AUC `{card['leakage_canary']['stage1_max_symmetric_auc']:.4f} <= 0.90` (**PASS**); Stage-2 OOF canary max AUC `{card['leakage_canary']['stage2_max_symmetric_auc']:.4f} <= 0.90` (**PASS**); pre-placement continuous surface `|Spearman rho| = {uniq['surface_before_placement']['max_abs_rank_correlation']:.4f} <= 0.90` (**PASS**); 9-focus-site competing `<100k`-dot 3-px overlap max `{uniq['focus9_and_mutual_uniqueness']['focus9_max_competing_3px_dot_overlap']:.4f} <= 0.70` (vs `GEMSDOE32 B2` = `0.5699`, vs `KPL-36` = `0.5672`, **PASS**); all-215 mutual 3-px overlap max `{uniq['focus9_and_mutual_uniqueness']['max_mutual_3px_dot_overlap']:.4f} <= 0.70` (**PASS**); literal unseparated `a > 0` overlap vs `reg-052` 5-px calibration lattice = `{uniq['literal_unseparated_a_gt_0']['max_3px_dot_overlap']:.4f} > 0.70` (**FAIL — automatic slot promotion remains closed per `PR #31` and Protocol Rule 6**)."""


def main() -> int:
    card_path = ROOT / "evidence" / "tcd36_run_card_20261027.json"
    card = json.loads(card_path.read_text(encoding="utf-8"))
    focus_ov = json.loads((ROOT / "evidence" / "tcd36_focus9_overlap_20261027.json").read_text(encoding="utf-8"))

    # 1. Update docs/current-run.json (preserve v5 KPL-36 schema contract + attach latest TCD-36 summary)
    cur_path = ROOT / "docs" / "current-run.json"
    cur = json.loads(cur_path.read_text(encoding="utf-8"))
    cur["latest_research_lane_tcd36"] = {
        "lane_id": "TCD-36",
        "best_arm": card["best_arm"],
        "verdict": card["verdict"],
        "slot_approved": False,
        "ok_to_download_and_submit": False,
        "ok_to_download_for_research": True,
        "tif_path": card["submission"]["file"].removeprefix("docs/"),
        "tif_sha256": card["submission"]["sha256"],
        "zip_path": card["submission"]["zip"].removeprefix("docs/"),
        "zip_sha256": card["submission"]["zip_sha256"],
        "holdout_label": "HOLDOUT-DTI",
        "holdout_dti": card["holdout"]["arms"][card["best_arm"]]["dti"],
        "ci95": card["holdout"]["arms"][card["best_arm"]]["ci95"],
        "delta_vs_kpl36_exp3": card["holdout"]["delta_vs_kpl36_exp3"],
        "evaluator_version": "gems-segment-pooled-v1",
        "withheld_positives": 60988,
        "run_card": "downloads/tcd36-run-card.json",
        "run_card_sha256": sha256_file(card_path),
        "submission_name": card["submission"]["name"],
        "note": card["submission"]["note"],
        "gates": card["gates"],
    }
    cur_path.write_text(json.dumps(cur, indent=2) + "\n", encoding="utf-8")

    # 2. Update docs/downloads/submissions_manifest.json (keep current_candidate=None, slot_approved=False, 9 archived rows)
    man_path = ROOT / "docs" / "downloads" / "submissions_manifest.json"
    man = json.loads(man_path.read_text(encoding="utf-8"))
    old_rc = man.get("research_candidate")
    if old_rc and old_rc.get("lane") == "KPL-36":
        man["superseded_kpl36_research_candidate"] = old_rc
    man["slot_approved"] = False
    man["current_candidate"] = None
    man["latest_run_card"] = "tcd36-run-card.json"
    man["research_candidate"] = {
        "lane": "TCD-36",
        "file": Path(card["submission"]["file"]).name,
        "sha256": card["submission"]["sha256"],
        "zip": Path(card["submission"]["zip"]).name,
        "zip_sha256": card["submission"]["zip_sha256"],
        "companion_nan_file": Path(card["submission"]["companion_nan_file"]).name,
        "companion_nan_sha256": card["submission"]["companion_nan_sha256"],
        "card": "tcd36-run-card.json",
        "submit_ok": False,
        "note": card["submission"]["note"],
        "holdout_dti_LABEL": "HOLDOUT-DTI",
        "holdout_dti": card["holdout"]["arms"][card["best_arm"]]["dti"],
        "organizer_score": None,
    }
    man_path.write_text(json.dumps(man, indent=2) + "\n", encoding="utf-8")

    # 3. Update docs/index.html & docs/executive-summary.html
    html_block = build_tcd36_html_section(card, focus_ov)
    for page_name in ("index.html", "executive-summary.html"):
        p = ROOT / "docs" / page_name
        txt = p.read_text(encoding="utf-8")
        txt = _replace_or_insert_after(txt, "TCD36", html_block, "<!-- LITERAL_REVIEW:END -->")
        p.write_text(txt, encoding="utf-8")

    # 4. Update README.md
    readme_p = ROOT / "README.md"
    rtxt = readme_p.read_text(encoding="utf-8")
    rtxt = _replace_or_insert_after(rtxt, "TCD36_README", build_tcd36_readme_block(card), "<!-- LITERAL_REVIEW:END -->")
    readme_p.write_text(rtxt, encoding="utf-8")

    print("[publish_tcd36_site] updated current-run.json, submissions_manifest.json, index.html, executive-summary.html, README.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
