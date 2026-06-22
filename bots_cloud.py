#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bots_cloud.py - Strategies pour execution CLOUD (GitHub Actions, one-shot/cron)
===============================================================================

PRINCIPE DE SECURITE (inchangé) :
  - LECTURE SEULE sur l'API PUBLIQUE Hyperliquid (aucune clé, aucun wallet, aucun
    ordre réel). 100 % FICTIF. On MESURE, sur des données réelles, l'espérance.

Deux strategies, conçues pour l'A/B du projet :
  - CarryFundingOnly  (= "23_carry_funding")    : réplique le bot 23 (coupon funding
    seul). C'est la BASELINE.
  - ConvergenceBasis  (= "25_convergence_basis"): l'hypothèse sous-exploitée. Entrée
    sur PREMIUM étiré (signal avancé) ; P&L = funding + CONVERGENCE du basis - frais.

DIFFERENCE CLE avec le code local : l'état JSON est écrit dans ./etat/ (relatif au
repo) pour qu'il soit COMMITTÉ par le workflow et survive entre deux exécutions cron.
Le %LOCALAPPDATA% / /tmp du local n'existe pas / n'est pas persistant sur le runner.

Chaque appel = UNE passe (un step). Le cron rappelle ~toutes les 15 min.

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


# --------------------------------------------------------------------------
# BASELINE : bot 23 (coupon funding seul). Réplique fidèle, état repo-relatif.
# --------------------------------------------------------------------------
class CarryFundingOnly(_EtatMixin, Strategy):
    name = "23_carry_funding"
    fichier_etat = "etat_bot23.json"

    def __init__(self, notional: float = 1000.0, actifs="*",
                 seuil_funding: float = 0.0001, frais_par_jambe: float = 0.00035,
                 periode_settle_h: float = 24.0, vol_min: float = 1_000_000.0):
        super().__init__(stake_usd=1.0)
        self.notional = notional
        if isinstance(actifs, str):
            actifs = tuple(a.strip().upper() for a in actifs.split(",") if a.strip())
        self.actifs = actifs or ("BTC", "ETH")
        self.seuil_funding = seuil_funding
        self.frais_par_jambe = frais_par_jambe
        self.periode_settle_h = periode_settle_h
        self.vol_min = vol_min
        self._etat = self._charger()

    def _a(self, a: str) -> dict:
        if a not in self._etat:
            self._etat[a] = {"accrue": 0.0, "ouvert": False, "dernier_ts": None,
                             "debut_periode_ts": _now().isoformat()}
        return self._etat[a]

    def step(self) -> list[Trade]:
        rep = _http_post_info({"type": "metaAndAssetCtxs"})
        if rep is None:
            return []
        data = parse_ctxs(rep, self.actifs)
        if not data:
            return []
        now = _now()
        regles: list[Trade] = []
        for a, info in data.items():
            if info["vol"] < self.vol_min:
                continue
            f = info["funding"]
            st = self._a(a)
            dt = _dt_h(st.get("dernier_ts"))
            if st["ouvert"]:
                st["accrue"] += abs(f) * self.notional * dt
            if not st["ouvert"] and abs(f) >= self.seuil_funding:
                st["accrue"] -= 2 * self.frais_par_jambe * self.notional
                st["ouvert"] = True
            elif st["ouvert"] and abs(f) < self.seuil_funding / 2.0:
                st["accrue"] -= 2 * self.frais_par_jambe * self.notional
                st["ouvert"] = False
            st["dernier_ts"] = now.isoformat()
            try:
                debut = datetime.fromisoformat(st["debut_periode_ts"])
            except (ValueError, TypeError, KeyError):
                debut = now
                st["debut_periode_ts"] = now.isoformat()
            if (now - debut).total_seconds() / 3600.0 >= self.periode_settle_h:
                if st["ouvert"] or abs(st["accrue"]) > 1e-9:
                    net = st["accrue"]
                    t = Trade(self.name, f"carry-{a}", "funding", 1.0, self.notional)
                    t.close(1.0 + net / self.notional)
                    regles.append(t)
                    st["accrue"] = 0.0
                st["debut_periode_ts"] = now.isoformat()
        self._sauver()
        return regles


