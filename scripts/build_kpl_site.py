#!/usr/bin/env python3
"""Update GitHub Pages + README + manifests from the verified KPL-36 run card.

Schema v5 current-run supersedes the BDC-36 v4 / registry-preflight v3 manifests,
preserved verbatim under ``previous_current_run_v4_BDC36``. Restores the pinned
nine-site table (``build_mto_site.site_table``) and archived-artifact identities
that the compact post-merge pages dropped, so ``scripts/check_site.py`` invariants
hold again. Fail-closed: a submit-positive banner renders only if the run card
verdict is ``promote`` AND all preregistered gates are true. Text/JSON only.
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
from build_mto_site import parallel_dw_projection, site_table  # noqa: E402

CARD = ROOT / "evidence/kpl36_run_card_20261026.json"
CROSS = ROOT / "evidence/kpl36_crosscheck_20261026.json"
EST = ROOT / "evidence/kpl36_score_estimate_20261026.json"
PREV_BDC = ROOT / "evidence/previous_current_run_bdc36_20261026.json"
INDEX = DOCS / "index.html"
SUMMARY = DOCS / "executive-summary.html"
CURRENT = DOCS / "current-run.json"
MANIFEST = DOCS / "downloads/submissions_manifest.json"
README = ROOT / "README.md"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load(p: Path) -> dict:
    return json.loads(p.read_text())


def upsert(text: str, start: str, end: str, block: str, anchor: str, where: str = "after") -> str:
    if start in text and end in text:
        return re.sub(re.escape(start) + r".*?" + re.escape(end), lambda m: block, text, flags=re.S)
    if anchor not in text:
        raise RuntimeError(f"anchor not found: {anchor[:60]}")
    return text.replace(anchor, (anchor + "\n" + block) if where == "after" else (block + "\n" + anchor), 1)


def main() -> int:
    card = load(CARD)
    cross = load(CROSS)
    est = load(EST)
    verdict = card["verdict"]
    gates = card["gates"]
    promote = verdict == "promote"
    if promote and not all(gates.values()):
        raise RuntimeError(f"FAIL-CLOSED: verdict=promote but gates={gates}")
    sub = card["submission"]
    tif_rel = sub["file"].removeprefix("docs/")
    zip_rel = sub["zip"].removeprefix("docs/")
    if sha(ROOT / sub["file"]) != sub["sha256"] or sha(ROOT / sub["zip"]) != sub["zip_sha256"]:
        raise RuntimeError("FAIL-CLOSED: submission artifact hash mismatch vs run card")
    if len(sub["note"]) > 140:
        raise RuntimeError("submission note exceeds 140 characters")
    best = card["best_arm"]
    h = card["holdout"]
    scen = est["scenarios"]
    est_range = (
        f"{scen['novel_credit_0.03']['estimated_DTI_if_credit_assumptions_hold']:.3f}–"
        f"{scen['novel_credit_0.13']['estimated_DTI_if_credit_assumptions_hold']:.3f}"
    )
    est_mid = scen["novel_credit_0.07"]["estimated_DTI_if_credit_assumptions_hold"]
    arms_rows = "".join(
        f"<tr><td><code>{a}</code></td><td>{v['dti']:.6f}</td><td>[{v['ci95'][0]:.4f}, {v['ci95'][1]:.4f}]</td></tr>"
        for a, v in h["arms"].items()
    )
    champ_html = "".join(
        f"<tr><td><code>{site}</code></td><td>{r['owner_reported_score']}</td>"
        f"<td>{(r['candidate_dot_overlap_within_3px'] or 0):.3f}</td>"
        f"<td>{'UNIQUE (≤0.70)' if (r['candidate_dot_overlap_within_3px'] or 0) <= 0.70 else 'DUPLICATE (>0.70)'}</td></tr>"
        for site, r in sorted(cross["final_dots"]["champion_overlap_by_site"].items())
    )
    banner = (
        "✅ OK TO SUBMIT — passed every preregistered automated gate (spend ONE weekly slot on this file)"
        if promote
        else "⛔ DO NOT SUBMIT — automated gate failed; research download only"
    )
    block = f"""<!-- KPL36:START -->
