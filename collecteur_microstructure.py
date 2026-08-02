#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
collecteur_microstructure.py - DEMARRE L'HORLOGE LENTE (02/08/2026).
=====================================================================
CE QU'IL COLLECTE, ET POURQUOI IL EXISTE
----------------------------------------
Verifie le 02/08/2026 sur l'API publique Hyperliquid :
    fundingHistory ...... historique complet          -> OK
    candleSnapshot ...... OHLCV + nb de trades        -> OK
    openInterestHistory . HTTP 422                    -> N'EXISTE PAS
    liquidations ........ HTTP 422                    -> N'EXISTE PAS
    l2Book .............. instantane courant seulement -> PAS D'HISTORIQUE

Deux variables centrales des hypotheses en attente ne sont donc PAS
backtestables :
  * l'OPEN INTEREST, variable d'encombrement du modele « Carry Provider »
    (le funding est-il eleve parce que le positionnement est encombre ?) ;
  * le CARNET D'ORDRES, sans lequel l'hypothese « les teneurs de marche se
    retirent avant une correction » ne peut pas etre testee du tout.

La seule facon d'y acceder est de les enregistrer SOI-MEME, en avant. Ce module
ne teste rien et ne conclut rien : il constitue le jeu de donnees qui rendra le
test possible plus tard. C'est un investissement de temps, pas de capital.

HORIZON AVANT PREMIER TEST EXPLOITABLE
--------------------------------------
Rappel de la lecon du 29/07 : l'unite statistique independante n'est PAS le
point de mesure, c'est la DATE (les pieces co-varient fortement). Il faut donc
compter en jours, pas en echantillons.
    ~30 dates en TRAIN + ~30 en TEST = 60 jours minimum   -> 8 a 9 semaines
    confort (marge pour les regimes)  = 90 jours          -> 13 semaines
Avant 8 semaines, tout verdict tire de ces donnees sera du bruit.

COUT : zero (API publique, lecture seule, GitHub Actions gratuit).
VOLUME : ~1,5 Mo/mois en JSONL compresse par la deduplication horaire.
stdlib uniquement.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "https://api.hyperliquid.xyz/info"
UA = "banc-paper-collecteur (read-only research)"
DONNEES = Path("donnees")
F_OI = DONNEES / "oi_history.jsonl"
F_BOOK = DONNEES / "book_history.jsonl"
F_META = DONNEES / "collecte_meta.json"

# Carnet L2 : couteux en volume, on se limite aux pieces ou l'hypothese
# « retrait des teneurs » a un sens (liquides, mais pas les mega-caps ou le
# carnet est trop profond pour bouger).
COINS_BOOK = ["HYPE", "PUMP", "PENGU", "FARTCOIN", "WIF", "TRUMP", "ENA", "TAO",
              "ASTER", "AVNT", "BERA", "KAITO"]
NIVEAUX = 5  # profondeur agregee retenue de chaque cote


