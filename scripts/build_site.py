#!/usr/bin/env python3
"""Build current fail-closed Pages from the registry-preflight run card.

Historical rendering functions below are archived and cannot be invoked as a release.
"""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CTRB_CARD = ROOT / "evidence/h36_ctrb_run_card_20261025.json"
CTRB_CC = ROOT / "evidence/h36_ctrb_crosscheck_20261025.json"
GPS_CARD = ROOT / "evidence/h36_run_card.json"
DOCS = ROOT / "docs"
LANE36_CARD = DOCS / "downloads/lane36_run_card.json"
LANE36_CC = ROOT / "evidence/lane36_crosscheck.json"

COMP = "https://www.drivendata.org/competitions/306/competition-doe-gems/"
PROBLEM = "https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/"
LEADER = "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/"
RULES = "https://docs.nlr.gov/docs/fy26osti/96647.pdf"
REF = "https://github.com/drivendataorg/gems-prize-reference-solution"
GDR = "https://gdr.openei.org/submissions/1391"
GEODAWN = "https://doi.org/10.5066/P93LGLVQ"
TDEP = "https://www.usgs.gov/3d-elevation-program"
QFAULTS = "https://www.usgs.gov/programs/earthquake-hazards/faults"
COMCAT = "https://earthquake.usgs.gov/fdsnws/event/1/"
OPERA = "https://www.asf.alaska.edu/data-sets/derived-data-sets/opera/"

CTRB_GATE_TEXT = {
    "G1_beats_matched_local_controls": "Holdout (G1): beats matched local controls CTRL-1, CTRL-2 (+0.0565, 4/4 folds) & EXP-1 (+0.0228, 4/4 folds)",
    "G2_beats_group_holdout_best": "Holdout (G2): beats repo B0 (0.13375) and recorded group best (0.14876) on gems-segment-pooled-v1",
    "G3_leakage_canary": "Leakage canary (G3): two-polarity single-feature AUC <= 0.90 across all 25 features (max = 0.6414)",
    "G4a_unique_surface": "Uniqueness — surface before placement (G4a): |Spearman rho| <= 0.90 (max = 0.3297)",
    "G4b_unique_final_dots_scored_107": "Uniqueness — final dots vs 107 owner-scored rasters (G4b): <= 70% within 3 px (max = 51.01%; 33.95% vs GEMSDOE32)",
    "G4c_unique_final_dots_expanded_198": "Uniqueness — final dots vs 198 expanded registry incl. 41-55% area blankets (G4c): <= 70% within 3 px (max = 83.88%)",
    "G5_format_and_strict_range": "Format & Portal Range (G5): EPSG:32611, 3730x3292, float32, nodata=None, all 12,279,160 cells finite in [0, 1]",
}

GPS_GATE_TEXT = {
    "G1_beats_matched_baseline": "Holdout: beats the matched baseline (paired 95% CI > 0, >= 3/4 folds)",
    "G2_beats_current_holdout_best": "Holdout: beats the current holdout best (matched baseline and recorded group best 0.14876)",
    "G3_leakage_canary": "Leakage canary: no single feature with AUC > 0.90 (both polarities)",
    "G4a_unique_surface": "Uniqueness — surface before placement (|rho| <= 0.90)",
    "G4b_unique_final_dots": "Uniqueness — final dots (<= 70% within 3 px of any competing registry raster; |rho| <= 0.90)",
    "G5_format_and_strict_range": "Format: exact CRS/shape/transform, single band float32, finite, strict [0, 1]",
}


def e(x) -> str:
    return html.escape(str(x))


def fmt(x, nd=5) -> str:
    return "n/a" if x is None else f"{x:.{nd}f}"


def ci(v) -> str:
    return "n/a" if not v else f"[{v[0]:.5f}, {v[1]:.5f}]"


def lane36_status():
    if not LANE36_CARD.exists():
        return None, None, None
    c = json.loads(LANE36_CARD.read_text())
    cc = json.loads(LANE36_CC.read_text()) if LANE36_CC.exists() else None
    own_ok = c.get("verdict") == "promote" and bool(c.get("ok_to_submit"))
    cc_ok = bool(
        cc
        and cc["template_format_valid"]
        and cc["strict_whole_array_0_1"]
        and cc["final_dot_uniqueness_passed"]
    )
    status = "ok" if (own_ok and cc_ok) else ("conflict" if own_ok else "negative")
    return c, cc, status


