
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run_once.py - point d'entrée CLOUD (une passe par exécution, appelé par le cron).

A chaque exécution (GitHub Actions, ~15 min) : UN step() pour témoin + bot 23
(baseline) + bot 24 (multi-venues) + bot 25 (hypothèse), journalise les trades
fermés, puis régénère docs/index.html. 100 % fictif, lecture seule. stdlib only.
"""
from __future__ import annotations

import json
from pathlib import Path

from banc_essai_paper_trading import ControleAleatoire, journaliser
from bot_25_convergence_basis import ConvergenceBasis
from bot_27_convex_buckets import ConvexBuckets
from bot_28_carry_hold import CarryHold
from bot_29_carry_neutre import CarryNeutre
from bot_32_carry_crossvenue import CarryCrossVenue
from bot_27e_arbitre import ArbitreRegime
from bot_27f_selecteur import SelecteurInforme
from dashboard import construire_dashboard


def lancer_passe() -> None:
    try:                          # GARDE-FOU comptable : aucun bot ne doit inventer son P&L
        import audit_conformite
        audit_conformite.auditer()
    except Exception as e:
        print(f"[run_once] audit_conformite a leve : {e}", flush=True)
    try:                          # gate du PROJET lui-meme (echeance 31/12/2026, critere capital)
        import regle_arret_projet
        regle_arret_projet.evaluer()
    except Exception as e:
        print(f"[run_once] regle_arret a leve : {e}", flush=True)
    try:                          # jalon 15/09 famille 29 : photographie le funding capte (lecture seule)
        import jalon_29
        jalon_29.observer()
    except Exception as e:
        print(f"[run_once] jalon_29 a leve : {e}", flush=True)
    # avis_piece_ia RETIRE le 15/08/2026 : son seul consommateur etait le bot 27f,
    # retire le meme jour. Appel payant sans lecteur -> supprime. Le module reste
    # dans le depot, il suffit de remettre l'appel pour le rallumer.
    bots = [
        ControleAleatoire(stake_usd=1.0),
        ConvergenceBasis(actifs="*"),   # bot 25 : comptabilite REELLE depuis le 29/07 (etait dans bots_cloud)
        ConvexBuckets(),          # bot 27 : experience edge convexe (4 buckets)
        CarryHold(),              # bot 28 : carry-hold, comptabilite CORRIGEE le 26/07 (prix + funding signe)
        CarryNeutre(),            # bot 29 : carry DOLLAR-NEUTRE (3 shorts/3 longs) - l'A/B montre que la neutralite EST l'edge
        ArbitreRegime(),          # bot 27e : arbitre regime 27b/27c (hypothese mesuree, prior negatif)
        SelecteurInforme(),               # bot 27f : selecteur informe (signal par piece + IA), seuil 20%
        SelecteurInforme(move_big=0.10),  # bot 27f10 : jumeau rapide seuil 10% (verdict ~1 sem.)
        SelecteurInforme(move_big=0.10, ia_seule=True),  # bot 27g10 : PUR LLM (agit uniquement sur avis IA)
        CarryCrossVenue(),        # bot 32 : carry de funding croise HL<->Nado. MESURE SEULEMENT :
                                  # NON_EXECUTABLES le bloque avant VERT (pas de compte Nado).
    ]
    # Cycle de vie (17/07) : un bot au verdict KILL pré-enregistré (etat/cycle_vie.json,
    # écrit par le moniteur) n'est plus échantillonné ; ledger et état conservés
    # (archive). Réactivation humaine : « relance <bot> » sur Telegram.
    try:
        cv = json.loads(Path("etat/cycle_vie.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cv = {}
    tues = {b for b, v in (cv.get("bots", {}) or {}).items() if v.get("etat") == "kill"}
    if tues:
        bots = [b for b in bots if b.name not in tues]
        print(f"[run_once] au tapis (verdict pré-enregistré) : {sorted(tues)}", flush=True)
    nouveaux = []
    # VERROU UNIVERSEL (28/08/2026). Le filtre ci-dessus teste le nom de l'OBJET.
    # Un module qui emet sous d'autres etiquettes lui echappe : c'est arrive avec
    # bot_27_convex_buckets, un seul objet "27_convex_buckets" qui emet 27a/27b/
    # 27c/27d -- retires le 15/08, ils ont ecrit 491 trades de plus. On filtre donc
    # aussi a la SORTIE, sur l'etiquette portee par chaque Trade.
    def _vivant(t):
        etiquette = getattr(t, "bot", None)
        if etiquette in tues:
            print(f"[run_once] trade ignore : {etiquette} est tue", flush=True)
            return False
        return True

    for b in bots:
        try:
            nouveaux.extend(t for t in b.step() if _vivant(t))
        except Exception as e:    # un bot ne doit jamais tuer la passe
            print(f"[run_once] {b.name} a leve : {e}", flush=True)
    if nouveaux:
        journaliser(nouveaux)
    print(f"[run_once] {len(nouveaux)} trade(s) solde(s) cette passe.", flush=True)


if __name__ == "__main__":
    lancer_passe()
    try:                          # gestion d'enveloppe 300 EUR/bot (avant le dashboard)
        import tresorier
        tresorier.gestion_enveloppe()
    except Exception as e:
        print(f"[run_once] gestion_enveloppe a leve : {e}", flush=True)
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
        import execution          # docs/execution.json : ordres testnet + mainnet
        execution.produire()
    except Exception as e:                       # jamais bloquant pour la passe
        print("[run_once] execution KO : %s" % e, flush=True)
    try:
        import equipage           # s'execute a l'import : ecrit docs/equipage.html
    except Exception as e:
        print(f"[run_once] equipage a leve : {e}", flush=True)
