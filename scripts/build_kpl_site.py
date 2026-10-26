#!/usr/bin/env python3
"""Update GitHub Pages + README + manifests from the verified KPL-36 run card.

Fail-closed: refuses to render a submit-positive banner unless the run card verdict
is ``promote`` AND all four preregistered gates are true in the card. Historical
scores are always labelled OWNER-REPORTED. Generates only text/JSON; never touches
any raster.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CARD = ROOT / "evidence/kpl36_run_card_20261026.json"
HOLD = ROOT / "evidence/kpl36_holdout_experiments_20261026.json"
CROSS = ROOT / "evidence/kpl36_crosscheck_20261026.json"
EST = ROOT / "evidence/kpl36_score_estimate_20261026.json"
INDEX = DOCS / "index.html"
SUMMARY = DOCS / "executive-summary.html"
CURRENT = DOCS / "current-run.json"
MANIFEST = DOCS / "downloads/submissions_manifest.json"
README = ROOT / "README.md"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def replace_block(text: str, start: str, end: str, block: str, anchor: str) -> str:
    if start in text and end in text:
        return re.sub(re.escape(start) + r".*?" + re.escape(end), block.replace("\\", "\\\\"), text, flags=re.S)
    if anchor not in text:
        raise RuntimeError(f"anchor not found: {anchor[:60]}")
    return text.replace(anchor, anchor + "\n" + block, 1)


def main() -> int:
    card = json.loads(CARD.read_text())
    hold = json.loads(HOLD.read_text())
    cross = json.loads(CROSS.read_text())
    est = json.loads(EST.read_text())
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
    arms_rows = "".join(
        f"<tr><td><code>{a}</code></td><td>{v['dti']:.6f}</td><td>[{v['ci95'][0]:.4f}, {v['ci95'][1]:.4f}]</td></tr>"
        for a, v in h["arms"].items()
    )
    scen = est["scenarios"]
    est_range = (
        f"{scen['novel_credit_0.03']['estimated_DTI_if_credit_assumptions_hold']:.3f}–"
        f"{scen['novel_credit_0.13']['estimated_DTI_if_credit_assumptions_hold']:.3f}"
    )
    est_mid = scen["novel_credit_0.07"]["estimated_DTI_if_credit_assumptions_hold"]
    champ_rows = cross["final_dots"]["champion_overlap_by_site"]
    champ_html = "".join(
        f"<tr><td><code>{site}</code></td><td>{r['owner_reported_score']}</td>"
        f"<td>{(r['candidate_dot_overlap_within_3px'] or 0):.3f}</td>"
        f"<td>{'UNIQUE (≤0.70)' if (r['candidate_dot_overlap_within_3px'] or 0) <= 0.70 else 'DUPLICATE (>0.70)'}</td></tr>"
        for site, r in sorted(champ_rows.items())
    )
    banner = (
        "✅ OK TO SUBMIT — passed every automated gate (selector: spend ONE weekly slot on this file)"
        if promote
        else "⛔ DO NOT SUBMIT — automated gate failed; research download only"
    )
    dl_banner = "DOWNLOAD: YES" + ("" if promote else " (research)")
    block = f"""<!-- KPL36:START -->
    <section class="verdict-banner" id="kpl36-release" aria-label="KPL-36 current release">
      <div class="verdict-head">
        <span class="verdict-pill">{dl_banner} · {banner}</span>
        <span class="verdict-pill secondary">KPL-36 verdict: {verdict} · automated gate, no human inspection</span>
      </div>
      <h2>⬇ The file to download{ ' and submit' if promote else ''} (GEMSDOE36, 2026-10-26)</h2>
      <p><a class="button" href="{html.escape(tif_rel)}"><strong>Download submission TIFF:</strong> <code>{html.escape(Path(sub['file']).name)}</code></a>
      <a class="button secondary" href="{html.escape(zip_rel)}">One-TIFF ZIP</a>
      <a class="button secondary" href="downloads/kpl36-run-card.json">Run card (JSON)</a></p>
      <ul>
        <li><strong>Unique name:</strong> <code>{html.escape(sub['name'])}</code></li>
        <li><strong>Copy-paste submission Note</strong> ({sub['note_characters']}/140 chars): <code>{html.escape(sub['note'])}</code></li>
        <li><strong>SHA-256:</strong> <code>{sub['sha256']}</code> · {sub['dots']:,} dots · whole-array values in [0,1] (zeros outside footprint — fixes the portal <em>“Predicted values must be in range [0, 1]”</em> error caused by NaN-outside files) · single-band GeoTIFF matching the sample CRS/shape/geotransform (validator-passed).</li>
        <li><strong>HOLDOUT-DTI</strong> (gems-segment-pooled-v1, {h['n_withheld_positive_pixels']:,} withheld positives): best arm <code>{best}</code> = <strong>{h['arms'][best]['dti']:.6f}</strong> [{h['arms'][best]['ci95'][0]:.4f}, {h['arms'][best]['ci95'][1]:.4f}] vs B0 {h['arms']['B0']['dti']:.6f}, C-GVSC replication {h['arms']['C-GVSC']['dti']:.6f}. This is an internal hide-and-recover number, <em>not</em> a leaderboard score.</li>
        <li><strong>Leaderboard estimate (scenario model, not a score):</strong> {est_range} depending on novel-dot credit 0.03–0.13 (mid scenario {est_mid:.3f}); novel dots must average ≥{est['novel_credit_needed_to_match_0.2778']:.3f} credit to match the historical 0.2778 OWNER-REPORTED champion. Only an actual portal submission can measure the true value; no organizer receipt exists yet.</li>
        <li><strong>Uniqueness (measured, 3-px dot overlap vs each focus-site champion; ≤0.70 = unique):</strong> max = {cross['final_dots']['max_champion_3px_overlap']:.3f}; vs GEMSDOE32-B2 champion = {cross['final_dots']['overlap_vs_GEMSDOE32_B2_3px']:.3f}; surface max |Spearman| vs {cross['focus9_entries_checked']} focus-9 rasters = {cross['surface_before_placement']['max_abs_rank_correlation']:.3f} (≤0.90 required).</li>
      </ul>
      <table><caption>KPL-36 holdout arms — HOLDOUT-DTI (gems-segment-pooled-v1)</caption>
      <thead><tr><th>Arm</th><th>HOLDOUT-DTI</th><th>95% CI</th></tr></thead><tbody>{arms_rows}</tbody></table>
      <table><caption>Uniqueness vs the 9 focus sites' highest-scoring files (scores OWNER-REPORTED, no organizer receipts archived)</caption>
      <thead><tr><th>Site</th><th>Champion score (OWNER-REPORTED)</th><th>KPL-36 dots within 3 px</th><th>Verdict</th></tr></thead><tbody>{champ_html}</tbody></table>
      <p>Method in one line: 3–5 km oriented line-coherence (expert-traceability) features + GVSC-89 geothermal/geophysics stack, LiDAR-blind bridge ensemble, quadrant-OOF surface, B2 catalogue collar, exact 300 m CELF submodular emission. Full audit: <a href="research/kpl36-20261026.md">KPL-36 monograph &amp; 9-site executive table</a>. How to submit: <a href="executive-summary.html">executive summary</a>.</p>
    </section>
