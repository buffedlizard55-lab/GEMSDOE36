#!/usr/bin/env python3
"""Refresh the public landing/guide/status from the audited MTO-36 run card.

The historical four-lane pages stay available for audit; this builder inserts a
prominent, fail-closed CURRENT lane at the top and regenerates the nine-site
source-linked table. It cannot turn an unverified owner score into a receipt.
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
LEDGER = ROOT / "evidence/focus_sites_9repo_summary_20261026.json"
UNIQUENESS = ROOT / "evidence/focus_sites_pairwise_uniqueness_20261026.json"
README = ROOT / "README.md"
INDEX = DOCS / "index.html"
SUMMARY = DOCS / "executive-summary.html"
START = "<!-- MTO-36:START -->"
END = "<!-- MTO-36:END -->"


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


def ensure_status(card: dict, ledger: dict) -> None:
    if card["verdict"] != "negative" or card["submit_ok"] or not card["download_ok_for_research"]:
        raise RuntimeError("This release is a negative research download, not a submission authorization")
    if card["budget"]["experiments_run"] > 3 or card["elapsed_wall_seconds"] > 7200:
        raise RuntimeError("Experiment/time cap breached")
    if not card["validator_output"]["all_passed"] or not card["leakage_canary"]["passed"]:
        raise RuntimeError("Invalid research file or leakage canary")
    if len(card["submission_note"]) > 140:
        raise RuntimeError("Submission note too long")
    for row in ledger["focus_sites"]:
        if "ORGANIZER-CONFIRMED" in row["highest_historical_submission"]["score_label"]:
            raise RuntimeError("Do not call owner-reported scores organizer-confirmed")
    from hashlib import sha256

    p = ROOT / card["download"]["tif"]
    z = ROOT / card["download"]["zip"]
    if sha256(p.read_bytes()).hexdigest() != card["raster_sha256"]:
        raise RuntimeError("TIFF SHA mismatch")
    if sha256(z.read_bytes()).hexdigest() != card["download"]["zip_sha256"]:
        raise RuntimeError("ZIP SHA mismatch")


def run_status(card: dict) -> str:
    h = card["holdout_dti"]
    r = card["registry"]["final_dots"]
    return (
        f"HOLDOUT-DTI {h['pooled_candidate']:.5f} (95% CI "
        f"[{h['ci95_candidate'][0]:.5f}, {h['ci95_candidate'][1]:.5f}]; "
        f"{h['evaluator_version']}, {h['withheld_positives']:,} withheld positives); "
        f"0.14876 recorded group best, not a live score. "
        f"Overlap vs B2: {r['overlap_vs_champion_B2']:.2%}; "
        f"nine-site max {r['max_dot_overlap_3px_focus9']:.2%}; "
        f"all-entry max {r['max_dot_overlap_3px_all']:.2%}."
    )


def index_card(card: dict) -> str:
    h = card["holdout_dti"]
    r = card["registry"]["final_dots"]
    d = card["download"]
    tif, z = Path(d["tif"]).name, Path(d["zip"]).name
    return f"""{START}
    <section class="verdict verdict-bad" id="current-mto36" aria-labelledby="mto36-title">
      <div class="eyebrow">Current experiment · MTO-36 · machine-checked on 2026-10-26 UTC</div>
      <h1 id="mto36-title">DO NOT SUBMIT — original research GeoTIFF is downloadable</h1>
      <p class="verdict-sub"><strong>DOWNLOAD: YES (research) · OK TO DOWNLOAD AND SUBMIT: NO.</strong>
        The new magnetic-contact / orthogonal-gravity model is <strong>not</strong> a copy of the nine highlighted sites,
        but it does <strong>not</strong> pass the all-registry 70% overlap gate or the holdout improvement gate.
        It has no organizer score or submission-page receipt. Stop this lane; protect the weekly slot.</p>
      <div class="hero-actions">
        <a class="button" href="downloads/{e(tif)}" download>Download original TIFF · <code>{e(tif)}</code> · research only &#8595;</a>
        <a class="button secondary" href="downloads/{e(z)}" download>ZIP (single TIFF)</a>
        <a class="button secondary" href="downloads/mto36-run-card.json">Run card &amp; validators</a>
        <a class="button secondary" href="executive-summary.html">How submissions work</a>
      </div>
      <div class="table-wrap verdict-meta"><table>
        <tr><th>Submission name / verdict</th><td><code>{e(card['submission_name'])}</code> · <strong>NEGATIVE — DO NOT SUBMIT</strong></td></tr>
        <tr><th>Note ({len(card['submission_note'])} / 140 chars)</th><td><code>{e(card['submission_note'])}</code></td></tr>
        <tr><th>SHA-256</th><td><code>{e(card['raster_sha256'])}</code></td></tr>
        <tr><th>Grid &amp; range</th><td>One <code>float32</code> band, <code>EPSG:32611</code>, <code>3730 &times; 3292</code>; <code>{d['dot_count']:,}</code> original dots; zero NaN / Inf across the entire grid, all cells in <code>[0,1]</code>; CRS, shape, transform match pinned owner-mirror template. <strong>Local format PASS is not portal acceptance.</strong></td></tr>
        <tr><th>Holdout result</th><td><strong>HOLDOUT-DTI {h['pooled_candidate']:.6f}</strong> · 95% CI <code>[{h['ci95_candidate'][0]:.6f}, {h['ci95_candidate'][1]:.6f}]</code> · <code>{e(h['evaluator_version'])}</code> · <code>{h['withheld_positives']:,}</code> withheld positives. Matched raw-edge control <code>{h['pooled_control']:.6f}</code>; paired CI <code>[{h['paired_ci95'][0]:+.6f}, {h['paired_ci95'][1]:+.6f}]</code> contains zero; recorded comparable best <code>0.14876</code>.</td></tr>
        <tr><th>Strict novelty</th><td>Surface max <code>|rho|={card['registry']['surface_before_placement']['max_abs_rank_correlation']:.3f}</code> PASS. Final dots <code>{r['overlap_vs_champion_B2']:.2%}</code> vs reported B2 champion and <code>{r['max_dot_overlap_3px_focus9']:.2%}</code> max across nine focus sites; <strong>{r['max_dot_overlap_3px_all']:.2%} max across {r['n_registry_rasters_verified']} pinned comparator rasters — FAIL</strong> (uniform 5-px calibration lattice; four other dense predictions also &gt;70%). Exactly following the literal any-registry rule, this is a duplicate gate stop, not a promotion.</td></tr>
      </table></div>
      <p class="small">Historical reported <code>0.2778</code>, <code>0.3195</code> and <code>0.4413</code> are <strong>OWNER-REPORTED / not verified here</strong>. <code>ORGANIZER-CONFIRMED</code> is reserved for a saved portal receipt; none is available. <a href="research/mto36-evidence-and-nine-sites.md">Source-linked nine-site audit, limitations &amp; next steps</a>.</p>
    </section>
    <section class="section" id="source-freshness" aria-labelledby="source-freshness-title">
      <div class="section-head"><div><div class="eyebrow">Current source feed · not a score feed</div><h2 id="source-freshness-title">Nine repository activity checks</h2></div><p>Refreshes public GitHub commit timestamps in your browser. Pinned raster checks and reported competition scores do not update automatically; <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/" target="_blank" rel="noopener">view the official leaderboard directly</a>.</p></div>
      <button type="button" class="button secondary" id="refresh-source-feed">Refresh source activity</button>
      <p id="source-feed-status" role="status" aria-live="polite">Public source freshness has not been checked in this browser session.</p>
      <ul id="source-feed-list" class="source-feed-list"></ul>
    </section>
{END}"""


def executive_card(card: dict) -> str:
    d = card["download"]
    tif, z = Path(d["tif"]).name, Path(d["zip"]).name
    return f"""{START}
    <section class="verdict verdict-bad" id="current-guide" aria-labelledby="mto-guide-title">
      <div class="eyebrow">Read this first · current validated file and automatic decision</div>
      <h2 id="mto-guide-title">DOWNLOAD: YES (research) · DO NOT SUBMIT this file</h2>
      <p class="verdict-sub">MTO-36 is an <strong>original</strong> GeoTIFF on the competition grid, but the <strong>holdout and all-registry uniqueness gates failed</strong>. Its local format checks pass; no DrivenData upload or submission slot was used. Do not mistake a downloadable format-safe file for a promoted competition entry.</p>
      <div class="hero-actions"><a class="button" href="downloads/{e(tif)}" download>Download original TIFF · <code>{e(tif)}</code> · research only &#8595;</a><a class="button secondary" href="downloads/{e(z)}" download>Download ZIP</a><a class="button secondary" href="downloads/mto36-run-card.json">JSON run card &amp; validators</a></div>
      <p><strong>Name:</strong> <code>{e(card['submission_name'])}</code><br>
        <strong>Note ({len(card['submission_note'])} / 140 chars; not for use while negative):</strong> <code>{e(card['submission_note'])}</code><br>
        <strong>TIF SHA-256:</strong> <code>{e(card['raster_sha256'])}</code></p>
      <div class="table-wrap verdict-meta"><table>
        <tr><th>Current research TIFF</th><td><a href="downloads/{e(tif)}" download>{e(tif)}</a></td></tr>
        <tr><th>Score evidence (not a leaderboard estimate)</th><td><strong>HOLDOUT-DTI {card['holdout_dti']['pooled_candidate']:.6f}</strong>, 95% CI <code>[{card['holdout_dti']['ci95_candidate'][0]:.6f}, {card['holdout_dti']['ci95_candidate'][1]:.6f}]</code>, <code>{e(card['holdout_dti']['evaluator_version'])}</code>, {card['holdout_dti']['withheld_positives']:,} withheld positives.</td></tr>
        <tr><th>Unique under registry rule?</th><td><strong>NO</strong> — final 3-px overlap {card['registry']['final_dots']['max_dot_overlap_3px_all']:.2%} &gt; 70% ceiling. Research download only.</td></tr>
        <tr><th>Decision</th><td><strong>DOWNLOAD: YES (research) · DO NOT SUBMIT</strong></td></tr>
      </table></div>
      <p><a href="research/mto36-evidence-and-nine-sites.md">Read audited nine-site summary, current hypothesis and all limitations</a>. <code>ORGANIZER-CONFIRMED</code> requires a submission-page receipt; the user-supplied older scores do not satisfy this.</p>
    </section>
{END}
{site_table(json.loads(LEDGER.read_text(encoding="utf-8")))}"""


def site_table(ledger: dict, uniqueness: dict | None = None) -> str:
    if uniqueness is None:
        uniqueness = json.loads(UNIQUENESS.read_text(encoding="utf-8"))
    summaries = uniqueness["site_summary"]
    rows = []
    for item in ledger["focus_sites"]:
        h = item["highest_historical_submission"]
        novelty = summaries[item["site"]]
        rows.append(
            "<tr><td><code>{site}</code></td><td><a href=\"{link}\" target=\"_blank\" rel=\"noopener\"><code>{name}</code></a> "
            "<small>SHA-256 {sha}</small></td><td>{dots:,} dots</td><td><strong>{score:.4f} OWNER-REPORTED</strong> "
            "(receipt missing)</td><td><strong>NO</strong> · at least {min_overlap:.2%} of its dots are within 3 px of each of the other 8</td></tr>".format(
                site=e(item["site"]), link=e(h["pinned_raster_source_url"]),
                name=e(h["name"]), sha=e(h["sha256_full"][:12]), dots=h["dots"],
                score=h["score"], min_overlap=novelty["min_overlap_vs_other_eight"],
            )
        )
    return """    <section class="section" aria-labelledby="focus-sites-title">
      <div class="section-head"><div><div class="eyebrow">Pinned byte-forensics, not live receipts</div><h2 id="focus-sites-title">Nine Focus Sites — best historical owner-reported results</h2></div>
      <p>All nine historical TIFF hashes, dots and grids were rechecked from pinned GitHub snapshots. No organizer submission-page receipt was available. All nine also fail the stated 3-px uniqueness rule against each other. Do not choose an old file to resubmit.</p></div>
      <div class="table-wrap"><table><tr><th>Site</th><th>Exact pinned file for audit</th><th>Measured</th><th>Reported score (unverified)</th><th>Unique vs other 8?</th></tr>
