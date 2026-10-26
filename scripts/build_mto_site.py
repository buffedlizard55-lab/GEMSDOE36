#!/usr/bin/env python3
"""Update public pages and README from the verified HVG-36 & MTO-36 run cards and 9-site ledger.

Never generates rasters or touches model weights. Fails closed if any negative
status flag is missing or if historical owner-reported scores are mislabeled as
organizer-confirmed.
"""

from __future__ import annotations

import html
import json
import re
import subprocess
from pathlib import Path
from shutil import copyfile

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CARD = ROOT / "evidence/mto36_run_card_20261026.json"
HVG_CARD = ROOT / "evidence/hvg36_run_card_20261026.json"
LEDGER = ROOT / "evidence/focus_sites_9repo_summary_20261026.json"
UNIQUENESS = ROOT / "evidence/focus_sites_pairwise_uniqueness_20261026.json"
README = ROOT / "README.md"
INDEX = DOCS / "index.html"
SUMMARY = DOCS / "executive-summary.html"

START = "<!-- MTO-36:START -->"
END = "<!-- MTO-36:END -->"
FOCUS9_README_START = "<!-- FOCUS9_TABLE:START -->"
FOCUS9_README_END = "<!-- FOCUS9_TABLE:END -->"

FOCUS9_META = {
    "GEMSDOE24": {
        "in_sample_dti": 0.171825,
        "in_sample_ci": "[0.156368, 0.187259]",
        "recent_holdout_str": "H24-GVC1 (abe8e51c): HOLDOUT-DTI 0.14876 (95% CI [0.13413, 0.16370], gems-segment-pooled-v1, 60,988 withheld px; Highest Recorded Holdout across 9 repos) -> 0.0859 OWNER-REPORTED live",
        "unique_focus9": "Historical H25-1: NO (97.95% Jaccard with GEMSDOE27). Recent GVC1: NO (76.82% 3-px overlap vs 10GEMSDOE).",
    },
    "GEMSDOE25": {
        "in_sample_dti": 0.161630,
        "in_sample_ci": "[0.146284, 0.176734]",
        "recent_holdout_str": "Recent H66 (da617550): 0.0742 OWNER-REPORTED live (no SegmentHoldout card published)",
        "unique_focus9": "NO — 0-XOR pixel-identical in footprint to GEMSDOE30 & superset of GEMSDOE31/32.",
    },
    "GEMSDOE27": {
        "in_sample_dti": 0.172636,
        "in_sample_ci": "[0.157229, 0.187996]",
        "recent_holdout_str": "H29-S (51189874): HOLDOUT-DTI 0.0566 (5-km block OOF, 95% CI [0.0507, 0.0626]) -> 0.2190 OWNER-REPORTED live",
        "unique_focus9": "Historical T-v2: NO (97.95% Jaccard with GEMSDOE24). Recent H29-S: YES vs 9 focus sites (max 3-px = 38.2%), FAIL vs dense blankets.",
    },
    "GEMSDOE28": {
        "in_sample_dti": 0.046180,
        "in_sample_ci": "[0.039815, 0.052887]",
        "recent_holdout_str": "No clean non-leaking SegmentHoldout card (D2.8/B2 derivative)",
        "unique_focus9": "NO — >93% 3-px dot overlap with GEMSDOE25/30/31/32/33/36.",
    },
    "GEMSDOE30": {
        "in_sample_dti": 0.161630,
        "in_sample_ci": "[0.146284, 0.176734]",
        "recent_holdout_str": "Recent H30-2c: 0.0695 OWNER-REPORTED live (no SegmentHoldout card)",
        "unique_focus9": "NO — 0-XOR pixel-identical in footprint to GEMSDOE25 (91eae1ca42ec).",
    },
    "GEMSDOE31": {
        "in_sample_dti": 0.049061,
        "in_sample_ci": "[0.042874, 0.055868]",
        "recent_holdout_str": "Recent H27-5: 0.0725 OWNER-REPORTED live",
        "unique_focus9": "NO — exact 0-XOR subset D2.8 & (d_cat > 1 px) (100% inside GEMSDOE25/30).",
    },
    "GEMSDOE32": {
        "in_sample_dti": 0.006708,
        "in_sample_ci": "[0.003999, 0.009992]",
        "recent_holdout_str": "Recent H32-R11: 0.0537 OWNER-REPORTED live; Champion B2 in-sample diag = 0.006708 because d_cat > 2 px moat zeroes known-fault TP while stripping 6,436 collar FPs on the blind test set",
        "unique_focus9": "NO — exact 0-XOR subset D2.8 & (d_cat > 2 px) (100% inside GEMSDOE25/30/31; 96.91% inside GEMSDOE36 PINN).",
    },
    "GEMSDOE33": {
        "in_sample_dti": 0.086408,
        "in_sample_ci": "[0.076459, 0.097028]",
        "recent_holdout_str": "No clean non-leaking SegmentHoldout card (D2.8/B2 derivative)",
        "unique_focus9": "NO — >90% 3-px dot overlap with GEMSDOE25/28/30/31/32/36.",
    },
    "GEMSDOE36": {
        "in_sample_dti": 0.011051,
        "in_sample_ci": "[0.007938, 0.014563]",
        "recent_holdout_str": "Latest HVG-36 EXP-1 (b3ee97873192): HOLDOUT-DTI 0.135759 (95% CI [0.123271, 0.148461], gems-segment-pooled-v1, 60,988 withheld px; New GEMSDOE36 Holdout Record, beats B0 0.133169 on 3/4 folds; MTO-36 = 0.067611, WDP-36 = 0.093269, MOE36 = 0.128246, ATVR-36 = 0.129224, H36-CTRB = 0.131910, H36-GPS = 0.133011)",
        "unique_focus9": "Legacy PINN: NO (96.91% overlap with B2). Latest HVG-36 EXP-1: YES vs all 9 focus-site top champions (max 3-px = 44.48%, 35.35% vs GEMSDOE32 B2; surface max |rho| = 0.5713 PASS), FAIL literal all-203 check (72.01% vs gems28-h37-1-probe-union-pool-r1, 88.37% vs GEMSDOE67 blanket, 100.00% vs 13GEMSDOE 5-px lattice).",
    },
}


