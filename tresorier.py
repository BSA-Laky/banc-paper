#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tresorier.py - le TRESORIER de la station (deterministe, 0 LLM, stdlib).
========================================================================
Sous-agent d'administration. Il ne DECIDE pas du reel (c'est le tap humain) et ne
RETIRE jamais. Missions :
  1. Detection VERT-STABLE : un bot n'est propose que s'il passe TOUTE la checklist
     (statut VERT tenu N jours + P&L cumule jamais negatif + drawdown sous plafond
     + bat le temoin + bat "toujours-reversion" si applicable).
  2. Allocation : enveloppe par bot depuis portefeuille.config.json.
  3. Controle capital + demande de fonds : si le capital dispo < besoin -> "il faut X USDC".
  4. Reconciliation : (live) solde reel HL vs allocations -- stub tant que paper.
  5. Compta par bot : P&L, frais (depuis le ledger).
  6. Garde-fou : drawdown d'un bot live > seuil -> alerte + PAUSE de ses nouvelles entrees
     (ne ferme jamais une position lui-meme).
  7. Rapatriement : bot retrograde (ROUGE/decrochage) -> libere son enveloppe.
  8. Rapport : etat/tresorier -> docs/tresorier.json + file d'interpellations Telegram.

Sortie : promotions.json (paper|candidat|live|pause par bot) + etat/tresorier_out.json
(file de messages que le telegram_gateway envoie). La mise en service reelle = le
Commandant repond "go <bot>" (gere par le gateway) -> passe le bot en 'live'.
"""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

DOCS = Path("docs"); ETAT = Path("etat")
F_GOREEL = DOCS / "go_reel.json"
LEDGER = Path("paper_trades.csv")          # (reel : ledger d'execution, plus tard)
F_PROMO = Path("promotions.json")
F_HISTO = ETAT / "promotion_histo.json"
F_OUT = ETAT / "tresorier_out.json"
F_RAPPORT = DOCS / "tresorier.json"
CONFIG_PF = Path("portefeuille.config.json")

N_JOURS_VERT = 5          # VERT depuis N jours consecutifs
DD_CAP = 30.0             # drawdown live max (%) avant pause
TEMOINS = {"10_controle_aleatoire", "10b_controle_book"}


def _lire_json(p, defaut):
    try:
        with Path(p).open(encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return defaut


def _ecrire_json(p, d):
    try:
        Path(p).parent.mkdir(parents=True, exist_ok=True)
        Path(p).write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        pass


def _pnl_par_bot():
    par = {}
    try:
        with LEDGER.open(encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                if r.get("status") != "closed":
                    continue
                try:
                    par.setdefault(r["bot"], []).append(float(r["pnl"]))
                except (KeyError, ValueError):
                    pass
    except OSError:
        pass
    return par


def _jamais_negatif(pnls):
    cum = 0.0
    for p in pnls:
        cum += p
        if cum < -1e-9:
            return False
    return len(pnls) > 0


def _maj_histo(histo, gr, jour):
    j = histo.setdefault("jours", {})
    etat_jour = {b: (v.get("statut") == "VERT") for b, v in gr.get("bots", {}).items()}
    j[jour] = etat_jour
    for vieux in sorted(j)[:-40]:            # ne garde que ~40 jours
        del j[vieux]
    return histo


def _vert_jours(histo, bot):
    n = 0
    for jour in sorted(histo.get("jours", {}), reverse=True):
        if histo["jours"][jour].get(bot):
            n += 1
        else:
            break
    return n


def _plafond(cfg, bot):
    b = cfg.get("bots", {}).get(bot, {})
    if b.get("max_notional") is not None:
        return float(b["max_notional"])
    if "alloc_pct" in b:
        return float(cfg.get("capital_total_usd", 0)) * float(b["alloc_pct"])
    return 0.0


def checklist(bot, v, histo, pnls):
    """Renvoie (pret: bool, manquants: list[str]). Toute la liste doit passer."""
    m = []
    if v.get("statut") != "VERT":
        m.append("statut != VERT (%s)" % v.get("statut"))
    if (v.get("t_stat") or 0) < 2:
        m.append("t %.2f < 2" % (v.get("t_stat") or 0))
    if not _jamais_negatif(pnls):
        m.append("P&L cumule deja passe negatif")
    if (v.get("mdd_live") or 0) > DD_CAP:
        m.append("drawdown %.0f%% > %.0f%%" % (v.get("mdd_live") or 0, DD_CAP))
    ab = v.get("ab")
    if isinstance(ab, dict) and ab.get("delta_esperance") is not None:
        if float(ab["delta_esperance"]) <= 0:
            m.append("perd l'A/B vs %s" % ab.get("contre", "?"))
    vj = _vert_jours(histo, bot)
    if vj < N_JOURS_VERT:
        m.append("VERT depuis %d j < %d" % (vj, N_JOURS_VERT))
    return (len(m) == 0, m)


def evaluer():
    now = datetime.now(timezone.utc)
    jour = now.date().isoformat()
    gr = _lire_json(F_GOREEL, {})
    cfg = _lire_json(CONFIG_PF, {"capital_total_usd": 0.0, "bots": {}})
    promo = _lire_json(F_PROMO, {"bots": {}, "deja": []})
    promo.setdefault("bots", {}); promo.setdefault("deja", [])
    histo = _maj_histo(_lire_json(F_HISTO, {}), gr, jour)
    pnls = _pnl_par_bot()
    out = _lire_json(F_OUT, {"pending": []})
    out.setdefault("pending", [])

    def interpelle(cle, texte):
        if cle in promo["deja"]:
            return
        out["pending"].append({"id": cle, "texte": texte, "ts": now.isoformat()})
        promo["deja"].append(cle)

    candidats, lives, pauses = [], [], []
    for bot, v in gr.get("bots", {}).items():
        if bot in TEMOINS:
            continue
        etat = promo["bots"].get(bot, {}).get("etat", "paper")

        # retrograde si le bot deraille
        if etat in ("candidat", "live", "pause") and (v.get("statut") == "ROUGE" or v.get("decrochage")):
            promo["bots"][bot] = {"etat": "paper"}
            interpelle("retro:%s:%s" % (bot, jour),
                       "Le bot %s a decroche (statut %s) -> retire du reel, enveloppe liberee."
                       % (bot, v.get("statut")))
            continue

        # garde-fou drawdown sur un bot live
        if etat == "live" and (v.get("mdd_live") or 0) > DD_CAP:
            promo["bots"][bot] = {"etat": "pause"}
            interpelle("dd:%s:%s" % (bot, jour),
                       "Bot %s : drawdown %.0f%% > %.0f%% -> nouvelles entrees EN PAUSE (positions non touchees)."
                       % (bot, v.get("mdd_live") or 0, DD_CAP))
            etat = "pause"

        pret, manque = checklist(bot, v, histo, pnls.get(bot, []))
        if pret and etat == "paper":
            promo["bots"][bot] = {"etat": "candidat", "depuis": jour}
            interpelle("cand:%s" % bot,
                       "Le bot %s a passe TOUTES les verifications (n=%s, t=%.2f, P&L jamais negatif, "
                       "VERT %d j). Pret a etre mis en service.\nRepondre \"go %s\" pour confirmer."
                       % (bot, v.get("n"), v.get("t_stat") or 0, _vert_jours(histo, bot), bot))

        e = promo["bots"].get(bot, {}).get("etat", "paper")
        if e == "candidat":
            candidats.append(bot)
        elif e == "live":
            lives.append(bot)
        elif e == "pause":
            pauses.append(bot)

    # controle du capital pour candidats + live
    besoin = sum(_plafond(cfg, b) for b in candidats + lives + pauses)
    dispo = float(cfg.get("capital_total_usd", 0.0))     # (reel : solde HL, plus tard)
    manque_usd = round(besoin - dispo, 2)
    if candidats and manque_usd > 0:
        interpelle("fonds:%s" % int(manque_usd),
                   "Capital insuffisant : il faut %.2f USDC de plus pour lancer %s "
                   "(besoin %.0f, dispo %.0f)." % (manque_usd, ", ".join(candidats), besoin, dispo))

    rapport = {"ts": now.isoformat(), "capital_dispo": dispo, "besoin_alloue": round(besoin, 2),
               "manque_usd": max(0.0, manque_usd),
               "candidats": candidats, "live": lives, "pause": pauses,
               "en_attente_telegram": len(out["pending"])}
    _ecrire_json(F_PROMO, promo)
    _ecrire_json(F_HISTO, histo)
    _ecrire_json(F_OUT, out)
    _ecrire_json(F_RAPPORT, rapport)
    print("[tresorier] candidats=%d live=%d pause=%d | interpellations en file=%d | manque=%.0f USDC"
          % (len(candidats), len(lives), len(pauses), len(out["pending"]), max(0.0, manque_usd)), flush=True)
    return rapport


if __name__ == "__main__":
    evaluer()
