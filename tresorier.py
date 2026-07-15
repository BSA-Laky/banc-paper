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

Sortie : promotions.json (paper|candidat|arme|live|pause par bot) + etat/tresorier_out.json
(file de messages que le telegram_gateway envoie). Mise en service = DOUBLE geste du
Commandant via le gateway : "go <bot>" (arme, 30 min) PUIS "confirme <bot>" -> 'live'.
Un armement non confirme est desarme ici a la passe suivante (>30 min).
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
# Drawdown : mdd_live du moniteur est en DOLLARS (drawdown du P&L cumule, mises
# paper ~100 $), PAS en %. Plafond = fraction de l'enveloppe, convertie en $.
DD_FRACTION_ENV = 0.30    # pause au-dela de 30 % de l'enveloppe (en $)
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
    if bot not in cfg.get("bots", {}):
        return 0.0
    return float(cfg.get("enveloppe_par_bot_eur", 0)) * float(cfg.get("eurusd", 1.07))


def _concurrence():
    """Positions simultanees estimees par bot (loi de Little) depuis le ledger."""
    hold = {"28_carry_hold": 2.0}
    ts_par = {}
    try:
        with LEDGER.open(encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                if r.get("status") != "closed":
                    continue
                try:
                    t = datetime.fromisoformat(str(r.get("closed_at") or r.get("opened_at")).replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    continue
                ts_par.setdefault(r["bot"], []).append(t)
    except OSError:
        pass
    out = {}
    for bot, ts in ts_par.items():
        if len(ts) < 3:
            out[bot] = 0.0
            continue
        ts.sort()
        jours = max(0.5, (ts[-1] - ts[0]).total_seconds() / 86400)
        out[bot] = (len(ts) / jours) * hold.get(bot, 1.0)
    return out


def gestion_enveloppe():
    """Rapport de gestion d'enveloppe (300 EUR/bot) -> docs/enveloppes.json.
    Montre, par bot : mise/entree, positions max, deploiement moyen estime, libre."""
    cfg = _lire_json(CONFIG_PF, {})
    eu = float(cfg.get("eurusd", 1.07))
    env_eur = float(cfg.get("enveloppe_par_bot_eur", 300))
    env_usd = env_eur * eu
    conc = _concurrence()
    rap = {}
    for bot, b in cfg.get("bots", {}).items():
        pmax = int(b.get("positions_max", 1)) or 1
        mise_usd = env_usd / pmax
        c = min(conc.get(bot, 0.0), pmax)               # borne par l'enveloppe
        deploye = min(c * mise_usd, env_usd)
        rap[bot] = {"enveloppe_eur": round(env_eur),
                    "positions_max": pmax,
                    "mise_entree_eur": round(mise_usd / eu, 2),
                    "positions_estimees": round(c, 1),
                    "deploye_moyen_eur": round(deploye / eu, 2),
                    "libre_moyen_eur": round((env_usd - deploye) / eu, 2),
                    "usage_pct": round(100 * deploye / env_usd)}
    _ecrire_json(DOCS / "enveloppes.json",
                 {"ts": datetime.now(timezone.utc).isoformat(),
                  "enveloppe_par_bot_eur": round(env_eur), "bots": rap})
    return rap


def checklist(bot, v, histo, pnls, cap_dd_usd):
    """Renvoie (pret: bool, manquants: list[str]). Toute la liste doit passer."""
    m = []
    if v.get("statut") != "VERT":
        m.append("statut != VERT (%s)" % v.get("statut"))
    if (v.get("t_stat") or 0) < 2:
        m.append("t %.2f < 2" % (v.get("t_stat") or 0))
    if not _jamais_negatif(pnls):
        m.append("P&L cumule deja passe negatif")
    if (v.get("mdd_live") or 0) > cap_dd_usd:
        m.append("drawdown %.0f$ > %.0f$ (30%% de l'enveloppe)"
                 % (v.get("mdd_live") or 0, cap_dd_usd))
    # garde TROP-BEAU (15/07) : bloque UNIQUEMENT si l'ecart n'a pas ete audite
    # (audit 28 du 15/07 : funding reel verifie -> champ trop_beau_audite du moniteur)
    mu_ref = v.get("mu_ref")
    if mu_ref and (v.get("esperance") or 0) > 2.0 * float(mu_ref) and not v.get("trop_beau_audite"):
        m.append("esp %.2f = %.1fx la ref backtest (%.2f) -- inexplique = pas de promotion"
                 % (v.get("esperance") or 0, (v.get("esperance") or 0) / float(mu_ref), float(mu_ref)))
    ab = v.get("ab")
    if isinstance(ab, dict) and ab.get("delta_esperance") is not None:
        if float(ab["delta_esperance"]) <= 0:
            m.append("perd l'A/B vs %s" % ab.get("contre", "?"))
    vj = _vert_jours(histo, bot)
    if vj < N_JOURS_VERT:
        m.append("VERT depuis %d j < %d" % (vj, N_JOURS_VERT))
    return (len(m) == 0, m)


def _returns_par_bot():
    """Rendements par trade (pnl / size_usd) par bot, depuis le ledger."""
    out = {}
    try:
        with LEDGER.open(encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                if r.get("status") != "closed":
                    continue
                try:
                    sz = float(r["size_usd"]); pnl = float(r["pnl"])
                    if sz > 0:
                        out.setdefault(r["bot"], []).append(pnl / sz)
                except (KeyError, ValueError):
                    pass
    except OSError:
        pass
    return out


def _levier_kelly(rets, kfrac, lmax):
    """Levier recommande = fraction de Kelly = kfrac * mu/var (rendements). Borne [1, lmax]."""
    n = len(rets)
    if n < 20:
        return 1.0
    mu = sum(rets) / n
    var = sum((x - mu) ** 2 for x in rets) / (n - 1)
    if var <= 0 or mu <= 0:
        return 1.0
    return round(max(1.0, min(kfrac * (mu / var), lmax)), 2)


def evaluer():
    now = datetime.now(timezone.utc)
    jour = now.date().isoformat()
    gr = _lire_json(F_GOREEL, {})
    cfg = _lire_json(CONFIG_PF, {"capital_total_usd": 0.0, "bots": {}})
    promo = _lire_json(F_PROMO, {"bots": {}, "deja": []})
    promo.setdefault("bots", {}); promo.setdefault("deja", [])
    histo = _maj_histo(_lire_json(F_HISTO, {}), gr, jour)
    pnls = _pnl_par_bot()
    rets = _returns_par_bot()
    kfrac = float(cfg.get("kelly_fraction", 0.25))
    lmax = float(cfg.get("levier_max", 3.0))
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

        # armement expire (>30 min sans "confirme") -> retour a l'etat d'avant
        if etat == "arme":
            b = promo["bots"].get(bot, {})
            try:
                age_min = (now - datetime.fromisoformat(str(b.get("arme")))).total_seconds() / 60
            except (ValueError, TypeError):
                age_min = 9999.0
            if age_min > 30:
                etat = b.get("etat_avant", "candidat")
                promo["bots"][bot] = {"etat": etat}
                interpelle("desarme:%s:%s" % (bot, jour),
                           "Armement de %s expire sans confirmation -> redevenu %s." % (bot, etat))

        # retrograde si le bot deraille
        if etat in ("candidat", "arme", "live", "pause") and (v.get("statut") == "ROUGE" or v.get("decrochage")):
            promo["bots"][bot] = {"etat": "paper"}
            interpelle("retro:%s:%s" % (bot, jour),
                       "Le bot %s a decroche (statut %s) -> retire du reel, enveloppe liberee."
                       % (bot, v.get("statut")))
            continue

        # garde-fou drawdown sur un bot live (plafond en $ = 30 % de l'enveloppe)
        cap_dd = DD_FRACTION_ENV * float(cfg.get("enveloppe_par_bot_eur", 300)) * float(cfg.get("eurusd", 1.07))
        if etat == "live" and (v.get("mdd_live") or 0) > cap_dd:
            promo["bots"][bot] = {"etat": "pause"}
            interpelle("dd:%s:%s" % (bot, jour),
                       "Bot %s : drawdown %.0f$ > %.0f$ (30%% de l'enveloppe) -> nouvelles entrees EN PAUSE (positions non touchees)."
                       % (bot, v.get("mdd_live") or 0, cap_dd))
            etat = "pause"

        pret, manque = checklist(bot, v, histo, pnls.get(bot, []), cap_dd)
        if pret and etat == "paper":
            lev = _levier_kelly(rets.get(bot, []), kfrac, lmax)
            promo["bots"][bot] = {"etat": "candidat", "depuis": jour, "levier": lev}
            interpelle("cand:%s" % bot,
                       "Le bot %s a passe TOUTES les verifications (n=%s, t=%.2f, P&L jamais negatif, "
                       "VERT %d j). Levier recommande %.2fx (Kelly frac.).\n"
                       "Repondre \"go %s\" pour confirmer."
                       % (bot, v.get("n"), v.get("t_stat") or 0, _vert_jours(histo, bot), lev, bot))

        e = promo["bots"].get(bot, {}).get("etat", "paper")
        if e in ("candidat", "arme"):
            candidats.append(bot)
        elif e == "live":
            lives.append(bot)
        elif e == "pause":
            pauses.append(bot)

    for _b in promo["bots"]:
        if promo["bots"][_b].get("etat") in ("candidat", "arme", "live", "pause"):
            promo["bots"][_b]["levier"] = _levier_kelly(rets.get(_b, []), kfrac, lmax)

    # controle du capital pour candidats + live
    besoin = sum(_plafond(cfg, b) for b in candidats + lives + pauses)
    dispo = float(cfg.get("capital_reel_usd", 0.0))       # solde HL reel (0 tant que paper)
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
