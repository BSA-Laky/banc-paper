#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bot_29c_decale.py - CARRY NEUTRE A PANIERS DECALES (05/08/2026).
=================================================================
LE PROBLEME QU'IL RESOUT
------------------------
Le bot 29 (et son jumeau 29b) ouvre UN panier, le tient 168 h, le solde, en
rouvre un. Consequence : une seule clôture par semaine, donc aucun retour
d'information entre-temps. Le Commandant le vit mal, et il a raison : on ne
pilote pas a l'aveugle pendant sept jours.

La tentation est de raccourcir la tenue. C'EST UN PIEGE, chiffre le 05/08 :

    tenue     1re donnee     t = 2 atteint en
     24 h        1 jour          29,5 mois
     48 h        2 jours          7,8 mois
    168 h        7 jours          4,3 mois     <- le meilleur
    336 h       14 jours          3,9 mois

Les frais sont FIXES (0,09 % par aller-retour). A 48 h on les paie 3,5 fois
plus souvent pour capter 3,5 fois moins de funding. Passer de 168 h a 48 h
gagnerait 5 jours de premiere donnee et couterait 3,5 MOIS de verdict.

LA SOLUTION : DECALER, PAS RACCOURCIR
-------------------------------------
On ouvre un panier neuf toutes les CADENCE_H heures, et chaque panier est tenu
TENUE_H heures. A regime etabli, TENUE_H / CADENCE_H paniers se chevauchent :

    ouverture .......... toutes les 48 h
    tenue de chacun .... 168 h  (inchangee)
    paniers simultanes . 3 a 4
    -> une clôture tous les 2 jours, SANS raccourcir la tenue,
       SANS payer les frais plus souvent, verdict inchange a 4,3 mois.

RESERVE HONNETE : les paniers qui se chevauchent partagent des periodes de
marche, ils sont donc CORRELES. Le n reellement independant reste proche du
nombre de paniers NON chevauchants -- c'est-a-dire celui du bot 29b. On gagne
la visibilite, pas la puissance statistique. On n'en perd pas non plus, et
c'est ce qui rend l'operation gratuite.

MISE EN GARDE POUR LA LECTURE DES RESULTATS : ne JAMAIS calculer un t sur les
jambes du 29c comme si elles etaient independantes. Elles le sont moins encore
que celles du 29b. C'est exactement le piege du 02/08 (t naif 3,99 -> t groupe
0,66). La gate doit grouper par DATE.

Chaque panier a son propre Livre : deux paniers peuvent detenir la meme piece
sans se telescoper. stdlib uniquement.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from banc_essai_paper_trading import Strategy, Trade
from bots_cloud import _http_post_info, parse_ctxs, _now, _dt_h, ETAT_DIR
from comptabilite import Livre, notionnel_par_ligne

K = 10                 # 10 shorts + 10 longs = 20 jambes, comme le 29b
TENUE_H = 168.0        # inchangee : c'est elle qui amortit les frais
CADENCE_H = 48.0       # un panier neuf tous les 2 jours
VOL_MIN = 500_000.0
PANIERS_MAX = 4        # ceil(168/48) : le regime etabli