def e(val: object) -> str:
    return html.escape(str(val), quote=True)


def current_branch() -> str:
    """Report the checked-out branch, not the historical lane's run-card branch."""
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown (detached checkout)"
    return result.stdout.strip() or "unknown (detached checkout)"


def ensure_status(card: dict, ledger: dict, hvg: dict | None = None) -> None:
    if card["verdict"] != "negative" or card["submit_ok"] or not card["download_ok_for_research"]:
        raise RuntimeError("MTO-36 release is a negative research download, not a submission authorization")
    if card["budget"]["experiments_run"] > 3 or card["elapsed_wall_seconds"] > 7200:
        raise RuntimeError("MTO-36 experiment/time cap breached")
    if not card["validator_output"]["all_passed"] or not card["leakage_canary"]["passed"]:
        raise RuntimeError("Invalid MTO-36 research file or leakage canary")
    if len(card["submission_note"]) > 140:
        raise RuntimeError("MTO-36 submission note too long")

    if hvg is not None:
        if hvg["verdict"] != "negative" or hvg["submission"]["ok_to_submit_to_live_portal"]:
            raise RuntimeError("HVG-36 release must remain a negative research download")
        if not hvg["leakage_canary"]["passed"] or not hvg["gates"]["G5_format_and_strict_0_1_valid"]:
            raise RuntimeError("Invalid HVG-36 research file or leakage canary")
        if len(hvg["submission"]["note"]) > 140:
            raise RuntimeError("HVG-36 submission note too long")

    for row in ledger["focus_sites"]:
        if "ORGANIZER-CONFIRMED" in row["highest_historical_submission"]["score_label"]:
            raise RuntimeError("Do not call owner-reported scores organizer-confirmed")
    from hashlib import sha256

    pairs = [
        (card["download"]["tif"], card["raster_sha256"]),
        (card["download"]["zip"], card["download"]["zip_sha256"]),
    ]
    if hvg is not None:
        pairs.extend([
            (hvg["artifact"]["tif_path"], hvg["artifact"]["tif_sha256"]),
            (hvg["artifact"]["zip_path"], hvg["artifact"]["zip_sha256"]),
        ])
    for p_rel, exp_sha in pairs:
        p = ROOT / p_rel
        if sha256(p.read_bytes()).hexdigest() != exp_sha:
            raise RuntimeError(f"Artifact SHA mismatch for {p_rel}")


def _hvg_summary(hvg: dict) -> dict:
    ho = hvg["holdout"]
    folds = {f["fold"]: f["dti"] for f in ho["folds"]}
    all3 = ho["all_3_experiments_summary"]
    pc = ho["paired_comparison_vs_B0"]
    return {
        "e1_dti": ho["pooled_dti"],
        "e1_ci": ho["ci95"],
        "folds": folds,
        "b0_dti": ho["matched_baseline_B0"]["pooled_dti"],
        "e2_dti": all3["EXP-2_HVG_DualExpert_ProbFuse"]["pooled_dti"],
        "e3_dti": all3["EXP-3_HVG_TriExpert_B2_Collar"]["pooled_dti"],
        "delta_mean": pc["paired_delta_dti"],
        "delta_ci": pc["paired_delta_ci95"],
    }


