#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bot_25_convergence_basis.py - CONVERGENCE DU BASIS, comptabilite corrigee (29/07/2026)
=======================================================================================
CE BOT VIVAIT DANS bots_cloud.py AVEC DEUX FAUTES DE COMPTABILITE
------------------------------------------------------------------
Ancienne version, coeur du calcul :

    st["accrue"] += abs(f) * self.notional * dt        # FAUTE 1
    conv = self.notional * (p_in - p_now)              # FAUTE 2
    net  = st["accrue"] + conv - frais

  FAUTE 1 - 'abs(f)' : le bot encaissait le funding QUEL QUE SOIT son sens. Sur
    Hyperliquid, f > 0 veut dire que les LONGS paient les SHORTS : un long sur
    funding positif PAIE. Encaisser des deux cotes rend la perte impossible.
  FAUTE 2 - le P&L utilisait la CONVERGENCE DU PREMIUM comme si c'etait un gain.
    Or le premium qui se resserre ne dit RIEN de ce que gagne la position : seul
    compte le mouvement du PRIX de marque. Le paper mesurait un indicateur, le
    compte reel encaissait autre chose.

Ce que ca a produit : paper t = +3,67 (verdict "VERT", candidat au passage en
argent reel du 29/07) contre une execution testnet reelle a t = -2,81 sur
n = 96, 65 % de perdants. Le garde-fou audit_conformite.py a retrouve la faute
en analyse statique (bots_cloud.py l.169 et l.275) et a bloque la promotion.

DESORMAIS : le SIGNAL est inchange (entree sur premium etire, sortie sur
convergence / stop / timeout) mais le P&L passe par comptabilite.PositionReelle :

    P&L = side * (mark_sortie - mark_entree)/mark_entree + funding SIGNE - frais reels

Le sens de la position est explicite : premium > 0 (marque au-dessus de l'oracle)
=> on SHORTE en pariant sur le resserrement ; premium < 0 => on LONGE.

/!\ L'historique paper anterieur au 26/07/2026 mesurait une autre grandeur et est
ecarte des statistiques (etat/correction_comptable.json). Le bot repart de zero.

stdlib uniquement.
"""
from __future__ import annotations

import json
from datetime import datetime

from banc_essai_paper_trading import Strategy, Trade
from bots_cloud import _http_post_info, parse_ctxs, _now, _dt_h, ETAT_DIR
from comptabilite import Livre, notionnel_par_ligne


class ConvergenceBasis(Strategy):
    name = "25_convergence_basis"

    def __init__(self, actifs="*", premium_enter: float = 0.0010,
                 premium_exit_frac: float = 0.30, premium_stop_mult: float = 2.5,
                 max_hold_h: float = 16.0, vol_min: float = 1_000_000.0,
                 lignes_max: int = 10):
        super().__init__(stake_usd=1.0)
        if isinstance(actifs, str):
            actifs = tuple(a.strip().upper() for a in actifs.split(",") if a.strip())
        self.actifs = actifs or ("*",)
        self.premium_enter = float(premium_enter)
        self.premium_exit_frac = float(premium_exit_frac)
        self.premium_stop_mult = float(premium_stop_mult)
        self.max_hold_h = float(max_hold_h)
        self.vol_min = float(vol_min)
        self.lignes_max = int(lignes_max)
        self._f = ETAT_DIR / "etat_bot25.json"
        self.livre = Livre(self.name)
        self._etat = self._charger()
        self.livre.charger(self._etat.get("positions", {}))

    def _charger(self) -> dict:
        try:
            d = json.loads(self._f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        # L'ancien format stockait {coin: {ouvert, premium_entree, accrue, ...}} a la
        # racine. Il n'est PAS convertible : 'accrue' melangeait un funding en valeur
        # absolue et une convergence de premium, sans aucun prix. On repart a neuf.
        return d if "positions" in d else {"positions": {}, "migre_le": _now().isoformat()}

    def _sauver(self) -> None:
        self._etat["positions"] = self.livre.vers_dict()
        try:
            ETAT_DIR.mkdir(parents=True, exist_ok=True)
            self._f.write_text(json.dumps(self._etat, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass

    def step(self) -> list[Trade]:
        rep = _http_post_info({"type": "metaAndAssetCtxs"})
        if rep is None:
            return []
        data = parse_ctxs(rep, self.actifs)
        if not data:
            return []
        now = _now()
        dt = _dt_h(self._etat.get("dernier_ts"))
        self._etat["dernier_ts"] = now.isoformat()

        # 1) funding SIGNE sur les positions ouvertes
        self.livre.accumuler_tout(data, dt)

        # 2) sorties : convergence / stop / timeout
        regles: list[Trade] = []
        meta = self._etat.setdefault("meta", {})
        for coin in list(self.livre.positions):
            info = data.get(coin)
            m = meta.get(coin) or {}
            p_in = abs(float(m.get("premium_entree") or 0.0))
            try:
                held = (now - datetime.fromisoformat(str(m.get("entree_ts")))).total_seconds() / 3600.0
            except (ValueError, TypeError):
                held = 0.0
            if info is None:
                # piece hors flux : on ne solde qu'a l'echeance, au prix d'entree
                if held >= self.max_hold_h:
                    tr = self.livre.fermer(coin, self.livre.positions[coin].mark_entree)
                    if tr:
                        regles.append(tr)
                    meta.pop(coin, None)
                continue
            p_now = abs(info["premium"])
            converge = p_in > 0 and p_now <= self.premium_exit_frac * p_in
            elargi = p_in > 0 and p_now >= self.premium_stop_mult * p_in
            if converge or elargi or held >= self.max_hold_h:
                tr = self.livre.fermer(coin, info["markPx"])
                if tr:
                    regles.append(tr)
                meta.pop(coin, None)

        # 3) entrees : premium etire, sens = -signe(premium)
        libres = self.lignes_max - len(self.livre.positions)
        if libres > 0:
            cand = [(c, d) for c, d in data.items()
                    if c not in self.livre.positions
                    and abs(d["premium"]) >= self.premium_enter
                    and d.get("vol", 0) >= self.vol_min
                    and d.get("markPx", 0) > 0]
            cand.sort(key=lambda x: -abs(x[1]["premium"]))
            notionnel = notionnel_par_ligne(self.lignes_max)
            for coin, d in cand[:libres]:
                side = -1 if d["premium"] > 0 else 1
                self.livre.ouvrir(coin, side, notionnel, d["markPx"])
                meta[coin] = {"premium_entree": d["premium"], "entree_ts": now.isoformat()}

        self._etat["ecart_neutralite"] = round(self.livre.ecart_neutralite(), 6)
        self._etat["exposition_nette"] = round(self.livre.exposition_nette, 2)
        self._sauver()
        if regles:
            print("[25] convergence basis (comptabilite reelle) : %d soldee(s)"
                  % len(regles), flush=True)
        return regles
