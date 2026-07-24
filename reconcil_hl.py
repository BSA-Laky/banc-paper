#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reconcil_hl.py - RECONCILIATION du reel avec la VERITE Hyperliquid (24/07/2026).
================================================================================
Lecon de l'audit du 24/07 : le suivi interne (marks estimes, sans frais reels ni
funding ni non-realise) affichait -1,68 $ quand le compte HL etait a -20,79 $.
Ce module interroge l'API publique /info avec l'ADRESSE du compte (env, jamais
en dur) et ecrit etat/reel_hl.json = LA source de verite affichee par reel.html :
  - equity (accountValue) et P&L COMPTE = equity - depot (le chiffre de l'UI HL),
  - positions reelles (entryPx, unrealizedPnl, liquidationPx),
  - fills reels (closedPnl, fees) + funding net depuis le 20/07,
  - identite comptable : realise - frais + funding + latent ~= P&L compte.
Lecture seule, best-effort, jamais bloquant. stdlib uniquement.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SORTIE = Path("etat") / "reel_hl.json"
DEPUIS_MS = 1784505600000   # 2026-07-20 00:00 UTC (avant le 1er ordre reel du 21/07)


def _info(base_url, body, timeout=12.0):
    try:
        req = urllib.request.Request(base_url + "/info", data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "banc-paper-reconcil"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, OSError):
        return None


def _f(x, d=0.0):
    try:
        return float(x)
    except (TypeError, ValueError):
        return d


def produire(base_url, account, depot_usdc):
    if not account:
        print("[reconcil] pas d'adresse de compte -> rien a faire.", flush=True)
        return None
    now = datetime.now(timezone.utc)
    doc = {"ts": now.isoformat(), "depot_usdc": round(_f(depot_usdc), 2),
           "equity": None, "withdrawable": None, "pnl_compte": None,
           "unrealized_total": None, "realized_fills": None, "fees_total": None,
           "funding_net": None, "residu_identite": None,
           "positions_hl": [], "fills_recents": [], "par_coin": {}, "n_fills": 0}

    # 1) Etat du compte (equity + positions + non-realise)
    ch = _info(base_url, {"type": "clearinghouseState", "user": account})
    if isinstance(ch, dict) and "marginSummary" in ch:
        ms = ch.get("marginSummary") or {}
        doc["equity"] = round(sum(_f(b.get("total")) for b in ((_info(base_url, {"type": "spotClearinghouseState", "user": account}) or {}).get("balances") or []) if str(b.get("coin")) == "USDC") or _f(ms.get("accountValue")), 2)
        doc["withdrawable"] = round(_f(ch.get("withdrawable")), 2)
        unreal = 0.0
        for p in ch.get("assetPositions", []):
            pos = p.get("position") or {}
            szi = _f(pos.get("szi"))
            if abs(szi) <= 0:
                continue
            u = _f(pos.get("unrealizedPnl"))
            unreal += u
            doc["positions_hl"].append({
                "coin": pos.get("coin"), "szi": szi,
                "sens": "long" if szi > 0 else "short",
                "entry": _f(pos.get("entryPx")),
                "valeur_usd": round(abs(_f(pos.get("positionValue"))), 2),
                "unrealized": round(u, 3),
                "liq_px": pos.get("liquidationPx"),
                "marge_usd": round(_f(pos.get("marginUsed")), 2)})
        doc["unrealized_total"] = round(unreal, 2); doc["equity"] = round(_f(doc["equity"]) + unreal, 2)
        if doc["equity"] is not None and doc["depot_usdc"]:
            doc["pnl_compte"] = round(doc["equity"] - doc["depot_usdc"], 2)

    # 2) Fills reels (realise + frais, par coin)
    fills = _info(base_url, {"type": "userFills", "user": account})
    if isinstance(fills, list):
        realise, frais = 0.0, 0.0
        par_coin = {}
        for x in fills:
            if not isinstance(x, dict) or _f(x.get("time")) < DEPUIS_MS:
                continue
            doc["n_fills"] += 1
            cp, fe = _f(x.get("closedPnl")), _f(x.get("fee"))
            realise += cp
            frais += fe
            c = par_coin.setdefault(str(x.get("coin")), {"n": 0, "closedPnl": 0.0, "fees": 0.0})
            c["n"] += 1
            c["closedPnl"] = round(c["closedPnl"] + cp, 3)
            c["fees"] = round(c["fees"] + fe, 4)
        doc["realized_fills"] = round(realise, 2)
        doc["fees_total"] = round(frais, 2)
        doc["par_coin"] = par_coin
        for x in fills[:20]:
            if not isinstance(x, dict):
                continue
            try:
                ts = datetime.fromtimestamp(_f(x.get("time")) / 1000, tz=timezone.utc).isoformat()[:16]
            except (ValueError, OSError, OverflowError):
                ts = ""
            doc["fills_recents"].append({
                "ts": ts, "coin": x.get("coin"), "dir": x.get("dir"),
                "px": _f(x.get("px")), "sz": _f(x.get("sz")),
                "closedPnl": round(_f(x.get("closedPnl")), 3),
                "fee": round(_f(x.get("fee")), 4)})

    # 3) Funding net paye/recu
    fund = _info(base_url, {"type": "userFunding", "user": account, "startTime": DEPUIS_MS})
    if isinstance(fund, list):
        doc["funding_net"] = round(sum(_f((x.get("delta") or {}).get("usdc"))
                                       for x in fund if isinstance(x, dict)), 3)

    # 4) Identite comptable (residu = depots/retraits non reportes + arrondis)
    if doc["pnl_compte"] is not None and None not in (doc["realized_fills"], doc["fees_total"],
                                                      doc["funding_net"], doc["unrealized_total"]):
        attendu = doc["realized_fills"] - doc["fees_total"] + doc["funding_net"] + doc["unrealized_total"]
        doc["residu_identite"] = round(doc["pnl_compte"] - attendu, 2)

    try:
        SORTIE.parent.mkdir(parents=True, exist_ok=True)
        SORTIE.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        pass
    print("[reconcil] equity=%s pnl_compte=%s realise=%s frais=%s funding=%s latent=%s (residu %s)"
          % (doc["equity"], doc["pnl_compte"], doc["realized_fills"], doc["fees_total"],
             doc["funding_net"], doc["unrealized_total"], doc["residu_identite"]), flush=True)
    return doc


if __name__ == "__main__":
    import os
    from execution_hl import ExecutionHL
    cfg = ExecutionHL().cfg
    produire(cfg.base_url, cfg.account, float(os.environ.get("DEPOT_USDC", "0") or 0))