# --------------------------------------------------------------------------
# HYPOTHESE : bot 25 - alpha de convergence du basis.
# --------------------------------------------------------------------------
class ConvergenceBasis(_EtatMixin, Strategy):
    """Entrée sur PREMIUM étiré ; P&L = funding collecté + convergence du basis - frais.

    convergence réalisée à la sortie = notional * (|premium_entree| - |premium_now|)
      > 0 si le basis s'est resserré (le perp est revenu vers l'oracle) -> GAIN
      < 0 si le basis s'est élargi (stop) -> PERTE mesurée honnêtement.
    Un Trade est émis par POSITION fermée (profil event-driven attendu).
    """
    name = "25_convergence_basis"
    fichier_etat = "etat_bot25.json"

    def __init__(self, notional: float = 1000.0, actifs="*",
                 premium_enter: float = 0.0010,   # 0,10 % : basis étiré
                 premium_exit_frac: float = 0.30,  # sortie quand |prem| <= 30 % de l'entrée
                 premium_stop_mult: float = 2.5,   # stop si |prem| >= 2,5 x l'entrée
                 max_hold_h: float = 16.0,         # borne (~2 demi-vies OU)
                 frais_par_jambe: float = 0.00035,
                 vol_min: float = 1_000_000.0):
        super().__init__(stake_usd=1.0)
        self.notional = notional
        if isinstance(actifs, str):
            actifs = tuple(a.strip().upper() for a in actifs.split(",") if a.strip())
        self.actifs = actifs or ("BTC", "ETH")
        self.premium_enter = premium_enter
        self.premium_exit_frac = premium_exit_frac
        self.premium_stop_mult = premium_stop_mult
        self.max_hold_h = max_hold_h
        self.frais_par_jambe = frais_par_jambe
        self.vol_min = vol_min
        self._etat = self._charger()

    def _a(self, a: str) -> dict:
        if a not in self._etat:
            self._etat[a] = {"ouvert": False, "premium_entree": 0.0, "accrue": 0.0,
                             "entree_ts": None, "dernier_ts": None}
        return self._etat[a]

    def step(self) -> list[Trade]:
        rep = _http_post_info({"type": "metaAndAssetCtxs"})
        if rep is None:
            return []
        data = parse_ctxs(rep, self.actifs)
        if not data:
            return []
        now = _now()
        regles: list[Trade] = []
        rt_fee_leg = 2 * self.frais_par_jambe * self.notional   # une jambe d'A/R = 2 cotés
        for a, info in data.items():
            if info["vol"] < self.vol_min:
                continue
            prem = info["premium"]
            f = info["funding"]
            st = self._a(a)
            dt = _dt_h(st.get("dernier_ts"))

            if st["ouvert"]:
                # 1) coupon funding accumulé sur l'intervalle
                st["accrue"] += abs(f) * self.notional * dt
                # 2) test de sortie
                p_in = abs(st["premium_entree"])
                p_now = abs(prem)
                try:
                    held = (now - datetime.fromisoformat(st["entree_ts"])).total_seconds() / 3600.0
                except (ValueError, TypeError, KeyError):
                    held = 0.0
                converge = p_now <= self.premium_exit_frac * p_in
                elargi = p_now >= self.premium_stop_mult * p_in
                timeout = held >= self.max_hold_h
                if converge or elargi or timeout:
                    conv = self.notional * (p_in - p_now)         # gain de convergence
                    net = st["accrue"] + conv - rt_fee_leg        # - frais de sortie
                    t = Trade(self.name, f"conv-{a}", "basis", 1.0, self.notional)
                    t.close(1.0 + net / self.notional)
                    regles.append(t)
                    st.update({"ouvert": False, "premium_entree": 0.0,
                               "accrue": 0.0, "entree_ts": None})
            else:
                # entrée sur premium étiré
                if abs(prem) >= self.premium_enter:
                    st["ouvert"] = True
                    st["premium_entree"] = prem
                    st["accrue"] = -rt_fee_leg                    # frais d'entrée
                    st["entree_ts"] = now.isoformat()
            st["dernier_ts"] = now.isoformat()
        self._sauver()
        return regles
