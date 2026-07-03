#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bot_27f_selecteur.py - SELECTEUR INFORME : choisir le cote (REV/MOM) PAR EVENEMENT
==================================================================================
Hypothese de Nino : des agents choisissent le bon cote de la paire miroir 27b/27c
selon l'INFO (veille + tendance) au lieu de subir le cote miroir. Le 27e teste ca
avec la tendance BTC GLOBALE -> presque toujours "neutre" -> REV par defaut : il ne
teste pas vraiment une selection informee. Ici, le signal est PROPRE A LA PIECE
(sa propre tendance 7j) + l'avis IA (si frais). Mecanique identique a 27b/27c/27e
(meme seuil, notional, horizon, frais) => comparaison a armes egales. 100 % fictif.

RATIONALE CHIFFRE (n=18 paires live, 24/06->03/07/2026) :
  toujours-REV (=27b) : esp +8,7 / t 2,34 / total +157
  oracle (selecteur parfait) : esp +12,9 / t 4,41 / total +232
  => l'ecart (~+75 sur 18 evts, 7 evts ou MOM gagne) est le prix qu'un BON
     selecteur capture. Le 27e ne le capte pas. On teste un signal par piece.

PRIOR HONNETE : hypothese A CONDAMNER si le banc ne la sauve pas. Critere de survie
STRICT : n>=50, t>=2, net de frais, ET battre le temoin ALEATOIRE, ET battre
"toujours REVERSION" (sinon l'agent n'apporte rien vs la politique bete). Ce bot ne
pilote RIEN : il est mesure comme les autres. stdlib only, lecture seule Hyperliquid.
"""
from __future__ import annotations

import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from banc_essai_paper_trading import Strategy, Trade
# Reutilise les helpers PURS du 27e (aucune duplication, memes appels HL) :
from bot_27e_arbitre import _http_post_info, _parse_ctxs

ETAT_DIR = Path("etat")
FICHIER_AVIS_IA = ETAT_DIR / "regime_ia.json"
JOURNAL_DECISIONS = ETAT_DIR / "journal_selecteur.csv"
FRAICHEUR_AVIS_H = 26.0
CONFIANCE_MIN = 0.55        # un cran sous le 27e (0.6) : on veut que l'IA s'exprime
TREND_MIN = 0.05            # |tendance 7j piece| mini pour parler d'"alignement"


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


def _avis_ia(now):
    """Lit etat/regime_ia.json (avis IA global). None si absent/perime/peu sur."""
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


def _decider(move, ret7, avis):
    """Renvoie (mode, source). mode in {MOM, REV}. REV = defaut prouve meilleur."""
    if avis is not None:                       # 1) l'IA parle et est sure -> priorite
        mode = "MOM" if avis["regime"] == "haussier" else "REV"
        return mode, "ia"
    if ret7 is not None and abs(ret7) >= TREND_MIN:   # 2) signal PROPRE a la piece
        aligne = (move > 0 and ret7 > 0) or (move < 0 and ret7 < 0)
        return ("MOM", "tendance_piece") if aligne else ("REV", "tendance_piece")
    return "REV", "defaut"                      # 3) inconnu -> baseline reversion


def _journaliser_decision(ligne):
    try:
        ETAT_DIR.mkdir(parents=True, exist_ok=True)
        neuf = not JOURNAL_DECISIONS.exists()
        with JOURNAL_DECISIONS.open("a", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            if neuf:
                w.writerow(["ts", "coin", "move_pct", "ret7_piece",
                            "regime_ia", "conf_ia", "source", "decision"])
            w.writerow(ligne)
    except OSError:
        pass


class SelecteurInforme(Strategy):
    """Bot 27f : un seul sens par evenement, choisi par signal PROPRE A LA PIECE + IA."""
    name = "27f_selecteur"

    def __init__(self, notional=100.0, move_big=0.20, horizon_h=24.0,
                 frais_par_jambe=0.00035, vol_min=1_000_000.0):
        super().__init__(stake_usd=1.0)
        self.notional = notional
        self.move_big = move_big
        self.horizon_h = horizon_h
        self.frais = frais_par_jambe
        self.vol_min = vol_min
        # nom dynamique : 20 % = "27f_selecteur" (comparable a 27b/27c) ;
        # tout seuil plus bas prend un suffixe (ex. 10 % -> "27f10_selecteur")
        # pour journaliser/scorer separement son propre univers d'evenements.
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
        if candidats:
            avis = _avis_ia(now)
            for coin, d in candidats:
                move = d["move"]
                ret7 = _ret7_coin(coin)          # signal PROPRE a la piece
                mode, source = _decider(move, ret7, avis)
                side = (1 if move > 0 else -1) if mode == "MOM" else (-1 if move > 0 else 1)
                self._etat[coin] = {"ouvert": True, "side": side, "entry": d["mark"],
                                    "ts": now.isoformat(), "mode": mode, "source": source}
                _journaliser_decision([
                    now.isoformat(), coin, round(move * 100, 2),
                    (round(ret7, 4) if ret7 is not None else ""),
                    (avis["regime"] if avis else ""),
                    (avis["confiance"] if avis else ""), source, mode])
        self._sauver()
        return out
