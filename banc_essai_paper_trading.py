#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
banc_essai_paper_trading.py - Banc d'essai de PAPER-TRADING (trading fictif)
============================================================================
Copie pour exécution cloud (GitHub Actions). Identique au moteur local :
mêmes Trade / Strategy / evaluer (espérance + t-stat + max drawdown).
Python 3.10+ -- bibliotheque standard uniquement.
"""

from __future__ import annotations

import csv
import math
import random
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

LEDGER_PATH = Path("paper_trades.csv")   # journal persistant (committé par Actions)


@dataclass
class Trade:
    bot: str
    market: str
    side: str
    entry_price: float
    size_usd: float
    opened_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat())
    closed_at: str | None = None
    exit_price: float | None = None
    pnl: float | None = None
    status: str = "open"

    def close(self, exit_price: float) -> None:
        self.exit_price = exit_price
        self.pnl = self.size_usd * (exit_price / self.entry_price - 1.0)
        self.closed_at = datetime.now(timezone.utc).isoformat()
        self.status = "closed"


class Strategy:
    """Classe de base. Une vraie strategie surcharge `step()`."""
    name: str = "base"

    def __init__(self, stake_usd: float = 1.0):
        self.stake_usd = stake_usd

    def step(self) -> list[Trade]:
        return []

    def manage(self, open_trades: list[Trade]) -> None:
        return None


class ControleAleatoire(Strategy):
    """Bot temoin : decisions a pile ou face, paie un spread. L'etalon du bruit."""
    name = "10_controle_aleatoire"

    def __init__(self, stake_usd: float = 1.0, spread: float = 0.02):
        super().__init__(stake_usd)
        self.spread = spread

    def step(self) -> list[Trade]:
        entry = 0.50 + self.spread / 2
        side = random.choice(["UP", "DOWN"])
        t = Trade(self.name, "fictif-50/50", side, entry, self.stake_usd)
        gagnant = random.random() < 0.50
        t.close(1.0 if gagnant else 0.0)
        return [t]


CHAMPS = ["bot", "market", "side", "entry_price", "size_usd",
          "opened_at", "closed_at", "exit_price", "pnl", "status"]


def journaliser(trades: list[Trade], chemin: Path = LEDGER_PATH) -> None:
    existe = chemin.exists()
    with chemin.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CHAMPS)
        if not existe:
            w.writeheader()
        for t in trades:
            w.writerow({c: getattr(t, c) for c in CHAMPS})


def charger_journal(chemin: Path = LEDGER_PATH) -> list[dict]:
    if not chemin.exists():
        return []
    with chemin.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def evaluer(lignes: list[dict]) -> dict[str, dict]:
    """Calcule, par bot, les statistiques qui decident de tout."""
    par_bot: dict[str, list[float]] = {}
    for ln in lignes:
        if ln.get("status") != "closed" or ln.get("pnl") in (None, "", "None"):
            continue
        par_bot.setdefault(ln["bot"], []).append(float(ln["pnl"]))

    resultats: dict[str, dict] = {}
    for bot, pnls in sorted(par_bot.items()):
        n = len(pnls)
        gains = [p for p in pnls if p > 0]
        pertes = [p for p in pnls if p <= 0]
        total = sum(pnls)
        esperance = total / n if n else 0.0

        if n >= 2:
            ecart = statistics.stdev(pnls)
            se = ecart / math.sqrt(n)
            if se > 1e-9:
                t_stat = esperance / se
            else:
                t_stat = 99.99 if esperance > 0 else (-99.99 if esperance < 0 else 0.0)
            t_stat = max(-99.99, min(99.99, t_stat))
        else:
            t_stat = 0.0

        cumul = sommet = dd = 0.0
        for p in pnls:
            cumul += p
            sommet = max(sommet, cumul)
            dd = max(dd, sommet - cumul)

        taux = len(gains) / n if n else 0.0
        if n < 30:
            verdict = "echantillon trop faible -- continuer"
        elif abs(t_stat) < 2:
            verdict = "indistinguable du hasard"
        elif t_stat >= 2:
            if taux < 0.45:
                verdict = "edge a CONFIRMER (profil asymetrique, t-stat peu fiable)"
            else:
                verdict = "edge POSITIF plausible (a confirmer)"
        else:
            verdict = "perdant de facon SIGNIFICATIVE"

        resultats[bot] = {
            "trades": n,
            "taux_reussite": len(gains) / n if n else 0.0,
            "gain_moyen": (sum(gains) / len(gains)) if gains else 0.0,
            "perte_moyenne": (sum(pertes) / len(pertes)) if pertes else 0.0,
            "esperance_par_trade": esperance,
            "pnl_total": total,
            "max_drawdown": dd,
            "t_stat": t_stat,
            "verdict": verdict,
        }
    return resultats
