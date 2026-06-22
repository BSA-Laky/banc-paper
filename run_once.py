#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run_once.py - point d'entrée CLOUD (une passe par exécution, appelé par le cron).

A chaque exécution (GitHub Actions, ~15 min) : UN step() pour témoin + bot 23
(baseline) + bot 24 (multi-venues) + bot 25 (hypothèse), journalise les trades
fermés, puis régénère docs/index.html. 100 % fictif, lecture seule. stdlib only.
"""
from __future__ import annotations

from banc_essai_paper_trading import ControleAleatoire, journaliser
from bots_cloud import CarryFundingOnly, ConvergenceBasis
from bot_24_funding_multivenues import FundingMultiVenues
from bot_27_convex_buckets import ConvexBuckets
from dashboard import construire_dashboard


def lancer_passe() -> None:
    bots = [
        ControleAleatoire(stake_usd=1.0),
        CarryFundingOnly(actifs="*"),
        ConvergenceBasis(actifs="*"),
        FundingMultiVenues(),     # bot 24 : HL/Paradex/ADEN (seuils 1e-4)
        ConvexBuckets(),          # bot 27 : experience edge convexe (3 buckets)
    ]
    nouveaux = []
    for b in bots:
        try:
            nouveaux.extend(b.step())
        except Exception as e:    # un bot ne doit jamais tuer la passe
            print(f"[run_once] {b.name} a leve : {e}", flush=True)
    if nouveaux:
        journaliser(nouveaux)
    print(f"[run_once] {len(nouveaux)} trade(s) solde(s) cette passe.", flush=True)


if __name__ == "__main__":
    lancer_passe()
    construire_dashboard()
