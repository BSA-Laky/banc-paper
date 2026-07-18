#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run_book.py - point d'entree du BOOK marches traditionnels (cron mensuel).
Recupere les donnees une fois, fait tourner trend (#30) + VRP (#31) + controle book,
journalise dans book_trades.csv (separe du banc crypto), regenere docs/book.html.
100 % fictif, lecture seule. stdlib only.
"""
from __future__ import annotations

import html
import time
from datetime import datetime, timezone
from pathlib import Path

from banc_essai_paper_trading import journaliser, charger_journal, evaluer
from bot_trend import TrendFollowing, ControleBook, UNIVERS
from bot_variance import VarianceRiskPremium
import donnees_marche as dm

LEDGER = Path("book_trades.csv")
DOCS = Path("docs")

ORDRE = ["30_trend_following", "31_variance_premium", "10b_controle_book"]
JOLI = {
    "30_trend_following": "Bot 30 - Trend-following (edge VALIDE OOS, t 2,8)",
    "31_variance_premium": "Bot 31 - Prime de variance risque defini (edge VALIDE OOS, t 3,7)",
    "10b_controle_book": "Temoin book (signal aleatoire - etalon du bruit)",
}


def fetch_marche() -> dict:
    monthly = {}
    for i, s in enumerate(UNIVERS):
        d = dm.monthly(s, 10)
        if d:
            monthly[s] = d
        if i < len(UNIVERS) - 1:
            time.sleep(8)   # 8 req/min max sur le tier gratuit Twelve Data
    spy = dm.daily("SPY", 30)
    vix = dm.vix_now()
    allm = sorted({k for d in monthly.values() for k in d})
    asof = allm[-1] if allm else datetime.now(timezone.utc).strftime("%Y-%m")
    return {"monthly": monthly, "spy_daily": spy, "vix": vix, "asof": asof}


def construire_book_html():
    lignes = charger_journal(LEDGER)
    res = evaluer(lignes)
    try:
        from zoneinfo import ZoneInfo
        maj = datetime.now(ZoneInfo("Europe/Paris")).strftime("%Y-%m-%d %H:%M (Paris)")
    except Exception:
        maj = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    css = ("body{font-family:-apple-system,Segoe UI,Roboto,sans-serif;margin:0;"
           "background:#11141a;color:#e8eaed;padding:14px}h1{font-size:1.2rem;margin:.2rem 0}"
           ".maj{color:#9aa0a6;font-size:.8rem;margin-bottom:12px}"
           ".carte{background:#171b22;border:1px solid #262c38;border-radius:12px;"
           "padding:14px;margin-bottom:12px}.carte h2{font-size:1rem;margin:0 0 10px}"
           ".kpis{display:grid;grid-template-columns:repeat(2,1fr);gap:8px 14px}"
           ".lab{display:block;color:#9aa0a6;font-size:.72rem}.val{display:block;font-size:1rem;font-weight:600}"
           ".pos{color:#2ecc71}.neg{color:#e74c3c}.muted{color:#9aa0a6}"
           ".verdict{font-size:.85rem;color:#cdd2d8;margin:.4rem 0 0}"
           "footer{color:#6b7280;font-size:.74rem;margin-top:18px;line-height:1.5}")
    cartes = []
    for bot in ORDRE:
        titre = html.escape(JOLI.get(bot, bot))
        r = res.get(bot)
        if not r:
            cartes.append(f'<div class="carte"><h2>{titre}</h2>'
                          f'<p class="muted">Aucun trade solde (attend la 1re rotation mensuelle).</p></div>')
            continue
        esp = r["esperance_par_trade"]
        cls = "pos" if esp > 0 else ("neg" if esp < 0 else "")
        k = (f'<div><span class="lab">Trades (mois)</span><span class="val">{r["trades"]}</span></div>'
             f'<div><span class="lab">Esperance / mois</span><span class="val {cls}">{esp:+.4f}</span></div>'
             f'<div><span class="lab">P&amp;L cumule</span><span class="val">{r["pnl_total"]:+.3f}</span></div>'
             f'<div><span class="lab">t-stat</span><span class="val">{r["t_stat"]:+.2f}</span></div>')
        cartes.append(f'<div class="carte"><h2>{titre}</h2><div class="kpis">{k}</div>'
                      f'<p class="verdict">{html.escape(r["verdict"])}</p></div>')
    doc = ('<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">'
           '<meta name="viewport" content="width=device-width, initial-scale=1">'
           '<title>Book marches traditionnels</title><style>' + css + '</style></head><body>'
           '<h1>Book paper-forward - trend + prime de variance</h1>'
           f'<div class="maj">Mis a jour : {maj} - rotation mensuelle - 100 % fictif</div>'
           + "".join(cartes) +
           '<footer>Deux edges valides out-of-sample sur 30 ans (backtest). Ce book les '
           'CONFIRME en forward, argent 100 % fictif, avant tout capital reel. Le verdict '
           'mensuel est lent par nature (1 point/mois) : la preuve principale reste le '
           'backtest ; le forward verifie les frictions live. Rien en reel sans verdict '
           'confirme battant le temoin.</footer></body></html>')
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "book.html").write_text(doc, encoding="utf-8")
    print("[book] docs/book.html regenere", flush=True)


def lancer():
    marche = fetch_marche()
    try:
        DOCS.mkdir(parents=True, exist_ok=True)
        import json as _json
        (DOCS / "book_health.json").write_text(_json.dumps({
            "asof": marche["asof"], "vix": marche["vix"],
            "n_monthly": len(marche["monthly"]),
            "spy_days": len(marche["spy_daily"] or {}),
            "ts": datetime.now(timezone.utc).isoformat()}), encoding="utf-8")
    except OSError:
        pass
    if not marche["monthly"]:
        print("[book] AUCUNE donnee (cle TD_KEY absente ou API KO) -> rien.", flush=True)
        construire_book_html()
        return
    bots = [TrendFollowing(), VarianceRiskPremium(), ControleBook()]
    nouveaux = []
    for b in bots:
        try:
            nouveaux.extend(b.step(marche))
        except Exception as e:
            print(f"[book] {b.name} a leve : {e}", flush=True)
    if nouveaux:
        journaliser(nouveaux, LEDGER)
    print(f"[book] {len(nouveaux)} trade(s) solde(s) (asof {marche['asof']}, "
          f"vix={marche['vix']}).", flush=True)
    construire_book_html()


if __name__ == "__main__":
    lancer()
