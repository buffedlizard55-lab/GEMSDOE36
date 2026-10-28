#!/usr/bin/env python3
"""Publish S2D-36 research candidate additively onto GitHub Pages, manifests, and README.

Preserves all existing KPL-36, TCD-36, SFD-36, CSDL-36, GVSC-36, HVG-36, MTO-36,
DW36, LITERAL_REVIEW, FOCUS9_EXEC, and verbatim standing owner brief invariants.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

S2D_CARD = ROOT / "evidence/s2d36_run_card_20261027.json"
S2D_CROSS = ROOT / "evidence/s2d36_crosscheck_20261027.json"
S2D_PEERS = ROOT / "evidence/s2d36_oct27_peer_audit_20261027.json"
TCD_CARD = ROOT / "evidence/tcd36_run_card_20261027.json"
KPL_CARD = ROOT / "evidence/kpl36_run_card_20261026.json"

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
    if promote:
        raise RuntimeError("Separate selector authorization required; this historical publisher cannot promote")

    sub = card["submission"]
    tif_rel = sub["file"].removeprefix("docs/")
    zip_rel = sub["zip"].removeprefix("docs/")
    h = card["holdout"]
    best = card["best_arm"]

    arms_rows = "".join(
        f"<tr><td><code>{a}</code></td>"
        f"<td><strong>{v['dti']:.6f}</strong> HOLDOUT-DTI</td>"
        f"<td>[{v['ci95'][0]:.4f}, {v['ci95'][1]:.4f}]</td></tr>"
        for a, v in h["arms"].items()
    )

    exec_rows = [
        (
            "GEMSDOE36 · S2D-36 EXP-2 (current highest holdout)",
            f'<a href="{html.escape(tif_rel)}" download><code>{html.escape(Path(sub["file"]).name)}</code></a>'
            f'<br><small>SHA-256 <code>{sub["sha256"][:16]}…</code> · {sub["dots"]:,} dots · [0,1] zeros-outside</small>',
            f"<strong>HOLDOUT-DTI {h['arms'][best]['dti']:.6f}</strong> [{h['arms'][best]['ci95'][0]:.4f}, {h['arms'][best]['ci95'][1]:.4f}]<br>"
            f"<small>{h['evaluator_version']} · {h['n_withheld_positive_pixels']:,} withheld positives</small>",
            "Not defensibly estimable; prior scenario withdrawn",
            f"<strong>PASS modern ≤45k external peers</strong> (max {peers['max_oct25_27_peer_3px_overlap']*100:.2f}%; "
            f"vs B2 {cross['final_dots']['overlap_vs_GEMSDOE32_B2_3px']*100:.2f}%; vs SFD-36 57.53%) · "
            f"<strong>FAIL literal</strong> ({cross['final_dots']['max_overlap_literal_all_198']*100:.2f}% reg-052; "
            f"70.93% vs parallel TCD-36)",
            "<strong>DO NOT SUBMIT</strong> (literal uniqueness failure; no override)",
        ),
        (
            "GEMSDOE36 · TCD-36 EXP-2 (parallel Oct 27)",
            '<a href="downloads/gemsdoe36-tcd36-exp2-20261027-9970b80c6585-zeros.tif" download>'
            "<code>gemsdoe36-tcd36-exp2-20261027-9970b80c6585-zeros.tif</code></a>"
            "<br><small>SHA-256 <code>513a7378a96452fa…</code> · 37,654 dots</small>",
            "HOLDOUT-DTI 0.194164 [0.1803, 0.2083]",
            "Unscored (superseded on holdout by S2D-36 +0.0066)",
            "Focus-9 ≤66.82% · reg-052 99.35% · vs S2D-36: 70.93%",
            "<strong>DO NOT SUBMIT</strong> (research only)",
        ),
        (
            "GEMSDOE36 · SFD-36 EXP-2 & KPL-36 EXP-3",
            '<a href="downloads/gemsdoe36-kpl36-exp3-20261026-fc869911e88c-zeros.tif" download>'
            "<code>gemsdoe36-kpl36-exp3-20261026-fc869911e88c-zeros.tif</code></a>"
            "<br><small>SFD-36 SHA-12 <code>89db5e348baa</code> · KPL-36 SHA-12 <code>86fc8243ad57</code></small>",
            "SFD-36 HOLDOUT-DTI 0.178394; KPL-36 HOLDOUT-DTI 0.170100 (<strong>0.1647 USER-REPORTED</strong>)",
            "KPL observed 0.1647 USER-REPORTED (no receipt)",
            "S2D-36 overlap: 57.53% vs SFD-36, 65.18% vs KPL-36",
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
<span class="eyebrow">GEMS DOE 36 · S2D-36 latest research candidate · 27 October 2026 · verdict: {verdict} · DOWNLOAD: YES</span>
<h1>S2D-36 EXP-2 (HOLDOUT-DTI 0.200766) — research download only</h1>
<p class="lede"><strong>{banner}.</strong> File <code>{html.escape(Path(sub['file']).name)}</code> · {sub['dots']:,} binary dots · single-band float32 GeoTIFF, EPSG:32611, 3730×3292 at 100 m, all 12,279,160 cells strictly in [0, 1] with 0 outside the footprint (0 NaN cells anywhere) · SHA-256 <code>{sub['sha256']}</code>. Automatic slot approval is <strong>NO</strong> (<code>slot_approved: false</code>).</p>
<div class="hero-actions">
<a class="button" href="{html.escape(tif_rel)}" download>⬇ Download S2D-36 GeoTIFF (.tif)</a>
<a class="button secondary" href="{html.escape(zip_rel)}" download>Download ZIP (.zip)</a>
<a class="button secondary" href="downloads/s2d36-run-card.json">S2D-36 JSON run card</a>
<a class="button secondary" href="research/s2d36-20261027.md">S2D-36 PhD monograph &amp; full audit →</a>
</div>
<p><strong>Unique submission name:</strong> <code>{html.escape(sub['name'])}</code><br>
<strong>Copy-paste Note</strong> ({sub['note_characters']}/140 chars, research only; not for upload): <code>{html.escape(sub['note'])}</code></p>
</div>
<aside class="status-card" aria-label="S2D-36 gate summary"><span class="eyebrow">Automated 6-gate verdict: {verdict.upper()}</span>
<p style="font-size:.93rem"><strong>G1 Canary PASS:</strong> max single-feature symmetric AUC = {card['leakage_canary']['max_symmetric_auc']:.4f} (&le;0.90).<br>
<strong>G2 Holdout PASS:</strong> <strong>HOLDOUT-DTI {h['arms'][best]['dti']:.6f}</strong> [{h['arms'][best]['ci95'][0]:.4f}, {h['arms'][best]['ci95'][1]:.4f}] ({h['evaluator_version']}, {h['n_withheld_positive_pixels']:,} withheld positives) — beats C-KPL ({h['arms']['C-KPL']['dti']:.6f}) by <strong>+{h['paired_vs_C_KPL']['paired_delta_dti']:.4f}</strong> (4/4 folds), TCD-36 (0.194164) by <strong>+0.0066</strong>, SFD-36 (0.178394) by <strong>+0.0224</strong>, and KPL-36 EXP-3 (0.170100) by <strong>+0.0307</strong>.<br>
<strong>G3a Surface PASS:</strong> pre-placement max |Spearman| = {cross['surface_before_placement']['max_abs_rank_correlation_all_198']:.4f} (&le;0.90 across 198 rasters).<br>
<strong>G3b/G3c Overlap STOP:</strong> passes 13/13 Oct 25–27 external peers (&le;68.49%) and 7/9 Focus-9 champions (vs GEMSDOE32 B2 = <strong>65.49%</strong>; vs SFD-36 = 57.53%; vs KPL-36 = 65.18%), while parallel TCD-36 (70.93%), wide &ge;60k blankets (GEMSDOE27 d1.5 = 70.96%, reg-062 = 96.23%), and the 5&times;5 calibration lattice reg-052 (99.48%) exceed 70%.<br>
<strong>G4 Format PASS:</strong> single-band float32, [0, 1] whole-grid finite, d_cat &gt; 2 px (min 2.236 px).</p>
</aside>
<div class="table-wrap"><table><caption>Executive summary ledger — downloadable files, measured provenance, score provenance and uniqueness</caption>
<thead><tr><th>Site / Lane</th><th>File to download &amp; SHA-256</th><th>Measured metric &amp; provenance</th><th>Leaderboard estimate / context</th><th>Uniqueness audit (3-px dot overlap)</th><th>Automated decision</th></tr></thead>
<tbody>{exec_html}</tbody></table></div>
<div class="table-wrap"><table><caption>S2D-36 4-quadrant buffered segment holdout — HOLDOUT-DTI ({h['evaluator_version']}, {h['n_withheld_positive_pixels']:,} withheld positives)</caption>
<thead><tr><th>Arm</th><th>Pooled Metric</th><th>95% Segment-Bootstrap CI</th></tr></thead><tbody>{arms_rows}</tbody></table></div>
<p style="font-size:.92rem"><strong>GEMSDOE32 B2 (0.2778 USER-REPORTED):</strong> Prior pinned forensics describe a catalogue-near-pruned D2.8-family subset. Pruning may reduce uncredited predictions, but hidden truth and an organizer receipt are unavailable. This is a hypothesis, not a proven causal explanation or leaderboard forecast.</p>
</section>
<!-- S2D36:END -->"""