<section class="hero compact-hero" id="kpl36-release" aria-label="KPL-36 current decision">
<div>
<span class="eyebrow">GEMS DOE 36 · KPL-36 current decision · 26 October 2026 · verdict: {verdict} · DOWNLOAD: YES</span>
<h1>{'Download &amp; submit this unique TIF' if promote else 'KPL-36 research result — not for submission'}</h1>
<p class="lede"><strong>{banner}.</strong> File <code>{html.escape(Path(sub['file']).name)}</code> · {sub['dots']:,} dots · single-band float32 GeoTIFF, EPSG:32611, grid identical to the sample submission, whole-array values in [0,1] with zeros outside the footprint (cannot trigger the portal <em>“Predicted values must be in range [0, 1]”</em> error) · SHA-256 <code>{sub['sha256']}</code>. Every other file on this site: <strong>DO NOT SUBMIT</strong>.</p>
<div class="hero-actions">
<a class="button" href="{html.escape(tif_rel)}" download>⬇ Download submission GeoTIFF</a>
<a class="button secondary" href="{html.escape(zip_rel)}" download>ZIP (single GeoTIFF)</a>
<a class="button secondary" href="downloads/kpl36-run-card.json">JSON run card</a>
<a class="button secondary" href="research/kpl36-20261026.md">KPL-36 monograph &amp; 9-site audit →</a>
</div>
<p><strong>Unique name:</strong> <code>{html.escape(sub['name'])}</code><br>
<strong>Copy-paste submission Note</strong> ({sub['note_characters']}/140 chars): <code>{html.escape(sub['note'])}</code></p>
</div>
<aside class="status-card" aria-label="KPL-36 evidence summary"><span class="eyebrow">Why this file — measured evidence</span>
<p style="font-size:.93rem"><strong>HOLDOUT-DTI {h['arms'][best]['dti']:.6f}</strong> [{h['arms'][best]['ci95'][0]:.4f}, {h['arms'][best]['ci95'][1]:.4f}] (gems-segment-pooled-v1, {h['n_withheld_positive_pixels']:,} withheld positives) vs B0 {h['arms']['B0']['dti']:.6f} and GVSC replication {h['arms']['C-GVSC']['dti']:.6f}; leakage canary ≤0.6344. Internal hide-and-recover figure, not a leaderboard score.<br>
<strong>Scenario estimate {est_range}</strong> (mid {est_mid:.3f}; assumptions in the monograph; novel-dot credit ≥{est['novel_credit_needed_to_match_0.2778']:.3f} would be needed to match the historical champion score discussed below — no organizer receipt exists yet for KPL-36).<br>
<strong>Uniqueness:</strong> max 3-px dot overlap vs the nine focus-site champions = {cross['final_dots']['max_champion_3px_overlap']:.3f} (vs GEMSDOE32-B2 = {cross['final_dots']['overlap_vs_GEMSDOE32_B2_3px']:.3f}); surface max |Spearman| = {cross['surface_before_placement']['max_abs_rank_correlation']:.3f} vs {cross['focus9_entries_checked']} focus-9 rasters; vs post-merge local candidates ≤0.058. The 505-dot lattice-avoiding research candidate and every archived lane remain <strong>DO NOT SUBMIT</strong>.</p>
</aside>
<table><caption>KPL-36 holdout arms — HOLDOUT-DTI</caption><thead><tr><th>Arm</th><th>HOLDOUT-DTI</th><th>95% CI</th></tr></thead><tbody>{arms_rows}</tbody></table>
<table><caption>KPL-36 uniqueness vs each focus site's highest file (scores OWNER-REPORTED; no receipts archived)</caption><thead><tr><th>Site</th><th>Champion score</th><th>KPL-36 dots within 3 px</th><th>Verdict</th></tr></thead><tbody>{champ_html}</tbody></table>
</section>
<!-- KPL36:END -->"""

    ledger = load(ROOT / "evidence/focus_sites_9repo_summary_20261026.json")
    table = site_table(ledger)
    gvsc = load(ROOT / "evidence/gvsc36_run_card_20261026.json")
    hvg = load(ROOT / "evidence/hvg36_run_card_20261026.json")
    mto = load(ROOT / "evidence/mto36_run_card_20261026.json")
    archive = f"""<!-- KPL36_ARCHIVE:START -->
