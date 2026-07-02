#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tour_de_controle.py - brief quotidien de la Station (cloud, PC eteint, 0 token)
===============================================================================
Genere docs/brief.md (lisible sur telephone via GitHub Pages) et docs/brief.json
(consomme par Fable 5 / agents en session) a partir de go_reel.json, du ledger
et de 2 appels Hyperliquid (evenements extremes du jour, tendances BTC n-x).
Detecte les CHANGEMENTS de statut depuis la veille (etat/statuts_veille.json).
Deterministe, stdlib only, lecture seule, jamais bloquant. Aucune decision :
il constate, il n'ordonne rien.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from banc_essai_paper_trading import charger_journal, LEDGER_PATH

BOOK_LEDGER = Path("book_trades.csv")
GO_REEL = Path("docs") / "go_reel.json"
BRIEF_MD = Path("docs") / "brief.md"
BRIEF_JSON = Path("docs") / "brief.json"
STATUTS_VEILLE = Path("etat") / "statuts_veille.json"
HL_INFO_URL = "https://api.hyperliquid.xyz/info"
USER_AGENT = "paper-trading-bench/1.0 (read-only research)"
MOVE_EXTREME = 0.20
VOL_MIN = 1_000_000.0


def _http_post_info(body, timeout=12.0):
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(HL_INFO_URL, data=data,
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, OSError):
        return None


def _evenements_extremes():
    rep = _http_post_info({"type": "metaAndAssetCtxs"})
    out = []
    try:
        univ, ctxs = rep[0]["universe"], rep[1]
    except (TypeError, KeyError, IndexError):
        return out
    for i, coin in enumerate(univ):
        if i >= len(ctxs):
            break
        c = ctxs[i] or {}
        try:
            mark, prev = float(c.get("markPx")), float(c.get("prevDayPx"))
            vol = float(c.get("dayNtlVlm") or 0.0)
        except (TypeError, ValueError):
            continue
        if prev > 0 and vol >= VOL_MIN:
            move = (mark - prev) / prev
            if abs(move) >= MOVE_EXTREME:
                out.append({"coin": str(coin.get("name", "?")), "move_pct": round(move * 100, 1)})
    return sorted(out, key=lambda d: -abs(d["move_pct"]))[:10]


def _tendances_btc():
    fin = int(time.time() * 1000)
    rep = _http_post_info({"type": "candleSnapshot",
                           "req": {"coin": "BTC", "interval": "1d",
                                   "startTime": fin - 40 * 86400_000, "endTime": fin}})
    if not isinstance(rep, list) or len(rep) < 31:
        return None
    try:
        cl = [float(b["c"]) for b in rep]
        return {"ret1": round(cl[-1] / cl[-2] - 1, 4), "ret7": round(cl[-1] / cl[-8] - 1, 4),
                "ret30": round(cl[-1] / cl[-31] - 1, 4), "prix": round(cl[-1])}
    except (TypeError, KeyError, ValueError, ZeroDivisionError):
        return None


def _dernieres_actions(n=8):
    """Derniers trades fermes (toutes salles trading), pour le journal de bord."""
    try:
        lignes = charger_journal(LEDGER_PATH) + charger_journal(BOOK_LEDGER)
    except Exception:
        return []
    fermes = [l for l in lignes if l.get("status") == "closed" and l.get("closed_at")]
    fermes.sort(key=lambda l: l.get("closed_at", ""), reverse=True)
    out = []
    for l in fermes[:n]:
        try:
            pnl = round(float(l.get("pnl") or 0.0), 2)
        except (TypeError, ValueError):
            pnl = 0.0
        out.append({"ts": str(l.get("closed_at", ""))[:16], "bot": l.get("bot", "?"),
                    "marche": l.get("market", "?"), "pnl": pnl})
    return out


