#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bot_27e_arbitre.py - HYPOTHESE MESUREE : arbitre de regime 27b vs 27c (paper)
=============================================================================
Question : choisir UN SEUL sens (reversion OU momentum) par evenement extreme,
en fonction (a) des tendances n-x (rendements BTC 1j/7j/30j) et (b) d'un avis
de regime ecrit par l'IA decideuse OpenClaw (etat/regime_ia.json, mode
conseil), fait-il MIEUX que 27b seul, 27c seul et le temoin ?

PRIOR AFFICHE (honnetete) : le switch deterministe 27b<->27c a deja ete teste
OOS -> t 0,24 (~0), PIRE que "toujours reversion" (t 0,70). Ce bot est donc
une hypothese A CONDAMNER si le banc ne la sauve pas (n>=30-50, t>=2, net de
frais, vs temoin). Il ne pilote RIEN : il est mesure comme les autres.

Mecanique identique a 27b/27c pour comparaison a armes egales :
  signal |move 24h| >= 20 %, vol >= 1 M$, notional 100 $, horizon 24 h,
  frais 0,035 %/jambe, pas de stop. 100 % fictif, lecture seule Hyperliquid.

Decision par evenement (full-auto, jamais bloquant) :
  1. Avis IA present, frais (< 26 h) et confiance >= 0,6 -> regime de l'IA.
  2. Sinon fallback deterministe "tendances n-x" : ret7 et ret30 BTC < 0
     -> baissier ; les deux > 0 -> haussier ; sinon neutre.
  3. Mapping fixe (le pattern in-sample) : baissier -> REVERSION (sens 27b),
     haussier -> MOMENTUM (sens 27c), neutre/inconnu -> REVERSION (defaut =
     la baseline "toujours reversion" qui dominait le switch naif).
