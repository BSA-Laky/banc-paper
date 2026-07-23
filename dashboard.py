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
    ".bdg{font-size:.68rem;font-weight:700;padding:1px 7px;border-radius:20px;margin-left:6px}"
    ".bdg.on{background:rgba(46,204,113,.16);color:#2ecc71}"
    ".bdg.reel{background:rgba(245,166,35,.18);color:#f5a623}"
    ".bdg.arret{background:rgba(231,76,60,.16);color:#e74c3c}"
    ".c-reel{border:1px solid #f5a623;box-shadow:0 0 0 1px rgba(245,166,35,.25)}"
    ".c-reel .verdict{color:#2ecc71;font-weight:600}"
    ".c-arret{opacity:.62}"
    ".cimet{margin-top:16px;border:1px solid #2a3242;border-radius:10px;padding:4px 12px;background:#12161f}"
    ".cimet summary{cursor:pointer;color:#e74c3c;font-size:.9rem;font-weight:600;padding:7px 0}"
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


ENVELOPPES_DEPUIS = "2026-07-11"    # activation des enveloppes 300 EUR


def _pnl_7j(lignes):
    from datetime import timedelta
    seuil = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    out = {}
    for l in lignes:
        if l.get("status") != "closed" or l.get("pnl") in (None, "", "None"):
            continue
        if str(l.get("closed_at") or "") >= seuil:
            out[l["bot"]] = out.get(l["bot"], 0.0) + float(l["pnl"])
    return out


def _carte(bot, r, spark, p7=None, etat="actif"):
    titre = html.escape(JOLI.get(bot, bot))
    badge = {"reel": '<span class="bdg reel">💰 RÉEL</span>',
             "arrete": '<span class="bdg arret">🛑 arrêté</span>'}.get(
                 etat, '<span class="bdg on">▶️ actif</span>')
    cc = "carte" + (" c-reel" if etat == "reel" else (" c-arret" if etat == "arrete" else ""))
    if not r:
        return (f'<div class="{cc}"><h2>{titre} {badge}</h2>'
                f'<p class="muted">Aucun trade fermé pour l\'instant.</p></div>')
    esp = r["esperance_par_trade"]
    cls = "pos" if esp > 0 else ("neg" if esp < 0 else "")
    k = (f'<div><span class="lab">Trades</span><span class="val">{r["trades"]}</span></div>'
         f'<div><span class="lab">Taux réussite</span><span class="val">{r["taux_reussite"]*100:.1f}%</span></div>'
         f'<div><span class="lab">Espérance / trade</span><span class="val {cls}">{esp:+.4f} $</span></div>'
         f'<div><span class="lab">P&amp;L total</span><span class="val">{r["pnl_total"]:+.2f} $</span></div>'
         f'<div><span class="lab">P&amp;L 7 jours</span><span class="val {"pos" if (p7 or 0) > 0 else ("neg" if (p7 or 0) < 0 else "")}">{(p7 or 0.0):+.2f} $</span></div>'
         f'<div><span class="lab">Max drawdown</span><span class="val">{r["max_drawdown"]:.2f} $</span></div>'
         f'<div><span class="lab">t-stat</span><span class="val">{r["t_stat"]:+.2f}</span></div>')
    verdict = ("💰 En ARGENT RÉEL — edge validé out-of-sample (t OOS +10). Suivi live : onglet 💰 réel."
               if etat == "reel" else html.escape(r["verdict"]))
    return (f'<div class="{cc}"><h2>{titre} {badge}</h2><div class="kpis">{k}</div>'
            f'<div class="spark">{spark}</div>'
            f'<p class="verdict">{verdict}</p></div>')


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


