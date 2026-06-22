#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bot_24_funding_multivenues.py - Strategie n°24 : funding multi-venues (mesure)
==============================================================================
COPIE CLOUD : identique au bot 24 local, SAUF _dossier() qui écrit dans ./etat/
(relatif au repo) pour que l'état soit committé par GitHub Actions et survive
entre deux exécutions cron. Logique + selftest inchangés.

Trois capteurs, un bot, zéro clé :
  A) CARRY PARADEX (API publique GET).
  B) SPREAD cross-venue Hyperliquid <-> Paradex sur les actifs communs.
  C) CAPTEUR ADEN (compteur d'extrêmes longue traîne ; jeté si feed stale).

MESURE uniquement (aucun ordre, argent 100 % fictif). Python 3.10+, stdlib.
  python bot_24_funding_multivenues.py --selftest   # logique hors-ligne
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from banc_essai_paper_trading import ControleAleatoire, Strategy, Trade

PDX_URL = "https://api.prod.paradex.trade/v1/markets/summary?market=ALL"
HL_INFO_URL = "https://api.hyperliquid.xyz/info"
ADEN_URL = "https://perp-api.aden.io/contracts"
USER_AGENT = "paper-trading-bench/1.0 (read-only research)"

EUR_PER_USD = 0.871


def _dossier() -> Path:
    # CLOUD : état dans le repo (committé), pas dans %LOCALAPPDATA%/tmp.
    d = Path("etat")
    d.mkdir(parents=True, exist_ok=True)
    return d


def _http_json(url: str, body: dict | None = None, timeout: float = 12.0):
    """GET (body=None) ou POST JSON. Renvoie l'objet JSON ou None."""
    try:
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            url, data=data,
            headers={"User-Agent": USER_AGENT, "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", errors="replace"))
    except (urllib.error.URLError, OSError, ValueError):
        return None


def _f(d: dict, *cles):
    """Premier champ parseable en float parmi les candidats (schema defensif)."""
    for c in cles:
        v = d.get(c)
        if v is None or v == "":
            continue
        try:
            return float(v)
        except (TypeError, ValueError):
            continue
    return None


def apy(f_horaire: float) -> float:
    return f_horaire * 24.0 * 365.0


def _aden_sym(c: dict) -> str:
    for cle in ("ticker_id", "index_name", "base_currency", "symbol", "contract"):
        v = c.get(cle)
        if v:
            return str(v)
    return ""


def fetch_paradex() -> dict[str, float]:
    rep = _http_json(PDX_URL)
    items = rep.get("results") if isinstance(rep, dict) else rep
    out: dict[str, float] = {}
    if not isinstance(items, list):
        return out
    for it in items:
        if not isinstance(it, dict):
            continue
        sym = str(it.get("symbol") or it.get("market") or "")
        if not sym:
            continue
        f = _f(it, "funding_rate", "last_funding_rate", "funding", "current_funding_rate")
        if f is None:
            continue
        out[sym.split("-")[0].upper()] = f
    return out


def fetch_hyperliquid() -> dict[str, float]:
    rep = _http_json(HL_INFO_URL, body={"type": "metaAndAssetCtxs"})
    out: dict[str, float] = {}
    try:
        univ, ctxs = rep[0]["universe"], rep[1]
    except (TypeError, KeyError, IndexError):
        return out
    for i, coin in enumerate(univ):
        if i >= len(ctxs):
            break
        nom = str(coin.get("name", "")).upper()
        f = _f(ctxs[i] or {}, "funding")
        if nom and f is not None:
            out[nom] = f
    return out


def fetch_aden() -> list[dict]:
    rep = _http_json(ADEN_URL)
    if isinstance(rep, dict):
        rep = rep.get("data") or rep.get("contracts") or rep.get("results")
    return rep if isinstance(rep, list) else []


