#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bot_variance.py - Bot #31 PRIME DE VARIANCE a RISQUE DEFINI (edge VALIDE OOS).
Chaque mois : on "vend" de la vol implicite (VIX) sur un mois, a RISQUE DEFINI
(spread credit : gain plafonne, perte plafonnee -> pas de queue catastrophique).
P&L du mois = clamp(IV_vendu - RV_realisee, -LOSS_CAP, +CREDIT_CAP) - frais, en
points de vol, converti en rendement. Dormant si VIX indisponible. stdlib only.

Rappel honnete : la version NUE a un skew -3,6 (pire mois -62 pts). Le plafonnement
(spread) borne la perte MAIS aussi la prime -> Sharpe realiste ~1,0-1,4. On mesure
en forward pour confirmer, argent 100 % fictif.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from banc_essai_paper_trading import Strategy, Trade

ETAT_DIR = Path("etat")
CREDIT_CAP = 3.0     # gain max en points de vol (prime du spread)
LOSS_CAP = 6.0       # perte max en points de vol (largeur - prime)
COST_PTS = 0.5       # frais aller-retour en points de vol
PT_TO_RET = 0.0033   # 1 pt de vol ~ 0,33 % du capital alloue (dimensionnement vega)


class VarianceRiskPremium(Strategy):
    name = "31_variance_premium"

    def __init__(self, notional: float = 1000.0):
        super().__init__(stake_usd=1.0)
        self.notional = notional
        self._f = ETAT_DIR / "etat_bot31.json"
        self._etat = self._charger()

    def _charger(self) -> dict:
        try:
            with self._f.open(encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, ValueError):
            return {}

    def _sauver(self) -> None:
        try:
            ETAT_DIR.mkdir(parents=True, exist_ok=True)
            with self._f.open("w", encoding="utf-8") as fh:
                json.dump(self._etat, fh)
        except OSError:
            pass

    def step(self, marche: dict):
        asof = marche.get("asof")
        vix = marche.get("vix")
        spy = marche.get("spy_daily") or {}
        if not asof:
            return []
        if self._etat.get("dernier_mois") == asof:
            return []
        trades = []
        iv_prev = self._etat.get("iv_vendu")
        if iv_prev is not None and len(spy) >= 10:
            ds = sorted(spy)
            rets = [math.log(spy[ds[i]] / spy[ds[i - 1]]) for i in range(1, len(ds))]
            moy = sum(rets) / len(rets)
            var = sum((x - moy) ** 2 for x in rets) / (len(rets) - 1)
            rv = math.sqrt(var * 252) * 100.0
            raw = iv_prev - rv
            pnl_pts = max(-LOSS_CAP, min(CREDIT_CAP, raw)) - COST_PTS
            t = Trade(self.name, "vrp-book", "short_vol_defini", 1.0, self.notional)
            t.close(1.0 + pnl_pts * PT_TO_RET)
            trades.append(t)
            print(f"[31] vrp : IV={iv_prev:.1f} RV={rv:.1f} -> {pnl_pts:+.1f} pts",
                  flush=True)
        if vix is not None:
            self._etat = {"dernier_mois": asof, "iv_vendu": float(vix)}
        else:
            self._etat["dernier_mois"] = asof   # dormant : pas de vente ce mois
        self._sauver()
        return trades
