#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bot_26_carry_nado.py - Candidat frontiere : carry funding CROSS-VENUE Nado vs Hyperliquid (paper)
=================================================================================================
Issu de la veille frontiere du 29/06/2026. Nado = perp DEX CLOB (Ink x Kraken, heritage Vertex,
API publique, funding HORAIRE). On MESURE en paper le spread de funding `Nado - Hyperliquid` sur
les paires communes ; position delta-neutre cross-venue quand |spread| > seuil. Edge = le SPREAD
(moins sensible au reversal que le niveau). 100 % fictif, lecture seule, stdlib only.

!!! ENDPOINT NADO A CONFIRMER !!!
Nado suit la convention Vertex (gateway REST : GET /query?type=...), mais l'URL exacte du gateway
et la requete funding n'ont PAS pu etre confirmees automatiquement (docs GitBook non rendues +
navigateur deconnecte). Les NADO_CANDIDATES ci-dessous sont des PARIS bases sur la convention
Vertex/Nado, et le parseur de funding est GENERIQUE (il scanne le JSON pour des couples
symbole+funding). Tant qu'aucun candidat ne renvoie de funding valide, le bot reste DORMANT
(0 trade, log explicite) sans rien casser. Des l'endpoint confirme (1 constante a corriger),
il s'active tout seul. Le bot ne plante jamais la passe (try/except dans run_once).
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

# Paris d'endpoint (convention Vertex/Nado) — a confirmer puis reduire a l'URL exacte.
NADO_CANDIDATES = (
    "https://gateway.prod.nado.xyz/v1/query?type=symbols",
    "https://gateway.prod.nado.xyz/v1/query?type=contracts",
    "https://archive.prod.nado.xyz/v1/symbols",
    "https://api.nado.xyz/v1/contracts",
)


def _http(url, body=None, timeout=8.0):
    try:
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data,
            headers={"User-Agent": USER_AGENT, "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", errors="replace"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, OSError):
        return None


def fetch_hl_funding() -> dict[str, float]:
    """{coin: funding HORAIRE} via Hyperliquid metaAndAssetCtxs (jambe de reference connue)."""
    rep = _http(HL_INFO_URL, body={"type": "metaAndAssetCtxs"})
    out = {}
    try:
        univ, ctxs = rep[0]["universe"], rep[1]
    except (TypeError, KeyError, IndexError):
        return out
    for i, coin in enumerate(univ):
        if i >= len(ctxs):
            break
        nom = str(coin.get("name", "")).upper()
        try:
            out[nom] = float((ctxs[i] or {}).get("funding"))
        except (TypeError, ValueError):
            pass
    return out


def _scan_funding(obj) -> dict[str, float]:
    """Parseur GENERIQUE : scanne un JSON arbitraire pour des couples (symbole, funding horaire).
    Tolerant aux schemas (Nado/Vertex exact inconnu). Renvoie {COIN: funding}."""
    out: dict[str, float] = {}
    SYM = ("symbol", "ticker", "ticker_id", "name", "product", "market",
           "product_symbol", "base", "base_currency")
    def walk(o):
        if isinstance(o, dict):
            sym = fund = None
            for k, v in o.items():
                kl = str(k).lower()
                if sym is None and kl in SYM and isinstance(v, (str, int)):
                    sym = str(v)
                if fund is None and "funding" in kl:
                    try:
                        fund = float(v)
                    except (TypeError, ValueError):
                        pass
            if sym and fund is not None:
                base = sym.replace("/", "-").split("-")[0].split("_")[0].upper()
                if base:
                    out[base] = fund
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(obj)
    return out


def fetch_nado_funding() -> dict[str, float]:
    """Essaie les candidats jusqu'a obtenir un dict {coin: funding}. Vide si Nado injoignable
    ou schema non reconnu (-> bot dormant, sans erreur)."""
    for url in NADO_CANDIDATES:
        rep = _http(url)
        if rep is None:
            continue
        f = _scan_funding(rep)
        if f:
            return f
    return {}


class CarryNado(Strategy):
    """Bot 26 : carry de funding cross-venue Nado<->Hyperliquid (mesure paper). Dormant tant que
    l'endpoint Nado n'est pas confirme. Meme moteur accrual/hysteresis/settle que le bot 24."""

    name = "26_carry_nado"

    def __init__(self, notional: float = 1000.0, seuil_spread: float = 1.5e-5,
                 frais_jambe_hl: float = 0.00035, frais_jambe_nado: float = 0.0002,
                 periode_settle_h: float = 24.0):
        super().__init__(stake_usd=1.0)
        self.notional = notional
        self.seuil_spread = seuil_spread        # |spread| horaire mini (1.5e-5/h ~ 13 % APR)
        self.frais = frais_jambe_hl + frais_jambe_nado
        self.periode_settle_h = periode_settle_h
        self._f = ETAT_DIR / "etat_bot26.json"
        self._etat = self._charger()

    def _charger(self):
        try:
            with self._f.open(encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, ValueError):
            return {}

    def _sauver(self):
        try:
            ETAT_DIR.mkdir(parents=True, exist_ok=True)
            with self._f.open("w", encoding="utf-8") as fh:
                json.dump(self._etat, fh)
        except OSError:
            pass

    def _slot(self, coin, now):
        if coin not in self._etat:
            self._etat[coin] = {"accrue": 0.0, "ouvert": False, "dernier_ts": None,
                                "debut_periode_ts": now.isoformat()}
        return self._etat[coin]

    def step(self):
        hl = fetch_hl_funding()
        nado = fetch_nado_funding()
        if not nado:
            print("[26] Nado injoignable / schema non reconnu — DORMANT "
                  "(endpoint a confirmer).", flush=True)
            return []
        communs = sorted(set(hl) & set(nado))
        if not communs:
            print(f"[26] Nado OK ({len(nado)} paires) mais 0 paire commune avec HL.", flush=True)
            return []
        now = datetime.now(timezone.utc)
        regles = []
        for c in communs:
            spread = nado[c] - hl[c]
            st = self._slot(c, now)
            dt = 0.0
            if st.get("dernier_ts"):
                try:
                    dt = (now - datetime.fromisoformat(st["dernier_ts"])).total_seconds() / 3600.0
                except (ValueError, TypeError):
                    dt = 0.0
            dt = max(0.0, min(dt, 6.0))
            if st["ouvert"]:
                st["accrue"] += abs(spread) * self.notional * dt
            if not st["ouvert"] and abs(spread) >= self.seuil_spread:
                st["accrue"] -= 2 * self.frais * self.notional
                st["ouvert"] = True
            elif st["ouvert"] and abs(spread) < self.seuil_spread / 2.0:
                st["accrue"] -= 2 * self.frais * self.notional
                st["ouvert"] = False
            st["dernier_ts"] = now.isoformat()
            try:
                debut = datetime.fromisoformat(st["debut_periode_ts"])
            except (ValueError, TypeError, KeyError):
                debut = now
                st["debut_periode_ts"] = now.isoformat()
            if (now - debut).total_seconds() / 3600.0 >= self.periode_settle_h:
                if st["ouvert"] or abs(st["accrue"]) > 1e-9:
                    t = Trade(self.name, f"nado-{c}", "spread", 1.0, self.notional)
                    t.close(1.0 + st["accrue"] / self.notional)
                    regles.append(t)
                    st["accrue"] = 0.0
                st["debut_periode_ts"] = now.isoformat()
        self._sauver()
        print(f"[26] Nado OK : {len(communs)} paires communes, {len(regles)} soldes.", flush=True)
        return regles