<!-- KPL36:END -->"""

    idx = INDEX.read_text()
    idx = replace_block(idx, "<!-- KPL36:START -->", "<!-- KPL36:END -->", block, '<main id="main" class="wrap">')
    # Replace the stale fail-closed inline script with a verdict-consistent check.
    idx = re.sub(
        r'<script>fetch\("current-run\.json"\).*?</script>',
        '<script>fetch("current-run.json").then(r=>r.json()).then(d=>{if(!d.kpl36)throw new Error("missing KPL-36 state");});</script>',
        idx, flags=re.S,
    )
    INDEX.write_text(idx)

    summ = SUMMARY.read_text()
    summ = replace_block(summ, "<!-- KPL36:START -->", "<!-- KPL36:END -->", block, '<main id="main" class="wrap">')
    SUMMARY.write_text(summ)

    prev = json.loads(CURRENT.read_text()) if CURRENT.exists() else {}
    current = {
        "updated_utc": datetime.now(timezone.utc).isoformat(),
        "lane_id": "KPL-36",
        "verdict": verdict,
        "slot_approved": bool(promote),
        "ok_to_download_for_research": True,
        "ok_to_download_and_submit": bool(promote),
        "tif": tif_rel,
        "zip": zip_rel,
        "tif_sha256": sub["sha256"],
        "zip_sha256": sub["zip_sha256"],
        "submission_name": sub["name"],
        "submission_note": sub["note"],
        "kpl36": card,
        "score_estimate": est,
        "previous_current_run_MTO36": prev,
    }
    CURRENT.write_text(json.dumps(current, indent=2, default=float) + "\n")

    (DOCS / "downloads/kpl36-run-card.json").write_bytes(CARD.read_bytes())

    man = json.loads(MANIFEST.read_text())
    man["current_kpl36"] = {
        "file": Path(sub["file"]).name,
        "sha256": sub["sha256"],
        "zip": Path(sub["zip"]).name,
        "zip_sha256": sub["zip_sha256"],
        "submission_name": sub["name"],
        "note": sub["note"],
        "verdict": verdict,
        "status": "PROMOTE_OK_TO_SUBMIT" if promote else "DO_NOT_SUBMIT",
        "ok_to_download": True,
        "ok_to_submit": bool(promote),
        "holdout_dti_label": "HOLDOUT-DTI",
        "holdout_dti": h["arms"][best]["dti"],
        "evaluator_version": "gems-segment-pooled-v1",
        "withheld_positives": h["n_withheld_positive_pixels"],
        "leaderboard_estimate_scenario_range": est_range,
        "organizer_score": None,
    }
    MANIFEST.write_text(json.dumps(man, indent=2, default=float) + "\n")

    readme = README.read_text()
    status = f"""<!-- STATUS:START -->
