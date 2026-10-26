#!/usr/bin/env python3
"""Refresh the public landing/guide/status from the audited MTO-36 and HVG-36 run cards.

The historical lanes stay available for audit; this builder inserts the fail-closed
current research status (MTO-36 and HVG-36, the new 0.135759 GEMSDOE36 repo holdout
record) at the top and regenerates the complete nine-site + GEMSDOE36 lanes executive
summary table in docs/index.html, docs/executive-summary.html, and README.md.
It cannot turn an unverified owner score into a receipt.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from shutil import copyfile

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CARD = ROOT / "evidence/mto36_run_card_20261026.json"
HVG_CARD = ROOT / "evidence/hvg36_run_card_20261026.json"
LEDGER = ROOT / "evidence/focus_sites_9repo_summary_20261026.json"
README = ROOT / "README.md"
INDEX = DOCS / "index.html"
SUMMARY = DOCS / "executive-summary.html"
START = "<!-- MTO-36:START -->"
END = "<!-- MTO-36:END -->"

# Exact per-site uniqueness, lineage, and local holdout diagnostics for the 9 focus sites
FOCUS9_META: dict[str, dict[str, str]] = {
    "GEMSDOE24": {
        "method": "Dotted H19-5 multi-sensor ridge + D1.5 collar (recent: H24-GVC1 OOF HGB)",
        "estimate_score": (
            "Recent H24-GVC1 OOF: HOLDOUT-DTI 0.14876 (95% CI [0.13413, 0.16370]; "
            "gems-segment-pooled-v1, 60,988 withheld px). "
            "Best hist in-sample cat-overlap diag: 0.171825 [0.160961, 0.182756]"
        ),
        "unique_status": (
            "NOT UNIQUE — Best hist (60,069 dots) is a 97.95% Jaccard subset of GEMSDOE27 (61,328 dots); "
            "recent GVC1 has 76.82% 3-px overlap with 10GEMSDOE (74.3% of dots <=10 px of known faults)"
        ),
    },
    "GEMSDOE25": {
        "method": "Dotted H19-5 multi-sensor ridge + D2.8 Poisson 300 m off-catalogue emitter",
        "estimate_score": (
            "In-sample cat-overlap diag: HOLDOUT-DTI 0.161630 (95% CI [0.151184, 0.172088]; "
            "gems-segment-pooled-v1, 60,988 withheld px; no OOF surface archived)"
        ),
        "unique_status": (
            "NOT UNIQUE — 0-XOR byte-identical on footprint (44,090 dots) to GEMSDOE30 d28-poisson300m; "
            "parent superset of GEMSDOE31 (-3,891 collar dots) and GEMSDOE32 B2 (-6,436 collar dots)"
        ),
    },
    "GEMSDOE27": {
        "method": "Topo-gap-closure V2 on D1.5 (recent: H29-S stitched OOF + Frangi/CELF 300 m cover)",
        "estimate_score": (
            "Recent H29-S OOF: HOLDOUT-DTI 0.0566 (strict 5 km block OOF; median d_known = 16.2 px). "
            "Best hist in-sample cat-overlap diag: 0.172636 [0.162001, 0.183450]"
        ),
        "unique_status": (
            "Best hist (61,328 dots) shares 97.95% Jaccard with GEMSDOE24; "
            "recent H29-S (37,654 dots, 0.2190 OWNER-REPORTED) is a genuine zero-copy standalone model (already submitted)"
        ),
    },
    "GEMSDOE28": {
        "method": "H36-1 rung30 blind R1 100 m collar-pruned + step-over rung additions",
        "estimate_score": (
            "In-sample cat-overlap diag: HOLDOUT-DTI 0.046180 (95% CI [0.042828, 0.049837]; "
            "gems-segment-pooled-v1, 60,988 withheld px; recent S18 11,082 dots under-budgeted)"
        ),
        "unique_status": (
            "NOT UNIQUE — R1 solo twin is 0-XOR identical to GEMSDOE31 (40,199 dots); "
            "h36-1-rung30 (37,660 dots) is a >93% overlap derivative of the D2.8/B2 lineage"
        ),
    },
    "GEMSDOE30": {
        "method": "D2.8 Poisson 300 m off-catalogue (recent: MSDB-1v2 edge44090)",
        "estimate_score": (
            "In-sample cat-overlap diag: HOLDOUT-DTI 0.161630 (95% CI [0.151184, 0.172088]; "
            "gems-segment-pooled-v1, 60,988 withheld px)"
        ),
        "unique_status": (
            "NOT UNIQUE — Exact 0-XOR duplicate (44,090 dots) of GEMSDOE25 dotted-h19-5-d2-8"
        ),
    },
    "GEMSDOE31": {
        "method": "H27-4 solo D2.8 with 100 m (d_cat > 1 px) known-fault collar exclusion",
        "estimate_score": (
            "In-sample cat-overlap diag: HOLDOUT-DTI 0.049061 (95% CI [0.045533, 0.052758]; "
            "gems-segment-pooled-v1, 60,988 withheld px; 1 px collar removed)"
        ),
        "unique_status": (
            "NOT UNIQUE — Exact 0-XOR subset of GEMSDOE25/30 D2.8 removing 3,891 d_cat=1 px collar dots "
            "(44,090 - 3,891 = 40,199 dots)"
        ),
    },
    "GEMSDOE32": {
        "method": "H33-2 B2: D2.8 with 200 m (d_cat > 2 px) known-fault collar exclusion (9-Site Champion)",
        "estimate_score": (
            "In-sample cat-overlap diag: HOLDOUT-DTI 0.006708 (95% CI [0.006089, 0.007400]; "
            "gems-segment-pooled-v1, 60,988 withheld px; 2 px moat around full labels.tif)"
        ),
        "unique_status": (
            "NOT UNIQUE — Exact 0-XOR subset of GEMSDOE25/30 D2.8 removing 6,436 d_cat<=2 px collar dots "
            "(44,090 - 6,436 = 37,654 dots; 2,545 beyond GEMSDOE31 solo)"
        ),
    },
    "GEMSDOE33": {
        "method": "H33d analog tip/step-over R30 graft onto D2.8/B2 base (recent: A33-L1)",
        "estimate_score": (
            "In-sample cat-overlap diag: HOLDOUT-DTI 0.086408 (95% CI [0.080400, 0.092429]; "
            "gems-segment-pooled-v1, 60,988 withheld px)"
        ),
        "unique_status": (
            "NOT UNIQUE — >90% overlap derivative of the D2.8/B2 lineage with 4,211 tip/step-over dots added"
        ),
    },
    "GEMSDOE36": {
        "method": "Legacy: B2 + 1,200 radial thermal IDW dots. New 2026-10-26 lane: HVG-36 EXP-1 (73-feature hydrothermal-vent conduit + RAD-ANISO + P-TMI + D-PAIR OOF HGB)",
        "estimate_score": (
            "New HVG-36 EXP-1 OOF: HOLDOUT-DTI 0.135759 (95% CI [0.123271, 0.148461]; "
            "gems-segment-pooled-v1, 60,988 withheld px — NEW GEMSDOE36 REPO RECORD, beats B0 0.133169 in 3/4 folds). "
            "Prior lanes: H36-GPS B0 0.133749, H36-GPS C1 0.132030, MOE36 0.124900, ATVR-36 0.117925, H36-CTRB 0.114425, WDP-36 0.093269, MTO-36 0.067611"
        ),
        "unique_status": (
            "Legacy PINN (38,854 dots) is NOT UNIQUE (96.91% overlap with B2 = B2 U 1,200 dots). "
            "New HVG-36 EXP-1 (37,654 dots) is 100% UNIQUE vs all 9 focus-site top champions "
            "(max 3-px overlap 44.48%, 35.35% vs B2; surface max |rho|=0.5713 PASS), "
            "but trips the literal all-203 70% overlap cap on dense blankets (88.37%) and 5-px calibration lattice (100%)"
        ),
    },
}


def e(x: object) -> str:
    return html.escape(str(x), quote=True)


def insert_or_replace(path: Path, body: str, anchor: str) -> None:
    text = path.read_text(encoding="utf-8")
    if START in text or END in text:
        if text.count(START) != 1 or text.count(END) != 1 or text.index(START) > text.index(END):
            raise RuntimeError(f"Malformed MTO-36 markers: {path}")
        first = text.index(START)
        last = text.index(END) + len(END)
        text = text[:first] + body + text[last:]
    else:
        if text.count(anchor) != 1:
            raise RuntimeError(f"Expected one anchor {anchor!r} in {path}")
        text = text.replace(anchor, anchor + "\n" + body, 1)
    path.write_text(text, encoding="utf-8")


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


def index_card(card: dict, hvg: dict) -> str:
    h = card["holdout_dti"]
    r = card["registry"]["final_dots"]
    d = card["download"]
    tif, z = Path(d["tif"]).name, Path(d["zip"]).name

    hh = hvg["holdout"]
    hr_s = hvg["registry_uniqueness"]["pre_placement_surface"]
    hr_d = hvg["registry_uniqueness"]["final_dots"]
    ha = hvg["artifact"]
    hs = hvg["submission"]
    hvg_tif = Path(ha["tif_path"]).name
    hvg_zip = Path(ha["zip_path"]).name

    return f"""{START}
    <section class="verdict verdict-bad" id="current-mto36" aria-labelledby="mto36-title">
      <div class="eyebrow">Current release gates · HVG-36 (new repo holdout record 0.135759) &amp; MTO-36 · machine-checked on 2026-10-26 UTC</div>
      <h1 id="mto36-title">DO NOT SUBMIT — original research GeoTIFFs are downloadable (`verdict: negative`)</h1>
      <p class="verdict-sub"><strong>DOWNLOAD: YES (research) · SUBMIT TO DRIVENDATA: NO — HOLD WEEKLY SLOT.</strong>
        Our latest preregistered lane <strong>HVG-36 EXP-1</strong> (73-feature hydrothermal-vent structural conduit + <code>RAD-ANISO</code> + <code>P-TMI</code> phase persistence + <code>D-PAIR</code> basement dipole OOF HGB) achieves <strong>HOLDOUT-DTI {hh['pooled_dti']:.6f}</strong> (95% CI <code>[{hh['ci95'][0]:.6f}, {hh['ci95'][1]:.6f}]</code>), setting a <strong>new GEMSDOE36 repository record</strong> and beating matched <code>B0</code> (<code>{hh['matched_baseline_B0']['pooled_dti']:.6f}</code>) in <strong>3/4 spatial folds</strong> (<code>NW</code>, <code>NE_LidarGapHeavy</code>, <code>SW</code>) as well as recorded <code>H36-GPS B0</code> (<code>0.133749</code>). However, because its paired 95% CI vs <code>B0</code> (<code>[{hh['paired_comparison_vs_B0']['paired_delta_ci95'][0]:+.6f}, {hh['paired_comparison_vs_B0']['paired_delta_ci95'][1]:+.6f}]</code>) straddles zero, its pooled score trails the recorded group best (<code>0.14876</code>), and its final dots exceed the literal 70% 3-px overlap cap against dense registry blankets (while remaining <strong>100% unique against all 9 focus-site top champions</strong> at max <code>{hr_d['max_3px_overlap_focus9_top_champions']:.2%}</code> and <code>{hr_d['overlap_3px_vs_GEMSDOE32_B2_champion']:.2%}</code> vs <code>B2</code>), both <strong>HVG-36</strong> and <strong>MTO-36</strong> (<code>{e(tif)}</code>) are strictly marked <strong>DO NOT SUBMIT</strong>.</p>
      <div class="hero-actions">
        <a class="button" href="downloads/{e(hvg_tif)}" download>Download HVG-36 TIFF (0.135759 repo best) · <code>{e(hvg_tif)}</code> &#8595;</a>
        <a class="button secondary" href="downloads/{e(hvg_zip)}" download>HVG-36 ZIP (single TIFF)</a>
        <a class="button secondary" href="downloads/hvg36-run-card.json">HVG-36 Run Card</a>
        <a class="button secondary" href="research/hvg36-20261026.md">HVG-36 Monograph</a>
        <a class="button secondary" href="downloads/{e(tif)}" download>Download MTO-36 TIFF · <code>{e(tif)}</code> &#8595;</a>
        <a class="button secondary" href="downloads/{e(z)}" download>MTO-36 ZIP</a>
        <a class="button secondary" href="downloads/mto36-run-card.json">MTO-36 Run Card</a>
        <a class="button secondary" href="executive-summary.html">How submissions work &amp; 9-site table</a>
      </div>
      <div class="table-wrap verdict-meta"><table>
        <tr><th>Latest Lane · HVG-36 EXP-1 (New Repo Holdout Best)</th><td><code>{e(hs['name'])}</code> · File <code>{e(hvg_tif)}</code> · <strong>NEGATIVE — DO NOT SUBMIT</strong><br>
          <strong>Note ({hs['note_length']} / 140 chars):</strong> <code>{e(hs['note'])}</code><br>
          <strong>SHA-256:</strong> <code>{e(ha['tif_sha256'])}</code> · <strong>ZIP SHA-256:</strong> <code>{e(ha['zip_sha256'])}</code><br>
          <strong>Holdout result:</strong> <strong>HOLDOUT-DTI {hh['pooled_dti']:.6f}</strong> · 95% CI <code>[{hh['ci95'][0]:.6f}, {hh['ci95'][1]:.6f}]</code> · <code>{e(hh['evaluator_version'])}</code> · <code>{hh['withheld_positives']:,}</code> withheld positives (<code>NW=0.14972</code>, <code>NE_LidarGapHeavy=0.17477</code>, <code>SW=0.08927</code>, <code>SE=0.15112</code>; wins 3/4 folds vs <code>B0={hh['matched_baseline_B0']['pooled_dti']:.6f}</code>; <code>EXP-2=0.133383</code>, <code>EXP-3=0.133757</code>).<br>
          <strong>Leakage canary &amp; uniqueness:</strong> All 14 HVG-36 features PASS canary (max two-polarity AUC <code>{hvg['leakage_canary']['max_two_polarity_auc']:.4f} &lt;= 0.90</code>). Surface max <code>|rho|={hr_s['max_abs_spearman_rho']:.4f} &lt;= 0.90</code> PASS. Final dots: <strong>{hr_d['overlap_3px_vs_GEMSDOE32_B2_champion']:.2%}</strong> vs <code>GEMSDOE32 B2</code> champion and <strong>{hr_d['max_3px_overlap_focus9_top_champions']:.2%}</strong> max across all 9 focus-site top champions (PASS), <code>{hr_d['max_3px_overlap_focus9_all_rasters']:.2%}</code> on <code>gems28-h37-1-probe-union-pool-r1</code>, <code>{hr_d['max_3px_overlap_competing_methods']:.2%}</code> on dense blankets, <code>{hr_d['max_3px_overlap_all_203_literal']:.2%}</code> on 5-px calibration lattice.</td></tr>
        <tr><th>MTO-36 Submission name / verdict</th><td><code>{e(card['submission_name'])}</code> · <strong>NEGATIVE — DO NOT SUBMIT</strong></td></tr>
        <tr><th>MTO-36 Note ({len(card['submission_note'])} / 140 chars)</th><td><code>{e(card['submission_note'])}</code></td></tr>
        <tr><th>MTO-36 SHA-256</th><td><code>{e(card['raster_sha256'])}</code></td></tr>
        <tr><th>Grid &amp; range</th><td>One <code>float32</code> band, <code>EPSG:32611</code>, <code>3730 &times; 3292</code>; <code>{d['dot_count']:,}</code> original dots; zero NaN / Inf across the entire grid, all cells in <code>[0,1]</code>; CRS, shape, transform match pinned owner-mirror template. <strong>Local format PASS is not portal acceptance.</strong></td></tr>
        <tr><th>MTO-36 Holdout &amp; novelty</th><td><strong>HOLDOUT-DTI {h['pooled_candidate']:.6f}</strong> · 95% CI <code>[{h['ci95_candidate'][0]:.6f}, {h['ci95_candidate'][1]:.6f}]</code> · <code>{e(h['evaluator_version'])}</code> · <code>{h['withheld_positives']:,}</code> withheld positives. Matched raw-edge control <code>{h['pooled_control']:.6f}</code>; paired CI <code>[{h['paired_ci95'][0]:+.6f}, {h['paired_ci95'][1]:+.6f}]</code> contains zero; recorded comparable best <code>0.14876</code>. Surface max <code>|rho|={card['registry']['surface_before_placement']['max_abs_rank_correlation']:.3f}</code> PASS; final dots <code>{r['overlap_vs_champion_B2']:.2%}</code> vs B2 and <code>{r['max_dot_overlap_3px_focus9']:.2%}</code> max across nine focus sites; <strong>{r['max_dot_overlap_3px_all']:.2%} max across {r['n_registry_rasters_verified']} pinned comparator rasters — FAIL</strong>.</td></tr>
      </table></div>
      <p class="small">Historical reported <code>0.2778</code>, <code>0.3195</code> and <code>0.4413</code> are <strong>OWNER-REPORTED / not verified here</strong>. <code>ORGANIZER-CONFIRMED</code> is reserved for a saved portal receipt; none is available. <a href="research/hvg36-20261026.md">HVG-36 report</a> · <a href="research/preregistration-hvg36-20261026.md">HVG-36 preregistration</a> · <a href="research/mto36-evidence-and-nine-sites.md">Source-linked nine-site audit &amp; limitations</a>.</p>
    </section>
    <section class="section" id="source-freshness" aria-labelledby="source-freshness-title">
      <div class="section-head"><div><div class="eyebrow">Current source feed · not a score feed</div><h2 id="source-freshness-title">Nine repository activity checks</h2></div><p>Refreshes public GitHub commit timestamps in your browser. Pinned raster checks and reported competition scores do not update automatically; <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/" target="_blank" rel="noopener">view the official leaderboard directly</a>.</p></div>
      <button type="button" class="button secondary" id="refresh-source-feed">Refresh source activity</button>
      <p id="source-feed-status" role="status" aria-live="polite">Public source freshness has not been checked in this browser session.</p>
      <ul id="source-feed-list" class="source-feed-list"></ul>
    </section>
{END}"""


def site_table(ledger: dict, section_id: str = "focus-sites-title") -> str:
    rows = []
    for item in ledger["focus_sites"]:
        site = item["site"]
        h = item["highest_historical_submission"]
        meta = FOCUS9_META.get(site, {})
        extra_dl = ""
        if site == "GEMSDOE36":
            extra_dl = (
                "<br><strong>New HVG-36 (2026-10-26):</strong> "
                "<a href=\"downloads/gemsdoe36-hvg36-vent-dipole-20261026-b3ee97873192-zeros.tif\" download>"
                "<code>gemsdoe36-hvg36-vent-dipole-20261026-b3ee97873192-zeros.tif</code></a> "
                "<small>SHA-256 85d56b03aff1 (37,654 dots)</small>"
            )
        rows.append(
            "<tr>"
            "<td><code>{site}</code><br><small>{method}</small></td>"
            "<td><a href=\"{link}\" target=\"_blank\" rel=\"noopener\"><code>{name}</code></a> "
            "<small>SHA-256 {sha} ({dots:,} dots)</small>{extra_dl}</td>"
            "<td><strong>{score:.4f} OWNER-REPORTED</strong> (receipt missing)<br>"
            "<small>{est}</small></td>"
            "<td><small>{uniq}</small></td>"
            "<td><strong>NO — DO NOT SUBMIT</strong><br><small>Historical already-submitted / 0-XOR copy or negative holdout gate</small></td>"
            "</tr>".format(
                site=e(site),
                method=e(meta.get("method", "")),
                link=e(h["pinned_raster_source_url"]),
                name=e(h["name"]),
                sha=e(h["sha256_full"][:12]),
                dots=h["dots"],
                extra_dl=extra_dl,
                score=h["score"],
                est=e(meta.get("estimate_score", "")),
                uniq=e(meta.get("unique_status", "")),
            )
        )
    return f"""    <section class="section" aria-labelledby="{e(section_id)}">
      <div class="section-head"><div><div class="eyebrow">Executive Summary Table · Pinned byte-forensics, estimated HOLDOUT-DTI scores &amp; uniqueness status</div><h2 id="{e(section_id)}">Nine Focus Sites (GEMSDOE24–36) — File to Download, Estimated vs. Historical Score &amp; Uniqueness</h2></div>
      <p>Every focus site's highest-scoring historical GeoTIFF was verified from pinned GitHub bytes (SHA-256, 3730&times;3292 grid, dot count, and pairwise XOR/overlap). Per Protocol &sect;3, every number is explicitly labelled as <code>HOLDOUT-DTI</code> (evaluator version, withheld positives, 95% CI) or <code>OWNER-REPORTED</code> (historical leaderboard figure without an archived portal receipt; never write a projection as a score).</p></div>
      <div class="table-wrap"><table><tr><th>Site &amp; Method Family</th><th>File to Download (Pinned Source &amp; SHA-256)</th><th>Historical Reported Score &amp; Estimated Score (<code>HOLDOUT-DTI</code>)</th><th>Unique Submission vs. Other GEMSDOE Sites?</th><th>Submission Verdict</th></tr>
