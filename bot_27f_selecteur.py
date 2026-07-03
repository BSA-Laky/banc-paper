#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bot_27f_selecteur.py - SELECTEUR INFORME PAR PIECE (paper)
==========================================================
Choisit REV/MOM par EVENEMENT (move 24h >= seuil), par ORDRE DE PRIORITE :
  1. AVIS PAR PIECE de l'IA (etat/avis_par_piece.json, ecrit par avis_piece_ia.py qui
     LIT LE CATALYSEUR du move via recherche web) -> le vrai signal informe, PAR COIN ;
  2. sinon TENDANCE PROPRE de la piece (rendement 7j) : move aligne -> momentum,
     spike a contre-tendance -> reversion ;
  3. sinon REVERSION (defaut prouve meilleur en OOS).
On a RETIRE l'avis BTC GLOBAL (le 27e le teste deja, et l'appliquer a tous les coins
est justement le defaut) : ici TOUT est PAR PIECE. Mecanique identique a 27b/27c/27e
(seuil, notional, horizon, frais) => comparaison a armes egales.

Survie STRICTE : n>=50, t>=2, net de frais, ET battre le temoin ALEATOIRE, ET battre
"toujours REVERSION". Ce bot ne pilote RIEN : mesure. 100% fictif, lecture seule HL, stdlib.
"""
from __future__ import annotations

import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from banc_essai_paper_trading import Strategy, Trade
from bot_27e_arbitre import _http_post_info, _parse_ctxs

ETAT_DIR = Path("etat")
F_AVIS_PIECE = ETAT_DIR / "avis_par_piece.json"
JOURNAL_DECISIONS = ETAT_DIR / "journal_selecteur.csv"
FRAICHEUR_AVIS_H = 26.0
CONF_MIN_PIECE = 0.5       # on ne suit l'avis IA par coin que si confiance >= 0.5
TREND_MIN = 0.05           # |tendance 7j piece| mini pour parler d'"alignement"


def _ret7_coin(coin: str):
    """Rendement 7j de la PIECE via ses bougies 1d Hyperliquid. None si indispo."""
    fin = int(time.time() * 1000)
    debut = fin - 10 * 24 * 3600 * 1000
    rep = _http_post_info({"type": "candleSnapshot",
                           "req": {"coin": coin, "interval": "1d",
                                   "startTime": debut, "endTime": fin}})
    if not isinstance(rep, list) or len(rep) < 8:
        return None
    try:
        closes = [float(b["c"]) for b in rep]
    except (TypeError, KeyError, ValueError):
        return None
    if closes[-8] <= 0:
        return None
    return closes[-1] / closes[-8] - 1.0


def _avis_piece(coin, now):
    """Avis IA SPECIFIQUE au coin (etat/avis_par_piece.json). None si absent/perime/peu sur."""
    try:
        with F_AVIS_PIECE.open(encoding="utf-8") as fh:
            e = json.load(fh).get(coin)
        if not isinstance(e, dict):
            return None
        sens = str(e.get("sens", "")).lower()
        conf = float(e.get("confiance", 0.0))
        ts = datetime.fromisoformat(str(e.get("ts", "")).replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
    except (OSError, ValueError, TypeError, KeyError):
        return None
    if sens not in ("momentum", "reversion"):
        return None
    age = (now - ts).total_seconds() / 3600.0
    if age < 0 or age > FRAICHEUR_AVIS_H or conf < CONF_MIN_PIECE:
        return None
    return {"sens": sens, "confiance": conf}


def _decider(move, ret7, avis_piece):
    """(mode, source). mode in {MOM, REV}. Priorite : avis IA par coin > tendance piece > REV."""
    if avis_piece is not None:                       # 1) l'IA a lu le catalyseur de CE coin
        return ("MOM" if avis_piece["sens"] == "momentum" else "REV"), "ia_piece"
    if ret7 is not None and abs(ret7) >= TREND_MIN:  # 2) tendance propre de la piece
        aligne = (move > 0 and ret7 > 0) or (move < 0 and ret7 < 0)
        return ("MOM", "tendance_piece") if aligne else ("REV", "tendance_piece")
    return "REV", "defaut"                            # 3) baseline reversion


def _journaliser_decision(ligne):
    try:
        ETAT_DIR.mkdir(parents=True, exist_ok=True)
        neuf = not JOURNAL_DECISIONS.exists()
        with JOURNAL_DECISIONS.open("a", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            if neuf:
                w.writerow(["ts", "coin", "move_pct", "ret7_piece",
                            "avis_sens", "avis_conf", "source", "decision"])
            w.writerow(ligne)
    except OSError:
        pass


class SelecteurInforme(Strategy):
    """Bot 27f : un seul sens par evenement, choisi PAR PIECE (avis IA du coin + tendance)."""
    name = "27f_selecteur"

    def __init__(self, notional=100.0, move_big=0.20, horizon_h=24.0,
                 frais_par_jambe=0.00035, vol_min=1_000_000.0):
        super().__init__(stake_usd=1.0)
        self.notional = notional
        self.move_big = move_big
        self.horizon_h = horizon_h
        self.frais = frais_par_jambe
        self.vol_min = vol_min
        self.name = ("27f_selecteur" if move_big >= 0.20
                     else "27f%d_selecteur" % int(round(move_big * 100)))
        self._f = ETAT_DIR / ("etat_%s.json" % self.name)
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
                  market="sel-%s-%s-%s" % (coin, st.get("mode", "?"), st.get("source", "?")),
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
        for coin, d in candidats:
            move = d["move"]
            ap = _avis_piece(coin, now)
            ret7 = None if ap is not None else _ret7_coin(coin)   # evite un appel si avis present
            mode, source = _decider(move, ret7, ap)
            side = (1 if move > 0 else -1) if mode == "MOM" else (-1 if move > 0 else 1)
            self._etat[coin] = {"ouvert": True, "side": side, "entry": d["mark"],
                                "ts": now.isoformat(), "mode": mode, "source": source}
            _journaliser_decision([
                now.isoformat(), coin, round(move * 100, 2),
                (round(ret7, 4) if ret7 is not None else ""),
                (ap["sens"] if ap else ""), (round(ap["confiance"], 2) if ap else ""),
                source, mode])
        self._sauver()
        return out
