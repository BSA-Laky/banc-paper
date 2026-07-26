#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bot_29_carry_neutre.py - CARRY TRANSVERSAL DOLLAR-NEUTRE (26/07/2026)
=====================================================================
L'HYPOTHESE, ET POURQUOI ELLE DIFFERE DU BOT 28
-----------------------------------------------
Le bot 28 prend TOUT ce qui a un |funding| extreme, sans jamais equilibrer : son
livre finit net directionnel. Mesure sur 7 mois d'historique HL (64 perps, split
TRAIN 01/01-30/04 / TEST 01/05-26/07), a selection, tenue et frais IDENTIQUES,
seule la neutralite changeant :

    livre NU (bot 28)      : derive de prix  -2,78 %/sem (train)  -1,36 % (OOS)
                             ecart-type du prix 7,16 %
    livre DOLLAR-NEUTRE    : derive de prix  +0,23 %/sem (train)  +0,81 % (OOS)
                             ecart-type du prix 3,42 %

Equilibrer le livre supprime la derive negative ET divise le bruit par deux. C'est
la cause, mesuree, des 10 episodes reels sur 11 ou le prix allait contre la
position (test des signes p = 0,006).

LA STRATEGIE
------------
Chaque semaine (168 h) :
  - SHORT les K pieces au funding le plus POSITIF  (on encaisse le funding)
  - LONG  les K pieces au funding le plus NEGATIF  (on encaisse aussi)
  - notionnels EGAUX -> exposition dollar nette nulle
puis on solde tout et on re-classe.

L'EDGE, PROUVE PAR DECOMPOSITION (pas par le P&L brut, trop bruite) :
  funding capte : +0,4602 %/sem t=+5,67 (TRAIN)  |  +0,3075 %/sem t=+5,20 (OOS)
  prix          : moyenne indiscernable de zero (t +0,26 / +0,71, IC95 contenant 0)
  frais         : deterministes
  => E[rendement] = E[funding] - frais > 0.  6 mois sur 6 positifs.
  Temoin aleatoire : funding capte ~ 0 (+0,023 % / +0,007 %) -> la capture est bien
  un effet de selection reel.

Rapport complet : Bot/BOT29_CARRY_NEUTRE_2026-07-26.md
Comptabilite : OBLIGATOIREMENT via comptabilite.PositionReelle (prix + funding
signe + frais reels). stdlib uniquement.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from banc_essai_paper_trading import Strategy, Trade
from bots_cloud import _http_post_info, parse_ctxs, _now, _dt_h, ETAT_DIR
from comptabilite import Livre, notionnel_par_ligne


class CarryNeutre(Strategy):
    name = "29_carry_neutre"

    def __init__(self, k: int = 3, hold_h: float = 168.0,
                 vol_min: float = 500_000.0, maker: bool = False):
        super().__init__(stake_usd=1.0)
        self.k = int(k)
        self.hold_h = float(hold_h)
        self.vol_min = float(vol_min)
        self.maker = bool(maker)
        self._f = ETAT_DIR / "etat_bot29.json"
        self.livre = Livre(self.name)
        self._etat = self._charger()
        self.livre.charger(self._etat.get("positions", {}))

    # -- persistance ---------------------------------------------------------
    def _charger(self) -> dict:
        try:
            return json.loads(self._f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _sauver(self) -> None:
        self._etat["positions"] = self.livre.vers_dict()
        try:
            ETAT_DIR.mkdir(parents=True, exist_ok=True)
            self._f.write_text(json.dumps(self._etat, ensure_ascii=False),
                               encoding="utf-8")
        except OSError:
            pass

    # -- selection -----------------------------------------------------------
    def selectionner(self, data: dict) -> list[tuple[str, int]]:
        """K shorts sur le funding le plus haut, K longs sur le plus bas."""
        elig = [(c, d["funding"]) for c, d in data.items()
                if d.get("vol", 0) >= self.vol_min and d.get("markPx", 0) > 0]
        if len(elig) < 2 * self.k:
            return []
        elig.sort(key=lambda x: -x[1])
        hauts = elig[:self.k]        # funding le plus positif -> on SHORTE
        bas = elig[-self.k:]         # funding le plus negatif -> on LONGE
        # garde-fou : on refuse un panier ou le signe ne va pas dans le bon sens
        if hauts[0][1] <= 0 and bas[-1][1] >= 0:
            return []
        return [(c, -1) for c, _ in hauts] + [(c, +1) for c, _ in bas]

    # -- une passe -----------------------------------------------------------
    def step(self) -> list[Trade]:
        rep = _http_post_info({"type": "metaAndAssetCtxs"})
        if rep is None:
            return []
        data = parse_ctxs(rep, ("*",))
        if not data:
            return []
        now = _now()
        dt = _dt_h(self._etat.get("dernier_ts"))
        self._etat["dernier_ts"] = now.isoformat()

        # 1) accumuler le funding SIGNE sur les positions ouvertes
        self.livre.accumuler_tout(data, dt)

        # 2) solder si la tenue est atteinte
        regles: list[Trade] = []
        if self.livre.positions:
            try:
                age = (now - datetime.fromisoformat(
                    str(self._etat.get("ouvert_le")))).total_seconds() / 3600.0
            except (ValueError, TypeError):
                age = 0.0
            if age >= self.hold_h:
                for coin in list(self.livre.positions):
                    d = data.get(coin)
                    # piece disparue du flux : on solde au prix d'entree (P&L =
                    # funding - frais). Jamais de cloture a l'aveugle sur un prix inconnu.
                    mark = d["markPx"] if d else self.livre.positions[coin].mark_entree
                    tr = self.livre.fermer(coin, mark)
                    if tr:
                        regles.append(tr)
                self._etat["ouvert_le"] = None

        # 3) ouvrir un panier neuf si le livre est vide
        if not self.livre.positions:
            jambes = self.selectionner(data)
            if jambes:
                notionnel = notionnel_par_ligne(len(jambes))
                for coin, side in jambes:
                    self.livre.ouvrir(coin, side, notionnel,
                                      data[coin]["markPx"], maker=self.maker)
                self._etat["ouvert_le"] = now.isoformat()

        # 4) trace de neutralite : doit rester ~0. Sert au garde-fou et au dashboard.
        self._etat["ecart_neutralite"] = round(self.livre.ecart_neutralite(), 6)
        self._etat["exposition_nette"] = round(self.livre.exposition_nette, 2)
        self._sauver()
        if regles:
            print("[29] carry neutre : %d jambe(s) soldee(s), ecart neutralite %.3f"
                  % (len(regles), self._etat["ecart_neutralite"]), flush=True)
        return regles