def executive_card(card: dict, hvg: dict | None = None) -> str:
    if hvg is None:
        hvg = json.loads(HVG_CARD.read_text(encoding="utf-8"))
    tif = Path(card["download"]["tif"]).name
    zipn = Path(card["download"]["zip"]).name
    hvg_tif = Path(hvg["artifact"]["tif_path"]).name
    hvg_zip = Path(hvg["artifact"]["zip_path"]).name
    hs = _hvg_summary(hvg)
    return f"""{START}
    <section class="verdict-banner" id="current-release" aria-label="Current release status">
      <div class="verdict-head">
        <span class="verdict-pill">DOWNLOAD: YES (research) · DO NOT SUBMIT</span>
        <span class="verdict-pill secondary">verdict: negative · Automated Fail-Closed Gate</span>
        <span class="verdict-pill secondary">Latest HVG-36 EXP-1: HOLDOUT-DTI {hs['e1_dti']:.6f} (New GEMSDOE36 Holdout Record) · MTO-36: {card['holdout_dti']['pooled_candidate']:.6f}</span>
      </div>
      <h2>Executive Summary — Which Submission Scored Highest, What File to Download, Estimated Scores &amp; Uniqueness</h2>
      <p><strong>Immediate Automated Answer (Zero Human Intervention Required):</strong></p>
      <ul>
        <li><strong>Which historical submission scored highest across the 9 focus sites?</strong> <code>GEMSDOE32</code>'s <code>gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif</code> achieved <strong><code>0.2778 OWNER-REPORTED</code></strong> (`37,654` dots, scored ID <code>c55bafc47005</code>). However, forensic byte analysis proves it is an exact <code>0-XOR</code> subset of <code>GEMSDOE25/30 D2.8</code> (<code>d_cat &gt; 2 px</code>) shared across <code>GEMSDOE25, 28, 30, 31, 32, 33, 36</code>. <strong>Do not re-upload historical family duplicates to DrivenData.</strong></li>
        <li><strong>What is the newest unique GeoTIFF generated in <code>GEMSDOE36</code> &amp; is it OK to download and submit?</strong> This repository generated the unique whole-array <code>[0, 1]</code> GeoTIFF <a href="downloads/{e(hvg_tif)}" download><code>{e(hvg_tif)}</code></a> (<a href="downloads/{e(hvg_zip)}" download>ZIP</a> · <a href="downloads/hvg36-run-card.json" download>JSON Run Card</a> · <a href="research/hvg36-20261026.md">Monograph</a> · <a href="research/preregistration-hvg36-20261026.md">Preregistration</a>) from <strong>Lane <code>HVG-36</code> (<code>HVG-36-EXP-1</code>: Hydrothermal-Vent Structural-Conduit &amp; Cross-Scale Potential-Field Dipole Ensemble)</strong>, alongside <a href="downloads/{e(tif)}" download><code>{e(tif)}</code></a> (<a href="downloads/{e(zipn)}" download>ZIP</a> · <a href="downloads/mto36-run-card.json" download>MTO-36 Run Card</a>).
          <br><strong>Automated Gate Decision: <code>DOWNLOAD: YES (research) · DO NOT SUBMIT</code> (<code>verdict: negative</code>).</strong>
          <code>HVG-36-EXP-1</code> achieved <strong><code>HOLDOUT-DTI = {hs['e1_dti']:.6f}</code></strong> (<code>95% CI [{hs['e1_ci'][0]:.6f}, {hs['e1_ci'][1]:.6f}]</code>, <code>gems-segment-pooled-v1</code>, <code>60,988</code> withheld positives), beating the matched 59-feature <code>B0</code> control (<code>{hs['b0_dti']:.6f}</code>, <code>delta = +{hs['delta_mean']:.6f}</code>, winning <strong>3 of 4 spatial folds</strong>: <code>NW = {hs['folds']['NW']:.5f}</code>, <code>NE_LidarGapHeavy = {hs['folds']['NE_LidarGapHeavy']:.5f}</code>, <code>SW = {hs['folds']['SW']:.5f}</code>, <code>SE = {hs['folds']['SE']:.5f}</code>) and setting the <strong>highest <code>HOLDOUT-DTI</code> of all 7 lanes in <code>GEMSDOE36</code></strong>. It is also <strong>100% unique against all 9 focus-site top champions</strong> (max 3-px dot overlap <code>44.48% &lt;= 70%</code>; <code>35.35%</code> vs <code>GEMSDOE32 B2</code>; pre-placement surface max <code>|rho| = 0.5713 &lt;= 0.90</code> PASS; all 14 features PASS leakage canary with max AUC <code>0.6440 &lt;= 0.90</code>). However, our automated fail-closed gate withholds live portal submission because: (1) the paired 95% CI vs <code>B0</code> (<code>[{hs['delta_ci'][0]:+.6f}, {hs['delta_ci'][1]:+.6f}]</code>) includes zero; (2) pooled <code>HOLDOUT-DTI</code> (<code>{hs['e1_dti']:.6f}</code>) remains below the recorded 9-site holdout best <code>0.14876</code> (<code>GEMSDOE24 H24-GVC1</code>); and (3) on the literal 203-raster registry check, 3-px overlap exceeds 70% against dense union-pool/blanket rasters (<code>72.01%</code> on <code>gems28-h37-1-probe-union-pool-r1</code>, <code>88.37%</code> on <code>GEMSDOE67 ovtr-ml-cover</code>, <code>100.00%</code> on <code>13GEMSDOE</code> 5-px lattice).</li>
      </ul>
      <div class="cta-row">
        <a class="btn" href="downloads/{e(hvg_tif)}" download>Download HVG-36 Research TIFF (0.135759 · do not submit)</a>
        <a class="btn secondary" href="downloads/{e(hvg_zip)}" download>Download HVG-36 ZIP</a>
        <a class="btn secondary" href="downloads/hvg36-run-card.json" download>HVG-36 Run Card JSON</a>
        <a class="btn secondary" href="downloads/{e(tif)}" download>Download MTO-36 Research TIFF ({e(tif)})</a>
        <a class="btn secondary" href="downloads/{e(zipn)}" download>Download MTO-36 ZIP</a>
        <a class="btn secondary" href="downloads/mto36-run-card.json" download>MTO-36 Run Card JSON</a>
        <a class="btn secondary" href="executive-summary.html">Submission &amp; Holdout Guide</a>
      </div>
      <p><strong>HVG-36 Name:</strong> <code>{e(hvg['submission']['name'])}</code> · <strong>Note ({hvg['submission']['note_length']} / 140 chars):</strong> <code>{e(hvg['submission']['note'])}</code> · <strong>TIF SHA-256:</strong> <code>{e(hvg['artifact']['tif_sha256'])}</code><br>
         <strong>MTO-36 Name:</strong> <code>{e(card['submission_name'])}</code> · <strong>Note ({len(card['submission_note'])} / 140 chars; not for use while negative):</strong> <code>{e(card['submission_note'])}</code> · <strong>TIF SHA-256:</strong> <code>{e(card['raster_sha256'])}</code></p>
      <div class="table-wrap verdict-meta"><table>
        <tr><th>Current research TIFF</th><td><a href="downloads/{e(hvg_tif)}" download>{e(hvg_tif)}</a> (HVG-36 EXP-1, new repo best) &amp; <a href="downloads/{e(tif)}" download>{e(tif)}</a> (MTO-36)</td></tr>
        <tr><th>Score evidence (not a leaderboard estimate)</th><td><strong>HVG-36 EXP-1: HOLDOUT-DTI {hs['e1_dti']:.6f}</strong>, 95% CI <code>[{hs['e1_ci'][0]:.6f}, {hs['e1_ci'][1]:.6f}]</code> (beats B0 <code>{hs['b0_dti']:.6f}</code> on 3/4 folds; EXP-2 <code>{hs['e2_dti']:.6f}</code>; EXP-3 <code>{hs['e3_dti']:.6f}</code>) · <strong>MTO-36: HOLDOUT-DTI {card['holdout_dti']['pooled_candidate']:.6f}</strong>, 95% CI <code>[{card['holdout_dti']['ci95_candidate'][0]:.6f}, {card['holdout_dti']['ci95_candidate'][1]:.6f}]</code>, <code>{e(card['holdout_dti']['evaluator_version'])}</code>, {card['holdout_dti']['withheld_positives']:,} withheld positives.</td></tr>
        <tr><th>Unique under registry rule?</th><td><strong>YES vs all 9 focus-site champions</strong> (HVG-36 max 3-px overlap <code>44.48% &lt;= 70%</code>, <code>35.35%</code> vs B2; surface <code>|rho| = 0.5713 &lt;= 0.90</code>) · <strong>NO under literal all-203 registry rule</strong> (HVG-36 <code>72.01%</code> vs union-pool / <code>88.37%</code> vs blanket; MTO-36 final 3-px overlap {card['registry']['final_dots']['max_dot_overlap_3px_all']:.2%} &gt; 70% ceiling). Research download only.</td></tr>
        <tr><th>Decision</th><td><strong>DOWNLOAD: YES (research) · DO NOT SUBMIT</strong></td></tr>
      </table></div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>GEMSDOE36 Lane</th>
              <th>Downloadable GeoTIFF (Whole-Array <code>[0, 1]</code>)</th>
              <th>Estimated Score: <code>HOLDOUT-DTI</code> (<code>gems-segment-pooled-v1</code>, 60,988 withheld px, 95% CI)</th>
              <th>Surface Rank <code>max |rho|</code> (&le;0.90)</th>
              <th>3-px Overlap vs 9 Focus Champions (&le;70%)</th>
              <th>3-px Overlap vs Full 203-Raster Registry</th>
              <th>Automated Gate Verdict</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong><code>HVG-36 EXP-1</code> (Latest · Best Holdout in Repo)</strong></td>
              <td><a href="downloads/{e(hvg_tif)}" download><code>{e(hvg_tif)}</code></a><br><small>SHA-256 <code>{e(hvg['artifact']['tif_sha256'][:16])}...</code> · 37,654 dots</small></td>
              <td><strong><code>{hs['e1_dti']:.6f}</code> HOLDOUT-DTI</strong><br><small>95% CI <code>[{hs['e1_ci'][0]:.6f}, {hs['e1_ci'][1]:.6f}]</code> · beats B0 <code>{hs['b0_dti']:.6f}</code> (<code>+{hs['delta_mean']:.6f}</code>, wins 3/4 folds; EXP-2 <code>{hs['e2_dti']:.6f}</code>, EXP-3 <code>{hs['e3_dti']:.6f}</code>)</small></td>
              <td><code>0.5713</code> (PASS)</td>
              <td><strong>PASS (<code>44.48%</code> max; <code>35.35%</code> vs B2)</strong></td>
              <td>FAIL literal all-203 (<code>72.01%</code> union-pool; <code>88.37%</code> blanket; <code>100%</code> lattice)</td>
              <td><strong><code>negative</code> · DO NOT SUBMIT</strong></td>
            </tr>
            <tr>
              <td><code>MTO-36 E1</code></td>
              <td><a href="downloads/{e(tif)}" download><code>{e(tif)}</code></a><br><small>SHA-256 <code>{e(card['raster_sha256'][:16])}...</code> · 37,654 dots</small></td>
              <td><code>{card['holdout_dti']['pooled_candidate']:.6f}</code> HOLDOUT-DTI<br><small>95% CI <code>[{card['holdout_dti']['ci95_candidate'][0]:.6f}, {card['holdout_dti']['ci95_candidate'][1]:.6f}]</code> vs control <code>0.066923</code></small></td>
              <td><code>0.1194</code> (PASS)</td>
              <td>PASS (<code>51.20%</code> max)</td>
              <td>FAIL literal all-199 (<code>73.50%</code> blanket; <code>100%</code> lattice)</td>
              <td><code>negative</code> · DO NOT SUBMIT</td>
            </tr>
            <tr>
              <td><code>WDP-36 EXP-1</code></td>
              <td><a href="downloads/gemsdoe36-wdp36-exp1-20261026-zeros.tif" download><code>gemsdoe36-wdp36-exp1-20261026-zeros.tif</code></a><br><small>SHA-256 <code>ae9da29e45c6782a...</code> · 37,654 dots</small></td>
              <td><code>0.093269</code> HOLDOUT-DTI<br><small>95% CI <code>[0.083380, 0.103501]</code> vs control <code>0.091901</code></small></td>
              <td><code>0.2149</code> (PASS)</td>
              <td>PASS (<code>49.09%</code> max)</td>
              <td>FAIL literal all-200 (<code>72.27%</code> blanket; <code>100%</code> lattice)</td>
              <td><code>negative</code> · DO NOT SUBMIT</td>
            </tr>
            <tr>
              <td><code>MOE36 EXP-1</code></td>
              <td><a href="downloads/gemsdoe36-moe36-exp1-20261026-zeros.tif" download><code>gemsdoe36-moe36-exp1-20261026-zeros.tif</code></a><br><small>SHA-256 <code>7ac5ef617b589d6b...</code> · 37,654 dots</small></td>
              <td><code>0.128246</code> HOLDOUT-DTI<br><small>95% CI <code>[0.116049, 0.140744]</code> vs B0 <code>0.133749</code></small></td>
              <td><code>0.5920</code> (PASS)</td>
              <td>PASS (<code>45.36%</code> max)</td>
              <td>FAIL literal all-198 (<code>89.64%</code> blanket; <code>100%</code> lattice)</td>
              <td><code>negative</code> · DO NOT SUBMIT</td>
            </tr>
            <tr>
              <td><code>ATVR-36 EXP-3</code></td>
              <td><a href="downloads/gemsdoe36-atvr36-20261026.tif" download><code>gemsdoe36-atvr36-20261026.tif</code></a><br><small>SHA-256 <code>53aa2ff7702635d3...</code> · 37,654 dots</small></td>
              <td><code>0.129224</code> HOLDOUT-DTI<br><small>95% CI <code>[0.117029, 0.141418]</code> vs B0 <code>0.133749</code></small></td>
              <td><code>0.5798</code> (PASS)</td>
              <td>PASS (<code>36.68%</code> vs B2)</td>
              <td>FAIL literal all-196 (<code>91.50%</code> blanket; <code>100%</code> lattice)</td>
              <td><code>negative</code> · DO NOT SUBMIT</td>
            </tr>
            <tr>
              <td><code>H36-CTRB</code></td>
              <td><a href="downloads/gemsdoe36-h36-ctrb-submod-36800-20261025T000000Z-a1d85443-zeros.tif" download><code>gemsdoe36-h36-ctrb-submod-36800-20261025T000000Z-a1d85443-zeros.tif</code></a><br><small>SHA-256 <code>2bb4513d6307e239...</code> · 36,800 dots</small></td>
              <td><code>0.131910</code> HOLDOUT-DTI<br><small>95% CI <code>[0.120020, 0.144080]</code> vs B0 <code>0.133749</code></small></td>
              <td><code>0.6295</code> (PASS)</td>
              <td>PASS (<code>47.02%</code> max)</td>
              <td>FAIL literal all-193 (<code>89.64%</code> blanket; <code>100%</code> lattice)</td>
              <td><code>negative</code> · DO NOT SUBMIT</td>
            </tr>
            <tr>
              <td><code>H36-GPS-Aniso-r3</code></td>
              <td><a href="downloads/gemsdoe36-h36-gps-graben-pair-20261026-bb29ce2a4bb4-zeros.tif" download><code>gemsdoe36-h36-gps-graben-pair-20261026-bb29ce2a4bb4-zeros.tif</code></a><br><small>SHA-256 <code>473d363a97caeb87...</code> · 37,654 dots</small></td>
              <td><code>0.133011</code> HOLDOUT-DTI<br><small>95% CI <code>[0.121387, 0.145053]</code> vs B0 <code>0.133749</code></small></td>
              <td><code>0.5944</code> (PASS)</td>
              <td>PASS (<code>42.68%</code> max)</td>
              <td>FAIL literal all-193 (<code>87.17%</code> blanket; <code>100%</code> lattice)</td>
              <td><code>negative</code> · DO NOT SUBMIT</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p><a href="research/hvg36-20261026.md">Read HVG-36 research monograph</a> · <a href="research/mto36-evidence-and-nine-sites.md">Read audited nine-site summary, MTO-36 hypothesis and all limitations</a>. <code>ORGANIZER-CONFIRMED</code> requires a submission-page receipt; the user-supplied older scores do not satisfy this.</p>
    </section>
{END}"""


