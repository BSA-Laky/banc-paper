#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bot_28_carry_hold.py - CARRY-HOLD, COMPTABILITE CORRIGEE le 26/07/2026
=======================================================================
CE QUI A ETE CORRIGE, ET POURQUOI
---------------------------------
Version d'origine (01/07/2026), coeur du calcul :

    st["accrue"] += abs(f) * self.notional * dt        # <-- DEUX FAUTES

  1. 'abs(f)' : le bot encaissait le funding QUEL QUE SOIT le sens de la position.
     En realite, sur Hyperliquid, f > 0 signifie que les LONGS paient les SHORTS :
     un long sur funding positif PAIE. Un bot qui encaisse des deux cotes ne peut
     que gagner.
  2. AUCUN terme de prix. Or l'executeur reel prend un perp NU : il subit tout le
     prix. Le paper mesurait un carry delta-neutre IDEALISE, le reel prenait un
     directionnel. Ce n'etaient pas la meme strategie.

Consequence mesuree (26/07/2026), sur deux echantillons reels independants :
    rendement par trade  paper annonce  +0,126 %
                         mainnet reel   -0,341 %   (n=11)
                         testnet reel   -0,335 %   (n=26)
    ecart constant : -0,46 pp par trade.
Et en argent reel : 10 episodes sur 11 avec le prix contre la position (test des
signes, p = 0,006), dont CASHCAT a -20,43 $ que l'ancienne formule comptait en GAIN.

DESORMAIS : P&L = PRIX + FUNDING SIGNE - FRAIS REELS, via comptabilite.PositionReelle.
Le paper et le reel mesurent enfin la meme chose.

/!\ L'HISTORIQUE paper de ce bot ANTERIEUR au 26/07/2026 mesurait une autre
grandeur : il ne doit pas etre agrege avec les trades posterieurs. Marqueur :
etat/correction_comptable.json

La strategie elle-meme (selection, tenue) est INCHANGEE, pour que la correction
soit un test propre de la seule comptabilite. Sur ce qu'elle vaut, voir
Bot/RECHERCHE_EXHAUSTIVE_HL_2026-07-26.md : le livre nu subit une derive de prix
de -1,4 a -2,8 %/semaine ; le remplacant equilibre est le bot 29.

stdlib uniquement.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from banc_essai_paper_trading import Strategy, Trade
from bots_cloud import _http_post_info, parse_ctxs, _now, _dt_h, ETAT_DIR
from comptabilite import Livre, notionnel_par_ligne

MARQUEUR = ETAT_DIR / "correction_comptable.json"


class CarryHold(Strategy):
    name = "28_carry_hold"

    def __init__(self, seuil_funding: float = 1e-4, hold_h: float = 48.0,
                 vol_min: float = 1_000_000.0, lignes_max: int = 10):
        super().__init__(stake_usd=1.0)
        self.seuil = float(seuil_funding)
        self.hold_h = float(hold_h)
        self.vol_min = float(vol_min)
        self.lignes_max = int(lignes_max)
        self._f = ETAT_DIR / "etat_bot28.json"
        self.livre = Livre(self.name)
        self._etat = self._charger()
        self.livre.charger(self._etat.get("positions", {}))
        self._marquer()

    def _charger(self) -> dict:
        try:
            d = json.loads(self._f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        # migration : l'ancien format stockait {coin: {ouvert, accrue, ...}} a la
        # racine. On repart d'un livre vide (l'ancien accrue n'est pas convertible :
        # il melangeait un funding en valeur absolue et aucun prix).
        return d if "positions" in d else {"positions": {}, "migre_le": _now().isoformat()}

    def _sauver(self) -> None:
        self._etat["positions"] = self.livre.vers_dict()
        try:
            ETAT_DIR.mkdir(parents=True, exist_ok=True)
            self._f.write_text(json.dumps(self._etat, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass

    def _marquer(self) -> None:
        """Trace la date de bascule : l'historique anterieur mesure autre chose."""
        if MARQUEUR.exists():
            return
        try:
            ETAT_DIR.mkdir(parents=True, exist_ok=True)
            MARQUEUR.write_text(json.dumps({
                "date": _now().isoformat(),
                "bots": ["28_carry_hold"],
                "raison": "P&L paper passe de abs(funding) sans prix a "
                          "prix + funding signe - frais reels (comptabilite.py). "
                          "Les trades anterieurs mesuraient une autre grandeur et "
                          "ne doivent pas etre agreges avec les suivants.",
            }, ensure_ascii=False, indent=1), encoding="utf-8")
        except OSError:
            pass

    def step(self) -> list[Trade]:
        rep = _http_post_info({"type": "metaAndAssetCtxs"})
        if rep is None:
            return []
        data = parse_ctxs(rep, ("*",))
        if not data:
            return []
        now = _now()
        dt = _dt_h(self._etat.get("dernier_ts"))
        self._etat["dernier_ts"] = now.isoformat()

        # 1) funding SIGNE sur les positions ouvertes
        self.livre.accumuler_tout(data, dt)

        # 2) solder les positions arrivees a terme
        regles: list[Trade] = []
        ouverts = self._etat.setdefault("ouvert_le", {})
        for coin in list(self.livre.positions):
            try:
                age = (now - datetime.fromisoformat(str(ouverts.get(coin)))).total_seconds() / 3600.0
            except (ValueError, TypeError):
                age = 0.0
            if age >= self.hold_h:
                d = data.get(coin)
                mark = d["markPx"] if d else self.livre.positions[coin].mark_entree
                tr = self.livre.fermer(coin, mark)
                if tr:
                    regles.append(tr)
                ouverts.pop(coin, None)

        # 3) ouvrir : |funding| >= seuil, side = -signe(funding) pour ENCAISSER
        libres = self.lignes_max - len(self.livre.positions)
        if libres > 0:
            cand = [(c, d) for c, d in data.items()
                    if c not in self.livre.positions
                    and abs(d["funding"]) >= self.seuil
                    and d.get("vol", 0) >= self.vol_min
                    and d.get("markPx", 0) > 0]
            cand.sort(key=lambda x: -abs(x[1]["funding"]))
            notionnel = notionnel_par_ligne(self.lignes_max)
            for coin, d in cand[:libres]:
                side = -1 if d["funding"] > 0 else 1
                self.livre.ouvrir(coin, side, notionnel, d["markPx"])
                ouverts[coin] = now.isoformat()

        # 4) l'ecart de neutralite de CE bot est structurellement eleve (livre nu) :
        #    on le publie pour que ce soit visible au dashboard et par le garde-fou.
        self._etat["ecart_neutralite"] = round(self.livre.ecart_neutralite(), 6)
        self._etat["exposition_nette"] = round(self.livre.exposition_nette, 2)
        self._sauver()
        if regles:
            print("[28] carry-hold (comptabilite reelle) : %d soldee(s), ecart neutralite %.3f"
                  % (len(regles), self._etat["ecart_neutralite"]), flush=True)
        return regles