def update_readme(card: dict, cross: dict, peers: dict) -> None:
    raw = README.read_text(encoding="utf-8")
    marker = "## Full standing owner brief (historical wording)"
    if marker not in raw:
        raise RuntimeError("Standing owner brief marker missing from README.md")
    standing_suffix = raw[raw.index(marker):]

    sub = card["submission"]
    h = card["holdout"]
    best = card["best_arm"]
    scen = card["scenario_projection_not_a_score"]

    s2d_readme = f"""<!-- S2D36_README:START -->
> ## NEWEST RESEARCH CANDIDATE (2026-10-27) · `S2D-36` (`EXP-2`) · `HOLDOUT-DTI 0.200766` · DOWNLOAD: YES · DO NOT SUBMIT (`verdict: negative`)
>
> - **Validated `[0, 1]` GeoTIFF:** [`{Path(sub['file']).name}`]({sub['file']}) ([Single-TIFF ZIP]({sub['zip']}), [Run Card JSON](evidence/s2d36_run_card_20261027.json), [Monograph & PhD `0.2778` Proof](docs/research/s2d36-20261027.md), [Oct 25–27 Peer Audit](evidence/s2d36_oct27_peer_audit_20261027.json), [Locked Preregistration](evidence/s2d36_preregistration_20261027.json)).
> - **SHA-256 (`-zeros.tif`):** `{sub['sha256']}` · **Dots:** `{sub['dots']:,}` · **Grid:** `EPSG:32611`, `3730×3292` at `100 m`, all `12,279,160` cells finite in `[0.0, 1.0]` (`0` NaN/Inf, `min(d_cat) = 2.236 px`).
> - **Unique Name:** `{sub['name']}` · **Copy-Paste Note (`{sub['note_characters']}/140` chars):** `{sub['note']}`
> - **Spatially-Blocked Holdout (`gems-segment-pooled-v1`, `60,988` withheld positives):** **`HOLDOUT-DTI = {h['arms'][best]['dti']:.6f}`** (`95% CI [{h['arms'][best]['ci95'][0]:.6f}, {h['arms'][best]['ci95'][1]:.6f}]`) — highest validated holdout in `GEMSDOE36`, beating parallel `TCD-36 EXP-2` (`0.194164`) by **`+0.006602`**, `SFD-36 EXP-2` (`0.178394`) by **`+0.022372`**, `KPL-36 EXP-3` (`0.170100`, `0.1647 USER-REPORTED`) by **`+0.030666`**, `C-KPL` (`0.169892`) by **`+0.030874`** across **all 4/4 spatial folds** (`NW 0.21254`, `NE_LidarGapHeavy 0.26718`, `SW 0.13744`, `SE 0.21604`), and `B0` (`0.132760`) by **`+0.068006`** (`EXP-1 = 0.184769`, `EXP-3 = 0.200593`).
> - **Scenario Projection (`NOT A SCORE`, no organizer receipt):** `{scen['peer_mechanism_matched_scenario_range'][0]:.3f}–{scen['peer_mechanism_matched_scenario_range'][1]:.3f}` peer-mechanism transfer range (conservative KPL-ratio floor `{scen['conservative_kpl_ratio_projection']:.3f}`; see [monograph §2.4](docs/research/s2d36-20261027.md)).
> - **Canary & Scoped-vs-Literal Uniqueness:** Single-feature canary max symmetric AUC `0.6684 <= 0.90` (**PASS**); pre-placement surface `|Spearman rho| = {cross['surface_before_placement']['max_abs_rank_correlation_all_198']:.4f} <= 0.90` (**PASS**); passes **13/13 Oct 25–27 modern external peers** (`max = {peers['max_oct25_27_peer_3px_overlap']*100:.2f}% <= 70%`; `54.23%` vs `GEMSDOE70 0.2478`, `59.98%` vs `GEMSDOE76 0.2343`, `68.49%` vs `GEMSDOE27 H31 0.2250`), **18/18 prior `GEMSDOE36` files** (`<= 65.95%`; `57.53%` vs `SFD-36`), and **7/9 Focus-9 champions** (`65.49%` vs `GEMSDOE32 B2 0.2778`), while failing closed (`verdict: "negative"`, `slot_approved: false`) on parallel `TCD-36` (`70.93%`), `>= 60k`-dot wide blankets (`GEMSDOE27 d1.5 = 70.96%`, `reg-062 = 96.23%`), and `reg-052` `5x5` calibration lattice (`99.48%`).
<!-- S2D36_README:END -->"""

    updated = upsert(raw, "<!-- S2D36_README:START -->", "<!-- S2D36_README:END -->", s2d_readme, "<!-- LITERAL_REVIEW:END -->", where="after")
    assert updated.endswith(standing_suffix), "Standing owner brief suffix drifted!"
    README.write_text(updated, encoding="utf-8")


