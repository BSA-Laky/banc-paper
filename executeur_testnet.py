#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
executeur_testnet.py - MIROIR TESTNET des bots selecteurs (validation machine + frais).
=======================================================================================
Reflete les positions des bots PILOTES (paper) sur Hyperliquid TESTNET via le portefeuille
(enveloppe 300 EUR) + execution_hl. Verifie le VRAI statut de chaque ordre (pas seulement
le "ok" de l'API), se reconcilie avec les positions reelles (nettoie les fantomes), et
prend prix + univers depuis le TESTNET. Testnet = argent FICTIF. Best-effort, non bloquant.
"""
from __future__ import annotations

import csv
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from bot_27e_arbitre import _parse_ctxs

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


def _info(base_url, body):
    try:
        req = urllib.request.Request(base_url + "/info", data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "banc-paper-executeur"})
        with urllib.request.urlopen(req, timeout=12) as r:
            return json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, OSError):
        return None


def _ordre_reussi(resp):
    """Vrai statut d'un ordre HL. (ok: bool, detail). Gere aussi le paper."""
    if isinstance(resp, dict) and resp.get("status") == "paper_simule":
        return True, "paper"
    try:
        st = resp["response"]["data"]["statuses"][0]
    except (KeyError, IndexError, TypeError):
        return False, "reponse inattendue"
    if isinstance(st, dict) and "error" in st:
        return False, st["error"]
    return True, st


def _positions_reelles(base_url, account):
    """Set des coins avec une position perp reelle. None si requete impossible (on ne purge pas)."""
    if not account:
        return None
    d = _info(base_url, {"type": "clearinghouseState", "user": account})
    if not isinstance(d, dict):
        return None
    out = set()
    for p in d.get("assetPositions", []):
        pos = p.get("position", {})
        try:
            if abs(float(pos.get("szi", 0))) > 0:
                out.add(pos.get("coin"))
        except (TypeError, ValueError):
            pass
    return out


def executer():
    from execution_hl import ExecutionHL
    from portefeuille import Portefeuille

    ex = ExecutionHL()
    if not ex.cfg.live_arme:
        print("[executeur] live non arme (paper) - dormant.", flush=True)
        return
    if ex.cfg.net != "testnet":
        print("[executeur] SECURITE : refuse hors testnet.", flush=True)
        return
    pf = Portefeuille(executor=ex)

    # prix + univers depuis le TESTNET (coherent avec l'execution)
    data = _parse_ctxs(_info(ex.cfg.base_url, {"type": "metaAndAssetCtxs"}) or [])
    if not data:
        print("[executeur] pas de donnees marche testnet.", flush=True)
        return
    now = datetime.now(timezone.utc)
    state = _lire_json(F_STATE, {})

    # RECONCILIATION : purge les positions suivies qui n'existent pas vraiment (fantomes)
    reelles = _positions_reelles(ex.cfg.base_url, ex.cfg.account)
    if reelles is not None:
        for bot in list(state):
            for coin in list(state.get(bot, {})):
                if coin not in reelles:
                    del state[bot][coin]
    # recalcule l'exposition du portefeuille depuis l'etat reconcilie
    pf.expo = {b: round(sum(p.get("notional", 0.0) for p in m.values()), 4) for b, m in state.items()}
    pf._sauver_expo()

    for bot in PILOTES:
        bet = _lire_json(ETAT / ("etat_%s.json" % bot), {})
        ouverts = {c: v for c, v in bet.items() if isinstance(v, dict) and v.get("ouvert")}
        mine = state.get(bot, {})

        # OUVRIR (avec verification du VRAI statut)
        for coin, v in ouverts.items():
            if coin in mine:
                continue
            d = data.get(coin)
            if not d:                       # coin absent du testnet
                continue
            ok, raison = pf.peut_ouvrir(bot)
            if not ok:
                print("[executeur] %s %s non ouvert : %s" % (bot, coin, raison), flush=True)
                continue
            side = int(v.get("side", -1))
            notion = pf.taille_entree(bot)
            lev = pf.levier(bot)
            ex.set_leverage(coin, lev)     # fixe le levier voulu (1x tant que non promu)
            try:
                r = pf.ouvrir(bot, coin, is_buy=(side > 0), prix_ref=d["mark"])
            except Exception as e:
                print("[executeur] OUVRIR %s %s KO : %s" % (bot, coin, e), flush=True)
                continue
            reussi, detail = _ordre_reussi(r.get("exec"))
            if not reussi:
                pf.cloturer(bot)            # revert l'expo : l'ordre n'est pas passe
                _log({"ts": now.isoformat(), "bot": bot, "coin": coin, "action": "REJET",
                      "side": side, "notional_usd": round(notion, 2), "mark": d["mark"], "resp": str(detail)[:60]})
                print("[executeur] REJET %s %s : %s" % (bot, coin, str(detail)[:80]), flush=True)
                continue
            mine[coin] = {"side": side, "notional": notion, "entry": d["mark"], "ts": now.isoformat()}
            _log({"ts": now.isoformat(), "bot": bot, "coin": coin, "action": "open",
                  "side": side, "notional_usd": round(notion, 2), "mark": d["mark"], "resp": "ok"})
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
                  "resp": "ok", "pnl_est_usd": round(pnl, 3)})
            pf.cloturer(bot)
            del mine[coin]
            print("[executeur] CLOSE testnet %s %s pnl~%.2f$" % (bot, coin, pnl), flush=True)

        state[bot] = mine
    _ecrire_json(F_STATE, state)
    print("[executeur] positions testnet : " +
          " ".join("%s=%d" % (b, len(state.get(b, {}))) for b in PILOTES), flush=True)


if __name__ == "__main__":
    executer()