""" + "\n".join(rows) + """
      </table></div>
      <p>Highest reported in this set: GEMSDOE32 <code>0.2778 OWNER-REPORTED</code>, but its mask is an exact D2.8 subset after removing the 200 m known-fault collar. All nine historical files fail the 70% 3-px overlap uniqueness ceiling; see the <a href="downloads/focus-sites-pairwise-uniqueness.json">72-pair audit JSON</a>. This is mask lineage, <strong>not</strong> proof that collar removal caused the blind score change. <a href="research/mto36-evidence-and-nine-sites.md">Method, data provenance and next steps</a>.</p>
    </section>"""


def readme_status(card: dict) -> str:
    h = card["holdout_dti"]
    r = card["registry"]["final_dots"]
    d = card["download"]
    return f"""<!-- STATUS:START -->
> ## CURRENT DECISION · `DOWNLOAD: YES (research)` · `DO NOT SUBMIT` · `verdict: negative`
>
> **New original MTO-36 file:** [`{Path(d['tif']).name}`]({d['tif']}) · [one-TIFF ZIP]({d['zip']}) · [validator/run card](evidence/mto36_run_card_20261026.json). **Not competition-authorized.**
> - Name: `{card['submission_name']}`. Note ({len(card['submission_note'])} / 140 characters): `{card['submission_note']}`.
> - SHA-256: `{card['raster_sha256']}`. Template, single band, CRS/shape/transform, all-grid finite `[0,1]` **PASS locally**; acceptance by DrivenData has **NOT** been tested.
> - **HOLDOUT-DTI:** `{h['pooled_candidate']:.6f}` (95% CI `[{h['ci95_candidate'][0]:.6f}, {h['ci95_candidate'][1]:.6f}]`; `{h['evaluator_version']}`, `{h['withheld_positives']:,}` withheld positives; 1.5 km buffer). Matched control `{h['pooled_control']:.6f}`; paired CI `[{h['paired_ci95'][0]:+.6f}, {h['paired_ci95'][1]:+.6f}]` crosses zero; recorded group best `0.14876` **HOLDOUT-DTI** (same evaluator, not recomputed here).
> - **Uniqueness:** surface max |rho| `{card['registry']['surface_before_placement']['max_abs_rank_correlation']:.4f}` PASS; B2 champion overlap `{r['overlap_vs_champion_B2']:.2%}`, nine focus max `{r['max_dot_overlap_3px_focus9']:.2%}`; **all {r['n_registry_rasters_verified']} references max `{r['max_dot_overlap_3px_all']:.2%}` FAIL** (synthetic calibration lattice and four dense non-focus rasters &gt;70%). **Not unique under the literal protocol. Stop; no weekly slot spent.**
> - Prior/parallel lanes: [ATVR-36](evidence/atvr36_run_card_20261026.json), [H36-CTRB](evidence/h36_ctrb_run_card_20261025.json), [H36-GPS](evidence/h36_run_card.json), [Lane36](evidence/lane36_crosscheck.json), [MOE36](evidence/moe36_run_card_20261026.json) (HOLDOUT-DTI 0.124900, strict 198-raster duplicate-flag; [report](docs/research/moe36-20261026.md)); **all negative**. [Nine-site SHA/dot crosscheck](evidence/mto36_ninesite_forensics.json) · [manual-review sources and next steps](docs/research/mto36-evidence-and-nine-sites.md).
> - Historical competition results are **OWNER-REPORTED**, not `ORGANIZER-CONFIRMED`: no submission-page receipts are archived. User-supplied public maxima `0.3195` and `0.4413` are inconsistent in date and not refreshed here. Live board: [DrivenData leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/).
<!-- STATUS:END -->"""


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


def main() -> int:
    card = json.loads(CARD.read_text(encoding="utf-8"))
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    ensure_status(card, ledger)
    insert_or_replace(INDEX, index_card(card), '<main id="main" class="wrap">')
    insert_or_replace(SUMMARY, executive_card(card), '<main id="main" class="wrap">')

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
    s = re.sub(r'<!-- STATUS:START -->.*?<!-- STATUS:END -->', readme_status(card), s, count=1, flags=re.S)
    branch = current_branch().replace("`", "")
    s = re.sub(
        r'^(\*\*Working branch:\*\* `)[^`]*(`.*)$',
        lambda match: f"{match.group(1)}{branch}{match.group(2)}",
        s,
        count=1,
        flags=re.M,
    )
    README.write_text(s, encoding="utf-8")

    current = {
        "schema_version": "gemsdoe36-current-run-v3", "updated_utc": card["generated_utc"],
        "lane_id": "MTO-36", "source_run_card": str(CARD.relative_to(ROOT)),
        "verdict": "negative", "slot_approved": False,
        "ok_to_download_research_tif": True, "ok_to_download_and_submit": False,
        "status_banner": "DOWNLOAD: YES (research) · DO NOT SUBMIT",
        "download_tif_href": "downloads/" + Path(card["download"]["tif"]).name,
        "download_zip_href": "downloads/" + Path(card["download"]["zip"]).name,
        "tif_sha256": card["raster_sha256"], "submission_name": card["submission_name"],
        "submission_note": card["submission_note"],
        "holdout_dti": {"label": "HOLDOUT-DTI", "evaluator_version": card["holdout_dti"]["evaluator_version"],
                         "withheld_positives": card["holdout_dti"]["withheld_positives"],
                         "value": card["holdout_dti"]["pooled_candidate"],
                         "ci95": card["holdout_dti"]["ci95_candidate"]},
        "registry": {"literal_unique": False,
                     "max_overlap": card["registry"]["final_dots"]["max_dot_overlap_3px_all"]},
    }
    (DOCS / "current-run.json").write_text(json.dumps(current, indent=2) + "\n")
    for source, name in (
        (CARD, "mto36-run-card.json"),
        (LEDGER, "focus9-verified-source-ledger.json"),
        (ROOT / "evidence/mto36_ninesite_forensics.json", "focus9-source-integrity.json"),
        (UNIQUENESS, "focus-sites-pairwise-uniqueness.json"),
    ):
        copyfile(source, DOCS / "downloads" / name)
    print(f"Refreshed site & README from negative MTO-36 card: {card['raster_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