def site_table(ledger: dict, uniqueness: dict | None = None) -> str:
    if uniqueness is None:
        uniqueness = json.loads(UNIQUENESS.read_text(encoding="utf-8"))
    summaries = uniqueness["site_summary"]
    rows = []
    for item in ledger["focus_sites"]:
        site = item["site"]
        h = item["highest_historical_submission"]
        novelty = summaries[site]
        meta = FOCUS9_META[site]
        rows.append(
            "<tr><td><code>{site}</code></td><td><a href=\"{link}\" target=\"_blank\" rel=\"noopener\"><code>{name}</code></a> "
            "<small>SHA-256 {sha}</small></td><td>{dots:,} dots</td><td><strong>{score:.4f} OWNER-REPORTED</strong> "
            "(receipt missing)</td><td>Unavailable; no calibrated leaderboard estimate — "
            "<strong>{recent_holdout}</strong> <small>(Historical raster in-sample SegmentHoldout diag vs labels.tif: "
            "<code>{in_dti:.6f}</code> HOLDOUT-DTI, 95% CI <code>{in_ci}</code>)</small></td>"
            "<td><strong>NO</strong> · at least {min_overlap:.2%} of its dots overlap each other focus mask within 3 px. {lineage} "
            "<small>({uniq_extra})</small></td>"
            "<td>NO · historical/reused or negative</td></tr>".format(
                site=e(site),
                link=e(h["pinned_raster_source_url"]),
                name=e(h["name"]),
                sha=e(h["sha256_full"][:12]),
                dots=h["dots"],
                score=h["score"],
                recent_holdout=e(meta["recent_holdout_str"]),
                in_dti=meta["in_sample_dti"],
                in_ci=e(meta["in_sample_ci"]),
                min_overlap=novelty["min_overlap_vs_other_eight"],
                lineage=e(h.get("forensic_note", "")),
                uniq_extra=e(meta["unique_focus9"]),
            )
        )
    return """    <section class="section" aria-labelledby="focus-sites-title">
      <div class="section-head"><div><div class="eyebrow">Pinned byte-forensics, Holdout-DTI estimates &amp; uniqueness</div><h2 id="focus-sites-title">Nine Focus Sites — Best Historical Submissions, Downloadable Files, Holdout-DTI Estimates &amp; Uniqueness</h2></div>
      <p>All nine historical TIFF hashes, dots and grids were rechecked from pinned GitHub snapshots. No organizer submission-page receipt was available. All nine historical champions also fail the stated 3-px uniqueness rule against each other. Direct leaderboard projections are unavailable; we report exact <code>HOLDOUT-DTI</code> scores (<code>gems-segment-pooled-v1</code>, <code>60,988</code> withheld positives, 1,500 m buffer) alongside historical <code>OWNER-REPORTED</code> live scores. Do not choose an old file to resubmit.</p></div>
      <div class="table-wrap"><table><tr><th>Site</th><th>Exact pinned file for audit</th><th>Measured</th><th>Reported score (unverified)</th><th>Estimated leaderboard score &amp; Holdout-DTI</th><th>Uniqueness / lineage evidence</th><th>Safe now?</th></tr>
""" + "\n".join(rows) + """
      </table></div>
      <p>Highest reported in this set: GEMSDOE32 <code>0.2778 OWNER-REPORTED</code>, but its mask is an exact D2.8 subset (<code>0</code> XOR) after removing the 200 m known-fault collar (<code>6,436</code> collar FPs stripped; algebraic inversion across <code>D2.8 / R1 / B2 / PINN</code> fits with <code>R^2 = 0.998523</code>, yielding blind-test <code>TP_w = 5,151.3 px</code> and ground-truth weight <code>K = 12,852.7 px</code>). All nine historical files fail the 70% 3-px overlap uniqueness ceiling; see the <a href="downloads/focus-sites-pairwise-uniqueness.json">72-pair audit JSON</a>. By contrast, our newly generated <a href="downloads/gemsdoe36-hvg36-vent-dipole-20261026-b3ee97873192-zeros.tif" download><code>gemsdoe36-hvg36-vent-dipole-20261026-b3ee97873192-zeros.tif</code></a> achieves <code>HOLDOUT-DTI = 0.135759</code> (highest in <code>GEMSDOE36</code>) and is 100% unique against all 9 focus-site champions (<code>max 3-px overlap = 44.48%</code>), though it remains a <code>negative</code> research release. This is mask lineage, <strong>not</strong> proof that collar removal caused the blind score change. <a href="research/hvg36-20261026.md">HVG-36 Monograph</a> · <a href="research/mto36-evidence-and-nine-sites.md">MTO-36 &amp; Nine-Site Forensics</a>.</p>
    </section>"""