class CarryNeutreDecale(Strategy):
    """Bot 29c : plusieurs paniers neutres decales dans le temps."""
    name = "29c_carry_decale"

    def __init__(self, k: int = K, tenue_h: float = TENUE_H,
                 cadence_h: float = CADENCE_H, vol_min: float = VOL_MIN,
                 paniers_max: int = PANIERS_MAX):
        super().__init__(stake_usd=1.0)
        self.k = int(k)
        self.tenue_h = float(tenue_h)
        self.cadence_h = float(cadence_h)
        self.vol_min = float(vol_min)
        self.paniers_max = int(paniers_max)
        self._f = ETAT_DIR / "etat_bot29c.json"
        self._etat = self._charger()
        # un Livre PAR panier : deux paniers peuvent tenir la meme piece
        self.livres: dict[str, Livre] = {}
        for pid, p in (self._etat.get("paniers") or {}).items():
            lv = Livre(self.name)
            lv.charger(p.get("positions", {}))
            self.livres[pid] = lv

    # -- persistance ---------------------------------------------------------
    def _charger(self) -> dict:
        try:
            return json.loads(self._f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {"paniers": {}, "dernier_ouvert": None, "compteur": 0}

    def _sauver(self) -> None:
        paniers = self._etat.setdefault("paniers", {})
        for pid, lv in self.livres.items():
            paniers.setdefault(pid, {})["positions"] = lv.vers_dict()
        try:
            ETAT_DIR.mkdir(parents=True, exist_ok=True)
            self._f.write_text(json.dumps(self._etat, ensure_ascii=False),
                               encoding="utf-8")
        except OSError:
            pass

    # -- selection : IDENTIQUE au bot 29, pour que l'A/B soit propre ---------
    def selectionner(self, data: dict) -> list[tuple[str, int]]:
        elig = [(c, d["funding"]) for c, d in data.items()
                if d.get("vol", 0) >= self.vol_min and d.get("markPx", 0) > 0]
        if len(elig) < 2 * self.k:
            return []
        elig.sort(key=lambda x: -x[1])
        hauts, bas = elig[:self.k], elig[-self.k:]
        if hauts[0][1] <= 0 and bas[-1][1] >= 0:
            return []
        return [(c, -1) for c, _ in hauts] + [(c, +1) for c, _ in bas]

    # -- une passe -----------------------------------------------------------
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
        paniers = self._etat.setdefault("paniers", {})

        # 1) funding signe sur TOUS les paniers ouverts
        for lv in self.livres.values():
            lv.accumuler_tout(data, dt)

        # 2) solder les paniers arrives a terme
        regles: list[Trade] = []
        for pid in list(self.livres):
            try:
                age = (now - datetime.fromisoformat(
                    str(paniers.get(pid, {}).get("ouvert_le")))).total_seconds() / 3600.0
            except (ValueError, TypeError):
                age = 0.0
            if age < self.tenue_h:
                continue
            lv = self.livres[pid]
            for coin in list(lv.positions):
                d = data.get(coin)
                mark = d["markPx"] if d else lv.positions[coin].mark_entree
                tr = lv.fermer(coin, mark)
                if tr:
                    regles.append(tr)
            self.livres.pop(pid, None)
            paniers.pop(pid, None)

        # 3) ouvrir un panier neuf si la cadence est atteinte
        try:
            depuis = (now - datetime.fromisoformat(
                str(self._etat.get("dernier_ouvert")))).total_seconds() / 3600.0
        except (ValueError, TypeError):
            depuis = 1e9
        if depuis >= self.cadence_h and len(self.livres) < self.paniers_max:
            jambes = self.selectionner(data)
            if jambes:
                # le capital est reparti sur TOUS les paniers simultanes :
                # l'exposition brute totale reste celle des bots 29 et 29b,
                # sinon l'A/B comparerait des tailles differentes.
                notionnel = notionnel_par_ligne(len(jambes) * self.paniers_max)
                self._etat["compteur"] = int(self._etat.get("compteur", 0)) + 1
                pid = "p%03d" % self._etat["compteur"]
                lv = Livre(self.name)
                for coin, side in jambes:
                    lv.ouvrir(coin, side, notionnel, data[coin]["markPx"])
                self.livres[pid] = lv
                paniers[pid] = {"ouvert_le": now.isoformat(),
                                "positions": lv.vers_dict()}
                self._etat["dernier_ouvert"] = now.isoformat()

        # 4) traces de neutralite, panier par panier ET au global
        brute = sum(lv.exposition_brute for lv in self.livres.values())
        nette = sum(lv.exposition_nette for lv in self.livres.values())
        self._etat["n_paniers"] = len(self.livres)
        self._etat["n_jambes"] = sum(len(lv.positions) for lv in self.livres.values())
        self._etat["ecart_neutralite"] = round(abs(nette) / brute, 6) if brute > 0 else 0.0
        self._etat["exposition_nette"] = round(nette, 2)
        self._sauver()
        if regles:
            print("[29c] panier solde : %d jambe(s) ; %d panier(s) en cours, "
                  "ecart neutralite %.3f" % (len(regles), len(self.livres),
                                             self._etat["ecart_neutralite"]), flush=True)
        return regles
