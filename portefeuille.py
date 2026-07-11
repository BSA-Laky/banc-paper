#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
portefeuille.py - Gestionnaire de portefeuille CENTRALISE (paper par defaut).
============================================================================
UN compte finance tous les bots crypto (Hyperliquid). Ce module :
  - repartit le capital par bot avec des PLAFONDS DURS (allocation),
  - centralise la comptabilite (exposition par bot + total, dispo),
  - route chaque ordre via execution_hl.ExecutionHL (paper -> live selon ses garde-fous).
AUCUN retrait ici : sortir les fonds = wallet PROPRIETAIRE = ta main (jamais un bot).

Modele recommande (voir GUIDE_WALLET.md) :
  1 compte MAITRE (depot + retrait humain) -> N bots, chacun avec un plafond logiciel.
  Passage aux SOUS-COMPTES Hyperliquid (marge isolee) quand le capital grossit.
stdlib only (la couche live de execution_hl amene ses deps).
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
        self.expo = self._charger_expo()          # {bot: notional_ouvert_usd}

    @staticmethod
    def _charger_cfg(p):
        try:
            return json.loads(Path(p).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {"capital_total_usd": 30.0, "reserve_pct": 0.2, "bots": {}}

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

    def plafond_bot(self, bot):
        b = self.cfg.get("bots", {}).get(bot, {})
        cap = float(self.cfg.get("capital_total_usd", 0))
        if b.get("max_notional") is not None:
            return float(b["max_notional"])
        if "alloc_pct" in b:
            return cap * float(b["alloc_pct"])
        return 0.0

    def dispo_bot(self, bot):
        return max(0.0, self.plafond_bot(bot) - float(self.expo.get(bot, 0.0)))

    def dispo_global(self):
        cap = float(self.cfg.get("capital_total_usd", 0)) * (1 - float(self.cfg.get("reserve_pct", 0)))
        return max(0.0, cap - sum(float(v) for v in self.expo.values()))

    def peut_ouvrir(self, bot, notional):
        if notional > self.dispo_bot(bot):
            return False, "plafond bot %s (%.2f$ dispo)" % (bot, self.dispo_bot(bot))
        if notional > self.dispo_global():
            return False, "plafond global (%.2f$ dispo)" % self.dispo_global()
        return True, "ok"

    def ouvrir(self, bot, coin, is_buy, notional, prix_ref):
        ok, raison = self.peut_ouvrir(bot, notional)
        if not ok:
            return {"status": "refuse", "raison": raison}
        res = self.exec.market_open(coin, is_buy, notional, prix_ref)
        self.expo[bot] = float(self.expo.get(bot, 0.0)) + notional
        self._sauver_expo()
        return {"status": "ouvert", "bot": bot, "notional": notional, "exec": res}

    def cloturer(self, bot, notional):
        self.expo[bot] = max(0.0, float(self.expo.get(bot, 0.0)) - notional)
        self._sauver_expo()

    def etat(self):
        par_bot = [{"bot": b, "plafond": round(self.plafond_bot(b), 2),
                    "utilise": round(float(self.expo.get(b, 0.0)), 2),
                    "dispo": round(self.dispo_bot(b), 2)}
                   for b in self.cfg.get("bots", {})]
        return {"mode": self.exec.cfg.resume()["mode"],
                "capital_total_usd": float(self.cfg.get("capital_total_usd", 0)),
                "reserve_pct": self.cfg.get("reserve_pct"),
                "dispo_global": round(self.dispo_global(), 2),
                "par_bot": par_bot}


def verifier():
    print(json.dumps(Portefeuille().etat(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "dryrun":
        p = Portefeuille()
        print("ouvrir 27f 8$ :", p.ouvrir("27f_selecteur", "DYDX", False, 8, 2.5)["status"])
        print("re-ouvrir 27f 8$ (doit REFUSER, plafond) :", p.ouvrir("27f_selecteur", "POPCAT", True, 8, 0.5))
        print(json.dumps(p.etat(), ensure_ascii=False, indent=2))
    else:
        verifier()
