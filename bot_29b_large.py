#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bot_29b_large.py - JUMEAU LARGE du carry neutre : 20 jambes au lieu de 6.
==========================================================================
POURQUOI CE BOT EXISTE
----------------------
Mesure du 05/08/2026, obtenue en recalculant avec la comptabilite correcte les
83 trades du bot 28 que la coupure du 26/07 avait ecartes (38 exploitables) :

    funding ... +0,2752 %/trade   t = +2,53   <- REEL ET SIGNIFICATIF
    prix ...... -1,3621 %/trade   t = -0,52   <- moyenne indiscernable de zero
    frais ..... -0,0900 %/trade
    NET ....... -1,1769 %/trade   t = -0,44
    ecart-type du prix : 16,15 %  -> rapport signal/bruit 0,0115

Le carry EXISTE. Ce n'est pas la moyenne du prix qui pose probleme (elle est
nulle), c'est sa VARIANCE : 16 % contre un signal de 0,185 %. Toute la question
est donc de reduire le bruit, pas de mieux predire.

DEUX LEVIERS EXAMINES, UN SEUL RETENU
-------------------------------------
1. ALLONGER LA TENUE -- ECARTE. Le rapport par trade s'ameliore, mais on fait
   d'autant moins de trades. A duree calendaire fixe :
        t = racine(T) * (f - frais/H) / sigma_horaire
   La tenue ne joue que par l'amortissement des frais : 168 h -> 720 h ne
   rapporte que x1,08 sur le t, tout en faisant passer de 52 a 12 paniers par
   an. On perdrait la granularite du suivi (un decrochage vu un mois trop tard)
   pour un gain negligeable. La tenue reste donc a 168 h.

2. PLUS DE JAMBES -- RETENU. Elles reduisent la variance DU PANIER sans reduire
   le NOMBRE de paniers. L'unite statistique independante reste le panier
   (lecon du 02/08 : les jambes co-varient fortement, le t naif surestime d'un
   facteur 3,5 a 6). Gain net : racine(20/6) = x1,83 sur le t, soit un temps de
   verdict divise par 3,3. Aucun cout : meme capital, positions de ~47 $ au lieu
   de ~158 $.

POURQUOI UN JUMEAU ET NON UNE MODIFICATION DU BOT 29
----------------------------------------------------
Changer k=3 en k=10 dans le bot 29 remplacerait une mesure en cours par une
autre, sans jamais savoir laquelle valait mieux. En le faisant tourner A COTE,
sur le meme signal et la meme tenue, seul le nombre de jambes differe : c'est
un A/B propre, exactement comme 27b/27c ou 30/30b. Si le 29b ne bat pas le 29,
l'hypothese "diversifier reduit le bruit utilement" sera fausse et on le saura.

Le bot 29 n'est pas touche. Etat separe (etat_bot29b.json), nom distinct.
stdlib uniquement.
"""
from __future__ import annotations

from pathlib import Path

from bots_cloud import ETAT_DIR
from comptabilite import Livre
from bot_29_carry_neutre import CarryNeutre

# 20 jambes : 10 shorts sur le funding le plus haut, 10 longs sur le plus bas.
# Contrainte verifiee le 05/08 : selectionner() exige 2*k pieces au-dessus de
# vol_min ; il y avait 46 perps liquides sur Hyperliquid, donc 20 est atteignable
# sans descendre dans l'illiquide.
K_LARGE = 10


class CarryNeutreLarge(CarryNeutre):
    """Bot 29b : identique au 29, seul le nombre de jambes change."""
    name = "29b_carry_neutre_large"

    def __init__(self, k: int = K_LARGE, hold_h: float = 168.0,
                 vol_min: float = 500_000.0, maker: bool = False):
        super().__init__(k=k, hold_h=hold_h, vol_min=vol_min, maker=maker)
        # Le parent code en dur etat_bot29.json : on le redirige AVANT toute
        # ecriture, sinon les deux bots se marcheraient dessus et l'A/B serait
        # ruine (chacun rechargerait les positions de l'autre).
        self.name = "29b_carry_neutre_large"
        self._f = ETAT_DIR / "etat_bot29b.json"
        self.livre = Livre(self.name)
        self._etat = self._charger()
        self.livre.charger(self._etat.get("positions", {}))
