ligne1
ligne2
    ligne3 indentee
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
comptabilite.py - COMPTABILITE REELLE UNIQUE ET OBLIGATOIRE (26/07/2026)
=======================================================================
POURQUOI CE MODULE EXISTE
-------------------------
Le bot 28 paper calculait son P&L ainsi :
    accrue += abs(funding) * notionnel * dt
c'est-a-dire : funding en VALEUR ABSOLUE (il encaissait toujours), et AUCUN terme
de prix. Un tel bot ne PEUT pas perdre : sa courbe est une derive positive
mecanique. En argent reel, la meme selection a donne t = -0,09 avec 10 episodes
sur 11 ou le prix allait contre la position (test des signes p = 0,006).

Ecart mesure le 26/07/2026 entre le paper et l'execution reelle : -0,46 pp par
trade, sur DEUX echantillons reels independants (mainnet et testnet).

REGLE STRUCTURELLE QUI EN DECOULE
---------------------------------
Toute strategie qui prend une POSITION DE MARCHE doit produire ses Trade via
'PositionReelle'. Aucune formule maison. La comptabilite est celle du compte :

    P&L = PRIX + FUNDING - FRAIS
    PRIX    = side * (mark_sortie - mark_entree) / mark_entree      (side +1 long, -1 short)
    FUNDING = somme sur la tenue de ( -side * funding_horaire * dt ) (HL : f>0 => les
              LONGS paient les SHORTS ; un short encaisse, un long paie)
    FRAIS   = 2 * FRAIS_PAR_JAMBE                                    (aller-retour)

Le garde-fou 'audit_conformite.py' verifie a CHAQUE passe qu'aucun bot ne
fabrique de Trade en dehors d'ici. Cela vaut pour les bots FUTURS.

stdlib uniquement.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from banc_essai_paper_trading import Trade

# Frais reels mesures sur les fills mainnet du 21-26/07/2026 : 0,0382 $ sur 84,96 $
# de notionnel = 0,045 % (taker HL). On facture le pire cas par defaut : un bot ne
# doit jamais paraitre rentable grace a une hypothese de frais optimiste.
FRAIS_PAR_JAMBE = 0.00045
FRAIS_MAKER = 0.00015

# Bots autorises a NE PAS utiliser ce module (aucune position de marche reelle).
DISPENSES = {
    "10_controle_aleatoire",   # temoin : pile ou face sur un marche fictif
}

# Capital REEL de reference. Demande du Commandant (26/07) : les bots paper doivent
# raisonner en euros REELS, pas en notionnels fictifs, pour que paper et reel soient
# directement comparables. Source unique : portefeuille.reel.json.
CAPITAL_DEFAUT = 946.0


def capital_reference() -> float:
    """Capital reel du compte (depot net), lu dans le registre unique."""
    try:
        cfg = json.loads(Path("portefeuille.reel.json").read_text(encoding="utf-8"))
        return float(cfg.get("depot_usdc") or CAPITAL_DEFAUT)
    except (OSError, ValueError, TypeError):
        return CAPITAL_DEFAUT


def notionnel_par_ligne(nb_lignes: int) -> float:
    """Taille d'une ligne si l'on deploie TOUT le capital reel sur nb_lignes."""
    return capital_reference() / max(1, int(nb_lignes))


def funding_signe(side: int, funding_horaire: float, dt_h: float) -> float:
    """Funding REELLEMENT encaisse (>0) ou paye (<0), en fraction du notionnel.

    Convention Hyperliquid : funding > 0  =>  les LONGS paient les SHORTS.
      - short (side=-1) sur funding>0  -> encaisse   (-(-1)*f = +f)
      - long  (side=+1) sur funding>0  -> paie       (-(+1)*f = -f)
      - long  (side=+1) sur funding<0  -> encaisse
    C'est la correction du bug historique 'abs(funding)', qui faisait encaisser
    les deux sens a la fois.
    """
    return -side * float(funding_horaire) * float(dt_h)


