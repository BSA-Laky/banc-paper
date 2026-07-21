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


def envoyer(texte: str, boutons=None) -> bool:
    """Envoie un message au Commandant (tronque a 3900 caracteres).
    boutons = clavier inline optionnel : liste de lignes de {text, callback_data}."""
    if not actif():
        return False
    params = {"chat_id": CHAT_ID, "text": texte[:3900]}
    if boutons:
        params["reply_markup"] = json.dumps({"inline_keyboard": boutons})
    rep = _api("sendMessage", params)
    return bool(rep and rep.get("ok"))


def maj(offset: int):
    """Recupere les messages ET les taps de boutons en attente (long-poll court)."""
    if not actif():
        return []
    rep = _api("getUpdates", {"offset": offset, "timeout": 0,
                              "allowed_updates": '["message","callback_query"]'}, timeout=20.0)
    return rep.get("result", []) if rep and rep.get("ok") else []


def accuser_bouton(cb_id: str, texte: str = "") -> None:
    """answerCallbackQuery : arrete le sablier de chargement apres un tap de bouton."""
    if actif() and cb_id:
        _api("answerCallbackQuery", {"callback_query_id": cb_id, "text": texte[:180]})
