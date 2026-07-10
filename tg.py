#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tg.py - mini-client Telegram de la station (stdlib, jamais bloquant)
====================================================================
Utilise le Bot API officiel. Sans TELEGRAM_TOKEN / TELEGRAM_CHAT_ID (secrets
GitHub), tout est neutralise proprement. Ne repond QU'AU chat du Commandant.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request

TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()


def actif() -> bool:
    return bool(TOKEN and CHAT_ID)


def _api(methode: str, params: dict, timeout: float = 15.0):
    url = f"https://api.telegram.org/bot{TOKEN}/{methode}"
    data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(url, data=data,
        headers={"User-Agent": "banc-paper-station"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
            ValueError, OSError) as e:
        print(f"[tg] API KO ({methode}) : {e}", flush=True)
        return None


def envoyer(texte: str) -> bool:
    """Envoie un message au Commandant (tronque a 3900 caracteres)."""
    if not actif():
        return False
    rep = _api("sendMessage", {"chat_id": CHAT_ID, "text": texte[:3900]})
    return bool(rep and rep.get("ok"))


def maj(offset: int):
    """Recupere les messages en attente (long-poll court)."""
    if not actif():
        return []
    rep = _api("getUpdates", {"offset": offset, "timeout": 0,
                              "allowed_updates": '["message"]'}, timeout=20.0)
    return rep.get("result", []) if rep and rep.get("ok") else []
