#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""donnees_marche.py - couche donnees marches traditionnels (atteignable depuis le
cloud, contrairement a Yahoo/Stooq bloques sur le runner).
- Prix ETF/SPY : Twelve Data (free tier, cle env TD_KEY).
- VIX (vol implicite) : CSV public CBOE (SANS cle), repli Twelve Data.
Ne leve jamais -> None si KO. stdlib only.
"""
from __future__ import annotations

import csv
import io
import json
import os
import urllib.request
import urllib.error

TD_KEY = os.environ.get("TD_KEY", "").strip()
BASE = "https://api.twelvedata.com"
CBOE_VIX = "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv"
UA = {"User-Agent": "paper-trading-bench/1.0 (read-only research)"}


def _get_json(path: str, params: dict):
    if not TD_KEY:
        return None
    q = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{BASE}/{path}?{q}&apikey={TD_KEY}"
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
            ValueError, OSError):
        return None


def monthly(symbol: str, n: int = 10):
    j = _get_json("time_series", {"symbol": symbol, "interval": "1month",
                                  "outputsize": str(n)})
    if not j or j.get("status") == "error" or "values" not in j:
        return None
    out = {}
    for v in j["values"]:
        try:
            out[str(v["datetime"])[:7]] = float(v["close"])
        except (KeyError, TypeError, ValueError):
            pass
    return out or None


def daily(symbol: str, n: int = 30):
    j = _get_json("time_series", {"symbol": symbol, "interval": "1day",
                                  "outputsize": str(n)})
    if not j or j.get("status") == "error" or "values" not in j:
        return None
    out = {}
    for v in j["values"]:
        try:
            out[str(v["datetime"])[:10]] = float(v["close"])
        except (KeyError, TypeError, ValueError):
            pass
    return out or None


def _vix_cboe():
    """Dernier close du VIX via le CSV public CBOE (sans cle). None si KO."""
    try:
        req = urllib.request.Request(CBOE_VIX, headers=UA)
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read().decode("utf-8", "replace")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
        return None
    try:
        rows = list(csv.reader(io.StringIO(raw)))
        header = [h.strip().upper() for h in rows[0]]
        ic = header.index("CLOSE")
        for row in reversed(rows[1:]):
            if len(row) > ic and row[ic].strip():
                return float(row[ic])
    except (ValueError, IndexError):
        return None
    return None


def _vix_td():
    d = daily("VIX", 3)
    if not d:
        return None
    return d[max(d)]


def vix_now():
    """VIX (vol implicite) : CBOE d'abord, repli Twelve Data. None si indispo."""
    v = _vix_cboe()
    if v is not None:
        return v
    return _vix_td()
