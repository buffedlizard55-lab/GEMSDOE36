#!/usr/bin/env python3
"""Build Pages from the negative preflight and archived, integrity-checked cards.

No raster generation, score projection, live slot selection, or leaderboard
scraping. The historical MTO name is retained for callers of this entrypoint.
"""
from __future__ import annotations

import hashlib
import html
import json
import subprocess
from fractions import Fraction
from pathlib import Path
from shutil import copyfile

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CARD = ROOT / "evidence/mto36_run_card_20261026.json"
HVG_CARD = ROOT / "evidence/hvg36_run_card_20261026.json"
GVSC_CARD = ROOT / "evidence/gvsc36_run_card_20261026.json"
STOP_CARD = ROOT / "evidence/registry_preflight_run_card_20261026.json"
LEDGER = ROOT / "evidence/focus_sites_9repo_summary_20261026.json"
UNIQUENESS = ROOT / "evidence/focus_sites_pairwise_uniqueness_20261026.json"
README = ROOT / "README.md"
LEADER = "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/"
PROBLEM = "https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/"
STAFF = "https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4"
G24_REVIEW = "https://github.com/buffedlizard55-lab/GEMSDOE24/blob/7ab1c8f77f0b4b8644e3929403a0dab65838b008/docs/data/current_best_review.json"
BRIEF_MARKER = "## Full standing owner brief (historical wording)"


def e(value: object) -> str:
    return html.escape(str(value), quote=True)


def current_branch() -> str:
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"], cwd=ROOT, check=True, capture_output=True, text=True
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown (detached checkout)"
    return result.stdout.strip() or "unknown (detached checkout)"


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ensure_status(card: dict, ledger: dict, hvg: dict | None = None) -> None:
    """Fail closed on archived artifact state, provenance, or changed bytes."""
    if card["verdict"] != "negative" or card["submit_ok"] or not card["download_ok_for_research"]:
        raise RuntimeError("MTO-36 release is a negative research download, not a submission authorization")
    if card["budget"]["experiments_run"] > 3 or card["elapsed_wall_seconds"] > 7200:
        raise RuntimeError("MTO-36 experiment/time cap breached")
    if not card["validator_output"]["all_passed"] or not card["leakage_canary"]["passed"]:
        raise RuntimeError("Invalid MTO-36 local research checks")
    if len(card["submission_note"]) > 140:
        raise RuntimeError("MTO-36 submission note too long")
    pairs = [(card["download"]["tif"], card["raster_sha256"]),
             (card["download"]["zip"], card["download"]["zip_sha256"])]
    if hvg is not None:
        if hvg["verdict"] != "negative" or hvg["submission"]["ok_to_submit_to_live_portal"]:
            raise RuntimeError("HVG-36 must remain a negative research download")
        if not hvg["leakage_canary"]["passed"] or not hvg["gates"]["G5_format_and_strict_0_1_valid"]:
            raise RuntimeError("Invalid HVG-36 local research checks")
        if len(hvg["submission"]["note"]) > 140:
            raise RuntimeError("HVG-36 submission note too long")
        pairs.extend([(hvg["artifact"]["tif_path"], hvg["artifact"]["tif_sha256"]),
                      (hvg["artifact"]["zip_path"], hvg["artifact"]["zip_sha256"])])
    if len(ledger["focus_sites"]) != 9:
        raise RuntimeError("Expected nine pinned historical entries")
    for row in ledger["focus_sites"]:
        label = row["highest_historical_submission"]["score_label"]
        if "ORGANIZER-CONFIRMED" in label or not any(x in label for x in ("OWNER-REPORTED", "USER-REPORTED")):
            raise RuntimeError("Historical scores must remain owner-reported or user-reported")
    for rel, expected in pairs:
        path = ROOT / rel
        if not path.is_file() or _digest(path) != expected:
            raise RuntimeError(f"Artifact SHA mismatch for {rel}")


