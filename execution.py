#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
execution.py - suivi des ORDRES REELLEMENT PASSES, testnet et mainnet
=====================================================================
Demande du Commandant (13/08/2026) : suivre bot par bot les positions ouvertes
en direct et l'historique de leurs placements, avec de quoi les retrouver sur
l'explorateur Hyperliquid.

Ce module ne DECIDE rien et n'execute rien : il lit ce que les executeurs ont
deja ecrit et le met en forme pour docs/execution.html.

Sources (aucune n'est creee ici) :
  testnet : etat/testnet_trades.csv      (journal des ordres)
            etat/executeur_testnet.json  (positions ouvertes, verite executeur)
  mainnet : etat/reel_trades.csv
            etat/reel_hl.json            (verite HL reconciliee)
  commun  : etat/cycle_vie.json          (quel bot est mort)

Adresses publiques : variables d'environnement HL_ADDRESS_TESTNET_PUBLIC /
HL_ADDRESS_MAINNET_PUBLIC. Ce sont des adresses de LECTURE : elles ne permettent
aucun ordre. Absentes, la page marche, simplement sans lien vers l'explorateur.

stdlib uniquement.
"""
from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ETAT = Path("etat")
DOCS = Path("docs")
SORTIE = DOCS / "execution.json"

MAX_HISTO = 150          # lignes de journal gardees par bot (les plus recentes)
# Ce fichier est regenere ~96 fois par jour et commite a chaque passe : chaque
# octet superflu finit multiplie par 96 dans l'historique git. D'ou la coupe a
# 150 lignes et le motif de rejet raccourci -- le CSV complet reste la source.


def _lj(p: Path, defaut):
    try:
        with p.open(encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return defaut


def _lignes(p: Path) -> list:
    try:
        with p.open(encoding="utf-8") as fh:
            return list(csv.DictReader(fh))
    except OSError:
        return []


def _f(x, defaut=0.0) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return defaut


def _age_h(iso: str, maintenant: datetime):
    try:
        return round((maintenant - datetime.fromisoformat(iso)).total_seconds() / 3600, 1)
    except (TypeError, ValueError):
        return None


def _recents(histo: list, maintenant: datetime, jours: float = 7.0) -> list:
    """Mouvements des N derniers jours. Une alerte doit porter sur ce que le bot
    fait MAINTENANT : le bot 29 traine 66 rejets d'une seule passe du 29/07, tous
    dus a la meme enveloppe manquante, corrigee depuis. Les compter a vie le
    ferait clignoter pour toujours et noierait un vrai probleme recent."""
    seuil = maintenant.timestamp() - jours * 86400
    out = []
    for h in histo:
        try:
            if datetime.fromisoformat(h["ts"]).timestamp() >= seuil:
                out.append(h)
        except (TypeError, ValueError):
            pass
    return out


def _resume(histo: list) -> dict:
    """Bilan d'un bot sur un environnement. Le taux de reussite ne porte que sur
    les positions SOLDEES : une position encore ouverte n'a pas de resultat."""
    fermes = [h for h in histo if h["action"] == "close" and h["pnl"] is not None]
    gagnants = [h for h in fermes if h["pnl"] > 0]
    pnl = round(sum(h["pnl"] for h in fermes), 3)
    return {
        "ordres": len([h for h in histo if h["action"] == "open"]),
        "soldes": len(fermes),
        "rejets": len([h for h in histo if h["action"] == "REJET"]),
        # 24/08/2026 : on ne melange plus "la venue a refuse mon ordre" avec
        # "il n'y avait pas de marche en face". Le second n'est pas un echec de
        # la strategie, et le confondre avec le premier a masque pendant des
        # semaines que le testnet n'a tout simplement pas de contrepartie.
        "illiquides": len([h for h in histo if h["action"] == "ILLIQUIDE"]),
        "non_apparies": len([h for h in histo if h["action"] == "NON_APPARIE"]),
        "clotures_refusees": len([h for h in histo if h["action"] == "REJET_CLOSE"]),
        "pnl_total": pnl,
        "pnl_moyen": round(pnl / len(fermes), 4) if fermes else None,
        "taux_reussite": round(len(gagnants) / len(fermes), 3) if fermes else None,
        # Motif de configuration le plus recent (action CONFIG) : dit POURQUOI un
        # bot ne place aucun ordre, au lieu de laisser deviner.
        "config": next((h["resp"] for h in histo if h["action"] == "CONFIG"), ""),
    }


def _alerte_bot(resume: dict, ouvertes: list, recent: dict = None,
                neutralite: dict = None) -> str:
    """Un bot qui ne parvient jamais a ouvrir ne perd rien -- et ne prouve rien.
    C'est la panne la plus couteuse du banc parce qu'elle est silencieuse : n
    reste bloque a zero, la gate ne peut jamais conclure, et rien ne le signale.
    Meme faute de fond que le seuil de funding trop haut du bot 28 (05/08)."""
    if resume.get("config"):
        return "NON EXECUTABLE : " + resume["config"]
    r = recent or resume          # on juge sur les 7 derniers jours
    if r["ordres"] == 0 and r["rejets"] >= 10:
        return ("MUET : %d tentatives sur 7 jours, aucune position ouverte. Ce bot "
                "ne produit AUCUNE donnee -- sa gate ne pourra jamais conclure."
                % r["rejets"])
    if r["ordres"] and r["rejets"] > 3 * r["ordres"]:
        return ("Taux de rejet eleve sur 7 jours : %d rejets pour %d ordres passes."
                % (r["rejets"], r["ordres"]))
    if r.get("clotures_refusees", 0) >= 3:
        return ("%d cloture(s) REFUSEE(S) sur 7 jours : des positions restent ouvertes "
                "au-dela de leur tenue, le miroir ne suit plus le bot."
                % r["clotures_refusees"])
    if neutralite and neutralite.get("ecart", 0) > 0.20:
        return ("Livre NON NEUTRE : exposition nette %+.0f $ sur %.0f $ brut (%.0f %%). "
                "La neutralite dollar EST l'edge de cette famille -- un panier "
                "desequilibre mesure un pari directionnel, pas la strategie."
                % (neutralite.get("net_usd", 0), neutralite.get("brut_usd", 0),
                   100 * neutralite.get("ecart", 0)))
    if r.get("illiquides", 0) >= 10 and r["ordres"] == 0:
        return ("%d jambe(s) ecartee(s) faute de carnet sur 7 jours, aucun ordre passe. "
                "Le testnet n'a pas de contrepartie sur ces pieces."
                % r["illiquides"])
    if resume["ordres"] == 0 and resume["rejets"] >= 10 and r["rejets"] == 0:
        return ("Aucun ordre passe a ce jour (%d rejets, tous anterieurs a 7 jours). "
                "Rien de recent a signaler -- surveiller la prochaine tentative."
                % resume["rejets"])
    return ""


def _environnement(journal: Path, positions: Path, tues: set, maintenant: datetime) -> dict:
    """Assemble un environnement (testnet ou mainnet) bot par bot."""
    etat_pos = _lj(positions, {})
    bots = {}

    for ln in _lignes(journal):
        bot = (ln.get("bot") or "").strip()
        if not bot:
            continue
        pnl = ln.get("pnl_est_usd")
        bots.setdefault(bot, {"histo": [], "ouvertes": []})["histo"].append({
            "ts": ln.get("ts", ""),
            "coin": ln.get("coin", ""),
            "action": ln.get("action", ""),
            "side": int(_f(ln.get("side"), 0)),
            "notional": round(_f(ln.get("notional_usd")), 2),
            "mark": _f(ln.get("mark")),
            # "ok" n'apprend rien : on ne garde le motif que quand ca a echoue.
            "resp": ((ln.get("resp") or "")[:44]
                     if (ln.get("resp") or "").strip().lower() != "ok" else ""),
            "pnl": round(_f(pnl), 3) if pnl not in (None, "") else None,
        })

    for bot, pos in etat_pos.items():
        if bot.startswith("_") or not isinstance(pos, dict):
            continue          # _rejets et compteurs internes ne sont pas des positions
        for coin, p in pos.items():
            if not isinstance(p, dict):
                continue
            bots.setdefault(bot, {"histo": [], "ouvertes": []})["ouvertes"].append({
                "coin": coin,
                "side": int(_f(p.get("side"), 0)),
                "notional": round(_f(p.get("notional")), 2),
                "entry": _f(p.get("entry")),
                "ts": p.get("ts", ""),
                "age_h": _age_h(p.get("ts", ""), maintenant),
                # Une position dont le bot est MORT n'a plus personne pour la
                # solder : elle doit sauter aux yeux, pas se fondre dans la liste.
                "orpheline": bot in tues,
            })

    sortie = {}
    for bot, d in bots.items():
        histo = sorted(d["histo"], key=lambda h: h["ts"], reverse=True)
        resume = _resume(histo)
        recent = _resume(_recents(histo, maintenant))
        ouvertes = sorted(d["ouvertes"], key=lambda p: p["ts"], reverse=True)
        sortie[bot] = {
            "tue": bot in tues,
            "neutralite": (etat_pos.get("_neutralite") or {}).get(bot),
            "alerte": _alerte_bot(resume, ouvertes, recent,
                                  (etat_pos.get("_neutralite") or {}).get(bot)),
            "resume_7j": {k: recent[k] for k in ("ordres", "soldes", "rejets", "pnl_total",
                                                 "illiquides", "non_apparies",
                                                 "clotures_refusees")},
            "ouvertes": ouvertes,
            "resume": resume,
            "histo": histo[:MAX_HISTO],
            "histo_tronque": max(0, len(histo) - MAX_HISTO),
        }
    return sortie


# --- POURQUOI LES CHIFFRES DIFFERENT (25/08/2026) ---------------------------
# Question posee : "je ne vois pas les memes chiffres sur le dashboard, sur
# execution.html et sur le testnet Hyperliquid". Reponse : ce sont TROIS
# registres distincts, et rien ne l'expliquait nulle part.
#   dashboard      = paper_trades.csv    -> le bot PAPIER, c'est lui que juge la gate
#   execution.html = testnet_trades.csv  -> les ordres REELLEMENT envoyes
#   compte testnet = ce qui a effectivement REMPLI
# Ils ne peuvent pas coincider : le testnet refuse des jambes (carnets vides), donc
# il execute un SOUS-ENSEMBLE du papier. Mesure du 24/08 : 40 % des jambes de 29c
# etaient ouvertes. Le bloc ci-dessous met les trois cote a cote avec le taux de
# remplissage, pour que l'ecart soit LU au lieu d'etre subi.
BOTS_NEUTRES = ("29_carry_neutre", "29b_carry_neutre_large", "29c_carry_decale")


def _paper_par_bot() -> dict:
    out = {}
    try:
        import csv as _csv
        with open("paper_trades.csv", encoding="utf-8") as f:
            for r in _csv.DictReader(f):
                if not r.get("pnl"):
                    continue
                d = out.setdefault(r["bot"], {"n": 0, "pnl": 0.0})
                d["n"] += 1
                d["pnl"] += _f(r["pnl"])
    except (OSError, ValueError):
        pass
    return out


def _comparaison(maintenant: datetime) -> dict:
    """Papier vs testnet, bot par bot, avec le taux de remplissage."""
    paper = _paper_par_bot()
    etat = _lj(ETAT / "executeur_testnet.json", {})
    neutre = etat.get("_neutralite") or {}
    demande = {}
    for bot, fic in (("29_carry_neutre", "etat_bot29.json"),
                     ("29b_carry_neutre_large", "etat_bot29b.json"),
                     ("29c_carry_decale", "etat_bot29c.json")):
        e = _lj(ETAT / fic, {})
        pos = e.get("positions") or {}
        if not pos:
            pos = {}
            for pid, pan in (e.get("paniers") or {}).items():
                for c, v in (pan.get("positions") or {}).items():
                    pos["%s/%s" % (pid, c)] = v
        demande[bot] = len(pos)
    lignes = []
    for bot in BOTS_NEUTRES:
        ouvert = len([k for k, v in (etat.get(bot) or {}).items() if isinstance(v, dict)])
        veut = demande.get(bot, 0)
        pa = paper.get(bot, {})
        nz = neutre.get(bot) or {}
        lignes.append({
            "bot": bot,
            "paper_n": pa.get("n"), "paper_pnl": round(pa.get("pnl", 0.0), 2),
            "jambes_demandees": veut, "jambes_ouvertes": ouvert,
            "remplissage": round(ouvert / veut, 3) if veut else None,
            "ecart_neutralite": nz.get("ecart"),
            "net_usd": nz.get("net_usd"),
        })
    morts = sorted((etat.get("_illiquides") or {}).keys())
    return {
        "lignes": lignes,
        "carnets_morts": morts,
        "n_carnets_morts": len(morts),
        "note": ("Le dashboard lit le bot PAPIER (juge par la gate). Cette page lit les "
                 "ordres REELLEMENT envoyes au testnet. Le testnet n'a pas de contrepartie "
                 "sur toutes les pieces : il execute donc un sous-ensemble du papier, et "
                 "les deux P&L n'ont aucune raison de coincider."),
        "ts": maintenant.isoformat(),
    }


def produire() -> dict:
    maintenant = datetime.now(timezone.utc)
    cv = (_lj(ETAT / "cycle_vie.json", {}).get("bots") or {})
    tues = set(b for b, v in cv.items() if (v or {}).get("etat") == "kill")

    doc = {
        "ts": maintenant.isoformat(),
        "tues": sorted(tues),
        "adresses": {
            "testnet": os.environ.get("HL_ADDRESS_TESTNET_PUBLIC", "").strip(),
            "mainnet": os.environ.get("HL_ADDRESS_MAINNET_PUBLIC", "").strip(),
        },
        "explorateur": {
            "testnet": "https://app.hyperliquid-testnet.xyz/explorer/address/",
            "mainnet": "https://app.hyperliquid.xyz/explorer/address/",
        },
        "env": {
            "testnet": _environnement(ETAT / "testnet_trades.csv",
                                      ETAT / "executeur_testnet.json", tues, maintenant),
            "mainnet": _environnement(ETAT / "reel_trades.csv",
                                      ETAT / "executeur_reel.json", tues, maintenant),
        },
    }

    doc["comparaison"] = _comparaison(maintenant)

    hl = _lj(ETAT / "reel_hl.json", {})
    if hl:
        doc["compte_mainnet"] = dict((k, hl.get(k)) for k in
                                     ("ts", "depot_usdc", "equity", "pnl_compte",
                                      "unrealized_total", "realized_fills",
                                      "fees_total", "funding_net"))
    stop = _lj(ETAT / "reel_stop.json", {})
    if stop.get("stop"):
        doc["mainnet_suspendu"] = stop.get("motif", "kill-switch actif")

    try:
        DOCS.mkdir(parents=True, exist_ok=True)
        SORTIE.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    except OSError as e:
        print("[execution] ecriture KO : %s" % e, flush=True)
        return doc

    for env in ("testnet", "mainnet"):
        b = doc["env"][env]
        ouv = sum(len(v["ouvertes"]) for v in b.values())
        print("[execution] %-8s : %d bot(s), %d position(s) ouverte(s)" % (env, len(b), ouv),
              flush=True)
    return doc


if __name__ == "__main__":
    produire()
