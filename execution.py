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
        "pnl_total": pnl,
        "pnl_moyen": round(pnl / len(fermes), 4) if fermes else None,
        "taux_reussite": round(len(gagnants) / len(fermes), 3) if fermes else None,
    }


def _alerte_bot(resume: dict, ouvertes: list) -> str:
    """Un bot qui ne parvient jamais a ouvrir ne perd rien -- et ne prouve rien.
    C'est la panne la plus couteuse du banc parce qu'elle est silencieuse : n
    reste bloque a zero, la gate ne peut jamais conclure, et rien ne le signale.
    Meme faute de fond que le seuil de funding trop haut du bot 28 (05/08)."""
    if resume["ordres"] == 0 and resume["rejets"] >= 10:
        return ("MUET : %d tentatives, aucune position ouverte. Ce bot ne produit "
                "AUCUNE donnee -- sa gate ne pourra jamais conclure." % resume["rejets"])
    if resume["ordres"] and resume["rejets"] > 3 * resume["ordres"]:
        return ("Taux de rejet eleve : %d rejets pour %d ordres passes."
                % (resume["rejets"], resume["ordres"]))
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
        ouvertes = sorted(d["ouvertes"], key=lambda p: p["ts"], reverse=True)
        sortie[bot] = {
            "tue": bot in tues,
            "alerte": _alerte_bot(resume, ouvertes),
            "ouvertes": ouvertes,
            "resume": resume,
            "histo": histo[:MAX_HISTO],
            "histo_tronque": max(0, len(histo) - MAX_HISTO),
        }
    return sortie


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
