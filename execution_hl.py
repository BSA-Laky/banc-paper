#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
execution_hl.py - COUCHE D'EXECUTION Hyperliquid (paper <-> live), DESACTIVEE par defaut.
========================================================================================
Rend les bots CAPABLES d'un vrai wallet sans franchir seul la barriere humaine.
  - PAPER (defaut) : simule les fills, AUCUN reseau. stdlib seul.
  - LIVE  : ordres reels via le SDK hyperliquid-python + un wallet AGENT (trade-only,
            NE PEUT PAS RETIRER). L'agent signe POUR le compte maitre (account_address).

GARDE-FOUS cumulatifs pour le LIVE (tous poses par un HUMAIN) :
  1. HL_MODE=live
  2. HL_LIVE_CONFIRM=OUI_ARGENT_REEL
  3. HL_NET=mainnet  (sinon TESTNET par defaut = argent de test)
  4. HL_MAX_NOTIONAL borne un ordre (defaut 25 $) -> refus au-dela
  5. HL_API_KEY = cle privee du wallet AGENT (jamais logguee)
  6. HL_ACCOUNT_ADDRESS = adresse publique du compte MAITRE (celui qui a approuve l'agent)
Sans ces variables, TOUT ordre est SIMULE. Aucune fonction de retrait, par conception.
"""
from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path

TESTNET_URL = "https://api.hyperliquid-testnet.xyz"
MAINNET_URL = "https://api.hyperliquid.xyz"
LEDGER_PAPER = Path("etat/execution_paper.csv")
CONFIRM_TOKEN = "OUI_ARGENT_REEL"


class ConfigExecution:
    def __init__(self):
        self.mode = os.environ.get("HL_MODE", "paper").strip().lower()
        self.confirm = os.environ.get("HL_LIVE_CONFIRM", "").strip()
        self.net = os.environ.get("HL_NET", "testnet").strip().lower()
        self.max_notional = float(os.environ.get("HL_MAX_NOTIONAL", "25"))
        self.key = os.environ.get("HL_API_KEY", "").strip()
        self.account = os.environ.get("HL_ACCOUNT_ADDRESS", "").strip()

    @property
    def live_arme(self):
        return self.mode == "live" and self.confirm == CONFIRM_TOKEN

    @property
    def base_url(self):
        return MAINNET_URL if self.net == "mainnet" else TESTNET_URL

    def resume(self):
        return {"mode": "LIVE" if self.live_arme else "PAPER",
                "reseau": (self.net if self.live_arme else "- (paper)"),
                "url": (self.base_url if self.live_arme else "-"),
                "max_notional_usd": self.max_notional,
                "cle_agent_presente": bool(self.key),
                "compte_maitre_present": bool(self.account),
                "argent_reel": bool(self.live_arme and self.net == "mainnet")}


def _ts():
    return datetime.now(timezone.utc).isoformat()


class ExecutionHL:
    """Executeur unifie. PAPER : simule. LIVE (double-confirme) : ordres reels Hyperliquid."""

    def __init__(self, cfg=None):
        self.cfg = cfg or ConfigExecution()
        self._live = None

    def _verifie_taille(self, notional):
        if notional > self.cfg.max_notional:
            raise ValueError("ordre %.2f$ > plafond %.2f$ (HL_MAX_NOTIONAL)"
                             % (notional, self.cfg.max_notional))

    def _charger_live(self):
        if self._live is not None:
            return self._live
        if not self.cfg.live_arme:
            raise RuntimeError("LIVE non arme (HL_MODE=live + HL_LIVE_CONFIRM) - reste en paper")
        if not self.cfg.key:
            raise RuntimeError("HL_API_KEY absente (cle du wallet agent trade-only)")
        if not self.cfg.account:
            raise RuntimeError("HL_ACCOUNT_ADDRESS absente (adresse du compte maitre) - l'agent doit signer POUR lui")
        from eth_account import Account            # non-stdlib, uniquement en LIVE
        from hyperliquid.exchange import Exchange
        from hyperliquid.info import Info
        wallet = Account.from_key(self.cfg.key)
        info = Info(self.cfg.base_url, skip_ws=True)
        exchange = Exchange(wallet, self.cfg.base_url, account_address=self.cfg.account)
        self._live = (exchange, info)
        return self._live

    def market_open(self, coin, is_buy, notional_usd, prix_ref):
        self._verifie_taille(notional_usd)
        sz = round(notional_usd / prix_ref, 6) if prix_ref else 0.0
        if not self.cfg.live_arme:
            return self._paper("market_open", coin, is_buy, sz, prix_ref, notional_usd)
        exchange, _ = self._charger_live()
        return exchange.market_open(coin, is_buy, sz)

    def limit_order(self, coin, is_buy, sz, px, tif="Gtc"):
        self._verifie_taille(sz * px)
        if not self.cfg.live_arme:
            return self._paper("limit", coin, is_buy, sz, px, sz * px)
        exchange, _ = self._charger_live()
        return exchange.order(coin, is_buy, sz, px, {"limit": {"tif": tif}})

    def cancel(self, coin, oid):
        if not self.cfg.live_arme:
            return self._paper("cancel", coin, None, None, None, 0.0, extra={"oid": oid})
        exchange, _ = self._charger_live()
        return exchange.cancel(coin, oid)

    def _paper(self, action, coin, is_buy, sz, px, notional, extra=None):
        ligne = {"ts": _ts(), "mode": "paper", "action": action, "coin": coin,
                 "is_buy": is_buy, "sz": sz, "px": px, "notional": round(notional, 4), "oid": ""}
        if extra:
            ligne.update(extra)
        try:
            LEDGER_PAPER.parent.mkdir(parents=True, exist_ok=True)
            neuf = not LEDGER_PAPER.exists()
            with LEDGER_PAPER.open("a", newline="", encoding="utf-8") as fh:
                cols = ["ts", "mode", "action", "coin", "is_buy", "sz", "px", "notional", "oid"]
                w = csv.DictWriter(fh, fieldnames=cols)
                if neuf:
                    w.writeheader()
                w.writerow({k: ligne.get(k, "") for k in cols})
        except OSError:
            pass
        return {"status": "paper_simule", **ligne}


def verifier():
    cfg = ConfigExecution()
    print(json.dumps(cfg.resume(), ensure_ascii=False, indent=2))
    if cfg.live_arme and cfg.net == "mainnet":
        print(">>> ATTENTION : LIVE MAINNET arme = ARGENT REEL.")
    else:
        print(">>> Sur : mode paper/simule ou testnet. Aucun argent reel.")


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "check":
        verifier()
    elif cmd == "dryrun":
        ex = ExecutionHL(ConfigExecution())
        print(ex.market_open("BTC", True, 10.0, 60000.0))
        print(ex.limit_order("ETH", False, 0.005, 3000.0))
        print("dry-run PAPER ecrit dans", LEDGER_PAPER)
    else:
        print("usage: python execution_hl.py [check|dryrun]")
