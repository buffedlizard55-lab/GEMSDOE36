#!/usr/bin/env python3
"""Generate docs/index.html and docs/executive-summary.html FROM the machine-written run card.

No human edits the verdict: the first-screen banner, download links, SHA-256, note and gate table
are rendered from ``evidence/h36_run_card.json`` (written by scripts/build_h36_submission.py).
"""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARD = ROOT / "evidence/h36_run_card.json"
DOCS = ROOT / "docs"

COMP = "https://www.drivendata.org/competitions/306/competition-doe-gems/"
PROBLEM = "https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/"
LEADER = "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/"
RULES = "https://docs.nlr.gov/docs/fy26osti/96647.pdf"
REF = "https://github.com/drivendataorg/gems-prize-reference-solution"
GDR = "https://gdr.openei.org/submissions/1391"
GEODAWN = "https://doi.org/10.5066/P93LGLVQ"
TDEP = "https://www.usgs.gov/3d-elevation-program"

GATE_TEXT = {
    "G1_beats_matched_baseline": "Holdout: beats the matched baseline (paired 95% CI > 0, ≥ 3/4 folds)",
    "G2_beats_current_holdout_best": "Holdout: beats the current holdout best (matched baseline and recorded group best 0.14876)",
    "G3_leakage_canary": "Leakage canary: no single feature with AUC > 0.90 (both polarities)",
    "G4a_unique_surface": "Uniqueness — surface before placement (|ρ| ≤ 0.90; overlap rule)",
    "G4b_unique_final_dots": "Uniqueness — final dots (≤ 70% within 3 px of any competing registry raster; |ρ| ≤ 0.90)",
    "G5_format_and_strict_range": "Format: exact CRS/shape/transform, single band float32, finite, strict [0, 1]",
}


def e(x) -> str:
    return html.escape(str(x))


def fmt(x, nd=5):
    return "n/a" if x is None else f"{x:.{nd}f}"


def ci(v):
    return "n/a" if not v else f"[{v[0]:.5f}, {v[1]:.5f}]"


