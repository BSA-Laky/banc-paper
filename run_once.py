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
from bot_26_carry_nado import CarryNado
from bot_27_convex_buckets import ConvexBuckets
from bot_28_carry_hold import CarryHold
from bot_27e_arbitre import ArbitreRegime
from bot_27f_selecteur import SelecteurInforme
from dashboard import construire_dashboard


def lancer_passe() -> None:
    try:                          # avis LLM par piece (best-effort, budget-cape, jamais bloquant)
        import avis_piece_ia
        avis_piece_ia.produire_avis()
    except Exception as e:
        print(f"[run_once] avis_piece a leve : {e}", flush=True)
    bots = [
        ControleAleatoire(stake_usd=1.0),
        CarryFundingOnly(actifs="*"),
        ConvergenceBasis(actifs="*"),
        FundingMultiVenues(),     # bot 24 : HL/Paradex/ADEN (seuils 1e-4)
        CarryNado(),              # bot 26 : carry cross-venue Nado (dormant si endpoint KO)
        ConvexBuckets(),          # bot 27 : experience edge convexe (4 buckets)
        CarryHold(),              # bot 28 : carry-hold (edge VALIDE OOS, confirmation forward)
        ArbitreRegime(),          # bot 27e : arbitre regime 27b/27c (hypothese mesuree, prior negatif)
        SelecteurInforme(),               # bot 27f : selecteur informe (signal par piece + IA), seuil 20%
        SelecteurInforme(move_big=0.10),  # bot 27f10 : jumeau rapide seuil 10% (verdict ~1 sem.)
        SelecteurInforme(move_big=0.10, ia_seule=True),  # bot 27g10 : PUR LLM (agit uniquement sur avis IA)
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
    try:                          # gate GO-reel + decrochage (jamais bloquant)
        from moniteur_go_reel import produire_go_reel
        produire_go_reel()
    except Exception as e:
        print(f"[run_once] moniteur go_reel a leve : {e}", flush=True)
    try:                          # tresorier : promotions + interpellations (jamais bloquant)
        import tresorier
        tresorier.evaluer()
    except Exception as e:
        print(f"[run_once] tresorier a leve : {e}", flush=True)
    try:                          # brief Station (PC eteint, jamais bloquant)
        from tour_de_controle import produire_brief
        produire_brief()
    except Exception as e:
        print(f"[run_once] tour de controle a leve : {e}", flush=True)
    try:                          # tableau Equipage (deterministe, jamais bloquant)
        import equipage           # s'execute a l'import : ecrit docs/equipage.html
    except Exception as e:
        print(f"[run_once] equipage a leve : {e}", flush=True)
