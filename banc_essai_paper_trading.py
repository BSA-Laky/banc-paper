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


SPREAD_TEMOIN = 0.02          # spread paye par le temoin (source unique)


class ControleAleatoire(Strategy):
    """Bot temoin : decisions a pile ou face, paie un spread. L'etalon du bruit.

    DERIVE ATTENDUE -- ce bot DOIT perdre, et d'une quantite exactement calculable.
    Il achete a entry = 0,5 + s/2 un binaire qui paie 1 avec probabilite 1/2 :
        gain   = (1 - entry)/entry = (1 - s)/(1 + s)
        perte  = -1
        E      = -s / (1 + s)
        ecart-type = (gain + 1)/2 = 1 / (1 + s)
        E / ecart-type = -s          <-- EXACTEMENT, pas une approximation
    Le t-stat d'un temoin sain vaut donc -s*racine(n) : il derive vers le rouge a
    mesure que n grandit, sans que rien n'aille mal. C'est pour cela que la gate
    corrige de +s*racine(n) avant de juger. La constante vit ICI, aupres du spread
    qu'elle decrit : la coder en dur ailleurs la rendrait fausse au premier
    changement de spread (meme faute que la liste de bots reels ecrite en dur).
    """
    name = "10_controle_aleatoire"
    DERIVE_ATTENDUE = SPREAD_TEMOIN     # |E| / ecart-type, par construction

    def __init__(self, stake_usd: float = 1.0, spread: float = SPREAD_TEMOIN):
        super().__init__(stake_usd)
        self.spread = spread
        self.DERIVE_ATTENDUE = spread

    def step(self) -> list[Trade]:
        entry = 0.50 + self.spread / 2
        side = random.choice(["UP", "DOWN"])
        t = Trade(self.name, "fictif-50/50", side, entry, self.stake_usd)
        gagnant = random.random() < 0.50
        t.close(1.0 if gagnant else 0.0)
        return [t]


# Derive attendue de chaque temoin (|E| / ecart-type). Voir ControleAleatoire :
# pour un binaire achete a 0,5 + s/2, ce rapport vaut EXACTEMENT s. Le temoin du
# book (bot_trend.ControleBook) ne paie aucun spread construit -> derive nulle ;
# lui appliquer celle du temoin crypto masquerait un temoin reellement casse.
DERIVES_TEMOINS = {
    ControleAleatoire.name: ControleAleatoire.DERIVE_ATTENDUE,
    "10b_controle_book": 0.0,
}

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


def _coupure_comptable() -> tuple[set, str]:
    """Bots dont la COMPTABILITE a change, et date de bascule (26/07/2026).

    Avant cette date, ces bots calculaient un P&L qui ne mesurait PAS ce que le
    compte reel enregistre (funding en valeur absolue, aucun terme de prix). Leurs
    trades anterieurs mesurent une AUTRE GRANDEUR : les agreger avec les suivants
    produirait un verdict faux. On les ecarte donc du calcul des statistiques.
    Le journal brut, lui, est conserve intact (auditabilite).
    """
    try:
        import json as _j
        from pathlib import Path as _P
        d = _j.loads((_P("etat") / "correction_comptable.json").read_text(encoding="utf-8"))
        return set(d.get("bots") or []), str(d.get("date") or "")
    except (OSError, ValueError, TypeError):
        return set(), ""


def evaluer(lignes: list[dict]) -> dict[str, dict]:
    """Calcule, par bot, les statistiques qui decident de tout."""
    bots_coupes, date_coupure = _coupure_comptable()
    par_bot: dict[str, list[float]] = {}
    ecartes = 0
    for ln in lignes:
        if ln.get("status") != "closed" or ln.get("pnl") in (None, "", "None"):
            continue
        if (ln["bot"] in bots_coupes and date_coupure
                and str(ln.get("closed_at") or "") < date_coupure):
            ecartes += 1
            continue
        par_bot.setdefault(ln["bot"], []).append(float(ln["pnl"]))
    if ecartes:
        print("[evaluer] %d trade(s) ecarte(s) : comptabilite d'avant le %s "
              "(mesuraient une autre grandeur)" % (ecartes, date_coupure[:10]), flush=True)

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

        # Cas des TEMOINS (13/08/2026) : un temoin qui paie un spread DOIT perdre.
        # Son t-stat brut vaut -s*racine(n) et s'enfonce a mesure que n grandit,
        # sans qu'aucune anomalie n'existe -- trois audits successifs ont lu ce
        # "-2,39 perdant SIGNIFICATIVEMENT" comme une alarme. Le verdict utile est
        # celui qui retire d'abord la derive construite : il repond a la seule
        # question qui compte, "le taux de reussite vaut-il toujours 50 % ?".
        derive = DERIVES_TEMOINS.get(bot)
        if derive is not None and n >= 30:
            t_corrige = t_stat + derive * math.sqrt(n)
            if abs(t_corrige) < 2:
                verdict = (f"temoin SAIN -- perd comme prevu (spread {derive:.0%}) ; "
                           f"t corrige {t_corrige:+.2f}, taux {taux:.1%} vs 50 % attendu")
            else:
                verdict = (f"temoin SUSPECT -- ecart au hasard apres retrait du spread "
                           f"{derive:.0%} : t corrige {t_corrige:+.2f}. NE RIEN CONCLURE "
                           "du banc tant que ce n'est pas elucide.")

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