> ## CURRENT DECISION · `DOWNLOAD: YES{'' if promote else ' (research)'}` · `{'OK TO SUBMIT' if promote else 'DO NOT SUBMIT'}` · `verdict: {verdict}` (KPL-36, 2026-10-26)
>
> **File:** [`{Path(sub['file']).name}`]({sub['file']}) · [ZIP]({sub['zip']}) · [run card](evidence/kpl36_run_card_20261026.json) · [monograph + 9-site executive table](docs/research/kpl36-20261026.md) · [preregistration](docs/research/preregistration-kpl36-20261026.md)
> - Name: `{sub['name']}`. Note ({sub['note_characters']}/140): `{sub['note']}`
> - SHA-256: `{sub['sha256']}` · {sub['dots']:,} dots · whole-array [0,1] zeros-outside (portal-safe).
> - **HOLDOUT-DTI {h['arms'][best]['dti']:.6f}** (gems-segment-pooled-v1, {h['n_withheld_positive_pixels']:,} withheld px, 95% CI [{h['arms'][best]['ci95'][0]:.4f}, {h['arms'][best]['ci95'][1]:.4f}]); B0 {h['arms']['B0']['dti']:.6f}; C-GVSC {h['arms']['C-GVSC']['dti']:.6f}. Not a leaderboard score.
> - **Leaderboard scenario estimate {est_range}** (novel-dot credit 0.03–0.13; needs ≥{est['novel_credit_needed_to_match_0.2778']:.3f} to match 0.2778 OWNER-REPORTED). No organizer receipt yet.
> - **Uniqueness:** max 3-px dot overlap vs the 9 focus-site champions = {cross['final_dots']['max_champion_3px_overlap']:.3f} (≤0.70 required); vs GEMSDOE32-B2 = {cross['final_dots']['overlap_vs_GEMSDOE32_B2_3px']:.3f}; surface max |Spearman| = {cross['surface_before_placement']['max_abs_rank_correlation']:.3f} vs {cross['focus9_entries_checked']} focus-9 rasters.
> - Historical best across the 9 sites remains GEMSDOE32-B2 **0.2778 OWNER-REPORTED** (already submitted; exact subset of GEMSDOE25/30 d2.8 — never re-upload). Verified live leaderboard #1 on 2026-10-26: **0.4437** (xiaofanhu, read from DrivenData).
<!-- STATUS:END -->"""
    if "<!-- STATUS:START -->" in readme and "<!-- STATUS:END -->" in readme:
        readme = re.sub(r"<!-- STATUS:START -->.*?<!-- STATUS:END -->", status.replace("\\", "\\\\"), readme, flags=re.S)
    else:
        readme = status + "\n\n" + readme
    README.write_text(readme)
    print(f"[site] KPL-36 verdict={verdict} promote={promote} -> pages, current-run.json, manifest, README updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
