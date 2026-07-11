#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
portefeuille.py - Gestionnaire d'ENVELOPPE + LEVIER par bot (deterministe).
==========================================================================
Enveloppe = marge allouee (300 EUR/bot). Le LEVIER (defaut 1x, fixe par le Tresorier
au moment de la promotion via Kelly fractionnaire) multiplie le NOTIONAL deploye :
  notional_max = enveloppe * levier ; mise/entree = notional_max / positions_max ;
  la marge utilisee ne depasse JAMAIS l'enveloppe. Levier=1 tant qu'un bot n'est pas
  promu (rien dans promotions.json) -> comportement identique a avant. stdlib.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from execution_hl import ExecutionHL

CONFIG = Path(os.environ.get("PORTEFEUILLE_CONFIG", "portefeuille.config.json"))
ETAT_EXPO = Path("etat/portefeuille_expo.json")
F_PROMO = Path("promotions.json")


class Portefeuille:
    def __init__(self, config_path=CONFIG, executor=None):
        self.cfg = self._json(config_path, {"enveloppe_par_bot_eur": 300, "eurusd": 1.07, "bots": {}})
        self.exec = executor or ExecutionHL()
        self.expo = self._json(ETAT_EXPO, {})
        self.promo = self._json(F_PROMO, {})

    @staticmethod
    def _json(p, d):
        try:
            return json.loads(Path(p).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return d

    def _sauver_expo(self):
        try:
            ETAT_EXPO.parent.mkdir(parents=True, exist_ok=True)
            ETAT_EXPO.write_text(json.dumps(self.expo), encoding="utf-8")
        except OSError:
            pass

    def _eurusd(self):
        return float(self.cfg.get("eurusd", 1.07))

    def enveloppe(self, bot):
        """Enveloppe (marge) du bot en USD. 0 si bot inconnu."""
        if bot not in self.cfg.get("bots", {}):
            return 0.0
        return float(self.cfg.get("enveloppe_par_bot_eur", 0)) * self._eurusd()

    def positions_max(self, bot):
        return int(self.cfg.get("bots", {}).get(bot, {}).get("positions_max", 1)) or 1

    def levier(self, bot):
        """Levier du bot (defaut 1x). Fixe par le Tresorier dans promotions.json. Borne [1, levier_max]."""
        l = float(self.promo.get("bots", {}).get(bot, {}).get("levier", 1.0))
        return max(1.0, min(l, float(self.cfg.get("levier_max", 3.0))))

    def plafond_notional(self, bot):
        """Notional total max = enveloppe * levier."""
        return self.enveloppe(bot) * self.levier(bot)

    def taille_entree(self, bot):
        """Mise a l'entree (notional USD) = (enveloppe * levier) / positions_max."""
        return self.plafond_notional(bot) / self.positions_max(bot)

    def dispo_bot(self, bot):
        return max(0.0, self.plafond_notional(bot) - float(self.expo.get(bot, 0.0)))

    def peut_ouvrir(self, bot, notional=None):
        notional = self.taille_entree(bot) if notional is None else notional
        if notional > self.dispo_bot(bot) + 1e-9:
            return False, "enveloppe %s pleine (%.2f$ libres, mise %.2f$)" % (bot, self.dispo_bot(bot), notional)
        return True, "ok"

    def ouvrir(self, bot, coin, is_buy, prix_ref, notional=None):
        notional = self.taille_entree(bot) if notional is None else notional
        ok, raison = self.peut_ouvrir(bot, notional)
        if not ok:
            return {"status": "refuse", "raison": raison}
        res = self.exec.market_open(coin, is_buy, notional, prix_ref)
        self.expo[bot] = float(self.expo.get(bot, 0.0)) + notional
        self._sauver_expo()
        return {"status": "ouvert", "bot": bot, "notional": round(notional, 2), "exec": res}

    def cloturer(self, bot, notional=None):
        notional = self.taille_entree(bot) if notional is None else notional
        self.expo[bot] = max(0.0, float(self.expo.get(bot, 0.0)) - notional)
        self._sauver_expo()

    def etat(self):
        eu = self._eurusd()
        lignes = []
        for bot in self.cfg.get("bots", {}):
            env = self.enveloppe(bot); used = float(self.expo.get(bot, 0.0)); lev = self.levier(bot)
            lignes.append({"bot": bot, "enveloppe_eur": round(env / eu),
                           "levier": lev, "notional_max_eur": round(env * lev / eu),
                           "mise_eur": round(self.taille_entree(bot) / eu, 2),
                           "positions_max": self.positions_max(bot),
                           "deploye_eur": round(used / eu, 2)})
        return {"mode": self.exec.cfg.resume()["mode"], "par_bot": lignes}


if __name__ == "__main__":
    print(json.dumps(Portefeuille().etat(), ensure_ascii=False, indent=1))