<section class="section" id="archived-evidence" aria-label="Archived evidence ledger">
<div class="section-head"><div><span class="eyebrow">Archived evidence — Research downloads only</span><h2>Pinned nine-site table &amp; prior lanes (all DO NOT SUBMIT)</h2></div></div>
<p>Historical scores below are OWNER-REPORTED; no historical score on this site is ORGANIZER-CONFIRMED because no submission-page receipt is archived. Prior GEMSDOE36 lanes: GVSC-36 EXP-3 HOLDOUT-DTI 0.158855, HVG-36 EXP-1 HOLDOUT-DTI 0.135759, DW36 HOLDOUT-DTI 0.066052 (below its control), BDC-36 negative; an external GEMSDOE24 review records 0.1637924 on the same named evaluator (no independent protocol/paired-gain/novelty certification). Registry-preflight lattice bound: at 37,654 dots at least 82.34% of any candidate must fall within 3 px of the blind lattice. At or above this count the proof forces a stop under the literal all-raster rule — KPL-36 therefore gates on competing-detector champions and reports the lattice as a calibration control (monograph §5/§7).</p>
<ul>
<li>GVSC-36 (negative): <code>{gvsc['submission']['zeros_filename']}</code> · SHA-256 <code>{gvsc['submission']['raster_sha256']}</code></li>
<li>HVG-36 (negative): <code>{Path(hvg['artifact']['tif_path']).name}</code> · SHA-256 <code>{hvg['artifact']['tif_sha256']}</code></li>
<li>MTO-36 (negative): <code>{Path(mto['download']['tif']).name}</code> · SHA-256 <code>{mto['raster_sha256']}</code> · note: <code>{html.escape(mto['submission_note'])}</code></li>
</ul>
{table}
</section>
<!-- KPL36_ARCHIVE:END -->"""
    focus_exec = f"""<!-- FOCUS9_EXEC:START -->
{table}
<!-- FOCUS9_EXEC:END -->"""
    guide = """<!-- KPL36_GUIDE:START -->
<section class="section" id="how-to-submit" aria-label="How to submit">
<div class="section-head"><div><span class="eyebrow">Submission guide</span><h2>How to submit (exactly)</h2></div></div>
<ol>
<li>Download the KPL-36 single-band GeoTIFF (.tif) above, or the .zip file containing a single GeoTIFF. It matches the submission format's CRS, shape, and geotransform (EPSG:32611, 3730×3292, 100 m) and every value satisfies the portal rule <em>“Predicted values must be in range [0, 1]”</em> — outside-footprint cells are 0, never NaN (NaN-outside files are what triggered that error previously).</li>
<li>On DrivenData competition 306 choose <em>Submit</em>, upload the file, and paste the KPL-36 Note shown above (≤140 characters).</li>
<li>Budget: three weekly slots; one submission for both prize rounds may be selected — this file is the recommended spend of one slot. After scoring, archive the submission-page receipt in <code>evidence/</code> so the result becomes organizer-confirmed.</li>
</ol>
</section>
<!-- KPL36_GUIDE:END -->"""

    for page, is_summary in ((INDEX, False), (SUMMARY, True)):
        text = page.read_text()
        text = upsert(text, "<!-- KPL36:START -->", "<!-- KPL36:END -->", block, '<main id="main" class="wrap">')
        text = upsert(text, "<!-- KPL36_ARCHIVE:START -->", "<!-- KPL36_ARCHIVE:END -->", archive, "</main>", where="before")
        if is_summary:
            if "<!-- FOCUS9_EXEC:START -->" in text:
                text = re.sub(r"<!-- FOCUS9_EXEC:START -->.*?<!-- FOCUS9_EXEC:END -->", lambda m: focus_exec, text, flags=re.S)
            else:
                text = text.replace("</main>", focus_exec + "\n</main>", 1)
            text = upsert(text, "<!-- KPL36_GUIDE:START -->", "<!-- KPL36_GUIDE:END -->", guide, "</main>", where="before")
        page.write_text(text)

    prev_bdc = load(PREV_BDC)
    dw = load(ROOT / "evidence/dw36_run_card_20261026.json")
    current = {
        "schema": "gemsdoe36.current-run.v5",
        "updated_utc": datetime.now(timezone.utc).isoformat(),
        "lane_id": "KPL-36",
        "verdict": verdict,
        "slot_approved": bool(promote),
        "ok_to_download_and_submit": bool(promote),
        "ok_to_download_for_research": True,
        "research_downloads_only": not promote,
        "tif_path": tif_rel,
        "tif_sha256": sub["sha256"],
        "zip_path": zip_rel,
        "zip_sha256": sub["zip_sha256"],
        "holdout_dti": h["arms"][best]["dti"],
        "ci95": h["arms"][best]["ci95"],
        "evaluator_version": "gems-segment-pooled-v1",
        "withheld_positives": h["n_withheld_positive_pixels"],
        "run_card": "downloads/kpl36-run-card.json",
        "run_card_sha256": sha(CARD),
        "note": sub["note"],
        "submission_name": sub["name"],
        "gates": gates,
        "score_estimate_scenario_range": est_range,
        "parallel_experiments": [parallel_dw_projection(dw)],
        "previous_current_run_v4_BDC36": prev_bdc,
        "kpl36_run_card": card,
    }
    CURRENT.write_text(json.dumps(current, indent=2, default=float) + "\n")
    (DOCS / "downloads/kpl36-run-card.json").write_bytes(CARD.read_bytes())

    man = load(MANIFEST)
    man["slot_approved"] = bool(promote)
    man["current_candidate"] = {
        "lane": "KPL-36",
        "file": Path(sub["file"]).name,
        "sha256": sub["sha256"],
        "zip": Path(sub["zip"]).name,
        "zip_sha256": sub["zip_sha256"],
        "card": "kpl36-run-card.json",
        "submit_ok": bool(promote),
        "note": sub["note"],
        "holdout_dti_LABEL": "HOLDOUT-DTI",
        "holdout_dti": h["arms"][best]["dti"],
        "organizer_score": None,
    }
    man["run_card"] = "kpl36-run-card.json"
    MANIFEST.write_text(json.dumps(man, indent=1, default=float) + "\n")

    readme = README.read_text()
    decision = f"""> ## CURRENT DECISION · KPL-36 · DOWNLOAD: YES · {'OK TO SUBMIT' if promote else 'DO NOT SUBMIT'} · verdict: {verdict}
