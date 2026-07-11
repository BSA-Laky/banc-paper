#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dashboard.py - génère docs/index.html (statique, mobile, zéro dépendance).

Importé par run_once.py. Lit le journal + l'état du bot 25 ; affiche une carte
par bot (espérance, t-stat, verdict, courbe P&L en SVG inline) et l'A/B 25 vs 23.
"""
from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path

from banc_essai_paper_trading import charger_journal, evaluer

DOCS = Path("docs")
ETAT = Path("etat")

ORDRE = ["28_carry_hold", "25_convergence_basis", "23_carry_funding", "24_funding_multivenues", "26_carry_nado",
         "27a_rev_premium", "27b_rev_move", "27c_mom_move", "27d_rev_move_stop", "27f_selecteur", "27f10_selecteur", "27g10_selecteur", "10_controle_aleatoire"]
JOLI = {
    "28_carry_hold": "Bot 28 — Carry-HOLD (edge VALIDÉ out-of-sample, t OOS +10)",
    "25_convergence_basis": "Bot 25 — Convergence du basis (hypothèse)",
    "23_carry_funding": "Bot 23 — Carry funding seul (baseline)",
    "24_funding_multivenues": "Bot 24 — Funding multi-venues (HL/Paradex/ADEN)",
    "26_carry_nado": "Bot 26 — Carry cross-venue Nado (candidat, dormant si endpoint KO)",
    "27a_rev_premium": "Bot 27a — Convexe : réversion premium extrême",
    "27b_rev_move": "Bot 27b — Convexe : réversion move 24h extrême",
    "27c_mom_move": "Bot 27c — Convexe : momentum move 24h extrême",
    "27d_rev_move_stop": "Bot 27d — Convexe : réversion move 24h + stop-loss",
    "27f_selecteur": "Bot 27f — Sélecteur informé : signal par pièce + IA (seuil 20%)",
    "27f10_selecteur": "Bot 27f10 — Sélecteur informé (seuil 10%, verdict rapide)",
    "27g10_selecteur": "Bot 27g10 - Selecteur PUR LLM (agit uniquement sur avis IA, seuil 10%)",
    "10_controle_aleatoire": "Témoin aléatoire (étalon du bruit)",
}

CSS = (
    "body{font-family:-apple-system,Segoe UI,Roboto,sans-serif;margin:0;"
    "background:#11141a;color:#e8eaed;padding:14px}h1{font-size:1.25rem;margin:.2rem 0}"
    ".maj{color:#9aa0a6;font-size:.8rem;margin-bottom:12px}"
    ".ab{background:#1b2230;border:1px solid #2a3242;border-radius:10px;padding:12px;"
    "margin-bottom:14px;font-size:.92rem}.carte{background:#171b22;border:1px solid #262c38;"
    "border-radius:12px;padding:14px;margin-bottom:12px}.carte h2{font-size:1rem;margin:0 0 10px}"
    ".kpis{display:grid;grid-template-columns:repeat(2,1fr);gap:8px 14px}"
    ".kpis .lab{display:block;color:#9aa0a6;font-size:.72rem}"
    ".kpis .val{display:block;font-size:1.02rem;font-weight:600}"
    ".pos{color:#2ecc71}.neg{color:#e74c3c}.muted{color:#9aa0a6}.spark{margin:12px 0 6px}"
    ".verdict{font-size:.86rem;color:#cdd2d8;margin:.4rem 0 0}"
    "table{width:100%;border-collapse:collapse;font-size:.86rem}"
    "th,td{text-align:left;padding:5px 6px;border-bottom:1px solid #262c38}"
    "footer{color:#6b7280;font-size:.74rem;margin-top:18px;line-height:1.5}"
)


def _cumul(lignes):
    serie = {}
    rangs = [l for l in lignes if l.get("status") == "closed"
             and l.get("pnl") not in (None, "", "None")]
    rangs.sort(key=lambda l: l.get("closed_at") or "")
    for l in rangs:
        serie.setdefault(l["bot"], [])
        prev = serie[l["bot"]][-1] if serie[l["bot"]] else 0.0
        serie[l["bot"]].append(prev + float(l["pnl"]))
    return serie


def _spark(vals, w=260, h=60):
    if len(vals) < 2:
        return f'<svg width="{w}" height="{h}"></svg>'
    lo, hi = min(vals), max(vals)
    rng = (hi - lo) or 1.0
    pts = " ".join(f"{w*i/(len(vals)-1):.1f},{h-(h-6)*(v-lo)/rng-3:.1f}"
                   for i, v in enumerate(vals))
    col = "#2ecc71" if vals[-1] >= 0 else "#e74c3c"
    zy = h - (h - 6) * (0 - lo) / rng - 3
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<line x1="0" y1="{zy:.1f}" x2="{w}" y2="{zy:.1f}" stroke="#555" '
            f'stroke-dasharray="3,3"/><polyline fill="none" stroke="{col}" '
            f'stroke-width="2" points="{pts}"/></svg>')


def _carte(bot, r, spark):
    titre = html.escape(JOLI.get(bot, bot))
    if not r:
        return (f'<div class="carte"><h2>{titre}</h2>'
                f'<p class="muted">Aucun trade fermé pour l\'instant.</p></div>')
    esp = r["esperance_par_trade"]
    cls = "pos" if esp > 0 else ("neg" if esp < 0 else "")
    k = (f'<div><span class="lab">Trades</span><span class="val">{r["trades"]}</span></div>'
         f'<div><span class="lab">Taux réussite</span><span class="val">{r["taux_reussite"]*100:.1f}%</span></div>'
         f'<div><span class="lab">Espérance / trade</span><span class="val {cls}">{esp:+.4f} $</span></div>'
         f'<div><span class="lab">P&amp;L total</span><span class="val">{r["pnl_total"]:+.2f} $</span></div>'
         f'<div><span class="lab">Max drawdown</span><span class="val">{r["max_drawdown"]:.2f} $</span></div>'
         f'<div><span class="lab">t-stat</span><span class="val">{r["t_stat"]:+.2f}</span></div>')
    return (f'<div class="carte"><h2>{titre}</h2><div class="kpis">{k}</div>'
            f'<div class="spark">{spark}</div>'
            f'<p class="verdict">{html.escape(r["verdict"])}</p></div>')


def _ab(res):
    r25, r23 = res.get("25_convergence_basis"), res.get("23_carry_funding")
    if not r25 or not r23:
        return ('<div class="ab muted">A/B 25 vs 23 : en attente de trades fermés '
                'des deux côtés.</div>')
    d = r25["esperance_par_trade"] - r23["esperance_par_trade"]
    cls = "pos" if d > 0 else "neg"
    txt = "Bot 25 DEVANT le carry simple" if d > 0 else "Bot 25 derrière le carry simple"
    return (f'<div class="ab"><b>A/B décisif — convergence vs carry simple :</b> '
            f'<span class="{cls}">Δ espérance = {d:+.4f} $/trade</span> — {txt}.'
            f'<br><span class="muted">Verdict recherché : bot 25 bat le bot 23 avec '
            f't-stat ≥ 2 sur ≥ 2–4 semaines. Sinon → KILL.</span></div>')


def _positions():
    try:
        with (ETAT / "etat_bot25.json").open(encoding="utf-8") as f:
            etat = json.load(f)
    except (OSError, ValueError):
        return ""
    rows = []
    for coin, st in sorted(etat.items()):
        if isinstance(st, dict) and st.get("ouvert"):
            p = st.get("premium_entree", 0.0) * 100
            since = html.escape(str(st.get("entree_ts") or "")[:16])
            rows.append(f"<tr><td>{html.escape(coin)}</td><td>{p:+.3f}%</td><td>{since}</td></tr>")
    if not rows:
        return ('<div class="carte"><h2>Positions bot 25 ouvertes</h2>'
                '<p class="muted">Aucune (en attente d\'un premium étiré).</p></div>')
    return ('<div class="carte"><h2>Positions bot 25 ouvertes</h2><table>'
            '<tr><th>Actif</th><th>Premium entrée</th><th>Depuis (UTC)</th></tr>'
            + "".join(rows) + "</table></div>")


def construire_dashboard():
    lignes = charger_journal()
    res = evaluer(lignes)
    series = _cumul(lignes)
    maj = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    cartes = "".join(_carte(b, res.get(b), _spark(series.get(b, []))) for b in ORDRE)
    doc = (
        '<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<meta http-equiv="refresh" content="600">'
        '<title>Banc paper-trading</title><style>' + CSS + '</style></head><body>'
        '<h1>Banc paper-trading — argent 100 % fictif</h1>'
        f'<div class="maj">Mis à jour : {maj} · rafraîchissement auto ~10 min</div>'
        '<div class="maj"><a href="station.html">station</a> · <a href="equipage.html">équipage</a> · <a href="brief.md">brief</a> · <a href="book.html">book</a></div>'
        + _ab(res) + cartes + _positions() +
        '<footer>Lecture seule sur APIs publiques (Hyperliquid, Paradex, ADEN). '
        'Aucun ordre réel, aucun wallet, aucune clé. Le t-stat est peu fiable pour '
        'un profil asymétrique : lire l\'espérance ET le nombre de trades. Rien en '
        'argent réel sans verdict « edge positif » confirmé.</footer></body></html>'
    )
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "index.html").write_text(doc, encoding="utf-8")
    print("[dashboard] docs/index.html régénéré", flush=True)