def main() -> int:
    s2d_card = load(S2D_CARD)
    s2d_cross = load(S2D_CROSS)
    s2d_peers = load(S2D_PEERS)
    tcd_card = load(TCD_CARD)
    kpl_card = load(KPL_CARD)

    sub = s2d_card["submission"]
    tif_path = ROOT / sub["file"]
    zip_path = ROOT / sub["zip"]
    if sha(tif_path) != sub["sha256"] or sha(zip_path) != sub["zip_sha256"]:
        raise RuntimeError("Artifact SHA-256 mismatch vs S2D-36 run card")

    (DOCS / "downloads/s2d36-run-card.json").write_bytes(S2D_CARD.read_bytes())

    # Update docs/current-run.json additively (preserving top-level KPL-36 v5 + TCD-36 + BDC-36 + DW36)
    current = load(CURRENT)
    best = s2d_card["best_arm"]
    h = s2d_card["holdout"]
    current["latest_research_lane_s2d36"] = {
        "lane_id": "S2D-36",
        "best_arm": best,
        "verdict": s2d_card["verdict"],
        "slot_approved": False,
        "ok_to_download_and_submit": False,
        "ok_to_download_for_research": True,
        "tif_path": sub["file"].removeprefix("docs/"),
        "tif_sha256": sub["sha256"],
        "zip_path": sub["zip"].removeprefix("docs/"),
        "zip_sha256": sub["zip_sha256"],
        "holdout_label": "HOLDOUT-DTI",
        "holdout_dti": h["arms"][best]["dti"],
        "ci95": h["arms"][best]["ci95"],
        "delta_vs_kpl36_exp3": round(float(h["arms"][best]["dti"]) - 0.17010000946379217, 6),
        "delta_vs_tcd36_exp2": round(float(h["arms"][best]["dti"]) - float(tcd_card["holdout"]["arms"]["EXP-2"]["dti"]), 6),
        "evaluator_version": h["evaluator_version"],
        "withheld_positives": h["n_withheld_positive_pixels"],
        "run_card": "downloads/s2d36-run-card.json",
        "run_card_sha256": sha(S2D_CARD),
        "submission_name": sub["name"],
        "note": sub["note"],
        "gates": s2d_card["gates"],
        "scenario_projection_not_a_score": s2d_card["scenario_projection_not_a_score"],
    }
    CURRENT.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")

    # Update docs/downloads/submissions_manifest.json additively
    manifest = load(MANIFEST)
    manifest["slot_approved"] = False
    manifest["current_candidate"] = None
    tcd_sub = tcd_card["submission"]
    manifest["superseded_tcd36_research_candidate"] = {
        "lane": "TCD-36",
        "file": Path(tcd_sub["file"]).name,
        "sha256": tcd_sub["sha256"],
        "zip": Path(tcd_sub["zip"]).name,
        "zip_sha256": tcd_sub["zip_sha256"],
        "companion_nan_file": Path(tcd_sub["companion_nan_file"]).name,
        "companion_nan_sha256": tcd_sub["companion_nan_sha256"],
        "card": "tcd36-run-card.json",
        "submit_ok": False,
        "note": tcd_sub["note"],
        "holdout_dti_LABEL": "HOLDOUT-DTI",
        "holdout_dti": tcd_card["holdout"]["arms"]["EXP-2"]["dti"],
        "organizer_score": None,
    }
    kpl_sub = kpl_card["submission"]
    manifest["superseded_kpl36_research_candidate"] = {
        "lane": "KPL-36",
        "file": Path(kpl_sub["file"]).name,
        "sha256": kpl_sub["sha256"],
        "zip": Path(kpl_sub["zip"]).name,
        "zip_sha256": kpl_sub["zip_sha256"],
        "card": "kpl36-run-card.json",
        "submit_ok": False,
        "note": kpl_sub["note"],
        "holdout_dti_LABEL": "HOLDOUT-DTI",
        "holdout_dti": kpl_card["holdout"]["arms"]["EXP-3"]["dti"],
        "organizer_score": None,
    }
    manifest["research_candidate"] = {
        "lane": "S2D-36",
        "file": Path(sub["file"]).name,
        "sha256": sub["sha256"],
        "zip": Path(sub["zip"]).name,
        "zip_sha256": sub["zip_sha256"],
        "card": "s2d36-run-card.json",
        "submit_ok": False,
        "note": sub["note"],
        "holdout_dti_LABEL": "HOLDOUT-DTI",
        "holdout_dti": h["arms"][best]["dti"],
        "organizer_score": None,
    }
    manifest["latest_run_card"] = "s2d36-run-card.json"
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    s2d_block = build_s2d_section(s2d_card, s2d_cross, s2d_peers)
    for page in (INDEX, SUMMARY):
        txt = page.read_text(encoding="utf-8")
        txt = upsert(txt, "<!-- S2D36:START -->", "<!-- S2D36:END -->", s2d_block, "<!-- LITERAL_REVIEW:END -->", where="after")
        page.write_text(txt, encoding="utf-8")

    update_readme(s2d_card, s2d_cross, s2d_peers)
    print("[build_s2d_site] additively updated Pages, manifests, and README on top of origin/main")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
