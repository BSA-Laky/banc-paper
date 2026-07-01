#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bot_trend.py - Bot #30 TREND-FOLLOWING (edge VALIDE OOS 30 ans) + controle book.
Time-series momentum : chaque mois, pour 14 ETF diversifies, si le rendement des
LOOKBACK derniers mois > 0 -> detenu le mois suivant, sinon cash. Equipondere.
Emet UN Trade portefeuille par mois (rendement reel net de frais). Etat repo-relatif
(commite par le workflow). Donnees injectees par run_book.py. stdlib only.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

from banc_essai_paper_trading import Strategy, Trade

ETAT_DIR = Path("etat")
UNIVERS = ["SPY", "QQQ", "IWM", "EFA", "EEM", "TLT", "IEF", "GLD", "SLV",
           "USO", "UUP", "VNQ", "HYG", "DBC"]
LOOKBACK = 6          # mois
COST = 0.0005         # 5 bps par rotation d'actif


def _charger(f: Path) -> dict:
    try:
        with f.open(encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def _sauver(f: Path, etat: dict) -> None:
    try:
        ETAT_DIR.mkdir(parents=True, exist_ok=True)
        with f.open("w", encoding="utf-8") as fh:
            json.dump(etat, fh)
    except OSError:
        pass


def _sig_momentum(m, asof):
    if not m or asof not in m:
        return 0
    mois = sorted(k for k in m if k <= asof)
    if len(mois) < LOOKBACK + 1:
        return 0
    passe = mois[-1 - LOOKBACK]
    return 1 if (m[asof] / m[passe] - 1.0) > 0 else 0


class TrendFollowing(Strategy):
    name = "30_trend_following"

    def __init__(self, notional: float = 1000.0):
        super().__init__(stake_usd=1.0)
        self.notional = notional
        self._f = ETAT_DIR / "etat_bot30.json"
        self._etat = _charger(self._f)

    def step(self, marche: dict):
        monthly = marche.get("monthly") or {}
        asof = marche.get("asof")
        if not asof or not monthly:
            return []
        if self._etat.get("dernier_mois") == asof:
            return []
        trades = []
        pos = self._etat.get("positions")
        entree = self._etat.get("prix_entree")
        if pos and entree:
            rets, change = [], 0
            for s in UNIVERS:
                m = monthly.get(s)
                if not m or s not in entree or asof not in m:
                    continue
                r = m[asof] / entree[s] - 1.0
                rets.append(pos.get(s, 0) * r)
                if pos.get(s, 0) != _sig_momentum(m, asof):
                    change += 1
            if rets:
                turn = change / max(1, len(UNIVERS))
                port = sum(rets) / len(rets) - COST * turn
                t = Trade(self.name, "trend-book", "long_flat", 1.0, self.notional)
                t.close(1.0 + port)
                trades.append(t)
        newpos, newentree = {}, {}
        for s in UNIVERS:
            m = monthly.get(s)
            newpos[s] = _sig_momentum(m, asof)
            if m and asof in m:
                newentree[s] = m[asof]
        self._etat = {"dernier_mois": asof, "positions": newpos,
                      "prix_entree": newentree}
        _sauver(self._f, self._etat)
        if trades:
            print(f"[30] trend : book solde {asof}.", flush=True)
        return trades


class ControleBook(Strategy):
    """Temoin du book : memes actifs, mais signal ALEATOIRE (0/1) au lieu du momentum.
    Etalon du bruit : le trend doit le battre."""
    name = "10b_controle_book"

    def __init__(self, notional: float = 1000.0):
        super().__init__(stake_usd=1.0)
        self.notional = notional
        self._f = ETAT_DIR / "etat_controle_book.json"
        self._etat = _charger(self._f)

    def step(self, marche: dict):
        monthly = marche.get("monthly") or {}
        asof = marche.get("asof")
        if not asof or not monthly:
            return []
        if self._etat.get("dernier_mois") == asof:
            return []
        trades = []
        pos = self._etat.get("positions")
        entree = self._etat.get("prix_entree")
        if pos and entree:
            rets = []
            for s in UNIVERS:
                m = monthly.get(s)
                if not m or s not in entree or asof not in m:
                    continue
                rets.append(pos.get(s, 0) * (m[asof] / entree[s] - 1.0))
            if rets:
                port = sum(rets) / len(rets) - COST * 0.5
                t = Trade(self.name, "controle-book", "aleatoire", 1.0, self.notional)
                t.close(1.0 + port)
                trades.append(t)
        newpos, newentree = {}, {}
        for s in UNIVERS:
            m = monthly.get(s)
            newpos[s] = random.choice([0, 1])
            if m and asof in m:
                newentree[s] = m[asof]
        self._etat = {"dernier_mois": asof, "positions": newpos,
                      "prix_entree": newentree}
        _sauver(self._f, self._etat)
        return trades