Chaque decision est journalisee dans etat/journal_arbitre.csv pour scorer la
calibration de l'IA a posteriori (l'estimation devient une PREVISION NOTEE).
stdlib only.
"""
from __future__ import annotations

import csv
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from banc_essai_paper_trading import Strategy, Trade

HL_INFO_URL = "https://api.hyperliquid.xyz/info"
USER_AGENT = "paper-trading-bench/1.0 (read-only research)"
ETAT_DIR = Path("etat")
FICHIER_AVIS_IA = ETAT_DIR / "regime_ia.json"
JOURNAL_DECISIONS = ETAT_DIR / "journal_arbitre.csv"
FRAICHEUR_AVIS_H = 26.0
CONFIANCE_MIN = 0.6


def _http_post_info(body, timeout=12.0):
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(HL_INFO_URL, data=data,
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, OSError):
        return None


def _parse_ctxs(meta_and_ctxs):
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
        mark, prev = g("markPx"), g("prevDayPx")
        vol = g("dayNtlVlm") or 0.0
        if not nom or mark is None:
            continue
        move = ((mark - prev) / prev) if (prev and prev > 0) else None
        out[nom] = {"mark": mark, "move": move, "vol": vol}
    return out


def _rendements_btc():
    """Rendements BTC 1j/7j/30j depuis les bougies 1d Hyperliquid (ou None)."""
    fin = int(time.time() * 1000)
    debut = fin - 40 * 24 * 3600 * 1000
    rep = _http_post_info({"type": "candleSnapshot",
                           "req": {"coin": "BTC", "interval": "1d",
                                   "startTime": debut, "endTime": fin}})
    if not isinstance(rep, list) or len(rep) < 31:
        return None
    try:
        closes = [float(b["c"]) for b in rep]
    except (TypeError, KeyError, ValueError):
        return None
    if any(c <= 0 for c in closes[-31:]):
        return None
    return {"ret1": closes[-1] / closes[-2] - 1.0,
            "ret7": closes[-1] / closes[-8] - 1.0,
            "ret30": closes[-1] / closes[-31] - 1.0}


def _regime_tendance(rets):
    if rets is None:
        return "inconnu"
    if rets["ret7"] < 0 and rets["ret30"] < 0:
        return "baissier"
    if rets["ret7"] > 0 and rets["ret30"] > 0:
        return "haussier"
    return "neutre"


def _avis_ia(now):
    """Lit etat/regime_ia.json (ecrit par l'IA decideuse OpenClaw). None si absent/perime."""
    try:
        with FICHIER_AVIS_IA.open(encoding="utf-8") as fh:
            d = json.load(fh)
        regime = str(d.get("regime", "")).lower()
        conf = float(d.get("confiance", 0.0))
        ts = datetime.fromisoformat(str(d.get("date", "")).replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
    except (OSError, ValueError, TypeError, KeyError):
        return None
    age_h = (now - ts).total_seconds() / 3600.0
    if regime not in ("haussier", "baissier", "neutre"):
        return None
    if age_h < 0 or age_h > FRAICHEUR_AVIS_H or conf < CONFIANCE_MIN:
        return None
    return {"regime": regime, "confiance": conf}


def _journaliser_decision(ligne):
    try:
        ETAT_DIR.mkdir(parents=True, exist_ok=True)
        neuf = not JOURNAL_DECISIONS.exists()
        with JOURNAL_DECISIONS.open("a", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            if neuf:
                w.writerow(["ts", "coin", "move_pct", "ret1", "ret7", "ret30",
                            "regime_tendance", "regime_ia", "conf_ia",
                            "source", "decision"])
            w.writerow(ligne)
    except OSError:
        pass


class ArbitreRegime(Strategy):
    """Bot 27e : un seul sens par evenement, choisi par regime (IA ou tendance)."""
    name = "27e_arbitre"

    def __init__(self, notional=100.0, move_big=0.20, horizon_h=24.0,
                 frais_par_jambe=0.00035, vol_min=1_000_000.0):
        super().__init__(stake_usd=1.0)
        self.notional = notional
        self.move_big = move_big
        self.horizon_h = horizon_h
        self.frais = frais_par_jambe
        self.vol_min = vol_min
        self._f = ETAT_DIR / "etat_bot27e.json"
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

    def _settle(self, coin, mark, now, out):
        st = self._etat.get(coin)
        if not st or not st.get("ouvert"):
            return
        try:
            held = (now - datetime.fromisoformat(st["ts"])).total_seconds() / 3600.0
        except (ValueError, TypeError, KeyError):
            held = 0.0
        if held < self.horizon_h:
            return
        entry, side = st["entry"], st["side"]
        ret = side * (mark - entry) / entry if entry else 0.0
        pnl = self.notional * ret - 2 * self.frais * self.notional
        t = Trade(bot=self.name,
                  market=f"arb-{coin}-{st.get('mode', '?')}-{st.get('source', '?')}",
                  side=("long" if side > 0 else "short"),
                  entry_price=1.0, size_usd=self.notional)
        t.close(1.0 + pnl / self.notional)
        out.append(t)
        self._etat[coin] = {"ouvert": False}

    def step(self):
        rep = _http_post_info({"type": "metaAndAssetCtxs"})
        if rep is None:
            return []
        data = _parse_ctxs(rep)
        if not data:
            return []
        now = datetime.now(timezone.utc)
        out = []
        for coin, d in data.items():
            self._settle(coin, d["mark"], now, out)

        candidats = [(c, d) for c, d in data.items()
                     if d["vol"] >= self.vol_min and d["move"] is not None
                     and abs(d["move"]) >= self.move_big
                     and not (self._etat.get(c) or {}).get("ouvert")]
        if candidats:
            rets = _rendements_btc()
            r_tend = _regime_tendance(rets)
            avis = _avis_ia(now)
            if avis is not None:
                regime, source, conf = avis["regime"], "ia", avis["confiance"]
            else:
                regime, source, conf = r_tend, "tendance", ""
            mode = "MOM" if regime == "haussier" else "REV"
            for coin, d in candidats:
                move = d["move"]
                side = (1 if move > 0 else -1) if mode == "MOM" else (-1 if move > 0 else 1)
                self._etat[coin] = {"ouvert": True, "side": side, "entry": d["mark"],
                                    "ts": now.isoformat(), "mode": mode, "source": source}
                _journaliser_decision([
                    now.isoformat(), coin, round(move * 100, 2),
                    (round(rets["ret1"], 4) if rets else ""),
                    (round(rets["ret7"], 4) if rets else ""),
                    (round(rets["ret30"], 4) if rets else ""),
                    r_tend, (avis["regime"] if avis else ""), conf, source, mode])
        self._sauver()
        return out