def _changements_statut(bots):
    actuels = {b: v.get("statut", "?") for b, v in bots.items()}
    anciens = {}
    try:
        with STATUTS_VEILLE.open(encoding="utf-8") as fh:
            anciens = json.load(fh)
    except (OSError, ValueError):
        pass
    chg = [{"bot": b, "avant": anciens.get(b, "—"), "apres": s}
           for b, s in sorted(actuels.items()) if anciens.get(b) != s and b in anciens]
    try:
        STATUTS_VEILLE.parent.mkdir(parents=True, exist_ok=True)
        with STATUTS_VEILLE.open("w", encoding="utf-8") as fh:
            json.dump(actuels, fh)
    except OSError:
        pass
    return chg


def produire_brief():
    try:
        with GO_REEL.open(encoding="utf-8") as fh:
            gr = json.load(fh)
    except (OSError, ValueError):
        gr = {"bots": {}, "alertes": [], "avertissements": [], "temoins": {}, "banc_suspect": False}

    bots = gr.get("bots", {})
    doc = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "alertes": gr.get("alertes", []),
        "avertissements": gr.get("avertissements", []),
        "banc_suspect": bool(gr.get("banc_suspect")),
        "changements_statut": _changements_statut(bots),
        "statuts": {b: {"statut": v.get("statut"), "n": v.get("n"),
                        "esperance": v.get("esperance"), "t": v.get("t_stat"),
                        "fwd_j": v.get("jours_forward")} for b, v in sorted(bots.items())},
        "tendances_btc": _tendances_btc(),
        "evenements_extremes": _evenements_extremes(),
        "dernieres_actions": _dernieres_actions(),
        "calibration_arbitre": gr.get("calibration_arbitre"),
    }
    try:
        BRIEF_JSON.parent.mkdir(parents=True, exist_ok=True)
        with BRIEF_JSON.open("w", encoding="utf-8") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=1)
    except OSError:
        pass

    # ---- markdown lisible sur telephone
    L = [f"# Brief Station — {doc['ts'][:16]} UTC", ""]
    if doc["alertes"] or doc["banc_suspect"]:
        L.append("## 🔴 ALERTES")
        if doc["banc_suspect"]:
            L.append("- **BANC SUSPECT** : un temoin a |t| >= 2 — ne rien conclure.")
        L += [f"- {a}" for a in doc["alertes"]]
        L.append("")
    if doc["avertissements"]:
        L.append("## 🟠 Avertissements")
        L += [f"- {a}" for a in doc["avertissements"]]
        L.append("")
    if doc["changements_statut"]:
        L.append("## Changements de statut depuis hier")
        L += [f"- {c['bot']} : {c['avant']} → **{c['apres']}**" for c in doc["changements_statut"]]
        L.append("")
    L.append("## Statuts gate (GO-reel)")
    L.append("| Bot | Statut | n | esp | t | fwd |")
    L.append("|---|---|---|---|---|---|")
    for b, v in doc["statuts"].items():
        L.append(f"| {b} | {v['statut']} | {v['n']} | {v['esperance']} | {v['t']} | {v['fwd_j']} j |")
    L.append("")
    tb = doc["tendances_btc"]
    if tb:
        L.append(f"**BTC** {tb['prix']} $ — ret 1j {tb['ret1']:+.2%} · 7j {tb['ret7']:+.2%} · 30j {tb['ret30']:+.2%}")
    if doc["evenements_extremes"]:
        ev = ", ".join(f"{e['coin']} {e['move_pct']:+.1f}%" for e in doc["evenements_extremes"])
        L.append(f"**Moves 24h ≥ 20 %** : {ev}")
    if doc["calibration_arbitre"]:
        L.append(f"**Calibration arbitre (J+7)** : {json.dumps(doc['calibration_arbitre'], ensure_ascii=False)}")
    L += ["", "_Genere automatiquement (PC eteint). Rien ici n'est un ordre : la gate decide,",
          "le Commandant tranche. Zero argent reel._"]
    try:
        with BRIEF_MD.open("w", encoding="utf-8") as fh:
            fh.write("\n".join(L) + "\n")
    except OSError:
        pass
    return doc


if __name__ == "__main__":
    d = produire_brief()
    print(f"[tour] brief genere : {len(d['statuts'])} bots, "
          f"{len(d['alertes'])} alerte(s), {len(d['changements_statut'])} changement(s).", flush=True)
