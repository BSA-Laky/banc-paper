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

COMPTABILITE — MIGRE LE 25/08/2026
----------------------------------
Ce module fabriquait ses Trade a la main (`Trade(...)` puis `.close(1+port)`),
et l'audit de conformite le signalait comme NON CONFORME depuis le 26/07. Le
reflexe aurait ete de le dispenser comme bot_trend.py et bot_variance.py, qui le
sont AVEC MOTIF : sur un book d'ETF ou d'options il n'y a pas de funding, donc
comptabilite.PositionReelle (concue pour un perp avec portage) ne s'applique pas.

Ce motif ne vaut PAS ici. Un CFD tenu au mois paie un SWAP overnight, et ce swap
est exactement le terme de portage que la comptabilite auditee existe pour
traiter. Le dispenser aurait laisse hors audit la variable que ce module declare
lui-meme comme "l'hypothese la plus sensible". Il est donc migre pour de vrai.

Ce que la migration change concretement :
  - chaque ligne detenue est une comptabilite.PositionReelle (side +1, long only) ;
  - le swap passe par `accumuler()`, donc par `funding_signe()` : pour un LONG,
    la convention rend bien un COUT (-side*f*dt avec side=+1 et f>0) ;
  - les frais deviennent ceux de comptabilite (FRAIS_PAR_JAMBE, aller-retour),
    soit 9 bp par ligne au lieu des 5 bp forfaitaires supposes avant. C'est PLUS
    PESSIMISTE, et c'est voulu : on ne discute pas les constantes du coeur audite ;
  - le rendement mensuel du book reste l'unite de mesure (les lignes d'un meme
    book ne sont pas independantes : compter chaque ligne comme un trade
    surestimerait le t-stat). On agrege donc les lignes AUDITEES en un trade
    mensuel, au lieu de fabriquer ce trade a partir de rien.

Timing des frais : l'aller-retour est impute au mois d'OUVERTURE, puis les mois
suivants ne portent que la variation de prix et le swap. La somme sur la vie de
la position est donc exactement `rendement_net()` a la cloture ; seul le calendrier
est legerement conservateur.

