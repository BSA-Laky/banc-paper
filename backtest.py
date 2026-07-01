#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
backtest.py - BACKTEST historique pour ACCELERER la validation des edges (paper, runner GitHub)
================================================================================================
Rejoue, sur l'HISTORIQUE reel Hyperliquid (funding + candles 1h), 4 strategies du banc et
calcule esperance + t-stat + verdict avec le MEME evaluateur que le live :
  - 23_carry_funding      : carry funding-rate (historique de funding)
  - 27b_rev_move          : reversion sur move 24h extreme (candles)
  - 27c_mom_move          : momentum sur move 24h extreme (candles, miroir de 27b)
  - 27d_rev_move_stop     : reversion 24h + stop-loss (candles)
But : obtenir des t-stats sur des CENTAINES d'evenements TOUT DE SUITE, au lieu d'attendre des
semaines de cron throttle. Tourne sur le runner (qui atteint HL). Ecrit docs/backtest.html.

BIAIS A LIRE AVANT DE CONCLURE (honnetete) :
  - SURVIVANCE : seuls les perps ACTUELLEMENT listes sont backtestes ; les coins delistes
    (souvent effondres) manquent -> biais possible PRO-reversion. Plafond, pas promesse.
  - PAS DE SLIPPAGE/LIQUIDITE : moves extremes = alts fins ; fills reels pires.
  - LOOK-AHEAD evite : l'entree n'utilise que le passe (move sur [t-24,t]) ; le reglement
    utilise les prix POSTERIEURS a l'entree (legitime).
  - TESTS MULTIPLES : 4 strategies -> au moins une peut sembler bonne par hasard.
  - REGIME-DEPENDANT : la reversion est aidee par un marche risk-off.
100 % fictif, lecture seule. Python 3.10+, stdlib uniquement.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from banc_essai_paper_trading import evaluer

HL_INFO_URL = "https://api.hyperliquid.xyz/info"
UA = "paper-trading-bench/1.0 (read-only research backtest)"

# --- parametres du backtest (memes seuils que les bots live) ---
JOURS = 75
TOP_N = 80                 # top coins par volume 24h (borne le nb d'appels)
VOL_MIN = 2_000_000.0
MOVE_BIG = 0.20            # 27b/c/d : |move 24h| >= 20 %
HORIZON_H = 24
STOP_FRAC = 0.06          # 27d
SEUIL_FUNDING = 1e-4      # bot 23
NOTIONAL_CONVEX = 100.0
NOTIONAL_CARRY = 1000.0
FRAIS = 0.00035