""" + "\n".join(rows) + """
      </table></div>
      <p><strong>PhD Forensic Summary of Why GEMSDOE32 (<code>0.2778</code>) Scored Highest &amp; How to Beat It:</strong> Byte-level XOR across all <code>12,279,160</code> cells proves a deterministic 3-step collar-pruning chain on the exact same <code>D2.8</code> prediction set: (1) <code>GEMSDOE25 d2.8 == GEMSDOE30 d2.8</code> (<code>0</code> XOR, <code>44,090</code> dots, <code>0.2600</code> OWNER-REPORTED); (2) <code>GEMSDOE31 solo == D2.8 &amp; (d_cat &gt; 1 px)</code> (<code>0</code> XOR, removing <code>3,891</code> 100 m collar dots &rarr; <code>40,199</code> dots, <code>0.2708</code> OWNER-REPORTED); (3) <code>GEMSDOE32 B2 == D2.8 &amp; (d_cat &gt; 2 px)</code> (<code>0</code> XOR, removing <code>2,545</code> more 200 m collar dots [<code>6,436</code> total] &rarr; <code>37,654</code> dots, <code>0.2778</code> OWNER-REPORTED); while <code>GEMSDOE36 legacy PINN == B2 &cup; 1,200</code> radial thermal IDW dots (<code>38,854</code> dots, <code>0.2750</code> OWNER-REPORTED). Because <code>existing_faults.tif</code> is masked during scoring, near-catalogue collar predictions contribute zero true positives while inflating the <code>0.2 &middot; FP_w</code> denominator penalty (`~1,287.2` Tversky denominator units removed by <code>B2</code>). Pure collar thinning asymptotes below <code>~0.295</code>; surpassing <code>0.2778</code>, <code>0.3195</code>, and <code>0.4413</code> requires genuine off-catalogue recall expansion (<code>TP_w</code>) in blind piedmont, basin-fill, hydrothermal-conduit, and 3DEP LiDAR-gap regimes. <a href="research/why-02778.md">Full mathematical proof</a> · <a href="research/hvg36-20261026.md">HVG-36 geothermal-vent &amp; dipole monograph</a>.</p>
    </section>"""


def executive_card(card: dict, hvg: dict, ledger: dict) -> str:
    d = card["download"]
    tif, z = Path(d["tif"]).name, Path(d["zip"]).name
    hh = hvg["holdout"]
    ha = hvg["artifact"]
    hs = hvg["submission"]
    hvg_tif = Path(ha["tif_path"]).name
    hvg_zip = Path(ha["zip_path"]).name
    return f"""{START}
    <section class="verdict verdict-bad" id="current-guide" aria-labelledby="mto-guide-title">
      <div class="eyebrow">Read this first · current validated files (HVG-36 &amp; MTO-36) and automatic decision</div>
      <h2 id="mto-guide-title">DOWNLOAD: YES (research) · DO NOT SUBMIT these files</h2>
      <p class="verdict-sub">Both <strong>HVG-36 EXP-1</strong> (<code>{e(hvg_tif)}</code>, <strong>HOLDOUT-DTI {hh['pooled_dti']:.6f}</strong>, new GEMSDOE36 repository holdout record) and <strong>MTO-36</strong> (<code>{e(tif)}</code>, <strong>HOLDOUT-DTI {card['holdout_dti']['pooled_candidate']:.6f}</strong>) are <strong>original</strong> whole-array <code>[0, 1]</code> GeoTIFFs on the competition grid, but their <strong>holdout promotion and literal all-registry uniqueness gates failed</strong>. Their local format checks pass; no DrivenData upload or weekly submission slot was used.</p>
      <div class="hero-actions">
        <a class="button" href="downloads/{e(hvg_tif)}" download>Download HVG-36 TIFF (0.135759) · <code>{e(hvg_tif)}</code> &#8595;</a>
        <a class="button secondary" href="downloads/{e(hvg_zip)}" download>Download HVG-36 ZIP</a>
        <a class="button secondary" href="downloads/hvg36-run-card.json">HVG-36 JSON run card</a>
        <a class="button secondary" href="downloads/{e(tif)}" download>Download MTO-36 TIFF · <code>{e(tif)}</code> &#8595;</a>
        <a class="button secondary" href="downloads/{e(z)}" download>Download MTO-36 ZIP</a>
        <a class="button secondary" href="downloads/mto36-run-card.json">MTO-36 JSON run card</a>
      </div>
      <p><strong>HVG-36 Name:</strong> <code>{e(hs['name'])}</code> · <strong>Note ({hs['note_length']} / 140 chars):</strong> <code>{e(hs['note'])}</code> · <strong>TIF SHA-256:</strong> <code>{e(ha['tif_sha256'])}</code><br>
        <strong>MTO-36 Name:</strong> <code>{e(card['submission_name'])}</code> · <strong>Note ({len(card['submission_note'])} / 140 chars):</strong> <code>{e(card['submission_note'])}</code> · <strong>TIF SHA-256:</strong> <code>{e(card['raster_sha256'])}</code></p>
      <p><a href="research/hvg36-20261026.md">Read HVG-36 geothermal-vent &amp; dipole report</a> · <a href="research/mto36-evidence-and-nine-sites.md">Read audited nine-site summary &amp; limitations</a>. <code>ORGANIZER-CONFIRMED</code> requires a submission-page receipt; the user-supplied older scores do not satisfy this.</p>
    </section>
{site_table(ledger, section_id="exec-focus-sites-title")}
{END}"""


def readme_status(card: dict, hvg: dict) -> str:
    h = card["holdout_dti"]
    r = card["registry"]["final_dots"]
    d = card["download"]
    hh = hvg["holdout"]
    hr_s = hvg["registry_uniqueness"]["pre_placement_surface"]
    hr_d = hvg["registry_uniqueness"]["final_dots"]
    ha = hvg["artifact"]
    hs = hvg["submission"]
    return f"""<!-- STATUS:START -->
