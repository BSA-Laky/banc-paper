#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""donnees_marche.py - couche donnees marches traditionnels (atteignable depuis le
cloud, contrairement a Yahoo/Stooq bloques sur le runner). Utilise Twelve Data
(free tier, sans carte). Cle lue dans la variable d'environnement TD_KEY.
Ne leve jamais -> None si KO. stdlib only.
"""
from __future__ import annotations

import json
import os
import urllib.request
import urllib.error

TD_KEY = os.environ.get("TD_KEY", "").strip()
BASE = "https://api.twelvedata.com"


def _get(path: str, params: dict):
    if not TD_KEY:
        return None
    q = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{BASE}/{path}?{q}&apikey={TD_KEY}"
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            return json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
            ValueError, OSError):
        return None


def monthly(symbol: str, n: int = 10):
    """Retourne {'YYYY-MM': close} (n derniers mois) ou None."""
    j = _get("time_series", {"symbol": symbol, "interval": "1month",
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
    """Retourne {'YYYY-MM-DD': close} (n derniers jours) ou None."""
    j = _get("time_series", {"symbol": symbol, "interval": "1day",
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


def vix_now():
    """Derniere valeur du VIX (vol implicite) ou None si indisponible."""
    d = daily("VIX", 3)
    if not d:
        return None
    return d[max(d)]
