#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bot_27_convex_buckets.py - EXPERIENCE : un edge CONVEXE existe-t-il ? (paper)
============================================================================
Question : une mise sur un EVENEMENT EXTREME, tenue un horizon court, a-t-elle
une esperance POSITIVE ? Ou est-ce, comme le momentum deja teste, du bruit ?
On ne decide rien : on MESURE, et le banc tranche (esperance + t-stat + profil
loterie). 100 % fictif, lecture seule API publique Hyperliquid. stdlib only.

Trois buckets mesures SEPAREMENT (3 noms de bot distincts dans le banc) :
  27a_rev_premium : premium geant    -> pari directionnel CONTRE (reversion).
  27b_rev_move    : move 24 h extreme -> pari CONTRE (reversion).
  27c_mom_move    : move 24 h extreme -> pari AVEC  (momentum/continuation).

Une position = petite mise directionnelle ouverte a l'evenement, tenue
`horizon_h`, puis soldee au RENDEMENT reel observe (net de frais). 27b et 27c
parient en sens OPPOSE sur le meme signal : le banc dira si l'argent est du
cote reversion, du cote momentum, ou nulle part. Aucun stop (mesure honnete
du rendement d'horizon) ; un stop pourra etre ajoute plus tard.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from banc_essai_paper_trading import Strategy, Trade

HL_INFO_URL = "https://api.hyperliquid.xyz/info"
USER_AGENT = "paper-trading-bench/1.0 (read-only research)"
ETAT_DIR = Path("etat")
BUCKETS = ("27a_rev_premium", "27b_rev_move", "27c_mom_move", "27d_rev_move_stop")


def _http_post_info(body, timeout=12.0):
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(HL_INFO_URL, data=data,
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, OSError):
        return None


def _parse(meta_and_ctxs):
    out = {}
    try:
        univ, ctxs = meta_and_ctxs[0]["universe"], meta_and_ctxs[1]
    except (TypeError, KeyError, IndexError):
        return out
    for i, coin in enumerate(univ):
        if i >= len(ctxs):
            break
        nom = str(coin.get("name", "")).upper()
        c = ctxs[i] or {}
        def g(k):
            try:
                return float(c.get(k))
            except (TypeError, ValueError):
                return None
        mark, oracle, prev = g("markPx"), g("oraclePx"), g("prevDayPx")
        vol = g("dayNtlVlm") or 0.0
        prem = c.get("premium")
        try:
            premium = float(prem)
        except (TypeError, ValueError):
            premium = ((mark - oracle) / oracle) if (mark and oracle) else None
        if not nom or mark is None:
            continue
        move = ((mark - prev) / prev) if (prev and prev > 0) else None
        out[nom] = {"mark": mark, "premium": premium, "move": move, "vol": vol}
    return out


class ConvexBuckets(Strategy):
    name = "27_convex_buckets"

    def __init__(self, notional=100.0, premium_big=0.005, move_big=0.20,
                 horizon_h=24.0, frais_par_jambe=0.00035, vol_min=1_000_000.0,
                 stop_frac=0.06):
        super().__init__(stake_usd=1.0)
        self.notional = notional
        self.premium_big = premium_big
        self.move_big = move_big
        self.horizon_h = horizon_h
        self.frais = frais_par_jambe
        self.vol_min = vol_min
        self.stop_frac = stop_frac  # stop appliqué au seul bucket 27d
        self._f = ETAT_DIR / "etat_bot27.json"
        self._etat = self._charger()
        for b in BUCKETS:
            self._etat.setdefault(b, {})

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

    def _try_open(self, bucket, coin, side, mark, now):
        slot = self._etat[bucket]
        if coin in slot and slot[coin].get("ouvert"):
            return
        slot[coin] = {"ouvert": True, "side": side, "entry": mark, "ts": now.isoformat()}

    def _settle(self, bucket, coin, mark, now, out):
        st = self._etat[bucket].get(coin)
        if not st or not st.get("ouvert"):
            return
        try:
            held = (now - datetime.fromisoformat(st["ts"])).total_seconds() / 3600.0
        except (ValueError, TypeError, KeyError):
            held = 0.0
        entry, side = st["entry"], st["side"]
        ret = side * (mark - entry) / entry if entry else 0.0
        stop = self.stop_frac if bucket == "27d_rev_move_stop" else None
        sortie = (stop is not None and ret <= -stop) or (held >= self.horizon_h)
        if not sortie:
            return
        pnl = self.notional * ret - 2 * self.frais * self.notional
        t = Trade(bot=bucket, market=f"{bucket[4:]}-{coin}",
                  side=("long" if side > 0 else "short"),
                  entry_price=1.0, size_usd=self.notional)
        t.close(1.0 + pnl / self.notional)
        out.append(t)
        self._etat[bucket][coin] = {"ouvert": False}

    def step(self):
        rep = _http_post_info({"type": "metaAndAssetCtxs"})
        if rep is None:
            return []
        data = _parse(rep)
        if not data:
            return []
        now = datetime.now(timezone.utc)
        out = []
        for coin, d in data.items():
            mark = d["mark"]
            for b in BUCKETS:               # solder d'abord (meme si vol a baisse)
                self._settle(b, coin, mark, now, out)
            if d["vol"] < self.vol_min:
                continue
            prem, move = d["premium"], d["move"]
            if prem is not None and abs(prem) >= self.premium_big:
                self._try_open("27a_rev_premium", coin, -1 if prem > 0 else 1, mark, now)
            if move is not None and abs(move) >= self.move_big:
                self._try_open("27b_rev_move", coin, -1 if move > 0 else 1, mark, now)
                self._try_open("27c_mom_move", coin, 1 if move > 0 else -1, mark, now)
                self._try_open("27d_rev_move_stop", coin, -1 if move > 0 else 1, mark, now)
        self._sauver()
        return out