class PositionReelle:
    """Une position ouverte, comptabilisee EXACTEMENT comme sur le compte reel."""

    __slots__ = ("bot", "coin", "side", "notionnel", "mark_entree",
                 "funding_cumule", "ouverte_le", "maker")

    def __init__(self, bot: str, coin: str, side: int, notionnel: float,
                 mark_entree: float, maker: bool = False):
        if side not in (1, -1):
            raise ValueError("side doit valoir +1 (long) ou -1 (short), recu %r" % (side,))
        if not mark_entree or mark_entree <= 0:
            raise ValueError("mark_entree doit etre > 0, recu %r" % (mark_entree,))
        if notionnel <= 0:
            raise ValueError("notionnel doit etre > 0, recu %r" % (notionnel,))
        self.bot = bot
        self.coin = coin
        self.side = int(side)
        self.notionnel = float(notionnel)
        self.mark_entree = float(mark_entree)
        self.funding_cumule = 0.0
        self.maker = bool(maker)
        self.ouverte_le = datetime.now(timezone.utc).isoformat()

    # -- accumulation --------------------------------------------------------
    def accumuler(self, funding_horaire: float, dt_h: float) -> None:
        """A appeler a chaque passe avec le funding courant et le temps ecoule."""
        self.funding_cumule += funding_signe(self.side, funding_horaire, dt_h)

    # -- composantes ---------------------------------------------------------
    def rendement_prix(self, mark_sortie: float) -> float:
        return self.side * (float(mark_sortie) - self.mark_entree) / self.mark_entree

    @property
    def frais(self) -> float:
        return 2.0 * (FRAIS_MAKER if self.maker else FRAIS_PAR_JAMBE)

    def rendement_net(self, mark_sortie: float) -> float:
        return self.rendement_prix(mark_sortie) + self.funding_cumule - self.frais

    # -- cloture -------------------------------------------------------------
    def cloturer(self, mark_sortie: float) -> Trade:
        """Produit le Trade a journaliser. C'est la SEULE sortie autorisee."""
        net = self.rendement_net(mark_sortie)
        t = Trade(self.bot, "%s-%s" % (self.coin, "long" if self.side > 0 else "short"),
                  "long" if self.side > 0 else "short", 1.0, self.notionnel)
        t.opened_at = self.ouverte_le
        t.close(1.0 + net)        # pnl = notionnel * net
        return t

    # -- (de)serialisation pour l'etat JSON ----------------------------------
    def vers_dict(self) -> dict:
        return {"side": self.side, "notionnel": self.notionnel,
                "mark_entree": self.mark_entree, "funding_cumule": self.funding_cumule,
                "ouverte_le": self.ouverte_le, "maker": self.maker}

    @classmethod
    def depuis_dict(cls, bot: str, coin: str, d: dict) -> "PositionReelle":
        p = cls(bot, coin, int(d["side"]), float(d["notionnel"]),
                float(d["mark_entree"]), bool(d.get("maker", False)))
        p.funding_cumule = float(d.get("funding_cumule", 0.0))
        p.ouverte_le = d.get("ouverte_le", p.ouverte_le)
        return p


class Livre:
    """Le livre d'un bot. Sert aussi a MESURER la neutralite dollar.

    Lecon du 26/07 : un livre desequilibre (le bot 28) subit une derive de prix de
    -1,4 a -2,8 %/semaine et deux fois plus de bruit qu'un livre equilibre. La
    neutralite n'est pas un detail de confort, c'est l'edge.
    """

    def __init__(self, bot: str):
        self.bot = bot
        self.positions: dict[str, PositionReelle] = {}

    def ouvrir(self, coin, side, notionnel, mark, maker=False) -> PositionReelle:
        p = PositionReelle(self.bot, coin, side, notionnel, mark, maker)
        self.positions[coin] = p
        return p

    def fermer(self, coin: str, mark_sortie: float) -> Trade | None:
        p = self.positions.pop(coin, None)
        return p.cloturer(mark_sortie) if p else None

    def accumuler_tout(self, marches: dict, dt_h: float) -> None:
        for coin, p in self.positions.items():
            d = marches.get(coin)
            if d and d.get("funding") is not None:
                p.accumuler(d["funding"], dt_h)

    @property
    def exposition_nette(self) -> float:
        """Somme signee des notionnels. 0 = dollar-neutre."""
        return sum(p.side * p.notionnel for p in self.positions.values())

    @property
    def exposition_brute(self) -> float:
        return sum(p.notionnel for p in self.positions.values())

    def ecart_neutralite(self) -> float:
        """|exposition nette| / exposition brute. 0 = parfait, 1 = totalement nu."""
        b = self.exposition_brute
        return abs(self.exposition_nette) / b if b > 0 else 0.0

    def vers_dict(self) -> dict:
        return {c: p.vers_dict() for c, p in self.positions.items()}

    def charger(self, d: dict) -> None:
        self.positions = {c: PositionReelle.depuis_dict(self.bot, c, v)
                          for c, v in (d or {}).items() if isinstance(v, dict)}