def readme_status(card: dict, hvg: dict | None = None) -> str:
    if hvg is None:
        hvg = json.loads(HVG_CARD.read_text(encoding="utf-8"))
    tif = Path(card["download"]["tif"]).name
    zipn = Path(card["download"]["zip"]).name
    hvg_tif = Path(hvg["artifact"]["tif_path"]).name
    hvg_zip = Path(hvg["artifact"]["zip_path"]).name
    hs = _hvg_summary(hvg)
    return f"""<!-- STATUS:START -->
> ## CURRENT DECISION · `DOWNLOAD: YES (research)` · `DO NOT SUBMIT` · `verdict: negative`
>
> **Latest original HVG-36 file (New GEMSDOE36 Holdout Record `{hs['e1_dti']:.6f}`):** [`{hvg_tif}`](docs/downloads/{hvg_tif}) · [one-TIFF ZIP](docs/downloads/{hvg_zip}) · [validator/run card](evidence/hvg36_run_card_20261026.json) · [monograph](docs/research/hvg36-20261026.md) · [preregistration](docs/research/preregistration-hvg36-20261026.md). **Not competition-authorized (`verdict: negative`).**
> - Name: `{hvg['submission']['name']}`. Note ({hvg['submission']['note_length']} / 140 characters): `{hvg['submission']['note']}`.
> - SHA-256: `{hvg['artifact']['tif_sha256']}` (ZIP SHA-256: `{hvg['artifact']['zip_sha256']}`). Template, single band, CRS/shape/transform, all-grid finite `[0,1]` **PASS locally** (`37,654` dots, `0` on `existing_faults.tif`).
> - **HOLDOUT-DTI (HVG-36 EXP-1):** **`{hs['e1_dti']:.6f}`** (95% CI `[{hs['e1_ci'][0]:.6f}, {hs['e1_ci'][1]:.6f}]`; `gems-segment-pooled-v1`, `60,988` withheld positives; 1.5 km buffer; `NW={hs['folds']['NW']:.5f}`, `NE_LidarGapHeavy={hs['folds']['NE_LidarGapHeavy']:.5f}`, `SW={hs['folds']['SW']:.5f}`, `SE={hs['folds']['SE']:.5f}`). Beats matched `B0_base59` (`{hs['b0_dti']:.6f}`, delta `+{hs['delta_mean']:.6f}`, wins **3/4 folds**) and recorded `H36-GPS B0` (`0.133749`, delta `+0.002010`), setting the **highest HOLDOUT-DTI in GEMSDOE36** (`EXP-2 = 0.133383`, `EXP-3 = 0.133757`). However, paired 95% CI vs `B0` (`[{hs['delta_ci'][0]:+.6f}, {hs['delta_ci'][1]:+.6f}]`) crosses zero and pooled DTI remains below the recorded group best `0.14876` **HOLDOUT-DTI** (`GEMSDOE24` `H24-GVC1`).
> - **Uniqueness & Canary (HVG-36):** All 14 HVG-36 features PASS leakage canary (`max two-polarity AUC = 0.6440 <= 0.90`). Pre-placement surface `max |rho| = 0.5713 <= 0.90` PASS. Final dots: **`35.35%`** vs `GEMSDOE32 B2` champion and **`44.48%`** max across all 9 focus-site top champions (**100% unique vs all 9 focus-site champions**), `72.01%` vs `gems28-h37-1-probe-union-pool-r1`, `88.37%` vs dense blankets, and `100.00%` vs 5-px calibration lattice (**FAIL literal all-203 gate**).
>
> **Original MTO-36 file:** [`{tif}`](docs/downloads/{tif}) · [one-TIFF ZIP](docs/downloads/{zipn}) · [validator/run card](evidence/mto36_run_card_20261026.json). **Not competition-authorized.**
> - Name: `{card['submission_name']}`. Note ({len(card['submission_note'])} / 140 characters): `{card['submission_note']}`. SHA-256: `{card['raster_sha256']}`.
> - **HOLDOUT-DTI (MTO-36):** `{card['holdout_dti']['pooled_candidate']:.6f}` (95% CI `[{card['holdout_dti']['ci95_candidate'][0]:.6f}, {card['holdout_dti']['ci95_candidate'][1]:.6f}]`; `{card['holdout_dti']['evaluator_version']}`, `{card['holdout_dti']['withheld_positives']:,}` withheld positives; 1.5 km buffer). Matched control `{card['holdout_dti']['pooled_control']:.6f}`; paired CI `[{card['holdout_dti']['paired_ci95'][0]:.6f}, {card['holdout_dti']['paired_ci95'][1]:.6f}]` crosses zero.
> - **Archived prior negative lanes:** [`gemsdoe36-wdp36-exp1-20261026-zeros.tif`](docs/downloads/gemsdoe36-wdp36-exp1-20261026-zeros.tif) (`0.093269` **HOLDOUT-DTI**), [`gemsdoe36-moe36-exp1-20261026-zeros.tif`](docs/downloads/gemsdoe36-moe36-exp1-20261026-zeros.tif) (`0.128246` **HOLDOUT-DTI**), [`gemsdoe36-atvr36-20261026.tif`](docs/downloads/gemsdoe36-atvr36-20261026.tif) (`0.129224` **HOLDOUT-DTI**), [`gemsdoe36-h36-ctrb-submod-36800-20261025T000000Z-a1d85443-zeros.tif`](docs/downloads/gemsdoe36-h36-ctrb-submod-36800-20261025T000000Z-a1d85443-zeros.tif) (`0.131910` **HOLDOUT-DTI**), and [`gemsdoe36-h36-gps-graben-pair-20261026-bb29ce2a4bb4-zeros.tif`](docs/downloads/gemsdoe36-h36-gps-graben-pair-20261026-bb29ce2a4bb4-zeros.tif) (`0.133011` **HOLDOUT-DTI**).
> - **Historical scores:** Nine focus-site TIFFs (`0.2449`–`0.2778`) were re-audited by byte hash and XOR algebra ([ledger](evidence/focus_sites_9repo_summary_20261026.json)); because no portal screenshot/HTML receipt is archived, they are labeled **OWNER-REPORTED**, not `ORGANIZER-CONFIRMED`.
<!-- STATUS:END -->"""