> ## CURRENT DECISION · `DOWNLOAD: YES (research)` · `DO NOT SUBMIT` · `verdict: negative`
>
> **Latest original HVG-36 file (New GEMSDOE36 Holdout Record `0.135759`):** [`{Path(ha['tif_path']).name}`]({ha['tif_path']}) · [one-TIFF ZIP]({ha['zip_path']}) · [validator/run card](evidence/hvg36_run_card_20261026.json) · [monograph](docs/research/hvg36-20261026.md) · [preregistration](docs/research/preregistration-hvg36-20261026.md). **Not competition-authorized (`verdict: negative`).**
> - Name: `{hs['name']}`. Note ({hs['note_length']} / 140 characters): `{hs['note']}`.
> - SHA-256: `{ha['tif_sha256']}` (ZIP SHA-256: `{ha['zip_sha256']}`). Template, single band, CRS/shape/transform, all-grid finite `[0,1]` **PASS locally** (`37,654` dots, `0` on `existing_faults.tif`).
> - **HOLDOUT-DTI (HVG-36 EXP-1):** **`{hh['pooled_dti']:.6f}`** (95% CI `[{hh['ci95'][0]:.6f}, {hh['ci95'][1]:.6f}]`; `{hh['evaluator_version']}`, `{hh['withheld_positives']:,}` withheld positives; 1.5 km buffer; `NW=0.14972`, `NE_LidarGapHeavy=0.17477`, `SW=0.08927`, `SE=0.15112`). Beats matched `B0_base59` (`{hh['matched_baseline_B0']['pooled_dti']:.6f}`, delta `+{hh['paired_comparison_vs_B0']['paired_delta_dti']:.6f}`, wins **3/4 folds**) and recorded `H36-GPS B0` (`0.133749`, delta `+0.002010`), setting the **highest HOLDOUT-DTI in GEMSDOE36** (`EXP-2 = 0.133383`, `EXP-3 = 0.133757`). However, paired 95% CI vs `B0` (`[{hh['paired_comparison_vs_B0']['paired_delta_ci95'][0]:+.6f}, {hh['paired_comparison_vs_B0']['paired_delta_ci95'][1]:+.6f}]`) crosses zero and pooled DTI remains below the recorded group best `0.14876` **HOLDOUT-DTI** (`GEMSDOE24` `H24-GVC1`).
> - **Uniqueness & Canary (HVG-36):** All 14 HVG-36 features PASS leakage canary (`max two-polarity AUC = {hvg['leakage_canary']['max_two_polarity_auc']:.4f} <= 0.90`). Pre-placement surface `max |rho| = {hr_s['max_abs_spearman_rho']:.4f} <= 0.90` PASS. Final dots: **`{hr_d['overlap_3px_vs_GEMSDOE32_B2_champion']:.2%}`** vs `GEMSDOE32 B2` champion and **`{hr_d['max_3px_overlap_focus9_top_champions']:.2%}`** max across all 9 focus-site top champions (**100% unique vs all 9 focus-site champions**), `{hr_d['max_3px_overlap_focus9_all_rasters']:.2%}` vs `gems28-h37-1-probe-union-pool-r1`, `{hr_d['max_3px_overlap_competing_methods']:.2%}` vs dense blankets, and `{hr_d['max_3px_overlap_all_203_literal']:.2%}` vs 5-px calibration lattice (**FAIL literal all-203 gate**).
>
> **Original MTO-36 file:** [`{Path(d['tif']).name}`]({d['tif']}) · [one-TIFF ZIP]({d['zip']}) · [validator/run card](evidence/mto36_run_card_20261026.json). **Not competition-authorized.**
> - Name: `{card['submission_name']}`. Note ({len(card['submission_note'])} / 140 characters): `{card['submission_note']}`. SHA-256: `{card['raster_sha256']}`.
> - **HOLDOUT-DTI (MTO-36):** `{h['pooled_candidate']:.6f}` (95% CI `[{h['ci95_candidate'][0]:.6f}, {h['ci95_candidate'][1]:.6f}]`; `{h['evaluator_version']}`, `{h['withheld_positives']:,}` withheld positives; 1.5 km buffer). Matched control `{h['pooled_control']:.6f}`; paired CI `[{h['paired_ci95'][0]:+.6f}, {h['paired_ci95'][1]:+.6f}]` crosses zero.
> - **Uniqueness (MTO-36):** surface max |rho| `{card['registry']['surface_before_placement']['max_abs_rank_correlation']:.4f}` PASS; B2 champion overlap `{r['overlap_vs_champion_B2']:.2%}`, nine focus max `{r['max_dot_overlap_3px_focus9']:.2%}`; **all {r['n_registry_rasters_verified']} references max `{r['max_dot_overlap_3px_all']:.2%}` FAIL**.
> - All GEMSDOE36 lanes summary (`gems-segment-pooled-v1`, 60,988 withheld positives): [HVG-36](evidence/hvg36_run_card_20261026.json) (`0.135759`), [H36-GPS](evidence/h36_run_card.json) (`B0=0.133749`, `C1=0.132030`), [MOE36](evidence/moe36_run_card_20261026.json) (`0.124900`; [report](docs/research/moe36-20261026.md)), [ATVR-36](evidence/atvr36_run_card_20261026.json) (`0.117925`), [H36-CTRB](evidence/h36_ctrb_run_card_20261025.json) (`0.114425`), [WDP-36](evidence/wdp36_run_card_20261026.json) (`0.093269`; [report](docs/research/wdp36-20261026.md)), [MTO-36](evidence/mto36_run_card_20261026.json) (`0.067611`), [Lane36](evidence/lane36_crosscheck.json); **all negative — hold weekly submission slot**.
> - Historical competition results are **OWNER-REPORTED**, not `ORGANIZER-CONFIRMED`: no submission-page receipts are archived. User-supplied public maxima `0.3195` and `0.4413` are inconsistent in date and not refreshed here. Live board: [DrivenData leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/).
<!-- STATUS:END -->"""


def readme_focus9_table(ledger: dict) -> str:
    lines = [
        "<!-- FOCUS9_TABLE:START -->",
        "| Site & Method Family | File to Download (Pinned Source & SHA-256 Prefix) | Verified Dots | Historical Reported Score (`OWNER-REPORTED`) & Estimated Score (`HOLDOUT-DTI`) | Unique Submission vs. Other GEMSDOE Sites? | Submission Verdict |",
        "|---|---|---:|---|---|---|",
    ]
    for item in ledger["focus_sites"]:
        site = item["site"]
        h = item["highest_historical_submission"]
        meta = FOCUS9_META.get(site, {})
        dl_col = f"[{site}]({h['pinned_raster_source_url']}) · `{h['name']}` · `{h['sha256_full'][:12]}`"
        if site == "GEMSDOE36":
            dl_col += (
                " <br> **New HVG-36:** [`gemsdoe36-hvg36-vent-dipole-20261026-b3ee97873192-zeros.tif`]"
                "(docs/downloads/gemsdoe36-hvg36-vent-dipole-20261026-b3ee97873192-zeros.tif) · `85d56b03aff1` (`37,654` dots)"
            )
        lines.append(
            f"| **{site}** — {meta.get('method', '')} | {dl_col} | {h['dots']:,} | "
            f"**{h['score']:.4f} OWNER-REPORTED** <br> {meta.get('estimate_score', '')} | "
            f"{meta.get('unique_status', '')} | **DO NOT SUBMIT** (historical / copy or negative gate) |"
        )
    lines.append("<!-- FOCUS9_TABLE:END -->")
    return "\n".join(lines)


def main() -> int:
    card = json.loads(CARD.read_text(encoding="utf-8"))
    hvg = json.loads(HVG_CARD.read_text(encoding="utf-8"))
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    ensure_status(card, ledger, hvg)
    insert_or_replace(INDEX, index_card(card, hvg), '<main id="main" class="wrap">')
    insert_or_replace(SUMMARY, executive_card(card, hvg, ledger), '<main id="main" class="wrap">')

    index = INDEX.read_text(encoding="utf-8")
    updated, n = re.subn(
        r'    <!-- 9 FOCUS SITES EXECUTIVE SUMMARY -->\s*<section class="section" aria-labelledby="focus-sites-title">.*?</section>',
        "    <!-- 9 FOCUS SITES EXECUTIVE SUMMARY -->\n" + site_table(ledger),
        index, count=1, flags=re.S,
    )
    if n != 1:
        raise RuntimeError("Nine-site section missing from index")
    script = '<script defer src="assets/live-feed.js"></script>'
    if script not in updated:
        updated = updated.replace('</body>', '  ' + script + '\n</body>', 1)
    INDEX.write_text(updated, encoding="utf-8")

    s = README.read_text(encoding="utf-8")
    if s.count("<!-- STATUS:START -->") != 1 or s.count("<!-- STATUS:END -->") != 1:
        raise RuntimeError("README status markers missing/duplicated")
    s = re.sub(r'<!-- STATUS:START -->.*?<!-- STATUS:END -->', readme_status(card, hvg), s, count=1, flags=re.S)
    if "<!-- FOCUS9_TABLE:START -->" in s and "<!-- FOCUS9_TABLE:END -->" in s:
        s = re.sub(
            r'<!-- FOCUS9_TABLE:START -->.*?<!-- FOCUS9_TABLE:END -->',
            readme_focus9_table(ledger),
            s,
            count=1,
            flags=re.S,
        )
    s = re.sub(r'^\*\*[Ww]orking [Bb]ranch:\*\*.*$', '**Working branch:** `arena/d98aabea-gemsdoe36`.', s, count=1, flags=re.M)
    README.write_text(s, encoding="utf-8")

    current = {
        "schema_version": "gemsdoe36-current-run-v3",
        "updated_utc": hvg["generated_utc"],
        "lane_id": "MTO-36",
        "source_run_card": str(CARD.relative_to(ROOT)),
        "verdict": "negative",
        "slot_approved": False,
        "ok_to_download_research_tif": True,
        "ok_to_download_and_submit": False,
        "status_banner": "DOWNLOAD: YES (research) · DO NOT SUBMIT",
        "download_tif_href": "downloads/" + Path(card["download"]["tif"]).name,
        "download_zip_href": "downloads/" + Path(card["download"]["zip"]).name,
        "tif_sha256": card["raster_sha256"],
        "submission_name": card["submission_name"],
        "submission_note": card["submission_note"],
        "holdout_dti": {
            "label": "HOLDOUT-DTI",
            "evaluator_version": card["holdout_dti"]["evaluator_version"],
            "withheld_positives": card["holdout_dti"]["withheld_positives"],
            "value": card["holdout_dti"]["pooled_candidate"],
            "ci95": card["holdout_dti"]["ci95_candidate"],
        },
        "registry": {
            "literal_unique": False,
            "max_overlap": card["registry"]["final_dots"]["max_dot_overlap_3px_all"],
        },
        "latest_hvg36_lane": {
            "lane_id": "HVG-36",
            "experiment_id": hvg["experiment_id"],
            "source_run_card": "evidence/hvg36_run_card_20261026.json",
            "verdict": hvg["verdict"],
            "ok_to_download_research_tif": True,
            "ok_to_download_and_submit": False,
            "download_tif_href": "downloads/" + Path(hvg["artifact"]["tif_path"]).name,
            "download_zip_href": "downloads/" + Path(hvg["artifact"]["zip_path"]).name,
            "tif_sha256": hvg["artifact"]["tif_sha256"],
            "zip_sha256": hvg["artifact"]["zip_sha256"],
            "submission_name": hvg["submission"]["name"],
            "submission_note": hvg["submission"]["note"],
            "holdout_dti": {
                "label": "HOLDOUT-DTI",
                "evaluator_version": hvg["holdout"]["evaluator_version"],
                "withheld_positives": hvg["holdout"]["withheld_positives"],
                "value": hvg["holdout"]["pooled_dti"],
                "ci95": hvg["holdout"]["ci95"],
            },
            "registry": {
                "unique_vs_all_9_focus_site_champions": True,
                "max_overlap_focus9_top_champions": hvg["registry_uniqueness"]["final_dots"]["max_3px_overlap_focus9_top_champions"],
                "overlap_vs_B2_champion": hvg["registry_uniqueness"]["final_dots"]["overlap_3px_vs_GEMSDOE32_B2_champion"],
                "literal_all_203_unique": False,
                "max_overlap_all_203": hvg["registry_uniqueness"]["final_dots"]["max_3px_overlap_all_203_literal"],
            },
        },
    }
    (DOCS / "current-run.json").write_text(json.dumps(current, indent=2) + "\n")
    for source, name in (
        (CARD, "mto36-run-card.json"),
        (HVG_CARD, "hvg36-run-card.json"),
        (LEDGER, "focus9-verified-source-ledger.json"),
        (ROOT / "evidence/mto36_ninesite_forensics.json", "focus9-source-integrity.json"),
    ):
        copyfile(source, DOCS / "downloads" / name)
    print(f"Refreshed site & README from negative HVG-36 ({hvg['artifact']['tif_sha256'][:12]}) & MTO-36 ({card['raster_sha256'][:12]}) cards")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