def _enveloppes(lignes):
    """SUIVI VIVANT des enveloppes 300 EUR (demande Commandant 15/07) : P&L a
    l'echelle de l'enveloppe depuis le 11/07 = somme (pnl/mise_paper) x mise_env."""
    try:
        cfg = json.loads(Path("portefeuille.config.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    bots_cfg = cfg.get("bots", {})
    if not bots_cfg:
        return ""
    eu = float(cfg.get("eurusd", 1.07))
    env_eur = float(cfg.get("enveloppe_par_bot_eur", 300))
    pnl_env = {}          # EUR a l'echelle enveloppe, depuis le 11/07
    n_tr = {}
    for l in lignes:
        b = l.get("bot")
        if b not in bots_cfg or l.get("status") != "closed":
            continue
        if str(l.get("closed_at") or "")[:10] < ENVELOPPES_DEPUIS:
            continue
        try:
            ret = float(l["pnl"]) / float(l["size_usd"])
        except (KeyError, ValueError, ZeroDivisionError, TypeError):
            continue
        pmax = int(bots_cfg[b].get("positions_max", 1)) or 1
        mise_eur = env_eur / pmax
        pnl_env[b] = pnl_env.get(b, 0.0) + ret * mise_eur
        n_tr[b] = n_tr.get(b, 0) + 1
    try:
        usage = json.loads((DOCS / "enveloppes.json").read_text(encoding="utf-8")).get("bots", {})
    except (OSError, ValueError):
        usage = {}
    rows, total = [], 0.0
    for b in sorted(bots_cfg):
        p = pnl_env.get(b, 0.0)
        total += p
        cls = "pos" if p > 0 else ("neg" if p < 0 else "muted")
        solde = env_eur + p
        u = usage.get(b, {}).get("usage_pct", "?")
        rows.append(
            "<tr><td>%s</td><td>%.1f&nbsp;\u20ac</td><td>%s</td>"
            "<td class=\"%s\">%+.2f&nbsp;\u20ac</td><td><b>%.2f&nbsp;\u20ac</b></td><td>%s%%</td></tr>"
            % (html.escape(b), env_eur / (int(bots_cfg[b].get("positions_max", 1)) or 1),
               n_tr.get(b, 0), cls, p, solde, u))
    cls_t = "pos" if total > 0 else ("neg" if total < 0 else "")
    rows.append("<tr><td><b>TOTAL station</b></td><td></td><td></td>"
                "<td class=\"%s\"><b>%+.2f&nbsp;\u20ac</b></td><td><b>%.2f&nbsp;\u20ac</b></td><td></td></tr>"
                % (cls_t, total, env_eur * len(bots_cfg) + total))
    return ("<div class=\"carte\"><h2>Enveloppes 300 \u20ac \u2014 suivi depuis le "
            + ENVELOPPES_DEPUIS + " (paper)</h2>"
            "<table style=\"width:100%;border-collapse:collapse;font-size:.85rem\">"
            "<tr style=\"text-align:left;color:#9aa0a6\"><th>Bot</th><th>Mise/entr\u00e9e</th>"
            "<th>Trades</th><th>P&amp;L env.</th><th>Solde virtuel</th><th>Usage moy.</th></tr>"
            + "".join(rows) + "</table><div style=\"color:#9aa0a6;font-size:.75rem;margin-top:6px\">"
            "P&amp;L converti \u00e0 l'\u00e9chelle de l'enveloppe : rendement de chaque trade paper "
            "\u00d7 mise r\u00e9elle (300\u202f\u20ac \u00f7 positions max). 100 % fictif.</div></div>")


def _lj(p, d):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return d


def _generer_reel_json():
    """Consolide l'etat ARGENT REEL -> docs/reel.json (lu par docs/reel.html, cote client)."""
    import csv as _csv
    import statistics as _st
    try:
        etat = _lj(ETAT / "executeur_reel.json", {})
        stop = bool(_lj(ETAT / "reel_stop.json", {}).get("stop"))
        cfg = _lj(Path("portefeuille.reel.json"), {})
        eurusd = float(cfg.get("eurusd", 1.07))
        enveloppe = round(float(cfg.get("enveloppe_par_bot_eur", 0)) * eurusd, 2)
        depot = float(cfg.get("depot_usdc", 36.27) or 0)
        gate = (_lj(DOCS / "go_reel.json", {}) or {}).get("bots", {})
        positions = []
        for b, m in etat.items():
            if b == "_rejets" or not isinstance(m, dict):
                continue
            for coin, v in m.items():
                if isinstance(v, dict):
                    positions.append({"bot": b, "coin": coin, "side": v.get("side"),
                                      "notional": v.get("notional"), "entry": v.get("entry"),
                                      "opened_at": v.get("ts")})
        trades = []
        p = ETAT / "reel_trades.csv"
        if p.exists():
            for r in _csv.DictReader(p.open(encoding="utf-8")):
                trades.append({k: r.get(k) for k in ("ts", "bot", "coin", "action", "side",
                              "notional_usd", "mark", "resp", "pnl_est_usd")})

        def _f(x):
            try:
                return float(x)
            except (TypeError, ValueError):
                return 0.0
        now = datetime.now(timezone.utc)
        closes = [t for t in trades if t.get("action") == "close"
                  and str(t.get("pnl_est_usd") or "").strip() not in ("", "None")]

        def _stats(sous):
            pn = [_f(t["pnl_est_usd"]) for t in sous]
            n = len(pn)
            esp = round(_st.mean(pn), 4) if n else 0.0
            sd = _st.pstdev(pn) if n > 1 else 0.0
            t_stat = round(esp / (sd / (n ** 0.5)), 2) if (n > 1 and sd > 0) else 0.0
            wins = sum(1 for x in pn if x > 0)

            def _rec7(t):
                try:
                    return (now - datetime.fromisoformat(str(t.get("ts")))).days < 7
                except (ValueError, TypeError):
                    return False
            return {"n": n, "pnl_total": round(sum(pn), 4), "esp": esp, "t_stat": t_stat,
                    "taux_reussite": round(100.0 * wins / n, 1) if n else 0.0,
                    "pnl_7j": round(sum(_f(t["pnl_est_usd"]) for t in sous if _rec7(t)), 4)}

        bots = sorted({t.get("bot") for t in trades if t.get("bot")} | {q["bot"] for q in positions})
        par_bot = {}
        for b in bots:
            g = gate.get(b, {})
            par_bot[b] = {"reel": _stats([t for t in closes if t.get("bot") == b]),
                          "expo": round(sum(_f(q["notional"]) for q in positions if q["bot"] == b), 2),
                          "enveloppe": enveloppe,
                          "paper": {"n": g.get("n"), "t": g.get("t_stat"), "esp": g.get("esperance"),
                                    "pnl": g.get("pnl_cumule"), "rend_j": g.get("rendement_j_pct"),
                                    "statut": g.get("statut")}}
        doc = {"genere": now.isoformat(), "stop": stop, "depot_usdc": depot,
               "enveloppe_usd": enveloppe, "positions": positions,
               "global": _stats(closes), "par_bot": par_bot, "trades": trades[-40:]}
        DOCS.mkdir(parents=True, exist_ok=True)
        (DOCS / "reel.json").write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
        print("[dashboard] docs/reel.json : %d position(s), %d trade(s) reels" %
              (len(positions), len(closes)), flush=True)
    except Exception as e:                             # noqa: BLE001
        print("[dashboard] reel.json KO : %s" % e, flush=True)


def construire_dashboard():
    _generer_reel_json()
    lignes = charger_journal()
    res = evaluer(lignes)
    series = _cumul(lignes)
    _now = datetime.now(timezone.utc)
    maj_iso = _now.isoformat()
    maj = _now.strftime("%Y-%m-%d %H:%M UTC")
    p7 = _pnl_7j(lignes)
    reels = set((_lj(Path("portefeuille.reel.json"), {}).get("bots") or {}).keys())
    cv = (_lj(ETAT / "cycle_vie.json", {}).get("bots") or {})
    gate = (_lj(DOCS / "go_reel.json", {}).get("bots") or {})

    def _etat(b):
        if b in reels:
            return "reel"
        dd = cv.get(b, {})
        if dd.get("etat") == "kill" or (gate.get(b, {}).get("statut") == "ROUGE" and not dd.get("relance")):
            return "arrete"
        return "actif"
    etats = {b: _etat(b) for b in ORDRE}

    def _c(b):
        return _carte(b, res.get(b), _spark(series.get(b, [])), p7.get(b), etats[b])
    cartes = "".join(_c(b) for b in ORDRE if etats[b] != "arrete")
    arretes = [b for b in ORDRE if etats[b] == "arrete"]
    bloc_arret = (('<details class="cimet"><summary>🛑 Bots arrêtés / tués (%d) — sortis du banc actif, cliquer pour voir</summary>%s</details>'
                   % (len(arretes), "".join(_c(b) for b in arretes))) if arretes else "")
    doc = (
        '<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<meta http-equiv="refresh" content="900">'
        '<title>Banc paper-trading</title><style>' + CSS + '</style></head><body>'
        '<h1>Banc paper-trading — argent 100 % fictif</h1>'
        f'<div class="maj">Mis à jour : <span id="maj" data-iso="{maj_iso}">{maj}</span> · régénéré à chaque passe (~15 min)</div>'
        '<div class="maj"><a href="reel.html"><b>💰 réel</b></a> · <a href="station.html">station</a> · <a href="equipage.html">équipage</a> · <a href="brief.md">brief</a> · <a href="book.html">book</a></div>'
        + _ab(res) + cartes + _positions() + _enveloppes(lignes) + bloc_arret +
        '<footer>Lecture seule sur APIs publiques (Hyperliquid, Paradex, ADEN). '
        'Aucun ordre réel, aucun wallet, aucune clé. Le t-stat est peu fiable pour '
        'un profil asymétrique : lire l\'espérance ET le nombre de trades. Rien en '
        'argent réel sans verdict « edge positif » confirmé.</footer>'
        '<script>(function(){var e=document.getElementById("maj");if(!e){return;}'
        'var iso=e.getAttribute("data-iso");function u(){var d=new Date(iso),n=new Date();'
        'var m=Math.max(0,Math.round((n-d)/60000));'
        'var loc=d.toLocaleString("fr-FR",{day:"2-digit",month:"2-digit",hour:"2-digit",minute:"2-digit"});'
        'var r=m<1?"maintenant":(m<60?("il y a "+m+" min"):("il y a "+Math.floor(m/60)+" h "+(m%60)+" min"));'
        'e.textContent=loc+" · "+r;e.style.color=m>20?"#c0392b":"";}u();setInterval(u,30000);})();</script>'
        '</body></html>'
    )
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "index.html").write_text(doc, encoding="utf-8")
    print("[dashboard] docs/index.html régénéré", flush=True)
