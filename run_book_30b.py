#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_book_30b.py - runner du JUMEAU EXECUTABLE du book trend (bot 30b + temoin).
===============================================================================
POURQUOI UN RUNNER SEPARE
-------------------------
Le bot 30b doit tourner a cote du bot 30, sur les MEMES donnees du meme mois,
pour que l'A/B « combien de l'edge survit a la traduction ETF -> CFD » soit
propre. La facon evidente serait d'ajouter deux lignes dans run_book.py.

On ne le fait pas, et c'est deliberé : editer un fichier existant dans
l'editeur web GitHub est precisement ce qui a duplique un fichier et casse la
station 24 h (CodeMirror virtualise les lignes, un collage ne couvre que la
partie visible). Tant que le Commandant ne peut pas editer lui-meme, on
n'ajoute QUE des fichiers neufs. C'est plus verbeux, c'est sans risque.

Ce runner reutilise telles quelles les fonctions de run_book.py : meme source
de donnees (Twelve Data via donnees_marche), meme mois de reference, meme
journal (book_trades.csv). Il ne duplique aucune logique.

CADENCE : mensuel, comme le book. Une passe = un point de mesure.
stdlib uniquement.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from banc_essai_paper_trading import journaliser
from bot_trend_executable import TrendExecutable, ControleCFD, cout_traduction

LEDGER = Path("book_trades.csv")
DOCS = Path("docs")


def lancer() -> None:
    # meme fetch que le book principal : une seule source de verite pour les prix
    try:
        from run_book import fetch_marche
    except Exception as e:  # noqa: BLE001
        print("[30b] import run_book impossible : %s" % e, flush=True)
        return
    try:
        marche = fetch_marche()
    except Exception as e:  # noqa: BLE001
        print("[30b] fetch marche KO : %s" % e, flush=True)
        return
    if not marche.get("monthly"):
        print("[30b] aucune donnee (TD_KEY absente ou API KO) -> rien.", flush=True)
        return

    bots = [TrendExecutable(), ControleCFD()]
    nouveaux = []
    for b in bots:
        try:
            nouveaux.extend(b.step(marche))
        except Exception as e:  # noqa: BLE001
            print("[30b] %s a leve : %s" % (b.name, e), flush=True)
    if nouveaux:
        journaliser(nouveaux, LEDGER)
        print("[30b] %d trade(s) solde(s) (asof %s)" % (len(nouveaux), marche["asof"]),
              flush=True)

    # diagnostic de traduction : ce que le passage ETF -> CFD COUTE, chiffre,
    # publie a chaque passe pour que l'A/B soit lisible sans attendre des annees.
    try:
        d = cout_traduction(marche["monthly"], marche["asof"])
        d["ts"] = datetime.now(timezone.utc).isoformat()
        DOCS.mkdir(parents=True, exist_ok=True)
        (DOCS / "traduction_cfd.json").write_text(
            json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        print("[30b] traduction : %d lignes ETF -> %d CFD (%.0f %% du book perdu)"
              % (d["lignes_etf"], d["lignes_cfd"], d["part_du_book_perdue_pct"]),
              flush=True)
    except Exception as e:  # noqa: BLE001
        print("[30b] diagnostic traduction KO : %s" % e, flush=True)


if __name__ == "__main__":
    lancer()
