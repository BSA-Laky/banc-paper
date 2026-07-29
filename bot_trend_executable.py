#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bot_trend_executable.py - Bot #30b : le JUMEAU EXECUTABLE du trend-following.
==============================================================================
POURQUOI CE BOT EXISTE
----------------------
Le bot 30 mesure un book de 14 ETF americains (SPY, QQQ, IWM, EFA, EEM, TLT,
IEF, GLD, SLV, USO, UUP, VNQ, HYG, DBC). Ce book a un Sharpe backteste de 0,8
sur 30 ans OOS -- mais il n'est PAS executable la ou du capital serait
accessible sans etre riche : une maison prop (FTMO & co) ne propose ni ETF ni
obligations, seulement du forex, des indices, des matieres et des actions, en CFD.

C'est la faute du bot 24 qui se repete : mesurer une strategie qu'on ne peut pas
executer. Le bot 24 a ete tue le 29/07 pour ce motif exact ("INEXECUTABLE : il
mesure un carry Paradex alors que nous n'avons de compte que sur Hyperliquid").
Le bot 30 a le meme defaut et personne ne l'avait releve.

CE QUE CE JUMEAU CHANGE, ET RIEN D'AUTRE
-----------------------------------------
Meme signal (momentum time-series sur LOOKBACK mois), meme tenue, meme
equiponderation. SEULES changent les deux choses qui rendent le book reel :

1. L'UNIVERS : uniquement des instruments disponibles en CFD chez une maison
   prop. Consequence mesuree ici, pas supposee : on PERD la poche obligataire
   et credit (TLT, IEF, HYG) -- or c'est elle qui porte le "crisis alpha" d'un
   book trend, le gain quand les actions chutent. On perd aussi VNQ et DBC.

2. LES SWAPS OVERNIGHT : un CFD tenu au mois paie un cout de portage quotidien
   (triple le mercredi chez la plupart des maisons). L'ETF, lui, ne paie rien.
   Sur un book a 6-8 %/an espere, 2-5 %/an de swap n'est pas un detail : c'est
   la moitie du rendement.

L'A/B QUE CE BOT PERMET
-----------------------
30 (ETF, inexecutable)  contre  30b (CFD, executable)
    -> combien de l'edge survit a la traduction ?

C'est la seule question qui compte avant d'engager quoi que ce soit dans une
structure a capital externe. Si 30b ne bat pas son temoin, le Sharpe 0,8 du
backtest est une propriete du book ETF, pas du signal -- et il ne voyagera pas.

Aucun parametre du signal n'est retouche : la traduction doit etre un test
PROPRE de la seule executabilite.

stdlib uniquement. Meme interface que bot_trend.py (step(marche)).
"""
from __future__ import annotations

import json
import random
from pathlib import Path

from banc_essai_paper_trading import Strategy, Trade

ETAT_DIR = Path("etat")

# --- Univers EXECUTABLE en CFD chez une maison prop -------------------------
# Cle = symbole de donnees (Twelve Data, comme bot_trend) ; valeur = l'instrument
# correspondant cote maison. On ne garde QUE ce qui existe vraiment des deux cotes.
UNIVERS_CFD = {
    "SPY": "US500",     # indice actions US large
    "QQQ": "US100",     # techno US
    "IWM": "US2000",    # petites capitalisations US
    "EFA": "EU50",      # actions developpees hors US (approximation)
    "EEM": "HK50",      # emergents (approximation)
    "GLD": "XAUUSD",    # or
    "SLV": "XAGUSD",    # argent
    "USO": "USOIL",     # petrole
    "UUP": "DXY",       # dollar (panier FX)
}
UNIVERS = list(UNIVERS_CFD)

# Ce qui DISPARAIT par rapport au bot 30, et pourquoi c'est grave :
PERDUS = {
    "TLT": "obligations longues US - aucun CFD equivalent",
    "IEF": "obligations intermediaires US - aucun CFD equivalent",
    "HYG": "credit haut rendement - aucun CFD equivalent",
    "VNQ": "immobilier cote - aucun CFD equivalent",
    "DBC": "panier matieres - pas d'equivalent direct",
}

LOOKBACK = 6          # mois, IDENTIQUE au bot 30
COST = 0.0005         # 5 bps par rotation, IDENTIQUE au bot 30

# Cout de portage CFD : ce que l'ETF ne paie pas et que le CFD paie.
# Ordre de grandeur usuel (taux directeur + marge maison) sur une position
# longue tenue en continu. Parametrable : c'est l'hypothese la plus sensible
# de tout ce module, elle doit rester visible et discutable.
SWAP_ANNUEL_LONG = 0.035      # 3,5 %/an sur le notionnel effectivement expose
MOIS_PAR_AN = 12.0


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
    """Signal IDENTIQUE au bot 30 : rendement des LOOKBACK derniers mois > 0."""
    if not m or asof not in m:
        return 0
    mois = sorted(k for k in m if k <= asof)
    if len(mois) < LOOKBACK + 1:
        return 0
    passe = mois[-1 - LOOKBACK]
    return 1 if (m[asof] / m[passe] - 1.0) > 0 else 0


class TrendExecutable(Strategy):
    """Bot 30b : le book trend restreint a ce qui est reellement executable."""
    name = "30b_trend_executable"

    def __init__(self, notional: float = 1000.0, swap_annuel: float = SWAP_ANNUEL_LONG):
        super().__init__(stake_usd=1.0)
        self.notional = notional
        self.swap_annuel = float(swap_annuel)
        self._f = ETAT_DIR / "etat_bot30b.json"
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
            rets, change, exposes = [], 0, 0
            for s in UNIVERS:
                m = monthly.get(s)
                if not m or s not in entree or asof not in m:
                    continue
                r = m[asof] / entree[s] - 1.0
                p = pos.get(s, 0)
                rets.append(p * r)
                exposes += p
                if p != _sig_momentum(m, asof):
                    change += 1
            if rets:
                turn = change / max(1, len(UNIVERS))
                # exposition moyenne du mois : seules les lignes DETENUES paient le swap
                part_exposee = exposes / max(1, len(rets))
                swap = self.swap_annuel / MOIS_PAR_AN * part_exposee
                port = sum(rets) / len(rets) - COST * turn - swap
                t = Trade(self.name, "trend-cfd", "long_flat", 1.0, self.notional)
                t.close(1.0 + port)
                trades.append(t)
                self._etat["dernier_swap"] = round(swap, 6)
                self._etat["part_exposee"] = round(part_exposee, 4)

        newpos, newentree = {}, {}
        for s in UNIVERS:
            m = monthly.get(s)
            newpos[s] = _sig_momentum(m, asof)
            if m and asof in m:
                newentree[s] = m[asof]
        self._etat.update({"dernier_mois": asof, "positions": newpos,
                           "prix_entree": newentree,
                           "univers_cfd": UNIVERS_CFD, "perdus_vs_bot30": PERDUS,
                           "swap_annuel": self.swap_annuel})
        _sauver(self._f, self._etat)
        if trades:
            print("[30b] trend EXECUTABLE : book solde %s (swap %.4f, expose %.0f %%)"
                  % (asof, self._etat.get("dernier_swap", 0),
                     100 * self._etat.get("part_exposee", 0)), flush=True)
        return trades


class ControleCFD(Strategy):
    """Temoin du book executable : MEMES instruments, signal ALEATOIRE, MEMES couts.

    Sans lui, on ne saurait pas si 30b gagne grace au signal ou grace au simple
    fait d'etre long des actifs en tendance haussiere sur la periode.
    """
    name = "10c_controle_cfd"

    def __init__(self, notional: float = 1000.0, swap_annuel: float = SWAP_ANNUEL_LONG):
        super().__init__(stake_usd=1.0)
        self.notional = notional
        self.swap_annuel = float(swap_annuel)
        self._f = ETAT_DIR / "etat_controle_cfd.json"
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
            rets, exposes = [], 0
            for s in UNIVERS:
                m = monthly.get(s)
                if not m or s not in entree or asof not in m:
                    continue
                p = pos.get(s, 0)
                rets.append(p * (m[asof] / entree[s] - 1.0))
                exposes += p
            if rets:
                part = exposes / max(1, len(rets))
                port = (sum(rets) / len(rets) - COST * 0.5
                        - self.swap_annuel / MOIS_PAR_AN * part)
                t = Trade(self.name, "controle-cfd", "aleatoire", 1.0, self.notional)
                t.close(1.0 + port)
                trades.append(t)
        newpos, newentree = {}, {}
        for s in UNIVERS:
            m = monthly.get(s)
            newpos[s] = random.choice([0, 1])
            if m and asof in m:
                newentree[s] = m[asof]
        self._etat = {"dernier_mois": asof, "positions": newpos, "prix_entree": newentree}
        _sauver(self._f, self._etat)
        return trades


# --------------------------------------------------------------- diagnostic
def cout_traduction(monthly: dict, asof: str, notional: float = 1000.0) -> dict:
    """Chiffre, sur les donnees du mois, ce que la traduction COUTE.

    Renvoie de quoi remplir l'A/B 30 vs 30b sans attendre des annees de forward :
    la part du book perdue, et le swap paye. C'est la mesure qui manque
    aujourd'hui pour decider si le Sharpe 0,8 voyage.
    """
    from bot_trend import UNIVERS as UNIV_ETF
    dispo_etf = [s for s in UNIV_ETF if monthly.get(s)]
    dispo_cfd = [s for s in UNIVERS if monthly.get(s)]
    return {
        "asof": asof,
        "lignes_etf": len(dispo_etf),
        "lignes_cfd": len(dispo_cfd),
        "part_du_book_perdue_pct": round(100 * (1 - len(dispo_cfd) / max(1, len(dispo_etf))), 1),
        "sleeves_perdus": PERDUS,
        "swap_annuel_hypothese": SWAP_ANNUEL_LONG,
        "swap_mensuel_si_100pct_expose": round(SWAP_ANNUEL_LONG / MOIS_PAR_AN, 5),
        "note": ("Le swap est l'hypothese la plus sensible de ce module. "
                 "A remplacer par les swaps REELS de la maison des qu'ils sont "
                 "connus : ils figurent dans la specification de chaque symbole."),
    }