def header(active: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="GEMSDOE36 — DOE GEMS Prize (DrivenData #306) research site: unique H36-GPS GeoTIFF, automatic submit/do-not-submit verdict, and exact submission guide.">
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
      <a href="research/why-02778.md">Why 0.2778</a>
      <a href="research/known_irregularities.md">Irregularities</a>
      <a href="{LEADER}" target="_blank" rel="noopener">Official leaderboard ↗</a>
    </nav>
  </header>
"""


FOOTER = f"""
  <footer class="site-footer wrap">
    <div class="footer-row">
      <p>GEMSDOE36 · AI-assisted research (see <a href="AI_DISCLOSURE.md">AI disclosure</a>). Not affiliated with DOE, NLR, USGS or DrivenData.</p>
      <p>Official: <a href="{PROBLEM}" target="_blank" rel="noopener">problem &amp; metric</a> · <a href="{RULES}" target="_blank" rel="noopener">rules PDF</a></p>
    </div>
  </footer>
</body>
</html>
"""


def banner(card: dict) -> str:
    ok = card["verdict"] == "promote"
    sub = card["submission"]
    r = card["raster"]
    zeros = Path(r["zeros_tif"]).name
    nan = Path(r["nan_tif"]).name
    zp = Path(r["zip"]).name
    rc = f"{zeros.rsplit('-zeros.tif', 1)[0]}-run-card.json"
    cls = "verdict-ok" if ok else "verdict-bad"
    title = "OK TO SUBMIT — passed every automatic gate" if ok else "DO NOT SUBMIT — automatic NEGATIVE verdict"
    sub_line = (
        "All gates passed. Spending a weekly slot is still a separate selector decision (3 per week)."
        if ok
        else "Download is fine for research and inspection. It did not pass every preregistered gate, so it must not be uploaded."
    )
    return f"""
    <section class="verdict {cls}" id="download" aria-labelledby="verdict-title">
      <div class="verdict-row">
        <div>
          <div class="eyebrow">Latest generated file · {e(card['generated_utc'])}</div>
          <h1 id="verdict-title">{title}</h1>
          <p class="verdict-sub"><strong>DOWNLOAD: YES · SUBMIT: {'YES (after selector)' if ok else 'NO'}</strong> — {e(sub_line)}</p>
          <div class="hero-actions">
            <a class="button" href="downloads/{e(zeros)}" download>Download GeoTIFF ({e(zeros)}) <span aria-hidden="true">↓</span></a>
            <a class="button secondary" href="downloads/{e(zp)}" download>ZIP (single GeoTIFF)</a>
            <a class="button secondary" href="downloads/{e(nan)}" download>NaN-outside twin</a>
            <a class="button secondary" href="downloads/{e(rc)}">JSON run card</a>
          </div>
        </div>
      </div>
      <div class="table-wrap verdict-meta">
        <table>
          <tr><th>Submission name</th><td><code>{e(sub['name'])}</code></td></tr>
          <tr><th>Note ({sub['note_chars']} ≤ 140 chars)</th><td><code>{e(sub['note'])}</code></td></tr>
          <tr><th>SHA-256 (zeros TIF)</th><td><code>{e(r['zeros_sha256'])}</code></td></tr>
          <tr><th>Content</th><td>{r['dots']:,} binary dots (values 0/1), float32, EPSG:32611, 3730 × 3292, 100 m, zeros outside the footprint (strict whole-array [0, 1] → fixes “Predicted values must be in range [0, 1]”)</td></tr>
          <tr><th>Organizer score</th><td>None. No ORGANIZER-CONFIRMED score exists; nothing here is a forecast.</td></tr>
        </table>
      </div>
    </section>
"""


def gate_table(card: dict) -> str:
    rows = "".join(
        f"<tr><td>{e(GATE_TEXT.get(k, k))}</td><td class=\"{'pass' if v else 'fail'}\">{'PASS' if v else 'FAIL'}</td></tr>"
        for k, v in card["gates"].items()
    )
    return f"""
    <section class="section" aria-labelledby="gates-title">
      <div class="section-head"><div><div class="eyebrow">Fail-closed automatic validation</div><h2 id="gates-title">Gate results</h2></div>
      <p>Every gate is computed by code from the shared template (holdout, writer, validator, registry novelty) — there is no human inspector step.</p></div>
      <div class="table-wrap"><table><tr><th>Gate</th><th>Result</th></tr>{rows}</table></div>
    </section>
"""


def holdout_section(card: dict) -> str:
    h = card["holdout"]
    c1, b0, p = h["candidate_C1"], h["baseline_B0"], h["paired_C1_minus_B0"]
    e2 = h.get("E2_physics_only")
    gb = h["recorded_group_best_not_rerun"]
    e2row = (
        f"<tr><td>E2 physics-only (label-free graben-pair + coherent scarp ranks)</td><td>{fmt(e2['dti'])}</td><td>{ci(e2['ci95'])}</td></tr>"
        if e2
        else ""
    )
    return f"""
    <section class="section" aria-labelledby="holdout-title">
      <div class="section-head"><div><div class="eyebrow">HOLDOUT-DTI · {e(h['evaluator_version'])} · {h['withheld_positive_pixels']:,} withheld positive pixels</div><h2 id="holdout-title">Hide-and-recover holdout</h2></div>
      <p>Whole 8-connected catalogue components hidden with a 1.5 km collar per quadrant; visible faults masked pixel-exactly; pooled TPw/FPw/FNw; α = 0.2, β = 0.8, 300 m kernel; 95% CI from a 10 km block bootstrap. Proxy truth = mapped faults, not the experts' new faults.</p></div>
      <div class="table-wrap"><table>
        <tr><th>Arm (37,654-dot budget, identical emission)</th><th>HOLDOUT-DTI</th><th>95% CI</th></tr>
        <tr><td><strong>C1 candidate</strong> — 59 base + 7 H36-GPS lane features</td><td><strong>{fmt(c1['dti'])}</strong></td><td>{ci(c1['ci95'])}</td></tr>
        <tr><td>B0 matched baseline — 59 base features</td><td>{fmt(b0['dti'])}</td><td>{ci(b0['ci95'])}</td></tr>
        <tr><td>Paired Δ (C1 − B0)</td><td>{fmt(p['paired_delta_dti'])}</td><td>{ci(p['paired_delta_ci95'])} · {p['fold_wins']}/{p['n_folds']} folds won</td></tr>
        {e2row}
        <tr><td>Recorded group best on the same evaluator (GEMSDOE24 H24-GVC1; not re-run here)</td><td>{fmt(gb['value'])}</td><td>{ci(gb['ci95'])}</td></tr>
      </table></div>
    </section>
"""


def duplicate_block(dots: dict) -> str:
    rows = [
        r for r in dots.get("top_overlap_rows", [])
        if r.get("comparator_class") == "competing_method" and (r.get("candidate_dot_overlap_within_3px") or 0) > 0.70
    ]
    if not rows:
        return '<p class="small">No competing-method raster exceeds the 70% final-dot overlap limit.</p>'
    body = "".join(
        f"<tr><td><code>{e(r['file'])}</code></td><td>{r['candidate_dot_overlap_within_3px']:.4f}</td><td>{(r.get('footprint_3px_coverage') or 0):.3f}</td></tr>"
        for r in rows
    )
    return f"""<div class="callout warning"><p><strong>Logged as a lane duplicate (final-dot stage) — stop.</strong> More than 70% of the final dots fall within 3 px of the dots of the registry rasters below, so by the parallel-run rule this file has drifted into another lane. The file itself is new (no copied pixels; max |ρ| {dots['max_abs_rank_correlation']:.4f}); many of these comparators are dense rasters whose 3-px halo covers 19–55% of the footprint.</p></div>
      <div class="table-wrap"><table><tr><th>Registry raster (top rows shown)</th><th>Share of our dots within 3 px</th><th>Its 3-px footprint coverage</th></tr>{body}</table></div>"""


def index_page(card: dict) -> str:
    rc = card["registry_comparison"]
    dots = rc["final_dots"]
    surf = rc["surface_before_placement"]
    return (
        header("Download & verdict")
        + '  <main id="main" class="wrap">\n'
        + banner(card)
        + gate_table(card)
        + holdout_section(card)
        + f"""
    <section class="section" aria-labelledby="unique-title">
      <div class="section-head"><div><div class="eyebrow">Parallel-run lane rule</div><h2 id="unique-title">Uniqueness against {dots['registry_unique_rasters']} registry rasters</h2></div>
      <p>Registry = every owner-scored GEMSDOE raster located on GitHub plus every current download of the priority sites (<code>registry/uniqueness_registry.json</code>). Checked with the template's <code>gems.novelty.compare_registry</code>.</p></div>
      <div class="table-wrap"><table>
        <tr><th>Check</th><th>Value</th><th>Limit</th></tr>
        <tr><td>Surface before placement — max |Spearman ρ|</td><td>{fmt(surf['max_abs_rank_correlation'], 4)}</td><td>0.90</td></tr>
        <tr><td>Final dots — max |Spearman ρ|</td><td>{fmt(dots['max_abs_rank_correlation'], 4)}</td><td>0.90</td></tr>
        <tr><td>Final dots — max share within 3 px of a competing-method raster</td><td>{fmt(dots.get('max_competing_dot_overlap'), 4)}</td><td>0.70</td></tr>
        <tr><td>Final dots — max share incl. space-filling calibration controls (reported, not gated)</td><td>{fmt(dots.get('max_dot_overlap'), 4)}</td><td>—</td></tr>
      </table></div>
      {duplicate_block(dots)}
    </section>

    <section class="section" aria-labelledby="why-title">
      <div class="section-head"><div><div class="eyebrow">Forensics on the published bytes</div><h2 id="why-title">Why GEMSDOE32 h33-2-b2 scored 0.2778</h2></div></div>
      <div class="grid cols-3">
        <article class="card"><span class="card-kicker">Field</span><h3>One strong field</h3><p>Its 37,654 dots are an exact subset of 19GEMSDOE's 121,131-pixel H19-5 ridges (multi-line corroborated LiDAR openness, thermal/geochemical, tip/step-over and potential-field lines).</p></article>
        <article class="card"><span class="card-kicker">Emission</span><h3>Dots, not lines</h3><p>Thinning to ~3 px spacing (44,090 dots) lifted 0.1922 → 0.2600: each emitted pixel pays a 0.2 false-positive tax, while one dot credits all truth within 300 m.</p></article>
        <article class="card"><span class="card-kicker">Dead annulus</span><h3>Deleting near-catalogue dots</h3><p>Removing 6,436 dots within 200 m of mapped faults (B = 1, 2) lifted 0.2600 → 0.2708 → 0.2778. Those dots carried ~0.002–0.006 credit each vs 0.13 on average (hidden truth = new faults only).</p></article>
      </div>
      <p><a href="research/why-02778.md">Full analysis, arithmetic and what beating 0.2778 requires →</a></p>
    </section>

    <section class="section" aria-labelledby="old-title">
      <div class="section-head"><div><div class="eyebrow">History · kept for audit</div><h2 id="old-title">Earlier GEMSDOE36 files — DO NOT SUBMIT</h2></div></div>
      <div class="table-wrap"><table>
        <tr><th>File</th><th>Status</th></tr>
        <tr><td><code>gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif</code></td><td>Owner-reported live 0.2750 &lt; 0.2778 (it is h33-2-b2 + 1,200 dots); the earlier projection on this site was wrong. Already scored — do not resubmit.</td></tr>
        <tr><td><code>GEMS36_h6_offcatalog_network_prior_…tif</code></td><td>Never scored; validated against an SGMC proxy built from the same family of layers (circular). Not submit-eligible.</td></tr>
        <tr><td><code>GEMS36_FORMAT_TEST_NOT_SUBMISSION.tif</code></td><td>Format demonstration only.</td></tr>
      </table></div>
    </section>

    <section class="section" aria-labelledby="src-title">
      <div class="section-head"><div><div class="eyebrow">Verify it yourself</div><h2 id="src-title">Official sources</h2></div></div>
      <ul>
        <li><a href="{PROBLEM}" target="_blank" rel="noopener">Problem description &amp; metric (page 967)</a> · <a href="{LEADER}" target="_blank" rel="noopener">Leaderboard</a> · <a href="{COMP}" target="_blank" rel="noopener">Competition home</a></li>
        <li><a href="{RULES}" target="_blank" rel="noopener">Official rules PDF (NLR 96647)</a> — 3 scored submissions per week; one final selection for both prize rounds; generative-AI use must be disclosed.</li>
        <li><a href="{REF}" target="_blank" rel="noopener">DrivenData reference solution</a> · <a href="{GDR}" target="_blank" rel="noopener">INGENIOUS / GDR 1391</a> · <a href="{GEODAWN}" target="_blank" rel="noopener">GeoDAWN (USGS)</a> · <a href="{TDEP}" target="_blank" rel="noopener">USGS 3DEP</a></li>
      </ul>
    </section>
  </main>
"""
        + FOOTER
    )


def exec_page(card: dict) -> str:
    ok = card["verdict"] == "promote"
    sub = card["submission"]
    r = card["raster"]
    zeros = Path(r["zeros_tif"]).name
    zp = Path(r["zip"]).name
    decision = (
        '<div class="callout"><p><strong>OK TO SUBMIT</strong> — every automatic gate passed. Use one of your three weekly slots only if the separate selector step chooses it.</p></div>'
        if ok
        else '<div class="callout warning"><p><strong>DO NOT SUBMIT this file.</strong> It is format-valid and unique, but it failed at least one preregistered scientific gate (see the gate table on the home page). Uploading it would spend a weekly slot on an idea that has not beaten the current holdout best.</p></div>'
    )
    return (
        header("Executive summary & how to submit")
        + f"""  <main id="main" class="wrap">
    <section class="page-hero">
      <div class="eyebrow">Executive summary · {e(card['generated_utc'])}</div>
      <h1>Exactly how to submit a GEMS prediction</h1>
      <p class="lede">The current GEMSDOE36 file is <code>{e(zeros)}</code>. Automatic verdict: <strong>{'OK TO SUBMIT (after selector)' if ok else 'DO NOT SUBMIT'}</strong>.</p>
      {decision}
    </section>

    <section class="section" aria-labelledby="steps-title">
      <h2 id="steps-title">Step by step (DrivenData portal)</h2>
      <ol class="steps">
        <li><div><h3>Check the verdict</h3><p>Only upload a file whose banner on the <a href="index.html">home page</a> says <strong>OK TO SUBMIT</strong>. The banner is generated from the JSON run card by code.</p></div></li>
        <li><div><h3>Download the file</h3><p><a href="downloads/{e(zeros)}" download>{e(zeros)}</a> (single-band float32 GeoTIFF) or the <a href="downloads/{e(zp)}" download>ZIP containing that single GeoTIFF</a>. SHA-256 <code>{e(r['zeros_sha256'])}</code>.</p></div></li>
        <li><div><h3>Open the competition</h3><p>Sign in at <a href="{COMP}" target="_blank" rel="noopener">drivendata.org/competitions/306</a> and open the submissions tab (login-walled; not fetched by this project).</p></div></li>
        <li><div><h3>Choose the file</h3><p>The form says: “You can submit a single-band GeoTIFF (.tif) file, or a .zip file containing a single GeoTIFF, with your predictions. It must match the submission format's CRS, shape, and geotransform.” This file uses EPSG:32611, 3730 × 3292 cells, transform (100, 0, 243350, 0, −100, 4508550).</p></div></li>
        <li><div><h3>Paste the unique note</h3><p>Note (optional, ≤ 140 chars): <code>{e(sub['note'])}</code> — it encodes the lane, the holdout number and the content id so submissions can be told apart.</p></div></li>
        <li><div><h3>Submit and record</h3><p>The rules allow three weekly slots of automated scoring (rules PDF §3.2, §3.4). Copy the score from the submission page into <code>registry/</code> as ORGANIZER-CONFIRMED only from that receipt. Never write a projection as a score.</p></div></li>
        <li><div><h3>Final selection</h3><p>Before the deadline choose exactly one submission for both prize rounds (rules PDF §3.5, §3.6.2); the private and expert-revised test sets decide the prizes.</p></div></li>
      </ol>
    </section>

    <section class="section" aria-labelledby="fix-title">
      <h2 id="fix-title">The “Predicted values must be in range [0, 1]” error</h2>
      <p>Files with NaN outside the footprint can fail a strict whole-array range check. GEMSDOE36 ships the <strong>zeros-outside</strong> variant as the primary download: every one of the 12,279,160 cells is finite and in [0, 1] (values are exactly 0 or 1), written by the template's strict writer and re-opened by its validator. A NaN-outside twin is provided only for completeness.</p>
    </section>

    <section class="section" aria-labelledby="sum-title">
      <h2 id="sum-title">What was done this session</h2>
      <ul>
        <li>Verified the metric, rules and leaderboard from official pages (leaderboard #1 = 0.4413 on 2026-10-25; the brief's 0.3195 is stale).</li>
        <li>Byte-level forensics of the 0.2778 file and 118 owner-scored rasters (<a href="research/why-02778.md">analysis</a>).</li>
        <li>Preregistered five hypotheses and ran the top one (H36-GPS) on the shared hide-and-recover evaluator with a paired baseline and a leakage canary.</li>
        <li>Generated a unique GeoTIFF, checked it against {card['registry_comparison']['final_dots']['registry_unique_rasters']} registry rasters, and wrote the JSON run card with an automatic verdict.</li>
      </ul>
      <p class="small">Verify locally: <code>python3 scripts/restore_data.py --group core</code> · <code>python3 scripts/build_h36_features.py</code> · <code>python3 scripts/run_h36_experiment.py --e2</code> · <code>python3 scripts/build_h36_submission.py</code> · <code>python3 -m pytest -q</code></p>
    </section>
  </main>
"""
        + FOOTER
    )


def readme_status(card: dict) -> str:
    ok = card["verdict"] == "promote"
    r, sub, h = card["raster"], card["submission"], card["holdout"]
    zeros = Path(r["zeros_tif"]).name
    gates = " · ".join(f"{k.split('_', 1)[0]} {'PASS' if v else 'FAIL'}" for k, v in card["gates"].items())
    c1, b0, p = h["candidate_C1"], h["baseline_B0"], h["paired_C1_minus_B0"]
    dots = card["registry_comparison"]["final_dots"]
    return f"""<!-- STATUS:START -->
> ## Latest file: `{zeros}`
> **DOWNLOAD: YES · SUBMIT: {'YES — after the separate selector step' if ok else 'NO — automatic NEGATIVE verdict (`DO_NOT_SUBMIT`)'}**
>
> [Download the GeoTIFF](docs/downloads/{zeros}) · [ZIP](docs/downloads/{Path(r['zip']).name}) · [NaN twin](docs/downloads/{Path(r['nan_tif']).name}) · [JSON run card](evidence/h36_run_card.json)
>
> * Name: `{sub['name']}` · SHA-256 `{r['zeros_sha256']}`
> * Note ({sub['note_chars']} chars): `{sub['note']}`
> * Lane H36-GPS: **HOLDOUT-DTI {c1['dti']:.5f}** (95% CI [{c1['ci95'][0]:.5f}, {c1['ci95'][1]:.5f}], `{h['evaluator_version']}`, {h['withheld_positive_pixels']:,} withheld positives) vs matched baseline {b0['dti']:.5f}; paired Δ {p['paired_delta_dti']:+.5f} (CI [{p['paired_delta_ci95'][0]:+.5f}, {p['paired_delta_ci95'][1]:+.5f}], {p['fold_wins']}/{p['n_folds']} folds); recorded group best 0.14876.
> * Uniqueness vs {dots['registry_unique_rasters']} registry rasters: max |ρ| {dots['max_abs_rank_correlation']:.4f} (≤ 0.90); max 3-px dot overlap with a competing method {dots.get('max_competing_dot_overlap') or 0:.4f} (≤ 0.70).
> * Gates: {gates}
> * Organizer score: none. Generated {card['generated_utc']}.
<!-- STATUS:END -->"""


def update_readme(card: dict) -> None:
    p = ROOT / "README.md"
    s = p.read_text(encoding="utf-8")
    a, b = s.index("<!-- STATUS:START -->"), s.index("<!-- STATUS:END -->") + len("<!-- STATUS:END -->")
    p.write_text(s[:a] + readme_status(card) + s[b:], encoding="utf-8")


def write_manifest(card: dict) -> None:
    r, sub = card["raster"], card["submission"]
    manifest = {
        "schema_version": 2,
        "generated_from": "evidence/h36_run_card.json",
        "current": {
            "file": Path(r["zeros_tif"]).name,
            "sha256": r["zeros_sha256"],
            "nan_twin": Path(r["nan_tif"]).name,
            "nan_sha256": r["nan_sha256"],
            "zip": Path(r["zip"]).name,
            "zip_sha256": r["zip_sha256"],
            "submission_name": sub["name"],
            "note": sub["note"],
            "verdict": card["verdict"],
            "status": card["status"],
            "ok_to_download": True,
            "ok_to_submit": card["verdict"] == "promote",
            "organizer_score": None,
        },
        "historical_do_not_submit": [
            {"file": "gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif",
             "status": "already scored: owner-reported 0.2750 (< 0.2778); do not resubmit"},
            {"file": "GEMS36_h6_offcatalog_network_prior_20261004T193432.021282Z_3276c04090_3c064db2.tif",
             "status": "never scored; validated on a circular SGMC proxy; not submit-eligible"},
            {"file": "GEMS36_FORMAT_TEST_NOT_SUBMISSION.tif", "status": "format fixture only"},
        ],
        "superseded_manifest": "submissions_manifest_2026-10-04_superseded.json (contains projections that were never scores)",
    }
    (DOCS / "downloads" / "submissions_manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")


def main() -> int:
    card = json.loads(CARD.read_text())
    write_manifest(card)
    (DOCS / "index.html").write_text(index_page(card), encoding="utf-8")
    (DOCS / "executive-summary.html").write_text(exec_page(card), encoding="utf-8")
    update_readme(card)
    print("site + README status written from", CARD.relative_to(ROOT), "verdict:", card["verdict"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