def ensure_stop_card(stop: dict, gvsc: dict) -> None:
    """Check that a mathematical stop cannot be rendered as a promotion."""
    if (stop.get("lane_id") != "REGISTRY-PREFLIGHT-36" or stop.get("verdict") != "negative"
            or stop.get("submit_ok") is not False or stop.get("slot_selected") is not False
            or stop.get("slot_spent") is not False):
        raise RuntimeError("Current preflight must remain negative; no slot")
    c, h = stop["candidate"], stop["holdout"]
    if (c["raster_path"] is not None or c["raster_sha256"] is not None
            or h["dti"] is not None or h["ci95"] is not None or h["label"] != "NOT RUN"
            or stop["experiment_budget"]["experiments_run"] != 0):
        raise RuntimeError("Do not invent a preflight candidate or holdout")
    if len(c["planned_note"]) > 140 or len(c["planned_note"]) != c["planned_note_length"]:
        raise RuntimeError("Invalid planned note length")
    proof = stop["registry"]["literal_preflight"]
    b = proof["bound"]
    n, m, k = b["footprint_pixels"], b["covered_pixels"], b["candidate_distinct_dots"]
    u = n - m
    forced = max(0, k - u)
    if (proof["reference_id"] != "reg-052" or proof["radius_pixels"] != 3 or not 0 <= m <= n
            or not 0 < k <= n or b["uncovered_pixels"] != u or b["minimum_overlapping_dots"] != forced
            or b["threshold_fraction"] != 0.7 or b["guaranteed_duplicate"] is not True
            or Fraction(forced, k) <= Fraction(7, 10)
            or abs(b["minimum_overlap_fraction"] - forced / k) > 1e-12
            or b["first_dot_count_forced_over_threshold"] != (u * 10 // 3 + 1)):
        raise RuntimeError("Invalid literal-registry bound or stop")
    registry = json.loads((ROOT / "registry/uniqueness_registry.json").read_text())
    reference = next(x for x in registry["entries"] if x["id"] == proof["reference_id"])
    manifest = json.loads((ROOT / "registry/data_manifest.json").read_text())
    template = next(x for x in manifest["files"] if x["id"] == "sample_submission")
    if (proof["reference_sha256"] != reference["file_sha256"]
            or proof["reference_footprint_sha256"] != reference["footprint_sha256"]
            or proof["template_sha256"] != template["sha256"]):
        raise RuntimeError("Preflight reference/template hashes do not match pinned inputs")
    if (stop["registry"]["surface_rank_correlation"] is not None
            or stop["registry"]["dot_overlap"] is not None
            or not c["validator"]["status"].startswith("NOT RUN")):
        raise RuntimeError("Preflight cannot claim candidate comparisons or validation")
    if gvsc["verdict"] != "negative" or gvsc["safe_to_submit_live_slot"]:
        raise RuntimeError("GVSC-36 must remain research-only")
    sub = gvsc["submission"]
    for name, expected in ((sub["zeros_filename"], sub["raster_sha256"]),
                           (sub["zip_archive_name"], sub["zip_sha256"])):
        if _digest(DOCS / "downloads" / name) != expected:
            raise RuntimeError(f"GVSC-36 artifact mismatch: {name}")


def additional_archives() -> list[dict]:
    """Preserve older downloads without treating a self-promotion as approval."""
    def read(rel: str) -> dict:
        return json.loads((ROOT / rel).read_text())

    wdp = read("evidence/wdp36_run_card_20261026.json")
    moe = read("evidence/moe36_run_card_20261026.json")
    atvr = read("evidence/atvr36_run_card_20261026.json")
    ctrb = read("evidence/h36_ctrb_run_card_20261025.json")
    gps = read("evidence/h36_run_card.json")
    lane = read("docs/downloads/lane36_run_card.json")
    lane_crosscheck = read("evidence/lane36_crosscheck.json")
    if any(x["verdict"] != "negative" for x in (wdp, moe, atvr, ctrb, gps)):
        raise RuntimeError("Archived research lane unexpectedly promoted")
    if (lane["verdict"] != "promote" or lane["ok_to_submit"] is not True
            or lane_crosscheck["final_dot_uniqueness_passed"] is not False
            or lane_crosscheck["max_competing_dot_overlap"] <= 0.70
            or lane["raster"]["sha256"] != lane_crosscheck["sha256"]):
        raise RuntimeError("Lane36 self-promotion / independent duplicate conflict changed")
    cs, gr = ctrb["submission"], gps["raster"]
    records = [
        {"lane": "WDP-36", "file": wdp["submission_file"], "sha256": wdp["raster_sha256"], "zip": wdp["submission_zip"], "zip_sha256": wdp["zip_sha256"], "card": "gemsdoe36-wdp36-exp1-20261026-zeros.receipt.json"},
        {"lane": "MOE36", "file": "gemsdoe36-moe36-exp1-20261026-zeros.tif", "sha256": moe["raster_sha256"], "zip": "gemsdoe36-moe36-exp1-20261026-zeros.zip", "zip_sha256": moe["zip_sha256"], "card": "moe36-run-card.json"},
        {"lane": "ATVR-36", "file": "gemsdoe36-atvr36-20261026.tif", "sha256": atvr["raster_sha256"], "zip": "gemsdoe36-atvr36-20261026.zip", "zip_sha256": atvr["zip_sha256"], "card": "atvr36-run-card.json"},
        {"lane": "H36-CTRB", "file": cs["zeros_filename"], "sha256": cs["raster_sha256"], "zip": cs["zip_archive_name"], "zip_sha256": cs["zip_sha256"], "card": "run_card.json"},
        {"lane": "H36-GPS", "file": Path(gr["zeros_tif"]).name, "sha256": gr["zeros_sha256"], "zip": Path(gr["zip"]).name, "zip_sha256": gr["zip_sha256"], "card": "gemsdoe36-h36-gps-graben-pair-20261026-bb29ce2a4bb4-run-card.json"},
        {"lane": "Lane36", "file": lane["raster"]["file"], "sha256": lane["raster"]["sha256"], "zip": None, "zip_sha256": None, "card": "lane36_run_card.json"},
    ]
    for item in records:
        for name, expected in ((item["file"], item["sha256"]), (item["zip"], item["zip_sha256"])):
            if name is not None and (not (DOCS / "downloads" / name).is_file() or _digest(DOCS / "downloads" / name) != expected):
                raise RuntimeError(f"Archived artifact SHA mismatch: {name}")
        if not (DOCS / "downloads" / item["card"]).is_file():
            raise RuntimeError(f"Missing archived card: {item['card']}")
        item["submit_ok"] = False
    for source, mirror in (
        ("evidence/wdp36_run_card_20261026.json", "gemsdoe36-wdp36-exp1-20261026-zeros.receipt.json"),
        ("evidence/moe36_run_card_20261026.json", "moe36-run-card.json"),
        ("evidence/atvr36_run_card_20261026.json", "atvr36-run-card.json"),
        ("evidence/h36_ctrb_run_card_20261025.json", "run_card.json"),
        ("evidence/h36_run_card.json", "gemsdoe36-h36-gps-graben-pair-20261026-bb29ce2a4bb4-run-card.json"),
    ):
        if (ROOT / source).read_bytes() != (DOCS / "downloads" / mirror).read_bytes():
            raise RuntimeError(f"Archived run-card mirror mismatch: {mirror}")
    # Preserve the NaN variants' old integrity checks, without promoting them.
    for name, expected in ((cs["companion_nan_name"], cs["companion_nan_sha256"]),
                           (Path(gr["nan_tif"]).name, gr["nan_sha256"])):
        if _digest(DOCS / "downloads" / name) != expected:
            raise RuntimeError(f"Archived NaN variant SHA mismatch: {name}")
    return records


def site_table(ledger: dict) -> str:
    """Historical file evidence, not a current roster or upload authorization."""
    audit = json.loads(UNIQUENESS.read_text())["site_summary"]
    rows = []
    for item in ledger["focus_sites"]:
        hist = item["highest_historical_submission"]
        site = item["site"]
        label = "USER-REPORTED" if hist["score_label"].startswith("USER-REPORTED") else "OWNER-REPORTED"
        overlap = audit[site]["max_overlap_vs_other_eight"] * 100
        rows.append(
            f'<tr><th scope="row">{e(site)}</th><td><a href="{e(hist["pinned_raster_source_url"])}">'
            f'{e(hist["name"])}</a><br><small>SHA-256 {e(hist["sha256_full"][:12])}… · '
            f'{hist["dots"]:,} dots</small></td><td><strong>{hist["score"]:.4f} {label}</strong>'
            f'</td><td><strong>NO</strong> · {overlap:.2f}% max directed overlap vs another pinned site</td></tr>'
        )
    return ('<div class="table-wrap"><table><thead><tr><th>Site</th><th>Pinned historical TIFF / SHA-256</th>'
            '<th>Reported score, no receipt</th><th>Uniqueness vs other 8 pinned sites</th></tr></thead>'
            '<tbody>' + ''.join(rows) + '</tbody></table></div>')


def readme_table(ledger: dict) -> str:
    audit = json.loads(UNIQUENESS.read_text())["site_summary"]
    rows = ["| Site | Pinned historical TIFF (SHA-12) | Reported score | Max 3-px overlap vs 8 |",
            "|---|---|---:|---:|"]
    for row in ledger["focus_sites"]:
        h = row["highest_historical_submission"]
        lab = "USER-REPORTED" if h["score_label"].startswith("USER-REPORTED") else "OWNER-REPORTED"
        pct = audit[row["site"]]["max_overlap_vs_other_eight"] * 100
        rows.append(f'| {row["site"]} | [{h["name"]}]({h["pinned_raster_source_url"]}) '
                    f'(`{h["sha256_full"][:12]}`) | {h["score"]:.4f} {lab} | {pct:.2f}% — NO |')
    return '\n'.join(rows)


def header(title: str) -> str:
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="GEMSDOE36: evidence-led geothermal fault research and a fail-closed submission decision.">
<title>{e(title)} · GEMS DOE 36</title><link rel="stylesheet" href="assets/site.css"></head>
<body><a class="skip-link" href="#main">Skip to main content</a>
<header class="site-header"><a class="brand" href="index.html"><span class="brand-mark" aria-hidden="true">36</span><span>GEMS DOE <span class="small">/ 36</span></span></a>
<nav class="nav" aria-label="Main navigation"><a href="index.html">Decision</a><a href="executive-summary.html">Executive guide</a><a href="research/registry-preflight-20261026.md">Evidence &amp; research</a><a href="{LEADER}" target="_blank" rel="noopener">Official leaderboard ↗</a></nav></header><main id="main" class="wrap">'''


FOOTER = f'''</main><footer class="site-footer wrap"><div class="footer-row"><p>GEMSDOE36 · <strong>Maximize P(Win)</strong> &amp; <strong>Own the Outcome</strong> · <a href="AI_DISCLOSURE.md">AI disclosure</a></p><p>Independent research; not affiliated with DOE, USGS or DrivenData. <a href="{PROBLEM}">Official specification</a></p></div></footer></body></html>'''


def archive_section(mto: dict, hvg: dict, gvsc: dict) -> str:
    gs = gvsc["submission"]
    records = [
        ("GVSC-36 EXP-3", gs["zeros_filename"], gs["zip_archive_name"], gs["raster_sha256"],
         gs["note"], "0.158855", "[0.145456, 0.173084]", "99.6176%", "gvsc36-run-card.json"),
        ("HVG-36 EXP-1", Path(hvg["artifact"]["tif_path"]).name, Path(hvg["artifact"]["zip_path"]).name,
         hvg["artifact"]["tif_sha256"], hvg["submission"]["note"], "0.135759", "[0.123271, 0.148461]", "100%", "hvg36-run-card.json"),
        ("MTO-36 E1", Path(mto["download"]["tif"]).name, Path(mto["download"]["zip"]).name,
         mto["raster_sha256"], mto["submission_note"], "0.067611", "[0.058449, 0.077867]", "100%", "mto36-run-card.json"),
    ]
    parts = []
    for lane, tif, zipname, sha, note, score, ci, overlap, card in records:
        parts.append(f'''<article class="card archive-card"><span class="card-kicker">{e(lane)} · negative</span>
<h3>HOLDOUT-DTI {score}</h3><p>95% CI {ci} · gems-segment-pooled-v1 · 60,988 withheld positives.
{overlap} of dots within 3 px of the registered lattice. Not a leaderboard score.</p>
<p><a href="downloads/{e(tif)}" download>{e(tif)}</a> · <a href="downloads/{e(zipname)}" download>ZIP</a> · <a href="downloads/{e(card)}">Run card</a></p>
<details><summary>Artifact hash and historical note (not for submission)</summary><p>SHA-256: <code>{e(sha)}</code><br>Note: <code>{e(note)}</code></p></details></article>''')
    others = []
    for item in additional_archives():
        zip_link = f' · <a href="downloads/{e(item["zip"])}" download>ZIP</a>' if item["zip"] else ""
        others.append(f'<li><strong>{e(item["lane"])}</strong> · <a href="downloads/{e(item["file"])}" download>{e(item["file"])}</a>{zip_link} · <a href="downloads/{e(item["card"])}">historical card</a> · DO NOT SUBMIT</li>')
    return '''<section class="section" id="archive"><div class="section-head"><div><span class="eyebrow">Prior work</span><h2>Research downloads only</h2></div><p>These are historical artifacts, not new unique submissions. DO NOT SUBMIT.</p></div>
<div class="grid cols-3">''' + ''.join(parts) + '''</div><p class="fine-print">GVSC also has a protocol-order flaw and partial prior-hypothesis overlap. Prior zeros-only TIFFs pass local full-grid range checks but their run cards report that they do not meet the official outside-NaN profile. No organizer acceptance is established.</p><details><summary>More archived research downloads</summary><p>All are research-only. Lane36's old card says promote, but the <a href="downloads/lane36-crosscheck.json">independent expanded-registry crosscheck</a> found 93.17% overlap, so it is not approved.</p><ul>''' + ''.join(others) + '''</ul></details></section>'''


def context_section(ledger: dict) -> str:
    return f'''<section class="section" id="nine-sites"><div class="section-head"><div><span class="eyebrow">Pinned forensic snapshot</span><h2>Nine historical sites</h2></div><p>The TIFFs and counts were rechecked; the scores have no archived submission-page receipts. This is not a current complete inventory.</p></div>
<p>All nine public <code>main</code> refs had changed relative to this snapshot on 26 October 2026. A changed ref does not prove a new raster; refresh the inventory before a full novelty audit. Maximum overlap is directional, candidate → comparator, within 3 pixels.</p>
<!-- FOCUS9_EXEC:START -->{site_table(ledger)}<!-- FOCUS9_EXEC:END -->
<p>GEMSDOE32's <strong>0.2778 OWNER-REPORTED</strong> is the highest of these pinned owner/user-reported numbers, not a verified competition receipt. Its B2 mask is exactly D2.8 with pixels ≤2 px from the visible catalogue removed; hidden false positives and causality are unknown. <a href="research/registry-preflight-20261026.md">Read the full explanation and limitations →</a></p></section>'''


def feed_section() -> str:
    return '''<section class="section" id="source-feed"><div class="section-head"><div><span class="eyebrow">Public repository activity</span><h2>Source freshness</h2></div><p>Live GitHub commit checks compare the nine public main refs with the pinned audit. They do not verify new TIFFs or scores.</p></div>
<button class="button secondary" type="button" id="refresh-source-feed">Refresh public source refs</button><p id="source-feed-status" role="status" aria-live="polite">Checking public source refs…</p><ul id="source-feed-list"></ul>
<p class="fine-print">GitHub rate limits or network restrictions can make this unavailable. The <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">official leaderboard</a> is checked manually, not scraped by this site.</p></section>'''


def index_page(stop: dict, mto: dict, hvg: dict, gvsc: dict, ledger: dict) -> str:
    b = stop["registry"]["literal_preflight"]["bound"]
    return header("Decision and evidence") + f'''<section class="hero"><div><span class="eyebrow">DOE GEMS · audit 26 October 2026</span><h1>A clear answer before a costly submission.</h1>
<p class="lede">We reviewed nine related projects and tested the literal novelty rule. At the standard dot budget, the rule blocks every possible placement.</p>
<div class="hero-actions"><a class="button" href="executive-summary.html">Read the executive guide →</a><a class="button secondary" href="downloads/registry-preflight-run-card.json">View the negative run card</a></div></div>
<aside class="status-card" aria-label="Current submission decision"><span class="eyebrow"><span class="status-pip"></span>Current decision</span><h2>DO NOT SUBMIT</h2><p>No new candidate TIFF was created, no holdout was run, and no weekly slot was selected or spent.</p><a href="research/registry-preflight-20261026.md">Why the run stopped →</a></aside></section>
<div class="download-strip"><div><strong>DOWNLOAD: YES — Research downloads only · DO NOT SUBMIT</strong><p>Prior research files remain available for inspection. None is an approved competition entry.</p></div><a class="button warning" href="#archive">Browse research files</a></div>
<section class="section"><div class="section-head"><div><span class="eyebrow">The limiting evidence</span><h2>The gate is impossible at this budget.</h2></div><p>Thresholds were not relaxed and dots were not moved to evade the registry.</p></div>
<div class="grid cols-3"><article class="card"><span class="card-kicker">Footprint covered by lattice</span><h3>{b['covered_pixels']:,} / {b['footprint_pixels']:,}</h3><p>Only {b['uncovered_pixels']:,} pixels lie more than 3 px from registered lattice dots.</p></article>
<article class="card"><span class="card-kicker">Any {b['candidate_distinct_dots']:,}-dot candidate</span><h3>≥ {b['minimum_overlap_fraction']*100:.2f}% overlap</h3><p>At least {b['minimum_overlapping_dots']:,} dots must overlap the lattice's 3-pixel neighborhood; the stop is &gt;70%.</p></article>
<article class="card"><span class="card-kicker">Bound begins</span><h3>{b['first_dot_count_forced_over_threshold']:,} dots</h3><p>Above this count the proof forces a stop. Smaller outputs are not automatically unique.</p></article></div>
<p><a href="research/registry-preflight-20261026.md">See the proof, inputs and ranked hypotheses →</a></p></section>
{archive_section(mto,hvg,gvsc)}
<section class="section"><div class="section-head"><div><span class="eyebrow">Context, not a projection</span><h2>Evidence is not a leaderboard estimate.</h2></div></div>
<p>GVSC's recorded local HOLDOUT-DTI 0.158855 exceeds HVG's 0.135759, but GVSC fails uniqueness and protocol order. <a href="{G24_REVIEW}">GEMSDOE24's newer review</a> records HOLDOUT-DTI 0.1637924 [0.150446, 0.177390] with the same named evaluator and 60,988 withheld positives; it explicitly does not independently certify protocol, paired gain or novelty. These are not calibrated forecasts.</p>
<p>The <a href="{LEADER}">official public leaderboard</a> showed 0.4437 on a manual read on 26 October 2026; this observation may be stale and is not a team receipt. <strong>ORGANIZER-CONFIRMED</strong> is reserved for a submission-page receipt, which is not archived here.</p></section>
{context_section(ledger)}{feed_section()}<script defer src="assets/live-feed.js"></script>''' + FOOTER


def executive_page(stop: dict, mto: dict, hvg: dict, gvsc: dict, ledger: dict) -> str:
    return header("Executive summary and submission guide") + f'''<section class="hero compact-hero"><div><span class="eyebrow">Decision brief · 26 October 2026</span><h1>What to submit? Nothing yet.</h1><p class="lede">No new unique GeoTIFF or new holdout result exists from this continuation. The numerical preflight is a stop, not an exception.</p></div><aside class="status-card"><span class="eyebrow">Current status</span><h2>DO NOT SUBMIT</h2><p>DOWNLOAD: YES — Research downloads only. No real weekly slot was selected or spent.</p><a href="downloads/registry-preflight-run-card.json">Machine-readable run card →</a></aside></section>
<section class="section"><div class="section-head"><div><span class="eyebrow">For the decision-maker</span><h2>Evidence at a glance</h2></div></div>
<p><strong>Planned identifier, not created:</strong> <code>{e(stop["candidate"]["planned_name"])}</code><br><strong>Draft note ({stop["candidate"]["planned_note_length"]}/140 characters, not for upload):</strong> <code>{e(stop["candidate"]["planned_note"])}</code></p>
<ol><li><strong>Historical leader:</strong> 0.2778 OWNER-REPORTED for GEMSDOE32 B2, with no archived receipt tying a score to exact bytes. A different public participant led at 0.4437 on a manual 26 October read; <a href="{LEADER}">check current standings</a>.</li>
<li><strong>Current release:</strong> none. At 37,654 distinct dots the 5-px registered lattice forces ≥82.34% directed 3-px overlap, exceeding the literal &gt;70% stop. No previous raster is being passed off as a unique replacement.</li>
<li><strong>Why B2 may have improved:</strong> it exactly removes 6,436 near-catalogue dots from D2.8. Pruning may reduce false positives, but unobserved labels and uploaded-file identity prevent a causal conclusion. <a href="{STAFF}">Staff clarify</a> that known faults are masked pixel-exactly and new truth can lie close by.</li>
<li><strong>Research value:</strong> GVSC recorded HOLDOUT-DTI 0.158855 [0.145456, 0.173084] and HVG 0.135759 [0.123271, 0.148461], each <code>gems-segment-pooled-v1</code>, 60,988 withheld positives; both fail the literal gate. <a href="{G24_REVIEW}">GEMSDOE24 DPRF1</a> records 0.1637924 [0.150446, 0.177390], same named evaluator/positive count, but its review does not independently certify protocol or paired gain.</li></ol>
<p>Scores above are not estimates of a new candidate. <strong>ORGANIZER-CONFIRMED</strong> requires a receipt, and none of the historical scores has one here.</p></section>
{context_section(ledger)}
<section class="section"><div class="section-head"><div><span class="eyebrow">Submission guide</span><h2>When a future file can be considered</h2></div></div>
<ol><li>Resolve the registry/budget blocker with a scientifically justified plan, not threshold changes or lattice-hole targeting. Refresh all nine pinned inventories and the full registry. A non-failing feasibility bound is not a uniqueness pass.</li>
<li>Use one preregistered lane and the shared feature stack, evaluator and writer. Screen the surface against every registry raster <em>before</em> placement and final dots afterward; stop on |rank correlation| &gt;0.90 or &gt;70% within 3 px of any entry.</li>
<li>For holdout, hide whole fault segments with buffer, derive catalogue features from visible faults only, mask visible pixels exactly, test each feature for AUC leakage and pool DTI using α=0.2, β=0.8 and a 300 m triangular kernel. Record evaluator, positives and 95% CI.</li>
<li>Validate the real file automatically: a <strong>single-band GeoTIFF (.tif)</strong>, float32, correct CRS, shape, and geotransform, all predicted values finite and within [0,1] as applicable, plus official null/NaN outside-footprint requirements. A <strong>.zip file containing a single GeoTIFF</strong> is also allowed. Resolve the full-array-vs-outside-NaN ambiguity from the authorized sample/organizer guidance; do not claim portal acceptance from a local check. A prior portal message was “Predicted values must be in range [0, 1]”. See the <a href="{PROBLEM}">official format and metric</a>.</li>
<li>Record the SHA-256, validator output, run card and ≤140-character note. Only a separate selector can choose a live upload; official rules allow three weekly slots and one submission for both prize rounds. None is selected now. The official competition page listed 3 December 2026, 23:59 UTC as the deadline when checked on 26 October; recheck the <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">competition page</a>, <a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">rules</a> and AI disclosure.</li></ol>
<p><a href="research/registry-preflight-20261026.md">Four ranked prospective hypotheses, data sources and full preflight →</a></p></section>{archive_section(mto,hvg,gvsc)}<script defer src="assets/live-feed.js"></script>''' + FOOTER


def update_readme(stop: dict, ledger: dict) -> None:
    original = README.read_text(encoding="utf-8")
    if BRIEF_MARKER not in original:
        raise RuntimeError("Cannot rewrite README without preserving the standing owner brief")
    standing = original[original.index(BRIEF_MARKER):]
    intro = f'''# GEMSDOE36 — current decision & reproducible research

**Read this decision and the [standing owner brief](#full-standing-owner-brief-historical-wording) at the start of every session.** Core values: **Maximize P(Win)** and **Own the Outcome**.

> ## CURRENT DECISION · DO NOT SUBMIT · negative
>
> **No new candidate TIFF, surface, holdout result, slot selection or submission.** The literal registry includes a 5-pixel lattice that covers 5,160,724 of 5,167,373 footprint pixels within 3 px. At the standard 37,654-dot budget at least 31,005 / 37,654 = **82.34185%** must overlap it, exceeding the &gt;70% stop; the proof first forces a stop at 22,164 dots. A smaller count is not automatically unique. Do not target the uncovered pixels or silently exempt controls. [Run card](evidence/registry_preflight_run_card_20261026.json) · [proof and ranked hypotheses](docs/research/registry-preflight-20261026.md) · [three review passes](evidence/registry_preflight_review_passes_20261026.md).
>
> **Research downloads only:** [GVSC-36 EXP-3 TIFF](docs/downloads/gemsdoe36-gvsc36-exp3-20261026-5fb822bdfb60-zeros.tif), [ZIP](docs/downloads/gemsdoe36-gvsc36-exp3-20261026-5fb822bdfb60-zeros.zip), [card](evidence/gvsc36_run_card_20261026.json); [HVG-36 EXP-1 TIFF](docs/downloads/gemsdoe36-hvg36-vent-dipole-20261026-b3ee97873192-zeros.tif), [card](evidence/hvg36_run_card_20261026.json); [MTO-36 TIFF](docs/downloads/gemsdoe36-mto36-ortho-contact-20261026-c41282e9da7a-zeros.tif), [card](evidence/mto36_run_card_20261026.json). All are **DO NOT SUBMIT**. GVSC's 99.6176% lattice overlap and post-placement surface check are blocking.
>
> GVSC recorded **HOLDOUT-DTI 0.158855** [0.145456, 0.173084]; HVG **HOLDOUT-DTI 0.135759** [0.123271, 0.148461], both `gems-segment-pooled-v1`, 60,988 withheld positives. Neither is a leaderboard projection. A newer [GEMSDOE24 DPRF1 review]({G24_REVIEW}) records **HOLDOUT-DTI 0.1637924** [0.150446, 0.177390], same named evaluator and positives, but does not independently certify protocol/paired gain/novelty; do not call the old 0.14876 the current group record or assume matched comparability.

## Nine-site executive summary — pinned historical snapshot

The TIFF links and masks are rehashed; no historical score has an archived organizer receipt and pinned bytes do not prove which file was uploaded. All nine main refs changed since the snapshot ([freshness receipt](evidence/source_freshness_20261026.json)); the table is **not** a current complete raster inventory. All nine historical masks fail the literal pairwise rule against at least one other pinned site. GEMSDOE32 B2 is exactly D2.8 with 6,436 catalogue-near dots removed; why its **0.2778 OWNER-REPORTED** score resulted cannot be proven without hidden labels and a receipt. Nearby new truth can be penalized, because the [organizer's mask is pixel-exact]({STAFF}).

<!-- FOCUS9_TABLE:START -->
{readme_table(ledger)}
<!-- FOCUS9_TABLE:END -->

The public [leaderboard]({LEADER}) showed **0.4437** on a manual 2026-10-26 read, not a team receipt and not necessarily current. Never call a historical score `ORGANIZER-CONFIRMED` without its submission-page receipt. No calibrated leaderboard estimate is available for a nonexistent candidate.

## Reproduce and review

```bash
python scripts/restore_data.py --group core
python scripts/restore_data.py --group scored
python scripts/registry_feasibility.py --dots 37654  # exit 2: guaranteed duplicate; 0: NOT proven; 1: error
python scripts/build_site.py
python scripts/check_site.py
python scripts/verify_gvsc36_release.py
python scripts/verify_mto_release.py
pytest -q
ruff check src scripts tests
```

For the pinned nine-site forensic rerun, run `python scripts/cache_focus9_audit.py` to fetch the ten SHA-verified comparison TIFFs at their pinned commits, then run `python scripts/audit_focus_sources.py` and `python scripts/audit_focus_uniqueness.py`. Owner-mirror hash verification is not organizer authentication. Prior all-finite TIFFs pass a local whole-grid range check but their cards flag noncompliance with the official outside-NaN profile; portal acceptance is unknown. The [site](docs/index.html) and [executive guide](docs/executive-summary.html) have the current negative decision. No automated leaderboard monitor is shipped.

**Next:** reconcile the budget/rule conflict without relaxing the user's protocol; refresh the registry, then perform a preregistered one-lane, leakage-canary and buffered whole-segment holdout with every surface/final-dot comparison, a real raster validator and a separate slot selector. Do not spend a slot to test a known duplicate.

---

'''
    README.write_text(intro + standing, encoding="utf-8")


def main() -> int:
    mto, hvg, gvsc, stop, ledger = (json.loads(p.read_text(encoding="utf-8")) for p in
                                   (CARD, HVG_CARD, GVSC_CARD, STOP_CARD, LEDGER))
    ensure_status(mto, ledger, hvg)
    ensure_stop_card(stop, gvsc)
    for source, target in (
        (STOP_CARD, DOCS / "downloads/registry-preflight-run-card.json"),
        (CARD, DOCS / "downloads/mto36-run-card.json"),
        (HVG_CARD, DOCS / "downloads/hvg36-run-card.json"),
        (GVSC_CARD, DOCS / "downloads/gvsc36-run-card.json"),
        (LEDGER, DOCS / "downloads/focus9-verified-source-ledger.json"),
        (UNIQUENESS, DOCS / "downloads/focus-sites-pairwise-uniqueness.json"),
        (ROOT / "evidence/mto36_ninesite_forensics.json", DOCS / "downloads/focus9-source-integrity.json"),
        (ROOT / "evidence/lane36_crosscheck.json", DOCS / "downloads/lane36-crosscheck.json"),
        (ROOT / "evidence/moe36_run_card_20261026.json", DOCS / "downloads/moe36-run-card.json"),
        (ROOT / "evidence/atvr36_run_card_20261026.json", DOCS / "downloads/atvr36-run-card.json"),
    ):
        copyfile(source, target)
    snapshot = json.loads((ROOT / "registry/priority_source_snapshot.json").read_text())
    refs = {x["repo"].split("/")[-1]: x["ref"] for x in snapshot["sources"]}
    (DOCS / "data").mkdir(exist_ok=True)
    (DOCS / "data/focus-refs.json").write_text(json.dumps(refs, indent=2) + "\n")
    current = {
        "schema": "gemsdoe36.current-run.v3", "lane_id": stop["lane_id"], "verdict": "negative",
        "slot_approved": False, "ok_to_download_and_submit": False, "research_downloads_only": True,
        "tif_path": None, "tif_sha256": None, "holdout_dti": None,
        "run_card": "downloads/registry-preflight-run-card.json", "run_card_sha256": _digest(STOP_CARD),
        "registry_preflight": stop["registry"]["literal_preflight"]["bound"],
    }
    (DOCS / "current-run.json").write_text(json.dumps(current, indent=2) + "\n")
    manifest = {"schema": "gemsdoe36.research-downloads.v3", "slot_approved": False,
                "current_candidate": None, "run_card": "registry-preflight-run-card.json",
                "archived_research_only": [
                    {"file": gvsc["submission"]["zeros_filename"], "sha256": gvsc["submission"]["raster_sha256"], "submit_ok": False},
                    {"file": Path(hvg["artifact"]["tif_path"]).name, "sha256": hvg["artifact"]["tif_sha256"], "submit_ok": False},
                    {"file": Path(mto["download"]["tif"]).name, "sha256": mto["raster_sha256"], "submit_ok": False},
                ] + additional_archives()}
    (DOCS / "downloads/submissions_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (DOCS / "index.html").write_text(index_page(stop, mto, hvg, gvsc, ledger), encoding="utf-8")
    (DOCS / "executive-summary.html").write_text(executive_page(stop, mto, hvg, gvsc, ledger), encoding="utf-8")
    update_readme(stop, ledger)
    print("Built Pages and README: literal-registry preflight NEGATIVE; no candidate or slot")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