class FundingMultiVenues(Strategy):
    """Bot n°24 : carry Paradex + spread HL<->PDX + capteur ADEN (mesure paper)."""

    name = "24_funding_multivenues"

    def __init__(self, stake_usd: float = 1.0, notional: float = 1000.0,
                 seuil_funding: float = 0.0001, seuil_spread: float = 0.0001,
                 frais_jambe_hl: float = 0.00035, frais_jambe_pdx: float = 0.0002,
                 pdx_periode_h: float = 8.0, aden_vol_min: float = 10000.0,
                 aden_seuil_apy: float = 0.50, periode_settle_h: float = 24.0,
                 pause_req: float = 0.3):
        super().__init__(stake_usd)
        self.notional = notional
        self.seuil_funding = seuil_funding
        self.seuil_spread = seuil_spread
        self.frais_jambe_hl = frais_jambe_hl
        self.frais_jambe_pdx = frais_jambe_pdx
        self.pdx_periode_h = max(pdx_periode_h, 0.01)
        self.aden_vol_min = aden_vol_min
        self.aden_seuil_apy = aden_seuil_apy
        self.periode_settle_h = periode_settle_h
        self.pause_req = pause_req
        self._fichier = _dossier() / "etat_bot24.json"
        self._etat: dict = self._charger()
        for poche in ("pdx", "sprd"):
            self._etat.setdefault(poche, {})
        self._etat.setdefault("aden", {"pairs": {}, "cumul_extremes": 0,
                                       "cumul_cycles": 0, "cumul_illiquides": 0})

    def _charger(self) -> dict:
        try:
            with self._fichier.open(encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return {}

    def _sauver(self) -> None:
        try:
            with self._fichier.open("w", encoding="utf-8") as f:
                json.dump(self._etat, f)
        except OSError:
            pass

    def _slot(self, poche: str, cle: str) -> dict:
        p = self._etat[poche]
        if cle not in p:
            p[cle] = {"accrue": 0.0, "ouvert": False, "dernier_ts": None,
                      "debut_periode_ts": datetime.now(timezone.utc).isoformat()}
        return p[cle]

    def _accrual(self, poche: str, prefixe: str, cle: str, taux_horaire: float,
                 seuil: float, frais_transition: float, now: datetime,
                 regles: list) -> dict:
        st = self._slot(poche, cle)
        dt_h = 0.0
        if st.get("dernier_ts"):
            try:
                dt_h = (now - datetime.fromisoformat(st["dernier_ts"])
                        ).total_seconds() / 3600.0
            except (ValueError, TypeError):
                dt_h = 0.0
        dt_h = max(0.0, min(dt_h, 6.0))
        if st["ouvert"]:
            st["accrue"] += abs(taux_horaire) * self.notional * dt_h
        if not st["ouvert"] and abs(taux_horaire) >= seuil:
            st["accrue"] -= frais_transition * self.notional
            st["ouvert"] = True
        elif st["ouvert"] and abs(taux_horaire) < seuil / 2.0:
            st["accrue"] -= frais_transition * self.notional
            st["ouvert"] = False
        st["dernier_ts"] = now.isoformat()
        try:
            debut = datetime.fromisoformat(st["debut_periode_ts"])
        except (ValueError, TypeError, KeyError):
            debut = now
            st["debut_periode_ts"] = now.isoformat()
        if (now - debut).total_seconds() / 3600.0 >= self.periode_settle_h:
            if st["ouvert"] or abs(st["accrue"]) > 1e-9:
                t = Trade(bot=self.name, market=f"{prefixe}-{cle}", side="funding",
                          entry_price=1.0, size_usd=self.notional)
                t.close(1.0 + st["accrue"] / self.notional)
                regles.append(t)
                st["accrue"] = 0.0
            st["debut_periode_ts"] = now.isoformat()
        return st

    def _scan_aden(self, contrats: list, now_ms: float) -> str:
        a = self._etat["aden"]
        a["cumul_cycles"] += 1
        if not contrats:
            return "[aden] feed vide/injoignable ce cycle."
        ts_max = 0.0
        for c in contrats:
            t = _f(c, "next_funding_rate_timestamp", "funding_timestamp") or 0.0
            ts_max = max(ts_max, t)
        if ts_max and ts_max < now_ms - 24 * 3600 * 1000:
            return ("[aden] feed STALE (dernier funding ts > 24 h) -> ignore. "
                    "Si ca persiste plusieurs jours : jeter ce capteur.")
        extremes, illiquides = [], 0
        for c in contrats:
            sym = _aden_sym(c)
            f_int = _f(c, "funding_rate")
            if not sym or f_int is None:
                continue
            vol = _f(c, "quote_volume", "volume_24h", "quoteVolume") or 0.0
            ts = _f(c, "next_funding_rate_timestamp", "funding_timestamp")
            prec = a["pairs"].get(sym)
            inter_h = 8.0
            if ts is not None:
                if prec and ts > prec:
                    inter_h = max(0.5, min((ts - prec) / 3600000.0, 24.0))
                a["pairs"][sym] = ts
            apy_pair = f_int * (8760.0 / inter_h)
            if abs(apy_pair) >= self.aden_seuil_apy:
                if vol >= self.aden_vol_min:
                    extremes.append((sym, f_int, apy_pair, vol))
                else:
                    illiquides += 1
        a["cumul_extremes"] += len(extremes)
        a["cumul_illiquides"] += illiquides
        extremes.sort(key=lambda x: -abs(x[2]))
        tete = " | ".join(f"{s} {f:+.4%}/int (~{p:+.0%}/an, vol {v/1000:.0f}k$)"
                          for s, f, p, v in extremes[:3]) or "aucun"
        return (f"[aden] extremes liquides: {len(extremes)} (cumul "
                f"{a['cumul_extremes']}) | illiquides ignores: {illiquides} | "
                f"top: {tete}")

    def step(self) -> list[Trade]:
        now = datetime.now(timezone.utc)
        regles: list[Trade] = []

        pdx = fetch_paradex()
        hl = fetch_hyperliquid()
        aden = fetch_aden()

        pos_pdx, top_pdx = 0, []
        for actif, f in pdx.items():
            f_h = f / self.pdx_periode_h
            st = self._accrual("pdx", "pdxcarry", actif, f_h, self.seuil_funding,
                               2 * self.frais_jambe_pdx, now, regles)
            pos_pdx += bool(st["ouvert"])
            top_pdx.append((actif, f_h, st["ouvert"]))
        top_pdx.sort(key=lambda x: (not x[2], -abs(x[1])))

        communs = sorted(set(pdx) & set(hl))
        pos_sprd, top_sprd = 0, []
        for actif in communs:
            spread = hl[actif] - pdx[actif] / self.pdx_periode_h
            st = self._accrual("sprd", "sprd", actif, spread, self.seuil_spread,
                               self.frais_jambe_hl + self.frais_jambe_pdx,
                               now, regles)
            pos_sprd += bool(st["ouvert"])
            top_sprd.append((actif, spread, st["ouvert"]))
        top_sprd.sort(key=lambda x: (not x[2], -abs(x[1])))

        ligne_aden = self._scan_aden(aden, now.timestamp() * 1000.0)
        self._sauver()

        if not pdx:
            print("[24] Paradex injoignable/illisible ce cycle.", flush=True)
        if not hl:
            print("[24] Hyperliquid injoignable ce cycle.", flush=True)
        print(f"[24] PDX carry ({len(pdx)} marches, {pos_pdx} pos) | "
              f"SPREAD HL<->PDX ({len(communs)} communs, {pos_sprd} pos) | "
              f"{len(regles)} soldes", flush=True)
        print(ligne_aden, flush=True)
        return regles


def selftest() -> int:
    """Logique hors-ligne : funding injecte connu -> accru/settle attendus."""
    bot = FundingMultiVenues(periode_settle_h=-1.0)
    bot._fichier = Path("selftest_bot24.json")
    bot._etat = {"pdx": {}, "sprd": {},
                 "aden": {"pairs": {}, "cumul_extremes": 0,
                          "cumul_cycles": 0, "cumul_illiquides": 0}}
    now = datetime.now(timezone.utc)
    regles: list[Trade] = []
    st = bot._accrual("pdx", "pdxcarry", "BTC", 5e-4, bot.seuil_funding,
                      2 * bot.frais_jambe_pdx, now, regles)
    assert st["ouvert"], "position non ouverte au-dessus du seuil"
    assert regles and regles[0].pnl is not None, "settle immediat attendu"
    pnl_ouverture = regles[0].pnl
    assert pnl_ouverture < 0, "le 1er settle ne porte que les frais d'entree"
    st = bot._accrual("pdx", "pdxcarry", "ETH", 5e-4, bot.seuil_funding,
                      2 * bot.frais_jambe_pdx, now, regles)
    st = bot._accrual("pdx", "pdxcarry", "ETH", bot.seuil_funding / 1.5,
                      bot.seuil_funding, 2 * bot.frais_jambe_pdx, now, regles)
    assert st["ouvert"], "hysteresis violee : sortie au-dessus de seuil/2"
    st = bot._accrual("pdx", "pdxcarry", "ETH", bot.seuil_funding / 3.0,
                      bot.seuil_funding, 2 * bot.frais_jambe_pdx, now, regles)
    assert not st["ouvert"], "pas de sortie sous seuil/2"
    now_ms = now.timestamp() * 1000.0
    msg = bot._scan_aden([
        {"symbol": "AAA-PERPUSDT", "funding_rate": "0.005",
         "quote_volume": "50000", "next_funding_rate_timestamp": now_ms},
        {"symbol": "BBB-PERPUSDT", "funding_rate": "0.005",
         "quote_volume": "500", "next_funding_rate_timestamp": now_ms},
    ], now_ms)
    assert "extremes liquides: 1" in msg and "illiquides ignores: 1" in msg, msg
    msg2 = bot._scan_aden([{"symbol": "AAA-PERPUSDT", "funding_rate": "0.005",
                            "quote_volume": "50000",
                            "next_funding_rate_timestamp": now_ms - 48 * 3600e3}],
                          now_ms)
    assert "STALE" in msg2, msg2
    try:
        bot._fichier.unlink()
    except OSError:
        pass
    print("SELFTEST OK — ouverture/frais, hysteresis, settle, capteur ADEN "
          f"(1er settle = frais d'entree : {pnl_ouverture:+.3f} USD).")
    return 0


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Bot n°24 funding multi-venues (mesure).")
    ap.add_argument("--cycles", type=int, default=3)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        raise SystemExit(selftest())
    from banc_essai_paper_trading import lancer
    print(__doc__)
    lancer([FundingMultiVenues(), ControleAleatoire(stake_usd=1.0)],
           cycles=args.cycles, rapport_tous_les=args.cycles)