def _post(body, timeout=15.0):
    try:
        req = urllib.request.Request(API, data=json.dumps(body).encode("utf-8"),
                                     headers={"Content-Type": "application/json",
                                              "User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
            ValueError, OSError):
        return None


def _f(x, d=0.0):
    try:
        return float(x)
    except (TypeError, ValueError):
        return d


def _ajouter(chemin: Path, lignes: list) -> int:
    if not lignes:
        return 0
    try:
        DONNEES.mkdir(parents=True, exist_ok=True)
        with chemin.open("a", encoding="utf-8") as fh:
            for l in lignes:
                fh.write(json.dumps(l, ensure_ascii=False, separators=(",", ":")) + "\n")
        return len(lignes)
    except OSError:
        return 0


def collecter_oi(now):
    """Instantane de l'open interest + volume + funding, TOUTES pieces."""
    rep = _post({"type": "metaAndAssetCtxs"})
    if not isinstance(rep, list) or len(rep) < 2:
        return []
    univers = (rep[0] or {}).get("universe") or []
    ctxs = rep[1] or []
    ts = now.isoformat(timespec="seconds")
    out = []
    for u, c in zip(univers, ctxs):
        if not isinstance(c, dict):
            continue
        mark = _f(c.get("markPx"))
        oi = _f(c.get("openInterest"))
        if mark <= 0 or oi <= 0:
            continue
        out.append({"ts": ts, "coin": u.get("name"),
                    "oi": round(oi, 4),
                    "oi_usd": round(oi * mark, 1),
                    "mark": mark,
                    "oracle": _f(c.get("oraclePx")),
                    "funding": _f(c.get("funding")),
                    "premium": _f(c.get("premium")),
                    "vol24_usd": round(_f(c.get("dayNtlVlm")), 1)})
    return out


def collecter_book(now):
    """Profondeur agregee du carnet : mesure du RETRAIT des teneurs de marche.

    On n'enregistre pas le carnet entier (volume inutile) mais ce qui repond a
    l'hypothese : combien de liquidite est postee de chaque cote, a quelle
    distance, et quel est le desequilibre. Un teneur qui se retire fait chuter
    'profondeur' et ecarter 'spread_bp' -- c'est le signal cherche.
    """
    ts = now.isoformat(timespec="seconds")
    out = []
    for coin in COINS_BOOK:
        d = _post({"type": "l2Book", "coin": coin})
        if not isinstance(d, dict):
            continue
        niv = d.get("levels") or []
        if len(niv) < 2 or not niv[0] or not niv[1]:
            continue
        bids, asks = niv[0][:NIVEAUX], niv[1][:NIVEAUX]
        try:
            bb, ba = _f(bids[0].get("px")), _f(asks[0].get("px"))
            if bb <= 0 or ba <= 0:
                continue
            mid = (bb + ba) / 2.0
            pb = sum(_f(x.get("px")) * _f(x.get("sz")) for x in bids)
            pa = sum(_f(x.get("px")) * _f(x.get("sz")) for x in asks)
        except (AttributeError, TypeError, IndexError):
            continue
        tot = pb + pa
        out.append({"ts": ts, "coin": coin,
                    "mid": mid,
                    "spread_bp": round(1e4 * (ba - bb) / mid, 3),
                    "prof_bid_usd": round(pb, 1),
                    "prof_ask_usd": round(pa, 1),
                    "desequilibre": round((pb - pa) / tot, 4) if tot > 0 else 0.0,
                    "n_bid": len(bids), "n_ask": len(asks)})
    return out


def executer():
    now = datetime.now(timezone.utc)
    oi = collecter_oi(now)
    book = collecter_book(now)
    n_oi = _ajouter(F_OI, oi)
    n_bk = _ajouter(F_BOOK, book)

    # meta : combien de JOURS distincts sont couverts ? C'est la seule mesure
    # qui compte pour savoir quand le jeu de donnees devient exploitable.
    meta = {}
    try:
        meta = json.loads(F_META.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    jours = set(meta.get("jours") or [])
    jours.add(now.date().isoformat())
    jours = sorted(jours)
    meta = {"debut": jours[0], "derniere_passe": now.isoformat(timespec="seconds"),
            "jours": jours, "n_jours": len(jours),
            "n_lignes_oi_dernier": n_oi, "n_lignes_book_dernier": n_bk,
            "coins_book": COINS_BOOK,
            "exploitable_a_partir_de": ("60 jours distincts (30 train + 30 test). "
                                        "Restant : %d jour(s)." % max(0, 60 - len(jours))),
            "pret": len(jours) >= 60}
    try:
        DONNEES.mkdir(parents=True, exist_ok=True)
        F_META.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        pass
    print("[collecteur] OI %d ligne(s) | carnet %d ligne(s) | %d jour(s) collecte(s) "
          "| exploitable dans %d jour(s)"
          % (n_oi, n_bk, len(jours), max(0, 60 - len(jours))), flush=True)
    return meta


if __name__ == "__main__":
    executer()