stdlib uniquement. Meme interface que bot_trend.py (step(marche)).
"""
from __future__ import annotations

import json
import random
from pathlib import Path

from banc_essai_paper_trading import Strategy, Trade
from comptabilite import FRAIS_PAR_JAMBE, Livre

ETAT_DIR = Path("etat")
HEURES_PAR_MOIS = 8760.0 / 12.0      # 730 h : duree d'accumulation du swap

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


def _pas_mensuel(livre: Livre, marks: dict, monthly: dict, asof: str,
                 signaux: dict, notional: float, swap_annuel: float) -> tuple:
    """Un mois de book, comptabilise ligne par ligne via comptabilite.PositionReelle.

    Renvoie (rendement_du_book, part_exposee, nb_rotations). Le rendement est la
    moyenne equiponderee sur les lignes DISPONIBLES : une ligne non detenue
    contribue zero, exactement comme dans bot_trend.
    """
    swap_h = swap_annuel / 8760.0        # taux horaire ; >0 = le LONG paie
    contribs, rotations = [], 0
    par_ligne = notional / max(1, len(UNIVERS))

    for s in UNIVERS:
        m = monthly.get(s)
        if not m or asof not in m:
            continue
        cfd = UNIVERS_CFD[s]
        mark = float(m[asof])
        veut = int(signaux.get(s, 0))
        p = livre.positions.get(cfd)

        if p is None and veut:                       # OUVERTURE
            p = livre.ouvrir(cfd, +1, par_ligne, mark)
            marks[cfd] = mark
            contribs.append(-p.frais)                # l'aller-retour, impute a l'ouverture
            rotations += 1
            continue
        if p is None:                                # ligne restee en cash
            contribs.append(0.0)
            continue

        # ligne detenue : swap du mois, puis variation depuis le dernier releve
        avant = p.rendement_net(marks.get(cfd, p.mark_entree))
        p.accumuler(swap_h, HEURES_PAR_MOIS)
        apres = p.rendement_net(mark)
        contribs.append(apres - avant)
        marks[cfd] = mark

        if not veut:                                 # FERMETURE
            livre.fermer(cfd, mark)
            marks.pop(cfd, None)
            rotations += 1

    if not contribs:
        return None, 0.0, 0
    detenues = sum(1 for s in UNIVERS if UNIVERS_CFD[s] in livre.positions)
    return (sum(contribs) / len(contribs),
            detenues / max(1, len(contribs)), rotations)


class TrendExecutable(Strategy):
    """Bot 30b : le book trend restreint a ce qui est reellement executable."""
    name = "30b_trend_executable"

    def __init__(self, notional: float = 1000.0, swap_annuel: float = SWAP_ANNUEL_LONG):
        super().__init__(stake_usd=1.0)
        self.notional = notional
        self.swap_annuel = float(swap_annuel)
        self._f = ETAT_DIR / "etat_bot30b.json"
        self._etat = _charger(self._f)
        self.livre = Livre(self.name)
        self.livre.charger(self._etat.get("positions", {}))

    def step(self, marche: dict):
        monthly = marche.get("monthly") or {}
        asof = marche.get("asof")
        if not asof or not monthly:
            return []
        if self._etat.get("dernier_mois") == asof:
            return []

        signaux = {s: _sig_momentum(monthly.get(s), asof) for s in UNIVERS}
        marks = self._etat.setdefault("marks", {})
        rendement, part, rot = _pas_mensuel(self.livre, marks, monthly, asof,
                                            signaux, self.notional, self.swap_annuel)
        trades = []
        if rendement is not None and self._etat.get("dernier_mois"):
            # UN trade par MOIS de book : les lignes d'un meme book ne sont pas
            # independantes, les compter separement gonflerait le t-stat.
            t = Trade(self.name, "trend-cfd", "long_flat", 1.0, self.notional)
            t.close(1.0 + rendement)
            trades.append(t)
            self._etat["dernier_rendement"] = round(rendement, 6)

        self._etat.update({"dernier_mois": asof, "part_exposee": round(part, 4),
                           "rotations": rot, "positions": self.livre.vers_dict(),
                           "univers_cfd": UNIVERS_CFD, "perdus_vs_bot30": PERDUS,
                           "swap_annuel": self.swap_annuel,
                           "frais_par_ligne_ar": round(2 * FRAIS_PAR_JAMBE, 6)})
        _sauver(self._f, self._etat)
        if trades:
            print("[30b] trend EXECUTABLE : book solde %s (rendement %+.4f, expose %.0f %%, %d rotation(s))"
                  % (asof, rendement, 100 * part, rot), flush=True)
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
        self.livre = Livre(self.name)
        self.livre.charger(self._etat.get("positions", {}))

    def step(self, marche: dict):
        monthly = marche.get("monthly") or {}
        asof = marche.get("asof")
        if not asof or not monthly:
            return []
        if self._etat.get("dernier_mois") == asof:
            return []
        # MEME comptabilite auditee que le 30b : sans ca, un ecart de P&L entre le
        # bot et son temoin pourrait venir de la methode de calcul, pas du signal.
        signaux = {s: random.choice([0, 1]) for s in UNIVERS}
        marks = self._etat.setdefault("marks", {})
        rendement, part, rot = _pas_mensuel(self.livre, marks, monthly, asof,
                                            signaux, self.notional, self.swap_annuel)
        trades = []
        if rendement is not None and self._etat.get("dernier_mois"):
            t = Trade(self.name, "controle-cfd", "aleatoire", 1.0, self.notional)
            t.close(1.0 + rendement)
            trades.append(t)
        self._etat.update({"dernier_mois": asof, "part_exposee": round(part, 4),
                           "rotations": rot, "positions": self.livre.vers_dict()})
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