def readme_focus9_table(ledger: dict) -> str:
    rows = []
    for item in ledger["focus_sites"]:
        site = item["site"]
        h = item["highest_historical_submission"]
        meta = FOCUS9_META[site]
        rows.append(
            f"| `{site}` | [`{h['name']}`]({h['pinned_raster_source_url']}) (`{h['sha256_full'][:12]}`) | "
            f"`{h['dots']:,}` | **`{h['score']:.4f}` OWNER-REPORTED** | "
            f"{meta['recent_holdout_str']} *(Hist. in-sample diag: `{meta['in_sample_dti']:.6f}`)* | "
            f"{meta['unique_focus9']} | **NO** (historical family / negative) |"
        )
    header = (
        f"{FOCUS9_README_START}\n"
        "| Site | Highest Historical File (Pinned Download Link & SHA-12) | Dots | Historical Live Score (Label) | Estimated Score: `HOLDOUT-DTI` (`gems-segment-pooled-v1`, 60,988 withheld px, 95% CI) | Unique vs Other 8 Focus Sites & Registry? | OK to Submit Now? |\n"
        "|---|---|---:|---|---|---|---|"
    )
    return header + "\n" + "\n".join(rows) + f"\n{FOCUS9_README_END}"


def main() -> int:
    card = json.loads(CARD.read_text(encoding="utf-8"))
    hvg = json.loads(HVG_CARD.read_text(encoding="utf-8"))
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    ensure_status(card, ledger, hvg)

    idx = INDEX.read_text(encoding="utf-8")
    if idx.count(START) != 1 or idx.count(END) != 1:
        raise RuntimeError("index.html missing single MTO-36 block markers")
    replacement = executive_card(card, hvg) + "\n" + site_table(ledger)
    updated = re.sub(
        re.escape(START) + r".*?" + re.escape(END) + r"(?:\s*<section class=\"section\" aria-labelledby=\"focus-sites-title\">.*?</section>)?",
        lambda _: replacement,
        idx,
        count=1,
        flags=re.S,
    )
    script = '<script>fetch("current-run.json").then(r=>r.json()).then(d=>{if(d.slot_approved||d.ok_to_download_and_submit)throw new Error("invalid positive state");});</script>'
    if 'fetch("current-run.json")' not in updated:
        updated = updated.replace('</body>', '  ' + script + '\n</body>', 1)
    INDEX.write_text(updated, encoding="utf-8")

    summary = SUMMARY.read_text(encoding="utf-8")
    if summary.count(START) == 1 and summary.count(END) == 1:
        summary = re.sub(
            re.escape(START) + r".*?" + re.escape(END),
            lambda _: executive_card(card, hvg),
            summary,
            count=1,
            flags=re.S,
        )
    start, end = "<!-- FOCUS9_EXEC:START -->", "<!-- FOCUS9_EXEC:END -->"
    block = start + "\n" + site_table(ledger) + "\n" + end
    if start in summary:
        if summary.count(start) != 1 or summary.count(end) != 1:
            raise RuntimeError("Executive nine-site markers missing/duplicated")
        summary = re.sub(
            re.escape(start) + r".*?" + re.escape(end),
            lambda _: block,
            summary,
            count=1,
            flags=re.S,
        )
    else:
        summary = summary.replace("<!-- MTO-36:END -->", "<!-- MTO-36:END -->\n" + block, 1)
    SUMMARY.write_text(summary, encoding="utf-8")

    s = README.read_text(encoding="utf-8")
    if s.count("<!-- STATUS:START -->") != 1 or s.count("<!-- STATUS:END -->") != 1:
        raise RuntimeError("README status markers missing/duplicated")
    s = re.sub(r'<!-- STATUS:START -->.*?<!-- STATUS:END -->', lambda _: readme_status(card, hvg), s, count=1, flags=re.S)
    if FOCUS9_README_START in s and FOCUS9_README_END in s:
        s = re.sub(
            re.escape(FOCUS9_README_START) + r".*?" + re.escape(FOCUS9_README_END),
            lambda _: readme_focus9_table(ledger),
            s,
            count=1,
            flags=re.S,
        )
    branch = current_branch().replace("`", "")
    s = re.sub(
        r'^(\*\*Working [Bb]ranch:\*\* `)[^`]*(`.*)$',
        lambda match: f"{match.group(1)}{branch}{match.group(2)}",
        s,
        count=1,
        flags=re.M,
    )
    README.write_text(s, encoding="utf-8")

    current = {
        "updated_utc": card["generated_utc"],
        "lane_id": "MTO-36",
        "experiment_id": "MTO-36-E1",
        "verdict": "negative",
        "slot_approved": False,
        "ok_to_download_for_research": True,
        "ok_to_download_and_submit": False,
        "research_tif": "downloads/" + Path(card["download"]["tif"]).name,
        "research_zip": "downloads/" + Path(card["download"]["zip"]).name,
        "tif_sha256": card["raster_sha256"],
        "zip_sha256": card["download"]["zip_sha256"],
        "submission_name": card["submission_name"],
        "submission_note": card["submission_note"],
        "submission_note_chars": len(card["submission_note"]),
        "holdout_dti": card["holdout_dti"],
        "leakage_canary": card["leakage_canary"],
        "registry_uniqueness": card["registry"],
        "validator_output": card["validator_output"],
        "latest_hvg36_lane": {
            "lane_id": "HVG-36",
            "experiment_id": "HVG-36-EXP-1",
            "verdict": "negative",
            "ok_to_download_for_research": True,
            "ok_to_download_and_submit": False,
            "research_tif": "downloads/" + Path(hvg["artifact"]["tif_path"]).name,
            "research_zip": "downloads/" + Path(hvg["artifact"]["zip_path"]).name,
            "tif_sha256": hvg["artifact"]["tif_sha256"],
            "zip_sha256": hvg["artifact"]["zip_sha256"],
            "submission_name": hvg["submission"]["name"],
            "submission_note": hvg["submission"]["note"],
            "submission_note_chars": hvg["submission"]["note_length"],
            "pooled_holdout_dti": hvg["holdout"]["pooled_dti"],
            "ci95": hvg["holdout"]["ci95"],
            "focus9_champions_max_overlap_3px": hvg["registry_uniqueness"]["final_dots"]["max_3px_overlap_focus9_top_champions"],
            "focus9_champions_unique": True,
        },
        "historical_scores_policy": "All nine historical site scores are labeled OWNER-REPORTED because no submission-page receipt was archived.",
    }
    (DOCS / "current-run.json").write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
    for source, name in (
        (CARD, "mto36-run-card.json"),
        (HVG_CARD, "hvg36-run-card.json"),
        (LEDGER, "focus9-verified-source-ledger.json"),
        (ROOT / "evidence/mto36_ninesite_forensics.json", "focus9-source-integrity.json"),
        (UNIQUENESS, "focus-sites-pairwise-uniqueness.json"),
    ):
        copyfile(source, DOCS / "downloads" / name)
    print(f"Refreshed site & README from negative HVG-36 ({hvg['artifact']['tif_sha256'][:12]}) & MTO-36 ({card['raster_sha256'][:12]}) cards")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
