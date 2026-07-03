#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
avis_piece_ia.py - AVIS PAR PIECE (LLM + recherche web) pour le bot 27f.
========================================================================
Pour chaque coin en move 24h >= seuil, l'IA CHERCHE le catalyseur sur le web
(listing, hack, deblocage, annonce, liquidations, whale) et juge : le move va-t-il
CONTINUER (momentum) ou RETOMBER (reversion) sur ~24h ? Ecrit etat/avis_par_piece.json
{coin:{sens,confiance,raison,ts,move_pct}} consomme par bot_27f_selecteur.

Garde-fous : budget JOURNALIER dur (AVIS_MAX_JOUR) + 1 avis / coin / 24h (dedup) +
purge des avis perimes. 100 % fictif : cet outil ne passe AUCUN ordre, il ecrit un avis.
Calque sur arbitre_ia.py (meme endpoint/headers, pattern prouve). stdlib only.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from bot_27e_arbitre import _http_post_info, _parse_ctxs   # helpers HL deja en repo

API_URL = "https://api.anthropic.com/v1/messages"
MODELE = os.environ.get("MODELE_AVIS", os.environ.get("MODELE_ARBITRE", "claude-sonnet-5"))
ETAT = Path("etat")
F_AVIS = ETAT / "avis_par_piece.json"
F_BUDGET = ETAT / "avis_budget.json"
SEUIL_MOVE = float(os.environ.get("AVIS_SEUIL", "0.10"))   # couvre 27f (20%) ET 27f10 (10%)
VOL_MIN = 1_000_000.0
MAX_AVIS_JOUR = int(os.environ.get("AVIS_MAX_JOUR", "6"))   # plafond de cout DUR
FRESH_H = 26.0
MAX_TOKENS = 400
MAX_SEARCHES = 3

SYSTEME = (
    "Tu es l'analyste 'catalyseur' du banc-paper (100% fictif, tu ne passes JAMAIS d'ordre). "
    "On te donne un actif crypto (perp Hyperliquid) qui vient de faire un move 24h extreme. "
    "Cherche sur le web la RAISON du move (listing, hack, deblocage de tokens, annonce, "
    "liquidations en cascade, whale, macro). Puis juge s'il va plutot CONTINUER (momentum) "
    "ou RETOMBER (reversion) sur ~24h. Froid, bref, chiffre. Reponds EXCLUSIVEMENT en JSON "
    "valide, sans texte autour : "
    '{"sens":"momentum|reversion","confiance":0.0,"raison":"<=180 car, cite le catalyseur"}. '
    "Si aucun catalyseur clair : sens='reversion' et confiance<=0.4."
)


def _lire_json(p):
    try:
        with Path(p).open(encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def _sauver_json(p, d):
    try:
        ETAT.mkdir(parents=True, exist_ok=True)
        with Path(p).open("w", encoding="utf-8") as fh:
            json.dump(d, fh, ensure_ascii=False)
    except OSError:
        pass


def _frais(entree, now):
    try:
        ts = datetime.fromisoformat(str(entree["ts"]).replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
    except (KeyError, ValueError, TypeError):
        return False
    return 0 <= (now - ts).total_seconds() / 3600.0 < FRESH_H


def _budget_restant(now):
    d = _lire_json(F_BUDGET)
    if d.get("date") != now.strftime("%Y-%m-%d"):
        return MAX_AVIS_JOUR
    return max(0, MAX_AVIS_JOUR - int(d.get("n", 0)))


def _incr_budget(now, k=1):
    d = _lire_json(F_BUDGET)
    jour = now.strftime("%Y-%m-%d")
    n = int(d.get("n", 0)) if d.get("date") == jour else 0
    _sauver_json(F_BUDGET, {"date": jour, "n": n + k})


def _texte(rep):
    return "\n".join(b.get("text", "") for b in (rep.get("content") or [])
                     if isinstance(b, dict) and b.get("type") == "text")


def _extraire_json(txt):
    i, j = txt.find("{"), txt.rfind("}")
    if i < 0 or j <= i:
        return None
    try:
        return json.loads(txt[i:j + 1])
    except ValueError:
        return None


def _appel_llm(cle, coin, move_pct):
    corps = {"model": MODELE, "max_tokens": MAX_TOKENS, "system": SYSTEME,
             "tools": [{"type": "web_search_20250305", "name": "web_search",
                        "max_uses": MAX_SEARCHES}],
             "messages": [{"role": "user", "content":
                 f"Actif {coin} (perp Hyperliquid), move 24h = {move_pct:+.1f}%. "
                 f"Catalyseur ? Momentum ou reversion sur 24h ? JSON strict."}]}
    req = urllib.request.Request(API_URL, data=json.dumps(corps).encode("utf-8"),
        headers={"x-api-key": cle, "anthropic-version": "2023-06-01",
                 "content-type": "application/json", "User-Agent": "banc-paper-avis"})
    with urllib.request.urlopen(req, timeout=120) as r:
        rep = json.loads(r.read().decode("utf-8"))
    d = _extraire_json(_texte(rep))
    if not d:
        return None
    sens = str(d.get("sens", "")).lower()
    if sens not in ("momentum", "reversion"):
        return None
    conf = max(0.0, min(1.0, float(d.get("confiance", 0.0))))
    return {"sens": sens, "confiance": round(conf, 2), "raison": str(d.get("raison", ""))[:180]}


def produire_avis():
    cle = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not cle:
        print("[avis] pas de cle ANTHROPIC_API_KEY - dormant", flush=True)
        return
    rep = _http_post_info({"type": "metaAndAssetCtxs"})
    if rep is None:
        return
    data = _parse_ctxs(rep)
    if not data:
        return
    now = datetime.now(timezone.utc)
    avis = {k: v for k, v in _lire_json(F_AVIS).items() if _frais(v, now)}   # purge perimes
    budget = _budget_restant(now)
    if budget <= 0:
        print("[avis] budget jour epuise", flush=True)
        _sauver_json(F_AVIS, avis)
        return
    cands = sorted([(c, d) for c, d in data.items()
                    if d["vol"] >= VOL_MIN and d["move"] is not None
                    and abs(d["move"]) >= SEUIL_MOVE and c not in avis],
                   key=lambda x: -abs(x[1]["move"]))
    fait = 0
    for coin, d in cands[:budget]:
        try:
            a = _appel_llm(cle, coin, d["move"] * 100)
        except urllib.error.HTTPError as e:
            print(f"[avis] {coin} HTTP {e.code}: {e.read().decode('utf-8','replace')[:200]}", flush=True)
            break        # stoppe net (ex. 400 sur le schema) sans bruler le budget
        except Exception as e:
            print(f"[avis] {coin} erreur: {e}", flush=True)
            continue
        if a:
            a["ts"] = now.isoformat().replace("+00:00", "Z")
            a["move_pct"] = round(d["move"] * 100, 2)
            avis[coin] = a
            fait += 1
            _incr_budget(now, 1)
            print(f"[avis] {coin} {d['move']*100:+.1f}% -> {a['sens']} "
                  f"(conf {a['confiance']}) {a['raison'][:70]}", flush=True)
    _sauver_json(F_AVIS, avis)
    print(f"[avis] {fait} nouvel(s) avis, {len(avis)} frais en base.", flush=True)


if __name__ == "__main__":
    produire_avis()
