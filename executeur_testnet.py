#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
executeur_testnet.py - MIROIR TESTNET des bots selecteurs (validation machine + frais).
=======================================================================================
Reflete les positions des bots PILOTES (paper) sur Hyperliquid TESTNET, via le
portefeuille (enveloppe 300 EUR/bot) + execution_hl. Objectif : eprouver l'execution
reelle (fills, FRAIS, gestion d'enveloppe, cycle de vie) SANS toucher la mesure d'edge
(qui reste en paper). Testnet = argent FICTIF. Best-effort, jamais bloquant.
Ne s'arme QUE si HL_MODE=live + HL_LIVE_CONFIRM + HL_NET=testnet. Refuse le mainnet.
"""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ETAT = Path("etat")
F_STATE = ETAT / "executeur_testnet.json"
LEDGER = ETAT / "testnet_trades.csv"
PILOTES = ["27f_selecteur", "27f10_selecteur", "27g10_selecteur"]
FRAIS = 0.00035


def _lire_json(p, d):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return d


def _ecrire_json(p, d):
    try:
        Path(p).parent.mkdir(parents=True, exist_ok=True)
        Path(p).write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


def _log(row):
    try:
        ETAT.mkdir(parents=True, exist_ok=True)
        neuf = not LEDGER.exists()
        with LEDGER.open("a", newline="", encoding="utf-8") as fh:
            cols = ["ts", "bot", "coin", "action", "side", "notional_usd", "mark", "resp", "pnl_est_usd"]
            w = csv.DictWriter(fh, fieldnames=cols)
            if neuf:
                w.writeheader()
            w.writerow({k: row.get(k, "") for k in cols})
    except OSError:
        pass


def executer():
    from execution_hl import ExecutionHL
    from portefeuille import Portefeuille
    from bot_27e_arbitre import _http_post_info, _parse_ctxs

    ex = ExecutionHL()
    if not ex.cfg.live_arme:
        print("[executeur] live non arme (paper) - dormant.", flush=True)
        return
    if ex.cfg.net != "testnet":
        print("[executeur] SECURITE : refuse de tourner hors testnet.", flush=True)
        return
    pf = Portefeuille(executor=ex)
    rep = _http_post_info({"type": "metaAndAssetCtxs"})
    data = _parse_ctxs(rep) if rep else {}
    if not data:
        print("[executeur] pas de donnees marche.", flush=True)
        return
    now = datetime.now(timezone.utc)
    state = _lire_json(F_STATE, {})

    for bot in PILOTES:
        bet = _lire_json(ETAT / ("etat_%s.json" % bot), {})
        ouverts = {c: v for c, v in bet.items() if isinstance(v, dict) and v.get("ouvert")}
        mine = state.get(bot, {})

        # OUVRIR : positions du bot pas encore refletees sur testnet
        for coin, v in ouverts.items():
            if coin in mine:
                continue
            d = data.get(coin)
            if not d:
                continue
            ok, raison = pf.peut_ouvrir(bot)
            if not ok:
                print("[executeur] %s %s non ouvert : %s" % (bot, coin, raison), flush=True)
                continue
            side = int(v.get("side", -1))
            notion = pf.taille_entree(bot)
            try:
                r = pf.ouvrir(bot, coin, is_buy=(side > 0), prix_ref=d["mark"])
            except Exception as e:
                print("[executeur] OUVRIR %s %s KO : %s" % (bot, coin, e), flush=True)
                continue
            if r.get("status") == "ouvert":
                mine[coin] = {"side": side, "notional": notion, "entry": d["mark"], "ts": now.isoformat()}
                _log({"ts": now.isoformat(), "bot": bot, "coin": coin, "action": "open",
                      "side": side, "notional_usd": round(notion, 2), "mark": d["mark"],
                      "resp": str((r.get("exec") or {}).get("status", ""))})
                print("[executeur] OPEN testnet %s %s (%.0f$)" % (bot, coin, notion), flush=True)

        # FERMER : mes positions dont le bot a solde
        for coin in list(mine):
            if coin in ouverts:
                continue
            st = mine[coin]
            d = data.get(coin)
            mark = d["mark"] if d else st["entry"]
            side, entry, notion = st["side"], st["entry"], st["notional"]
            try:
                r = ex.market_close(coin)
            except Exception as e:
                print("[executeur] FERMER %s %s KO : %s" % (bot, coin, e), flush=True)
                continue
            ret = side * (mark - entry) / entry if entry else 0.0
            pnl = notion * ret - 2 * FRAIS * notion
            _log({"ts": now.isoformat(), "bot": bot, "coin": coin, "action": "close",
                  "side": side, "notional_usd": round(notion, 2), "mark": mark,
                  "resp": str(r.get("status", "") if isinstance(r, dict) else "ok"),
                  "pnl_est_usd": round(pnl, 3)})
            pf.cloturer(bot)
            del mine[coin]
            print("[executeur] CLOSE testnet %s %s pnl~%.2f$" % (bot, coin, pnl), flush=True)

        state[bot] = mine
    _ecrire_json(F_STATE, state)
    print("[executeur] positions testnet : " +
          " ".join("%s=%d" % (b, len(state.get(b, {}))) for b in PILOTES), flush=True)


if __name__ == "__main__":
    executer()
