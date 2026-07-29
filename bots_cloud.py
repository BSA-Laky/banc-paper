#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bots_cloud.py - HELPERS PARTAGES pour l'acces lecture-seule a Hyperliquid
=========================================================================
Ce module ne contient PLUS AUCUN BOT depuis le 29/07/2026. Il expose uniquement
les utilitaires communs : _http_post_info, parse_ctxs, _now, _dt_h, ETAT_DIR et
_EtatMixin, importes par les bots.

POURQUOI les bots en sont partis :
  - bot 23 (CarryFundingOnly) : TUE le 22/07 (etat/cycle_vie.json). Code retire,
    il ne servait plus qu'a fausser l'audit de conformite.
  - bot 25 (ConvergenceBasis) : deplace dans bot_25_convergence_basis.py, avec la
    comptabilite REELLE.
Les deux partageaient la meme faute : accrue += abs(f) * notional * dt, soit un
funding en valeur absolue et AUCUN terme de prix. audit_conformite.py l'a
detectee en analyse statique (lignes 169 et 275 de l'ancien fichier).

LECTURE SEULE sur l'API PUBLIQUE Hyperliquid : aucune cle, aucun wallet, aucun
ordre. L'etat JSON est ecrit dans ./etat/ (relatif au repo) pour etre committe
par le workflow et survivre entre deux passes cron.
Python 3.10+ -- bibliotheque standard uniquement.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from banc_essai_paper_trading import Strategy, Trade

HL_INFO_URL = "https://api.hyperliquid.xyz/info"
USER_AGENT = "paper-trading-bench/1.0 (read-only research)"
ETAT_DIR = Path("etat")


def _http_post_info(body: dict, timeout: float = 12.0):
    """POST JSON vers l'API publique Hyperliquid /info. Ne lève jamais -> None si KO."""
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        HL_INFO_URL, data=data,
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
            ValueError, OSError):
        return None


def parse_ctxs(meta_and_ctxs, actifs: tuple[str, ...]
               ) -> dict[str, dict[str, float]]:
    """Extrait {coin: {funding, markPx, oraclePx, premium, vol}} de metaAndAssetCtxs.

    Format : [ {"universe":[{"name":...}, ...]}, [ {"funding","markPx","oraclePx",
               "premium","dayNtlVlm",...}, ... ] ]  (listes PARALLELES)."""
    out: dict[str, dict[str, float]] = {}
    try:
        meta, ctxs = meta_and_ctxs[0], meta_and_ctxs[1]
        univ = meta["universe"]
    except (TypeError, KeyError, IndexError):
        return out
    cibles = {a.upper() for a in actifs}
    tout = "*" in cibles
    for i, coin in enumerate(univ):
        nom = str(coin.get("name", "")).upper()
        if (not tout and nom not in cibles) or i >= len(ctxs):
            continue
        c = ctxs[i] or {}
        try:
            funding = float(c.get("funding"))
        except (TypeError, ValueError):
            continue
        def _f(key, default=0.0):
            try:
                return float(c.get(key))
            except (TypeError, ValueError):
                return default
        mark = _f("markPx")
        oracle = _f("oraclePx")
        prem = c.get("premium")
        try:
            premium = float(prem)
        except (TypeError, ValueError):
            premium = ((mark - oracle) / oracle) if oracle > 0 else 0.0
        out[nom] = {"funding": funding, "markPx": mark, "oraclePx": oracle,
                    "premium": premium, "vol": _f("dayNtlVlm")}
    return out


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _dt_h(dernier: str | None) -> float:
    if not dernier:
        return 0.0
    try:
        h = (_now() - datetime.fromisoformat(dernier)).total_seconds() / 3600.0
    except (ValueError, TypeError):
        return 0.0
    return max(0.0, min(h, 6.0))   # borne anti-aberration (gros trou entre runs)


class _EtatMixin:
    fichier_etat = "etat.json"

    def _charger(self) -> dict:
        try:
            with (ETAT_DIR / self.fichier_etat).open(encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return {}

    def _sauver(self) -> None:
        try:
            ETAT_DIR.mkdir(parents=True, exist_ok=True)
            with (ETAT_DIR / self.fichier_etat).open("w", encoding="utf-8") as f:
                json.dump(self._etat, f, indent=0)
        except OSError:
            pass