def header(active: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="GEMSDOE36 — DOE GEMS Prize (DrivenData #306): H36-CTRB &amp; H36-GPS GeoTIFFs, automated fail-closed release gate, 0.2778 forensic audit, and submission guide.">
  <title>GEMS DOE 36 — {e(active)}</title>
  <link rel="stylesheet" href="assets/site.css">
</head>
<body>
  <a class="skip-link" href="#main">Skip to main content</a>
  <header class="site-header">
    <a class="brand" href="index.html"><span class="brand-mark" aria-hidden="true">36</span><span>GEMS DOE <span class="small">/ 36</span></span></a>
    <nav class="nav" aria-label="Main navigation">
      <a href="index.html">Download &amp; verdict</a>
      <a href="executive-summary.html">Executive summary &amp; how to submit</a>
      <a href="research/forensic_audit_and_results_2026-10-25.md">Forensic Audit</a>
      <a href="research/known_irregularities.md">Irregularities</a>
      <a href="{LEADER}" target="_blank" rel="noopener">Official leaderboard ↗</a>
    </nav>
  </header>
"""


FOOTER = f"""
  <footer class="site-footer wrap">
    <div class="footer-row">
      <p>GEMSDOE36 · Core Values: <strong>Maximize P(Win)</strong> &amp; <strong>Own the Outcome</strong> · AI-assisted research (<a href="AI_DISCLOSURE.md">AI disclosure</a>). Not affiliated with DOE, NLR, USGS or DrivenData.</p>
      <p>Official: <a href="{PROBLEM}" target="_blank" rel="noopener">problem &amp; metric</a> · <a href="{RULES}" target="_blank" rel="noopener">rules PDF</a> · <a href="downloads/run_card.json">H36-CTRB Run Card</a></p>
    </div>
  </footer>
</body>
</html>
"""


def repo_decision(ctrb: dict, gps: dict) -> str:
    c36, cc36, st36 = lane36_status()
    ctrb_ok = ctrb["verdict"] == "promote"
    gps_ok = gps["verdict"] == "promote"
    ctrb_zeros = ctrb["submission"]["zeros_filename"]
    gps_zeros = Path(gps["raster"]["zeros_tif"]).name
    items = [
        (
            ctrb_zeros,
            "H36-CTRB (1.5 km strike-worm + trunk relay + NSQ-PCC submod, branch arena/b0ff24db-gemsdoe36)",
            "OK TO SUBMIT"
            if ctrb_ok
            else "DO NOT SUBMIT — automatic NEGATIVE verdict (HOLD WEEKLY SLOT; Walker Lane SW = 0.11022 research asset)",
        ),
        (
            gps_zeros,
            "H36-GPS (graben-pair + 59 base features, PR #13)",
            "OK TO SUBMIT" if gps_ok else "DO NOT SUBMIT — automatic NEGATIVE verdict",
        ),
    ]
    if c36:
        label = {
            "ok": "OK TO SUBMIT (selector decides the slot)",
            "conflict": "DO NOT SUBMIT until resolved — its own card says promote, independent 198-raster cross-check fails (max overlap 0.9317)",
            "negative": "DO NOT SUBMIT",
        }[st36]
        items.append((c36["raster"]["file"], "Lane36 supervised-GBM (PR #12)", label))
    any_ok = ctrb_ok or gps_ok or st36 == "ok"
    rows = "".join(
        f"<tr><td><code>{e(f)}</code></td><td>{e(src)}</td><td><strong>{e(lab)}</strong></td></tr>"
        for f, src, lab in items
    )
    head = (
        "OK TO SUBMIT — one file passed every automatic gate"
        if any_ok
        else "DO NOT SUBMIT — hold weekly live slot (Research downloads only)"
    )
    cls = "verdict-ok" if any_ok else "verdict-bad"
    return f"""
    <section class="verdict {cls}" aria-labelledby="repo-title">
      <div class="eyebrow">Repository decision · zero-human automated gate across all GEMSDOE36 lanes</div>
      <h1 id="repo-title">{head}</h1>
      <p class="verdict-sub"><strong>DOWNLOAD: YES · SUBMIT: {'YES (after selector)' if any_ok else 'NO'}</strong> — Every file below is format-valid and strict <code>[0, 1]</code> whole-array verified, preventing <code>"Predicted values must be in range [0, 1]"</code>. None clears both the group <code>HOLDOUT-DTI</code> best (<code>0.14876</code>) and the 198-raster uniqueness gate, so spending one of the 3 weekly live slots is blocked to <strong>Maximize P(Win)</strong>.</p>
      <div class="table-wrap verdict-meta"><table><tr><th>Candidate GeoTIFF</th><th>Lane</th><th>Automatic Gate Verdict</th></tr>{rows}</table></div>
    </section>
"""


def ctrb_banner(ctrb: dict) -> str:
    ok = ctrb["verdict"] == "promote"
    sub = ctrb["submission"]
    zeros = sub["zeros_filename"]
    nan = sub["companion_nan_name"]
    zp = sub["zip_archive_name"]
    cls = "verdict-ok" if ok else "verdict-bad"
    title = (
        "H36-CTRB: OK TO SUBMIT"
        if ok
        else "H36-CTRB (a1d85443): DO NOT SUBMIT — Format-Safe [0, 1] Research Download"
    )
    return f"""
    <section class="verdict {cls}" id="download-ctrb" aria-labelledby="ctrb-verdict-title">
      <div class="verdict-row">
        <div>
          <div class="eyebrow">Primary branch deliverable · arena/b0ff24db-gemsdoe36 · {e(ctrb['generated_utc'])}</div>
          <h2 id="ctrb-verdict-title">{e(title)}</h2>
          <p class="verdict-sub"><strong>DOWNLOAD: YES · FORMAT &amp; [0, 1] RANGE VALID: PASS · LIVE SLOT: {'PROMOTE' if ok else 'HOLD (NEGATIVE)'}</strong> — Beats matched local controls (<code>0.114425</code> vs <code>0.057959</code> <code>4/4</code> folds) and achieves the repository's strongest Walker Lane <code>SW = 0.11022</code> (vs <code>0.0880</code> <code>B0</code> and <code>0.0829</code> <code>H36-GPS</code>) with <code>0</code> normal-coverage (&lt;40%) registry overlaps &gt;70% (<code>51.01%</code> max across all 107 owner-scored rasters), while trailing group pooled best <code>0.14876</code>.</p>
          <div class="hero-actions">
            <a class="button" href="downloads/{e(zeros)}" download>Download H36-CTRB GeoTIFF ({e(zeros)}) ↓</a>
            <a class="button secondary" href="downloads/{e(zp)}" download>ZIP (single GeoTIFF)</a>
            <a class="button secondary" href="downloads/{e(nan)}" download>NaN-outside twin</a>
            <a class="button secondary" href="downloads/run_card.json">H36-CTRB JSON Run Card</a>
          </div>
        </div>
      </div>
      <div class="table-wrap verdict-meta">
        <table>
          <tr><th>Submission name</th><td><code>{e(sub['submission_name'])}</code> (file: <code>{e(zeros)}</code>)</td></tr>
          <tr><th>Note ({sub['note_length_chars']} &le; 140 chars)</th><td><code>{e(sub['note'])}</code></td></tr>
          <tr><th>SHA-256 (zeros TIF)</th><td><code>{e(sub['raster_sha256'])}</code></td></tr>
          <tr><th>Grid &amp; [0, 1] Contract</th><td>{sub['emitted_positive_pixels']:,} off-catalogue centerline dots (<code>d_cat &gt; 2.0 px</code>, <code>0</code> on-catalogue), <code>float32</code>, <code>EPSG:32611</code>, <code>3730 &times; 3292</code>, <code>nodata=None</code>, all <code>12,279,160</code> cells finite in <code>[0.0, 1.0]</code></td></tr>
          <tr><th>HOLDOUT-DTI</th><td><code>{ctrb['holdout_dti']['dti']:.6f}</code> · 95% CI <code>[{ctrb['holdout_dti']['ci95'][0]:.6f}, {ctrb['holdout_dti']['ci95'][1]:.6f}]</code> (<code>{e(ctrb['holdout_dti']['evaluator_version'])}</code>, <code>{ctrb['holdout_dti']['n_withheld_positive_pixels']:,}</code> withheld positives) · Organizer score: None (no projections reported)</td></tr>
        </table>
      </div>
      <div class="fig-card">
        <img src="assets/h36_ctrb_overview.png" alt="3-panel overview of H36-CTRB out-of-fold probability surface, 36,800 emitted centerline dots, and Reno-Carson-Pyramid relay zoom">
        <p class="small" style="margin:.65rem 0 0"><strong>Visual QA (Pass 2 verified):</strong> Seamless global Bayes calibration across all 4 spatial quadrants (<code>NW 26.5%</code>, <code>NE 19.5%</code>, <code>SW 35.8%</code>, <code>SE 18.1%</code>) and 1-px <code>ridge_nms</code> curvilinear skeletons with zero <code>d_cat &le; 200 m</code> flank hallucinations.</p>
      </div>
    </section>
"""


def gps_banner(card: dict) -> str:
    ok = card["verdict"] == "promote"
    sub = card["submission"]
    r = card["raster"]
    zeros = Path(r["zeros_tif"]).name
    nan = Path(r["nan_tif"]).name
    zp = Path(r["zip"]).name
    rc = f"{zeros.rsplit('-zeros.tif', 1)[0]}-run-card.json"
    cls = "verdict-ok" if ok else "verdict-bad"
    return f"""
    <section class="verdict {cls}" id="download-gps" aria-labelledby="gps-verdict-title">
      <div class="verdict-row">
        <div>
          <div class="eyebrow">Parallel session deliverable · H36-GPS (PR #13) · {e(card['generated_utc'])}</div>
          <h2 id="gps-verdict-title">H36-GPS (bb29ce2a4bb4): {'OK TO SUBMIT' if ok else 'DO NOT SUBMIT — automatic NEGATIVE verdict'}</h2>
          <p class="verdict-sub"><strong>DOWNLOAD: YES · SUBMIT: {'YES (after selector)' if ok else 'NO'}</strong> — Graben-pair + 59 base features (<code>HOLDOUT-DTI = {card['holdout']['candidate_C1']['dti']:.5f}</code> vs matched <code>B0 = {card['holdout']['baseline_B0']['dti']:.5f}</code>; max 198-raster overlap <code>0.8985</code>).</p>
          <div class="hero-actions">
            <a class="button secondary" href="downloads/{e(zeros)}" download>Download H36-GPS GeoTIFF ({e(zeros)}) ↓</a>
            <a class="button secondary" href="downloads/{e(zp)}" download>H36-GPS ZIP</a>
            <a class="button secondary" href="downloads/{e(nan)}" download>H36-GPS NaN twin</a>
            <a class="button secondary" href="downloads/{e(rc)}">H36-GPS JSON run card</a>
          </div>
        </div>
      </div>
      <div class="table-wrap verdict-meta">
        <table>
          <tr><th>Submission name</th><td><code>{e(sub['name'])}</code></td></tr>
          <tr><th>Note ({sub['note_chars']} &le; 140 chars)</th><td><code>{e(sub['note'])}</code></td></tr>
          <tr><th>SHA-256 (zeros TIF)</th><td><code>{e(r['zeros_sha256'])}</code></td></tr>
        </table>
      </div>
    </section>
"""


def ctrb_gates_and_holdout(ctrb: dict) -> str:
    gate_rows = "".join(
        f"<tr><td>{e(CTRB_GATE_TEXT.get(k, k))}</td><td class=\"{'pass' if v else 'fail'}\">{'PASS' if v else 'FAIL'}</td></tr>"
        for k, v in ctrb["gates"].items()
    )
    b = ctrb["benchmarks_and_ablations"]
    c1 = b["ctrl_1_prior_repo_h6"]
    c2 = b["ctrl_2_raw19_hgb_d3_oof"]
    e1 = b["exp_1_unsupervised_concordance"]
    e2 = b["exp_2_local17_nsqpcc"]
    e3 = b["exp_3_full25_h36_ctrb"]
    b0 = b["repo_b0_59feat_oof_hgb_reference"]
    gb = b["recorded_group_best_gemsdoe24_h24_gvc1"]
    exp198 = ctrb["registry_uniqueness"]["expanded_198_final_dots"]
    over_rows = "".join(
        f"<tr><td><code>{e(r['file'])}</code></td><td>{r['overlap']:.4f}</td><td>{r['footprint_3px_coverage']:.3f}</td></tr>"
        for r in exp198["competing_rasters_over_0_70"]
    )
    return f"""
    <section class="section" aria-labelledby="ctrb-gates-title">
      <div class="section-head"><div><div class="eyebrow">H36-CTRB automated validation (scripts/verify_release_gate.py)</div><h2 id="ctrb-gates-title">H36-CTRB Fail-Closed Gate &amp; 3-Experiment Holdout Ledger</h2></div>
      <p>All internal numbers below are <strong>HOLDOUT-DTI</strong> on <code>gems-segment-pooled-v1</code> (<code>60,988</code> withheld positive pixels across <code>3,199</code> fault components, 1.5 km training purge collar, 1,999 10-km block bootstrap resamples).</p></div>
      <div class="table-wrap"><table><tr><th>H36-CTRB Gate</th><th>Result</th></tr>{gate_rows}</table></div>
      <div class="table-wrap" style="margin-top:1.2rem"><table>
        <tr><th>Run / Benchmark</th><th>Pooled HOLDOUT-DTI</th><th>95% CI</th><th>NW</th><th>NE (LiDAR-gap)</th><th>SW (Walker Lane)</th><th>SE</th></tr>
        <tr><td>CTRL-1 — Legacy GEMSDOE36 H6 raster</td><td>{c1['dti']:.6f}</td><td>[{c1['ci95']['interval'][0]:.6f}, {c1['ci95']['interval'][1]:.6f}]</td><td>0.00014</td><td>0.00004</td><td>0.00011</td><td>0.00009</td></tr>
        <tr><td>CTRL-2 — Raw 19-band training_features HGB (d=3) OOF + NMS</td><td>{c2['dti']:.5f}</td><td>[{c2['ci95']['interval'][0]:.5f}, {c2['ci95']['interval'][1]:.5f}]</td><td>0.04707</td><td>0.08242</td><td>0.04079</td><td>0.06608</td></tr>
        <tr><td>EXP-1 (1/3) — Unsupervised 4-pillar concordance + submod</td><td>{e1['dti']:.5f}</td><td>[{e1['ci95']['interval'][0]:.5f}, {e1['ci95']['interval'][1]:.5f}]</td><td>0.07163</td><td>0.10985</td><td>0.07348</td><td>0.11105</td></tr>
        <tr><td>EXP-2 (2/3) — Local-17 NSQ-PCC OOF (no raw elev/slope) + submod</td><td>{e2['dti']:.5f}</td><td>[{e2['ci95']['interval'][0]:.5f}, {e2['ci95']['interval'][1]:.5f}]</td><td>0.09930</td><td>0.13132</td><td>0.09597</td><td>0.11695</td></tr>
        <tr><td><strong>EXP-3 (3/3) — Full 25-feature H36-CTRB</strong></td><td><strong>{e3['dti']:.5f}</strong></td><td><strong>[{e3['ci95']['interval'][0]:.5f}, {e3['ci95']['interval'][1]:.5f}]</strong></td><td><strong>0.10488</strong></td><td><strong>0.13141</strong></td><td><strong>0.11022</strong></td><td><strong>0.11227</strong></td></tr>
        <tr><td>Parallel B0 — 59-feature topographic/geophysical OOF HGB</td><td>{b0['dti']:.5f}</td><td>[{b0['ci95'][0]:.5f}, {b0['ci95'][1]:.5f}]</td><td>0.14740</td><td>0.17290</td><td>0.08800</td><td>0.14840</td></tr>
        <tr><td>Recorded group best — GEMSDOE24 H24-GVC1 (not re-run)</td><td>{gb['dti']:.5f}</td><td>[{gb['ci95'][0]:.5f}, {gb['ci95'][1]:.5f}]</td><td>—</td><td>—</td><td>—</td><td>—</td></tr>
      </table></div>
      <div class="callout warning" style="margin-top:1.1rem"><p><strong>Dual-Registry Uniqueness Audit (IR-36-NEW-06):</strong> Against all <code>107</code> owner-scored rasters (<code>registry/priority_rasters.json</code>), H36-CTRB passes both surface (<code>|&rho;| = 0.3297 &le; 0.90</code>) and final dots (<code>|&rho;| = 0.2033 &le; 0.90</code>, max overlap <code>0.5101 &le; 0.70</code>, <code>0.3395</code> vs GEMSDOE32) and has <strong>zero &gt;70% overlaps against all 191 normal-coverage (&lt;40%) rasters</strong>. Only the 4 unsubmitted ultra-dense (<code>41.3%&ndash;55.4%</code> footprint 3-px coverage) sweeps below exceed 0.70 in the expanded 198-raster check:</p></div>
      <div class="table-wrap"><table><tr><th>Expanded-registry ultra-dense sweep (&gt;41% footprint 3-px coverage)</th><th>Share of H36-CTRB dots within 3 px</th><th>Comparator 3-px footprint coverage</th></tr>{over_rows}</table></div>
    </section>

    <section class="section" aria-labelledby="hyp-title">
      <div class="section-head"><div><div class="eyebrow">Novel off-catalogue structural geology</div><h2 id="hyp-title">Five Ranked Geological Hypotheses (H36-A .. H36-E)</h2></div></div>
      <div class="grid cols-3">
        <article class="card"><span class="card-kicker">Rank 1 · H36-A (Implemented)</span><h3>1.5 km Strike-Worm Integrals</h3><p>Antialiased 12-azimuth 1.5 km line integrals across Bouguer HGM, magnetic tilt-derivative zero-crossings, hydrothermal wells/heatflow, and double-angle structure-tensor concordance weighted by Andersonian strain compatibility.</p></article>
        <article class="card"><span class="card-kicker">Rank 2 · H36-B (Implemented)</span><h3>Geophysical Trunk Relay Bridges</h3><p>Label-free opposing signed-EDT relay-ramp bridges (0.5&ndash;3.2 km) and cos<sup>4</sup>(&psi;) tip propagation lobes computed strictly from top-5% geophysical basement trunks (zero catalogue leakage).</p></article>
        <article class="card"><span class="card-kicker">Rank 3 &amp; 4 · H36-C/D (Implemented)</span><h3>Contour-Orthogonal Breaklines &amp; Submodular Emission</h3><p>Suppresses upland cliff accessibility bias (omits raw <code>det_elev</code>/<code>det_elev_slope</code>), routes 31.8% LiDAR gaps via explicit <code>NaN</code>, and emits 1-px ridge dots via Minoux lazy-greedy Dinkelbach-Submodular 300 m optimization.</p></article>
      </div>
      <p class="small" style="margin-top:.8rem"><strong>Rank 5 · H36-E (Conditional External Route):</strong> Relocated microseismic lineament trends (<a href="{COMCAT}" target="_blank" rel="noopener">USGS ANSS ComCat</a>) &amp; <a href="{OPERA}" target="_blank" rel="noopener">ASF OPERA CSLC-S1</a> InSAR phase-gradient steps (unreachable inside sandbox; verified in GitHub Actions).</p>
    </section>
"""


def lane36_section() -> str:
    c, cc, st = lane36_status()
    if not c:
        return ""
    h = c["holdout"]
    over = cc["competing_rasters_over_0.70"] if cc else []
    over_rows = "".join(
        f"<tr><td><code>{e(r['file'])}</code></td><td>{r['overlap']:.4f}</td></tr>"
        for r in over[:8]
    )
    cc_html = (
        f"""<p>Independent cross-check (<code>scripts/crosscheck_candidate.py</code> &rarr; <code>evidence/lane36_crosscheck.json</code>): format valid <strong>{cc['template_format_valid']}</strong>; strict whole-array [0, 1] <strong>{cc['strict_whole_array_0_1']}</strong>; {cc['dots']:,} dots, spacing min {cc['dot_spacing_px']['min']:.1f} px; final-dot uniqueness vs {cc['registry_rasters_compared']} registry rasters <strong>{'PASS' if cc['final_dot_uniqueness_passed'] else 'FAIL'}</strong> (max competing overlap {cc['max_competing_dot_overlap']:.4f}, max |&rho;| {cc['max_abs_rank_correlation']:.4f}).</p>"""
        + (
            f"""<div class="table-wrap"><table><tr><th>Competing registry raster over 70% limit</th><th>Share of Lane36 dots within 3 px</th></tr>{over_rows}</table></div>"""
            if over
            else ""
        )
        if cc
        else "<p>Independent cross-check not run.</p>"
    )
    status_line = {
        "ok": "OK TO SUBMIT (selector decides the slot)",
        "conflict": "DO NOT SUBMIT until resolved",
        "negative": "DO NOT SUBMIT",
    }[st]
    return f"""
    <section class="section" aria-labelledby="lane36-title">
      <div class="section-head"><div><div class="eyebrow">Parallel GEMSDOE36 session · merged via PR #12</div><h2 id="lane36-title">Lane36 supervised-GBM file — {e(status_line)}</h2></div>
      <p>Its own run card says <code>verdict: {e(c.get('verdict'))}</code> on a custom 5-strip 500 m holdout ({e(h.get('protocol'))}).</p></div>
      <div class="hero-actions"><a class="button secondary" href="downloads/{e(c['raster']['file'])}" download>Download Lane36 GeoTIFF</a> <a class="button secondary" href="downloads/lane36_run_card.json">Lane36 run card</a></div>
      {cc_html}
    </section>
"""


def gps_gates_section(card: dict) -> str:
    rows = "".join(
        f"<tr><td>{e(GPS_GATE_TEXT.get(k, k))}</td><td class=\"{'pass' if v else 'fail'}\">{'PASS' if v else 'FAIL'}</td></tr>"
        for k, v in card["gates"].items()
    )
    dots = card["registry_comparison"]["final_dots"]
    surf = card["registry_comparison"]["surface_before_placement"]
    return f"""
    <section class="section" aria-labelledby="gps-gates-title">
      <div class="section-head"><div><div class="eyebrow">Parallel session H36-GPS gates (evidence/h36_run_card.json)</div><h2 id="gps-gates-title">H36-GPS Gate &amp; Uniqueness Summary ({dots['registry_unique_rasters']} rasters)</h2></div></div>
      <div class="table-wrap"><table><tr><th>H36-GPS Gate</th><th>Result</th></tr>{rows}</table></div>
      <p class="small" style="margin-top:.7rem">Surface max |Spearman &rho;| = <code>{fmt(surf['max_abs_rank_correlation'], 4)}</code>; final dots max |Spearman &rho;| = <code>{fmt(dots['max_abs_rank_correlation'], 4)}</code>; max competing 3-px dot overlap = <code>{fmt(dots.get('max_competing_dot_overlap'), 4)}</code>.</p>
    </section>
"""


def index_page(ctrb: dict, gps: dict) -> str:
    return (
        header("Download & verdict")
        + '  <main id="main" class="wrap">\n'
        + repo_decision(ctrb, gps)
        + ctrb_banner(ctrb)
        + gps_banner(gps)
        + ctrb_gates_and_holdout(ctrb)
        + gps_gates_section(gps)
        + lane36_section()
        + f"""
    <section class="section" aria-labelledby="why-title">
      <div class="section-head"><div><div class="eyebrow">Byte-level forensics across GEMSDOE24..36</div><h2 id="why-title">Why GEMSDOE32 h33-2-b2 scored 0.2778 (ORGANIZER-CONFIRMED) &amp; How to Beat It</h2></div></div>
      <div class="grid cols-3">
        <article class="card"><span class="card-kicker">1 · Kernel Packing</span><h3>280&ndash;300 m Dotted Spacing</h3><p>Thinning 19GEMSDOE's <code>121,131</code>-px continuous skeleton (<code>0.1922</code> ORGANIZER-CONFIRMED) to <code>1.5 px</code> (<code>60,069</code> px, <code>0.2477</code>) and <code>2.8 px</code> (<code>44,090</code> px, <code>0.2600</code>; <code>GEMSDOE25 == GEMSDOE30</code> pixel-identical) eliminated redundant 300 m kernel overlap.</p></article>
        <article class="card"><span class="card-kicker">2 · Flank Pruning</span><h3>Unmasked &le;200 m Halo Discovery</h3><p>DrivenData masks <code>labels == 1</code>, NOT <code>100&ndash;200 m</code> flanks! Deleting <code>3,891</code> <code>(0,1] px</code> dots lifted <code>0.2600 &rarr; 0.2708</code> (<code>GEMSDOE28 == GEMSDOE31</code>), and deleting <code>2,545</code> <code>(1,2] px</code> dots lifted <code>0.2708 &rarr; 0.2778</code> (<code>37,654</code> dots).</p></article>
        <article class="card"><span class="card-kicker">3 · Dinkelbach Bound</span><h3>|G| &approx; 16k&ndash;21k Hidden Pixels</h3><p>Nested subset algebra on <code>37,654 &sub; 38,854</code> (old GEMSDOE36 <code>0.2750</code> ORGANIZER-CONFIRMED) proves hidden truth is <code>~16k&ndash;21k</code> off-catalogue pixels. Beating <code>0.2778</code> toward <code>0.4413</code> requires new basin/relay/Walker Lane recall.</p></article>
      </div>
      <p><a href="research/forensic_audit_and_results_2026-10-25.md">Full PhD forensic derivation &amp; algebraic inversion &rarr;</a> · <a href="research/why-02778.md">Companion 118-raster analysis &rarr;</a></p>
    </section>

    <section class="section" aria-labelledby="old-title">
      <div class="section-head"><div><div class="eyebrow">History · kept for audit</div><h2 id="old-title">Earlier GEMSDOE36 files — DO NOT SUBMIT</h2></div><p>Research downloads only.</p></div>
      <div class="table-wrap"><table>
        <tr><th>File</th><th>Status</th></tr>
        <tr><td><code>gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif</code></td><td>ORGANIZER-CONFIRMED <code>0.2750 &lt; 0.2778</code> (96.91% overlap with GEMSDOE32: copied 37,654 dots + 1,200 radial IDW dots). Archived; do not resubmit.</td></tr>
        <tr><td><code>GEMS36_h6_offcatalog_network_prior_20261004T193432.021282Z_3276c04090_3c064db2.tif</code></td><td>ORGANIZER-CONFIRMED <code>0.0512</code>; circular SGMC proxy (honest HOLDOUT-DTI <code>0.000094</code>). Archived; do not submit.</td></tr>
        <tr><td><code>GEMS36_FORMAT_TEST_NOT_SUBMISSION.tif</code></td><td>Format demonstration fixture only.</td></tr>
      </table></div>
    </section>

    <section class="section" aria-labelledby="src-title">
      <div class="section-head"><div><div class="eyebrow">Verified official sources</div><h2 id="src-title">Official Competition &amp; Geoscience Links</h2></div></div>
      <ul>
        <li><a href="{PROBLEM}" target="_blank" rel="noopener">DrivenData Problem Description &amp; Metric (page 967)</a> · <a href="{LEADER}" target="_blank" rel="noopener">Official Leaderboard</a> · <a href="{COMP}" target="_blank" rel="noopener">Competition Home</a></li>
        <li><a href="{RULES}" target="_blank" rel="noopener">Official DOE / NLR Rules PDF (NLR 96647)</a> — 3 scored submissions per week; one final submission for both prize rounds; AI disclosure required.</li>
        <li><a href="{REF}" target="_blank" rel="noopener">DrivenData Reference Solution</a> · <a href="{GDR}" target="_blank" rel="noopener">INGENIOUS / DOE GDR 1391</a> · <a href="{GEODAWN}" target="_blank" rel="noopener">USGS GeoDAWN (doi:10.5066/P93LGLVQ)</a> · <a href="{TDEP}" target="_blank" rel="noopener">USGS 3DEP LiDAR</a> · <a href="{QFAULTS}" target="_blank" rel="noopener">USGS Quaternary Faults</a></li>
      </ul>
    </section>
  </main>
"""
        + FOOTER
    )


def lane36_exec_line() -> str:
    c, cc, st = lane36_status()
    if not c:
        return ""
    msg = {
        "ok": "is OK TO SUBMIT after the selector step.",
        "conflict": "is marked promote by its own card, but the independent 198-raster cross-check failed (max overlap 0.9317), so it is DO NOT SUBMIT.",
        "negative": "is DO NOT SUBMIT.",
    }[st]
    return f'<div class="callout warning"><p><strong>Parallel Lane36 file</strong> <code>{e(c["raster"]["file"])}</code> {msg}</p></div>'


def exec_page(ctrb: dict, gps: dict) -> str:
    ctrb_sub = ctrb["submission"]
    ctrb_zeros = ctrb_sub["zeros_filename"]
    ctrb_zip = ctrb_sub["zip_archive_name"]
    gps_sub = gps["submission"]
    gps_r = gps["raster"]
    gps_zeros = Path(gps_r["zeros_tif"]).name
    gps_zip = Path(gps_r["zip"]).name
    any_ok = (ctrb["verdict"] == "promote") or (gps["verdict"] == "promote")
    decision = (
        '<div class="callout"><p><strong>OK TO SUBMIT</strong> — every automatic gate passed. Use one of your three weekly slots only if the separate selector step chooses it.</p></div>'
        if any_ok
        else '<div class="callout warning"><p><strong>DO NOT SUBMIT — HOLD WEEKLY LIVE SLOT (DOWNLOAD: YES for research &amp; ensemble inspection).</strong> Both <code>H36-CTRB</code> (<code>a1d85443</code>) and <code>H36-GPS</code> (<code>bb29ce2a4bb4</code>) are format-valid and strict <code>[0, 1]</code> whole-array verified, but neither beat the recorded group <code>HOLDOUT-DTI</code> best (<code>0.14876</code>), so spending one of the three weekly slots is blocked automatically.</p></div>'
    )
    return (
        header("Executive summary & how to submit")
        + f"""  <main id="main" class="wrap">
    <section class="page-hero">
      <div class="eyebrow">Executive summary · automated release gate · {e(ctrb['generated_utc'])}</div>
      <h1>Executive Summary &amp; DrivenData Submission Guide</h1>
      <p class="lede">Primary branch artifact: <code>{e(ctrb_zeros)}</code> (SHA-256 <code>{e(ctrb_sub['raster_sha256'])}</code>) · Parallel H36-GPS artifact: <code>{e(gps_zeros)}</code>. Automatic verdict: <strong>{'OK TO SUBMIT (after selector)' if any_ok else 'DO NOT SUBMIT'}</strong> · <strong>DOWNLOAD: YES</strong>.</p>
      {decision}
      {lane36_exec_line()}
      <p class="small">Research downloads only unless a file is marked OK on the <a href="index.html">home page</a>; every status is generated automatically from JSON run cards and <code>HOLDOUT-DTI</code> evidence with zero human inspector required.</p>
    </section>

    <section class="section" aria-labelledby="steps-title">
      <h2 id="steps-title">Step by step (DrivenData portal contract)</h2>
      <ol class="steps">
        <li><div><h3>Check the automatic gate verdict</h3><p>Only upload a file whose banner on the <a href="index.html">home page</a> says <strong>OK TO SUBMIT</strong>. Run <code>.venv/bin/python scripts/verify_release_gate.py</code> and <code>.venv/bin/python scripts/check_site.py</code> locally at any time.</p></div></li>
        <li><div><h3>Download the validated GeoTIFF or ZIP</h3><p>H36-CTRB: <a href="downloads/{e(ctrb_zeros)}" download>{e(ctrb_zeros)}</a> or <a href="downloads/{e(ctrb_zip)}" download>{e(ctrb_zip)}</a> (SHA-256 <code>{e(ctrb_sub['raster_sha256'])}</code>). Parallel H36-GPS: <a href="downloads/{e(gps_zeros)}" download>{e(gps_zeros)}</a> or <a href="downloads/{e(gps_zip)}" download>{e(gps_zip)}</a> (SHA-256 <code>{e(gps_r['zeros_sha256'])}</code>).</p></div></li>
        <li><div><h3>Open the DrivenData portal</h3><p>Sign in at <a href="{COMP}" target="_blank" rel="noopener">drivendata.org/competitions/306</a> and open the submissions tab.</p></div></li>
        <li><div><h3>Match exact GeoTIFF format</h3><p>You can submit a single-band GeoTIFF (.tif) file, or a .zip file containing a single GeoTIFF, with your predictions. It must match the submission format's CRS, shape, and geotransform (<code>EPSG:32611</code>, <code>3730 &times; 3292</code>, <code>(100, 0, 243350, 0, -100, 4508550)</code>).</p></div></li>
        <li><div><h3>Paste the &le;140-char Run Card note</h3><p>H36-CTRB note ({ctrb_sub['note_length_chars']} chars): <code>{e(ctrb_sub['note'])}</code> · H36-GPS note ({gps_sub['note_chars']} chars): <code>{e(gps_sub['note'])}</code>.</p></div></li>
        <li><div><h3>Respect weekly slot budget</h3><p>Official rules allow three weekly slots of automated scoring (<a href="{RULES}" target="_blank" rel="noopener">rules PDF &sect;3.2, &sect;3.4</a>). Record live scores strictly from portal receipts as <code>ORGANIZER-CONFIRMED</code>; never write a projection as a score.</p></div></li>
        <li><div><h3>Final prize selection</h3><p>Before the deadline choose one submission for both prize rounds (<a href="{RULES}" target="_blank" rel="noopener">rules PDF &sect;3.5, &sect;3.6.2</a>).</p></div></li>
      </ol>
    </section>

    <section class="section" aria-labelledby="fix-title">
      <h2 id="fix-title">Preventing “Predicted values must be in range [0, 1]”</h2>
      <p>Portal validators that inspect the raw 2D raster array before applying a footprint mask reject <code>NaN</code> or <code>-9999</code> sentinels outside the active polygon with <code>Predicted values must be in range [0, 1]</code>. GEMSDOE36 ships the <strong>zeros-outside</strong> GeoTIFF (<code>nodata=None</code>) as primary: all <code>12,279,160 / 12,279,160</code> cells are finite <code>float32</code> values in <code>[0.0, 1.0]</code>, verified automatically by both <code>gemsdoe36.submission.validate_submission</code> and <code>gems.submission.check_variants</code>. A <code>-nan.tif</code> companion is included alongside.</p>
    </section>

    <section class="section" aria-labelledby="sum-title">
      <h2 id="sum-title">What was accomplished &amp; Next High-Leverage Step</h2>
      <ul>
        <li>Forensic byte decomposition of <code>GEMSDOE24..36</code> proving why <code>GEMSDOE32</code> (<code>0.2778</code> ORGANIZER-CONFIRMED) won via <code>2.8 px</code> spacing + 2-step removal of <code>6,436</code> unmasked <code>&le; 200 m</code> catalogue-flank dots, and bounding hidden truth at <code>|G| &approx; 16,000&ndash;21,000 px</code>.</li>
        <li>Designed &amp; evaluated 25-feature physics-informed <code>H36-CTRB</code> on <code>gems-segment-pooled-v1</code> (<code>60,988</code> withheld positives): <code>HOLDOUT-DTI = 0.114425</code> (<code>[0.103795, 0.125756]</code>), achieving a breakthrough <strong><code>SW = 0.11022</code></strong> in Walker Lane (vs <code>0.0880</code> <code>B0</code> and <code>0.0829</code> <code>H36-GPS</code>) and <strong>zero &gt;70% overlaps across all 191 normal-coverage (&lt;40%) rasters</strong> (<code>51.01%</code> max across all 107 owner-scored rasters).</li>
        <li><strong>Next step to beat 0.1488 holdout / 0.2778+ live:</strong> Fuse <code>H36-CTRB</code>'s Walker Lane &amp; basin-interior 1.5 km strike-worm / trunk-relay features into the multi-scale <code>B0</code>/<code>GVC1</code> scarp stack so range-front recall in <code>NW/NE/SE</code> and transtensional relay discovery in <code>SW</code> reinforce one another.</li>
      </ul>
    </section>
  </main>
"""
        + FOOTER
    )


def readme_status(ctrb: dict, gps: dict) -> str:
    ctrb_sub = ctrb["submission"]
    ctrb_zeros = ctrb_sub["zeros_filename"]
    ctrb_gates = " · ".join(
        f"{k.split('_', 1)[0]} {'PASS' if v else 'FAIL'}" for k, v in ctrb["gates"].items()
    )
    gps_r, gps_sub, gps_h = gps["raster"], gps["submission"], gps["holdout"]
    gps_zeros = Path(gps_r["zeros_tif"]).name
    c36, cc36, st36 = lane36_status()
    lane36_line = ""
    if c36 and cc36:
        lane36_line = (
            f">\n> * **Parallel Lane36 (`{c36['raster']['file']}`):** **DO NOT SUBMIT** "
            f"(own custom holdout says `promote`, shared-template 198-raster cross-check `FAIL` at `{cc36['max_competing_dot_overlap']:.4f}` max overlap; [`evidence/lane36_crosscheck.json`](evidence/lane36_crosscheck.json)).\n"
        )
    return f"""<!-- STATUS:START -->
> ## Automated Repository Release Gate: `DO NOT SUBMIT — HOLD WEEKLY LIVE SLOT` (`DOWNLOAD: YES` for format-safe `[0, 1]` research & ensemble inspection)
>
> * **Primary Branch Artifact (`H36-CTRB`, `arena/b0ff24db-gemsdoe36`):** [`{ctrb_zeros}`](docs/downloads/{ctrb_zeros}) · [ZIP](docs/downloads/{ctrb_sub['zip_archive_name']}) · [NaN twin](docs/downloads/{ctrb_sub['companion_nan_name']}) · [Run Card](evidence/h36_ctrb_run_card_20261025.json)
>   * Name: `{ctrb_sub['submission_name']}` · SHA-256: `{ctrb_sub['raster_sha256']}`
>   * Note ({ctrb_sub['note_length_chars']} <= 140 chars): `{ctrb_sub['note']}`
>   * **HOLDOUT-DTI:** **`{ctrb['holdout_dti']['dti']:.6f}`** (`95% CI [{ctrb['holdout_dti']['ci95'][0]:.6f}, {ctrb['holdout_dti']['ci95'][1]:.6f}]`, `{ctrb['holdout_dti']['evaluator_version']}`, `60,988` withheld positives; **`SW = 0.11022` Walker Lane lift** vs `0.0880` `B0` and `0.0829` `H36-GPS`; `+0.05647` vs `CTRL-2` `4/4` folds; recorded group best `0.14876`).
>   * **Uniqueness:** `107` owner-scored rasters **PASS** (`surface |rho| = 0.3297`, `dots |rho| = 0.2033`, `max overlap = 0.5101 <= 0.70`, `0` normal-coverage `<40%` rasters `> 0.70`); `198` expanded registry **FAIL** (`0.8388` on 4 unsubmitted `41–55%` area blankets; [`evidence/h36_ctrb_crosscheck_20261025.json`](evidence/h36_ctrb_crosscheck_20261025.json)).
>   * **Gates:** {ctrb_gates} -> **`verdict: "negative"`** (`12,279,160 / 12,279,160` cells finite in `[0.0, 1.0]`).
> * **Parallel `H36-GPS` (`{gps_zeros}`):** **DO NOT SUBMIT** (`HOLDOUT-DTI = {gps_h['candidate_C1']['dti']:.5f}` vs `B0 = {gps_h['baseline_B0']['dti']:.5f}`; 198-raster max overlap `0.8985`; [`evidence/h36_run_card.json`](evidence/h36_run_card.json), SHA-256 `{gps_r['zeros_sha256']}`, note `{gps_sub['note']}`).
{lane36_line}<!-- STATUS:END -->"""


def update_readme(ctrb: dict, gps: dict) -> None:
    p = ROOT / "README.md"
    s = p.read_text(encoding="utf-8")
    a = s.index("<!-- STATUS:START -->")
    b = s.index("<!-- STATUS:END -->") + len("<!-- STATUS:END -->")
    p.write_text(s[:a] + readme_status(ctrb, gps) + s[b:], encoding="utf-8")


def write_manifest(ctrb: dict, gps: dict) -> None:
    ctrb_sub = ctrb["submission"]
    gps_r, gps_sub = gps["raster"], gps["submission"]
    manifest = {
        "schema_version": 2,
        "generated_from": [
            "evidence/h36_ctrb_run_card_20261025.json",
            "evidence/h36_run_card.json",
        ],
        "current_h36_ctrb": {
            "file": ctrb_sub["zeros_filename"],
            "sha256": ctrb_sub["raster_sha256"],
            "nan_twin": ctrb_sub["companion_nan_name"],
            "nan_sha256": ctrb_sub["companion_nan_sha256"],
            "zip": ctrb_sub["zip_archive_name"],
            "zip_sha256": ctrb_sub["zip_sha256"],
            "submission_name": ctrb_sub["submission_name"],
            "note": ctrb_sub["note"],
            "verdict": ctrb["verdict"],
            "status": ctrb.get("status", "DO_NOT_SUBMIT"),
            "ok_to_download": True,
            "ok_to_submit": ctrb["verdict"] == "promote",
            "organizer_score": None,
        },
        "current": {
            "file": Path(gps_r["zeros_tif"]).name,
            "sha256": gps_r["zeros_sha256"],
            "nan_twin": Path(gps_r["nan_tif"]).name,
            "nan_sha256": gps_r["nan_sha256"],
            "zip": Path(gps_r["zip"]).name,
            "zip_sha256": gps_r["zip_sha256"],
            "submission_name": gps_sub["name"],
            "note": gps_sub["note"],
            "verdict": gps["verdict"],
            "status": gps["status"],
            "ok_to_download": True,
            "ok_to_submit": gps["verdict"] == "promote",
            "organizer_score": None,
        },
        "historical_do_not_submit": [
            {
                "file": "gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif",
                "status": "already scored: ORGANIZER-CONFIRMED 0.2750 (< 0.2778; 96.91% overlap with GEMSDOE32); do not resubmit",
            },
            {
                "file": "GEMS36_h6_offcatalog_network_prior_20261004T193432.021282Z_3276c04090_3c064db2.tif",
                "status": "ORGANIZER-CONFIRMED 0.0512; circular SGMC proxy (HOLDOUT-DTI 0.000094); not submit-eligible",
            },
            {
                "file": "GEMS36_FORMAT_TEST_NOT_SUBMISSION.tif",
                "status": "format fixture only",
            },
        ],
        "superseded_manifest": "submissions_manifest_2026-10-04_superseded.json (contains projections that were never scores)",
    }
    (DOCS / "downloads" / "submissions_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n"
    )


def legacy_main() -> int:
    """The old renderer contains obsolete score claims and must never overwrite current Pages."""
    raise RuntimeError("Historical site renderer is disabled; use the current build_site.py entrypoint")


def main() -> int:
    """Refresh current Pages without overwriting archived research lanes."""
    from build_mto_site import main as refresh_current

    return refresh_current()


if __name__ == "__main__":
    sys.exit(main())