def _post(body, timeout=20.0, essais=3):
    data = json.dumps(body).encode()
    for k in range(essais):
        try:
            req = urllib.request.Request(HL_INFO_URL, data=data,
                headers={"Content-Type": "application/json", "User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, OSError):
            time.sleep(0.6 * (k + 1))
    return None


def univers_top() -> list[str]:
    rep = _post({"type": "metaAndAssetCtxs"})
    out = []
    try:
        univ, ctxs = rep[0]["universe"], rep[1]
    except (TypeError, KeyError, IndexError):
        return out
    for i, coin in enumerate(univ):
        if i >= len(ctxs):
            break
        try:
            vol = float((ctxs[i] or {}).get("dayNtlVlm"))
        except (TypeError, ValueError):
            vol = 0.0
        nom = str(coin.get("name", "")).upper()
        if nom and vol >= VOL_MIN:
            out.append((nom, vol))
    out.sort(key=lambda x: -x[1])
    return [c for c, _ in out[:TOP_N]]


def candles_1h(coin, start_ms, end_ms) -> list[float]:
    rep = _post({"type": "candleSnapshot",
                 "req": {"coin": coin, "interval": "1h",
                         "startTime": start_ms, "endTime": end_ms}})
    if not isinstance(rep, list):
        return []
    out = []
    for c in rep:
        try:
            out.append(float(c["c"]))
        except (TypeError, ValueError, KeyError):
            pass
    return out


def funding_hist(coin, start_ms, end_ms) -> list[float]:
    """Funding horaire sur la fenetre (pagination 500/appel)."""
    out, cur, garde = [], start_ms, 0
    while garde < 30:
        garde += 1
        rep = _post({"type": "fundingHistory", "coin": coin,
                     "startTime": cur, "endTime": end_ms})
        if not isinstance(rep, list) or not rep:
            break
        for r in rep:
            try:
                out.append(float(r["fundingRate"]))
            except (TypeError, ValueError, KeyError):
                pass
        last = rep[-1].get("time")
        if last is None or len(rep) < 500:
            break
        cur = int(last) + 1
    return out


# ---------------------------------------------------------------- replays
def replay_convex(closes: dict[str, list[float]]) -> dict[str, list[float]]:
    """Rejoue 27b/27c/27d. Entree si |move 24h| >= MOVE_BIG (passe seul), reglement a HORIZON_H
    (ou stop pour 27d). Une position a la fois par coin/bucket (comme le live)."""
    buckets = {"27b_rev_move": [], "27c_mom_move": [], "27d_rev_move_stop": []}
    for coin, cl in closes.items():
        n = len(cl)
        if n < HORIZON_H + 25:
            continue
        libre_a = {b: -1 for b in buckets}    # index a partir duquel le bucket est libre
        for t in range(24, n - 1):
            base = cl[t - 24]
            if base <= 0:
                continue
            move = (cl[t] - base) / base
            if abs(move) < MOVE_BIG:
                continue
            entry = cl[t]
            if entry <= 0:
                continue
            exit_t = min(t + HORIZON_H, n - 1)
            for b in buckets:
                if t <= libre_a[b]:
                    continue
                side = (1 if move > 0 else -1) if b == "27c_mom_move" else (-1 if move > 0 else 1)
                et = exit_t
                if b == "27d_rev_move_stop":
                    for h in range(t + 1, exit_t + 1):
                        if side * (cl[h] - entry) / entry <= -STOP_FRAC:
                            et = h
                            break
                ret = side * (cl[et] - entry) / entry
                pnl = NOTIONAL_CONVEX * ret - 2 * FRAIS * NOTIONAL_CONVEX
                buckets[b].append(pnl)
                libre_a[b] = et
    return buckets


def replay_carry(fundings: dict[str, list[float]]) -> list[float]:
    """Rejoue le bot 23 (hysteresis + settle 24 h) sur le funding horaire historique."""
    pnls = []
    for coin, f in fundings.items():
        if len(f) < 48:
            continue
        accrue, ouvert, debut = 0.0, False, 0
        for i in range(len(f)):
            if ouvert:
                accrue += abs(f[i]) * NOTIONAL_CARRY * 1.0
            if not ouvert and abs(f[i]) >= SEUIL_FUNDING:
                accrue -= 2 * FRAIS * NOTIONAL_CARRY
                ouvert = True
            elif ouvert and abs(f[i]) < SEUIL_FUNDING / 2.0:
                accrue -= 2 * FRAIS * NOTIONAL_CARRY
                ouvert = False
            if (i - debut) >= HORIZON_H:
                if ouvert or abs(accrue) > 1e-9:
                    pnls.append(accrue)
                    accrue = 0.0
                debut = i
    return pnls


# ---------------------------------------------------------------- rapport
def _rows(pnls_par_bot: dict[str, list[float]]) -> list[dict]:
    rows = []
    for bot, pnls in pnls_par_bot.items():
        for p in pnls:
            rows.append({"bot": bot, "status": "closed", "pnl": p})
    return rows


CSS = ("body{font-family:-apple-system,Segoe UI,Roboto,sans-serif;background:#11141a;"
       "color:#e8eaed;padding:16px;margin:0}h1{font-size:1.2rem}.maj{color:#9aa0a6;font-size:.8rem}"
       "table{width:100%;border-collapse:collapse;font-size:.85rem;margin-top:10px}"
       "th,td{padding:6px 8px;border-bottom:1px solid #262c38;text-align:right}"
       "th:first-child,td:first-child{text-align:left}.pos{color:#2ecc71}.neg{color:#e74c3c}"
       "caveats{color:#9aa0a6}li{margin:3px 0}footer{color:#6b7280;font-size:.75rem;margin-top:14px}")

JOLI = {"23_carry_funding": "23 — Carry funding (baseline)",
        "27b_rev_move": "27b — Réversion move 24h",
        "27c_mom_move": "27c — Momentum move 24h",
        "27d_rev_move_stop": "27d — Réversion move 24h + stop"}


def ecrire_html(res, meta):
    lignes = []
    for bot in ("23_carry_funding", "27b_rev_move", "27c_mom_move", "27d_rev_move_stop"):
        r = res.get(bot)
        if not r:
            lignes.append(f"<tr><td>{JOLI.get(bot,bot)}</td><td colspan=6>aucun trade</td></tr>")
            continue
        esp = r["esperance_par_trade"]
        cl = "pos" if esp > 0 else "neg"
        lignes.append(
            f"<tr><td>{JOLI.get(bot,bot)}</td><td>{r['trades']}</td>"
            f"<td>{r['taux_reussite']*100:.0f}%</td>"
            f"<td class='{cl}'>{esp:+.4f}</td><td>{r['pnl_total']:+.1f}</td>"
            f"<td>{r['t_stat']:+.2f}</td><td>{r['max_drawdown']:.1f}</td></tr>")
    maj = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    doc = (
        f"<!DOCTYPE html><html lang=fr><head><meta charset=utf-8>"
        f"<meta name=viewport content='width=device-width,initial-scale=1'>"
        f"<title>Backtest historique</title><style>{CSS}</style></head><body>"
        f"<h1>Backtest historique — Hyperliquid</h1>"
        f"<div class=maj>Généré {maj} · fenêtre {meta['jours']} j · {meta['coins']} coins · "
        f"{meta['candles']} candles, {meta['fund']} points funding</div>"
        f"<table><tr><th>Stratégie</th><th>Trades</th><th>Win%</th><th>Espérance/trade $</th>"
        f"<th>PnL $</th><th>t-stat</th><th>MaxDD $</th></tr>{''.join(lignes)}</table>"
        f"<h3>À lire avant de conclure</h3><ul class=caveats>"
        f"<li><b>Survivance</b> : seuls les perps encore listés sont testés (delistés absents) "
        f"→ biais possible pro-réversion.</li>"
        f"<li><b>Pas de slippage</b> : moves extrêmes = alts fins ; fills réels pires. Plafond.</li>"
        f"<li><b>Look-ahead évité</b> : entrée sur passe seul ; règlement sur prix postérieurs.</li>"
        f"<li><b>Tests multiples</b> : 4 stratégies → viser t &ge; ~3 pour être prudent.</li>"
        f"<li><b>Régime</b> : la réversion est aidée par un marché risk-off (juin baissier).</li>"
        f"<li>Le t-stat est peu fiable sur profil asymétrique : lire espérance ET nb de trades.</li>"
        f"</ul><footer>Argent 100 % fictif. Rien de réel sans confirmation live + hors-échantillon.</footer>"
        f"</body></html>")
    Path("docs").mkdir(parents=True, exist_ok=True)
    Path("docs/backtest.html").write_text(doc, encoding="utf-8")


def main():
    now = int(time.time() * 1000)
    start = now - JOURS * 86400 * 1000
    coins = univers_top()
    print(f"[bt] univers : {len(coins)} coins", flush=True)
    closes, fundings = {}, {}
    nc = nf = 0
    for i, c in enumerate(coins):
        cl = candles_1h(c, start, now)
        if cl:
            closes[c] = cl; nc += len(cl)
        fh = funding_hist(c, start, now)
        if fh:
            fundings[c] = fh; nf += len(fh)
        if i % 10 == 0:
            print(f"[bt] {i+1}/{len(coins)} ({c}) candles={len(cl)} fund={len(fh)}", flush=True)
        time.sleep(0.05)
    conv = replay_convex(closes)
    carry = {"23_carry_funding": replay_carry(fundings)}
    res = evaluer(_rows({**conv, **carry}))
    meta = {"jours": JOURS, "coins": len(closes), "candles": nc, "fund": nf}
    ecrire_html(res, meta)
    print("\n=== RESULTATS BACKTEST ===", flush=True)
    for bot in ("23_carry_funding", "27b_rev_move", "27c_mom_move", "27d_rev_move_stop"):
        r = res.get(bot)
        if r:
            print(f"{bot:22s} n={r['trades']:5d} esp={r['esperance_par_trade']:+.4f} "
                  f"t={r['t_stat']:+.2f} win={r['taux_reussite']*100:.0f}% "
                  f"pnl={r['pnl_total']:+.1f} -> {r['verdict']}", flush=True)
        else:
            print(f"{bot:22s} aucun trade", flush=True)
    print("[bt] docs/backtest.html écrit.", flush=True)


if __name__ == "__main__":
    main()
