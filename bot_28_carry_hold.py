#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bot_28_carry_hold.py - CARRY-HOLD : l'edge VALIDE OUT-OF-SAMPLE (paper, live)
============================================================================
Issu du sweep du 01/07/2026 : sur 150 j d'historique HL, split train/test, la seule
strategie qui survit en OUT-OF-SAMPLE est le carry "hold" :
  entrer quand |funding| >= seuil, puis TENIR `hold_h` heures en accumulant le funding,
  puis sortir (UNE seule fois les frais d'aller-retour).
  -> train : n=243, esp +2.39 $, t=+7.0 ; TEST OOS : n=113, esp +1.26 $, t=+10.0.
Contraste avec le bot 23 (hysteresis + settle 24h) qui CHURN les frais et perd (t -4).

Ce bot rejoue EXACTEMENT ce config en live (funding reel Hyperliquid, argent 100 % fictif,
lecture seule) pour CONFIRMER l'edge en forward (out-of-sample dans le temps). Reserve
(comme bot 23) : on mesure la COMPOSANTE FUNDING d'un carry delta-neutre, hors slippage/
frais spot/risque de queue. stdlib only.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from banc_essai_paper_trading import Strategy, Trade
from bots_cloud import _http_post_info, parse_ctxs, _now, _dt_h, ETAT_DIR


class CarryHold(Strategy):
    name = "28_carry_hold"

    def __init__(self, notional: float = 1000.0, seuil_funding: float = 1e-4,
                 hold_h: float = 48.0, frais_par_jambe: float = 0.00035,
                 vol_min: float = 1_000_000.0):
        super().__init__(stake_usd=1.0)
        self.notional = notional
        self.seuil = seuil_funding
        self.hold_h = hold_h
        self.frais = frais_par_jambe
        self.vol_min = vol_min
        self._f = ETAT_DIR / "etat_bot28.json"
        self._etat = self._charger()

    def _charger(self):
        try:
            with self._f.open(encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, ValueError):
            return {}

    def _sauver(self):
        try:
            ETAT_DIR.mkdir(parents=True, exist_ok=True)
            with self._f.open("w", encoding="utf-8") as fh:
                json.dump(self._etat, fh)
        except OSError:
            pass

    def _slot(self, a, now):
        if a not in self._etat:
            self._etat[a] = {"ouvert": False, "accrue": 0.0,
                             "entree_ts": None, "dernier_ts": None}
        return self._etat[a]

    def step(self):
        rep = _http_post_info({"type": "metaAndAssetCtxs"})
        if rep is None:
            return []
        data = parse_ctxs(rep, ("*",))
        if not data:
            return []
        now = _now()
        regles = []
        for a, info in data.items():
            f = info["funding"]
            st = self._slot(a, now)
            dt = _dt_h(st.get("dernier_ts"))
            # accumulation du funding pendant la tenue
            if st["ouvert"]:
                st["accrue"] += abs(f) * self.notional * dt
            # entree : |funding| >= seuil et liquidite ok (frais A/R bookes UNE fois)
            if not st["ouvert"] and abs(f) >= self.seuil and info["vol"] >= self.vol_min:
                st["ouvert"] = True
                st["accrue"] = -2 * self.frais * self.notional
                st["entree_ts"] = now.isoformat()
            st["dernier_ts"] = now.isoformat()
            # sortie : apres hold_h heures -> on solde UN Trade
            if st["ouvert"]:
                try:
                    held = (now - datetime.fromisoformat(st["entree_ts"])).total_seconds() / 3600.0
                except (ValueError, TypeError, KeyError):
                    held = 0.0
                if held >= self.hold_h:
                    net = st["accrue"]
                    t = Trade(self.name, f"carryhold-{a}", "funding", 1.0, self.notional)
                    if st.get("entree_ts"):
                        t.opened_at = st["entree_ts"]   # vraie entree (expo/duree correctes)
                    t.close(1.0 + net / self.notional)
                    regles.append(t)
                    st.update({"ouvert": False, "accrue": 0.0, "entree_ts": None})
        self._sauver()
        if regles:
            print(f"[28] carry-hold : {len(regles)} soldes.", flush=True)
        return regles
