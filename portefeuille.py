#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
portefeuille.py - Gestionnaire d'ENVELOPPE par bot (300 EUR/bot), deterministe.
==============================================================================
Chaque bot a SA propre enveloppe. Il dimensionne chaque entree a
  mise = enveloppe / positions_max
et ne deploie JAMAIS plus que son enveloppe (les entrees au-dela sont refusees).
Route l'execution via execution_hl (paper -> live). AUCUN retrait. stdlib only.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from execution_hl import ExecutionHL

CONFIG = Path(os.environ.get("PORTEFEUILLE_CONFIG", "portefeuille.config.json"))
ETAT_EXPO = Path("etat/portefeuille_expo.json")


class Portefeuille:
    def __init__(self, config_path=CONFIG, executor=None):
        self.cfg = self._charger_cfg(config_path)
        self.exec = executor or ExecutionHL()
        self.expo = self._charger_expo()          # {bot: notional_deploye_usd}

    @staticmethod
    def _charger_cfg(p):
        try:
            return json.loads(Path(p).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {"enveloppe_par_bot_eur": 300, "eurusd": 1.07, "bots": {}}

    def _charger_expo(self):
        try:
            return json.loads(ETAT_EXPO.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _sauver_expo(self):
        try:
            ETAT_EXPO.parent.mkdir(parents=True, exist_ok=True)
            ETAT_EXPO.write_text(json.dumps(self.expo), encoding="utf-8")
        except OSError:
            pass

    def _eurusd(self):
        return float(self.cfg.get("eurusd", 1.07))

    def enveloppe(self, bot):
        """Enveloppe du bot en USD (0 si bot inconnu)."""
        if bot not in self.cfg.get("bots", {}):
            return 0.0
        return float(self.cfg.get("enveloppe_par_bot_eur", 0)) * self._eurusd()

    def positions_max(self, bot):
        return int(self.cfg.get("bots", {}).get(bot, {}).get("positions_max", 1)) or 1

    def taille_entree(self, bot):
        """Mise a l'entree (USD) = enveloppe / positions_max."""
        return self.enveloppe(bot) / self.positions_max(bot)

    def dispo_bot(self, bot):
        return max(0.0, self.enveloppe(bot) - float(self.expo.get(bot, 0.0)))

    def peut_ouvrir(self, bot, notional=None):
        notional = self.taille_entree(bot) if notional is None else notional
        if notional > self.dispo_bot(bot) + 1e-9:
            return False, "enveloppe %s pleine (%.2f$ libres, mise %.2f$)" % (
                bot, self.dispo_bot(bot), notional)
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
            env = self.enveloppe(bot); used = float(self.expo.get(bot, 0.0))
            lignes.append({"bot": bot, "enveloppe_eur": round(env / eu, 0),
                           "mise_eur": round(self.taille_entree(bot) / eu, 2),
                           "positions_max": self.positions_max(bot),
                           "deploye_eur": round(used / eu, 2),
                           "libre_eur": round((env - used) / eu, 2)})
        return {"mode": self.exec.cfg.resume()["mode"], "par_bot": lignes}


if __name__ == "__main__":
    verifier = Portefeuille()
    print(json.dumps(verifier.etat(), ensure_ascii=False, indent=1))