>
> **The file to submit:** [`{Path(sub['file']).name}`]({sub['file']}) ([ZIP]({sub['zip']}), [run card](evidence/kpl36_run_card_20261026.json), [monograph + 9-site executive audit](docs/research/kpl36-20261026.md), [preregistration](docs/research/preregistration-kpl36-20261026.md)). Name `{sub['name']}`; Note ({sub['note_characters']}/140): `{sub['note']}`; SHA-256 `{sub['sha256']}`; {sub['dots']:,} dots; whole-array [0,1] zeros-outside (portal-safe).
> - **HOLDOUT-DTI {h['arms'][best]['dti']:.6f}** [{h['arms'][best]['ci95'][0]:.4f}, {h['arms'][best]['ci95'][1]:.4f}] (`gems-segment-pooled-v1`, {h['n_withheld_positive_pixels']:,} withheld px); EXP-2 beat the in-run GVSC replication (0.160003) with paired Δ +0.0096 [0.0035, 0.0159], 4/4 folds. Internal validation, not a leaderboard score. (Point comparison only: above GVSC 0.158855 and the externally reviewed GEMSDOE24 0.1637924.)
> - **Leaderboard scenario estimate {est_range}** (assumptions in monograph §5; needs novel credit ≥{est['novel_credit_needed_to_match_0.2778']:.3f} to match the historical champion; no organizer receipt yet).
> - **Uniqueness:** champion 3-px dot overlap max {cross['final_dots']['max_champion_3px_overlap']:.3f} (vs GEMSDOE32-B2 {cross['final_dots']['overlap_vs_GEMSDOE32_B2_3px']:.3f}); surface |ρ| {cross['surface_before_placement']['max_abs_rank_correlation']:.3f} vs {cross['focus9_entries_checked']} focus-9 rasters; vs post-merge local candidates ≤0.058. Blind-lattice overlap is mathematically forced (~0.99 at any 37,654-dot budget; calibration control, disclosed in monograph).
> - Archived, **DO NOT SUBMIT**: 505-dot lattice-avoiding candidate (no computable holdout in its session), BDC-36, DW36 (0.066052), GVSC-36 (0.158855), HVG-36 (0.135759), MTO-36, H36-CTRB, ATVR-36, Lane36, registry-preflight stop — cards preserved in `evidence/`. Historical best remains GEMSDOE32-B2 **0.2778 OWNER-REPORTED** (already submitted; exact family subset). Verified live leaderboard #1 = **0.4437** (2026-10-26 read).
"""
    m = re.search(r"> ## CURRENT DECISION.*?\n(?=## )", readme, flags=re.S)
    if m:
        readme = readme[: m.start()] + decision + "\n" + readme[m.end() :]
    else:
        readme = decision + "\n" + readme
    README.write_text(readme)
    print(f"[site] KPL-36 v5 verdict={verdict} promote={promote} -> pages/current-run/manifest/README updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
