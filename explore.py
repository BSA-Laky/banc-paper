#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
explore.py - EXPLORATEUR d'hypotheses (batterie), pipeline rigoureux complet. Runner GitHub.
============================================================================================
Teste EN UN RUN une batterie d'hypotheses nouvelles/sous-exploitees, chacune passee au meme
crible que la verif serieuse :
  - split TRAIN / TEST (out-of-sample),
  - jugee NET des frictions REALISTES (cout baked : 0,10 % directionnel 2 jambes ;
    0,18 % carry delta-neutre 4 jambes),
  - focus LIQUIDITE (le tueur du bot 28 etait les alts fins),
  - carry funding POSITIF uniquement (pas de short-spot/borrow).
VIABLE = test t >= 2,5 (barre stricte, tests multiples) ET esp nette > 0 ET n_test >= 20.

Batterie :
  H1 carry-hold, funding POS, coins>=5M$, hold 48h            (le "fix" du bot 28)
  H2 carry-hold, funding POS, MAJORS>=50M$, hold 48h
  H3 carry-hold, funding POS, coins>=5M$, hold 24h
  H4 fonction-signal FADE  : |funding|>=3e-4 -> fade la foule (pos->short), 24h, >=5M$
  H5 fonction-signal FOLLOW: |funding|>=3e-4 -> suit la foule (pos->long),  24h, >=5M$
  H6 reversion move 24h>=25%, coins>=5M$, 24h
  H7 momentum  move 24h>=25%, coins>=5M$, 24h
  H8 reversion move 24h>=25%, MAJORS>=50M$, 24h
Argent 100 % fictif, lecture seule, stdlib.
"""
from __future__ import annotations

import json
import math
import statistics
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HL = "https://api.hyperliquid.xyz/info"
UA = "paper-trading-bench/1.0 (read-only explore)"
JOURS = 150
TOP_N = 90
VOL_MIN = 1_000_000.0
TRAIN_FRAC = 0.66
COST_DIR = 0.0010     # directionnel : 2 jambes taker + petit slippage
COST_CARRY = 0.0018   # carry delta-neutre : 4 jambes
VIABLE_T = 2.5
VIABLE_NMIN = 20


def _post(body, timeout=20.0, essais=3):
    data = json.dumps(body).encode()
    for k in range(essais):
        try:
            req = urllib.request.Request(HL, data=data,
                headers={"Content-Type": "application/json", "User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, OSError):
            time.sleep(0.5 * (k + 1))
    return None


def univers():
    rep = _post({"type": "metaAndAssetCtxs"})
    out = {}
    try:
        univ, ctxs = rep[0]["universe"], rep[1]
    except (TypeError, KeyError, IndexError):
        return {}
    tmp = []
    for i, coin in enumerate(univ):
        if i >= len(ctxs):
            break
        try:
            vol = float((ctxs[i] or {}).get("dayNtlVlm"))
        except (TypeError, ValueError):
            vol = 0.0
        nom = str(coin.get("name", "")).upper()
        if nom and vol >= VOL_MIN:
            tmp.append((nom, vol))
    tmp.sort(key=lambda x: -x[1])
    return dict(tmp[:TOP_N])


def candles(coin, start, end):
    rep = _post({"type": "candleSnapshot",
                 "req": {"coin": coin, "interval": "1h", "startTime": start, "endTime": end}})
    out = {}
    if isinstance(rep, list):
        for c in rep:
            try:
                out[int(c["t"]) // 3600000] = float(c["c"])
            except (TypeError, ValueError, KeyError):
                pass
    return out


def funding(coin, start, end):
    out, cur, g = {}, start, 0
    while g < 40:
        g += 1
        rep = _post({"type": "fundingHistory", "coin": coin, "startTime": cur, "endTime": end})
        if not isinstance(rep, list) or not rep:
            break
        for r in rep:
            try:
                out[int(r["time"]) // 3600000] = float(r["fundingRate"])
            except (TypeError, ValueError, KeyError):
                pass
        if len(rep) < 500:
            break
        cur = int(rep[-1]["time"]) + 1
    return out


def merge(cl, fu):
    hs = sorted(set(cl) & set(fu))
    return [(h * 3600000, cl[h], fu[h]) for h in hs]


def stats(x):
    n = len(x)
    if n < 2:
        return (n, 0.0, 0.0)
    m = sum(x) / n
    sd = statistics.stdev(x)
    t = m / (sd / math.sqrt(n)) if sd > 0 else (99.0 if m > 0 else -99.0)
    return (n, m, max(-99.0, min(99.0, t)))


# --------- replays (renvoient [(t, pnl_net)]) ----------
def carry(series, seuil, hold, sign, notional=1000.0):
    out, i, n = [], 0, len(series)
    while i < n:
        f = series[i][2]
        ok = abs(f) >= seuil and ((sign == "both") or (sign == "pos" and f > 0) or (sign == "neg" and f < 0))
        if ok:
            end = min(i + hold, n)
            gross = sum(abs(series[j][2]) for j in range(i, end))
            out.append((series[i][0], (gross - COST_CARRY) * notional))
            i = end
        else:
            i += 1
    return out


def fundsig(series, seuil, horizon, side_pos, notional=100.0):
    out, i, n, libre = [], 0, len(series), -1
    while i < n - 1:
        t, c, f = series[i]
        if abs(f) >= seuil and i > libre and c > 0:
            pos = side_pos if f > 0 else -side_pos
            ex = min(i + horizon, n - 1)
            ret = pos * (series[ex][1] - c) / c
            out.append((t, (ret - COST_DIR) * notional))
            libre = ex
        i += 1
    return out


def movedir(series, lookback, thresh, horizon, side, notional=100.0):
    cl = [c for _, c, _ in series]
    n = len(cl)
    out, libre = [], -1
    for i in range(lookback, n - 1):
        base = cl[i - lookback]
        if base <= 0 or i <= libre:
            continue
        move = (cl[i] - base) / base
        if abs(move) < thresh:
            continue
        pos = side * (1 if move > 0 else -1)
        ex = min(i + horizon, n - 1)
        ret = pos * (cl[ex] - cl[i]) / cl[i]
        out.append((series[i][0], (ret - COST_DIR) * notional))
        libre = ex
    return out


def main():
    now = int(time.time() * 1000)
    start = now - JOURS * 86400 * 1000
    cutoff = start + int((now - start) * TRAIN_FRAC)
    vols = univers()
    coins = list(vols)
    print(f"[explore] {len(coins)} coins", flush=True)

    S = {}   # coin -> merged series
    for k, c in enumerate(coins):
        cl = candles(c, start, now)
        fu = funding(c, start, now)
        m = merge(cl, fu)
        if len(m) > 100:
            S[c] = m
        if k % 20 == 0:
            print(f"[explore] {k+1}/{len(coins)}", flush=True)
        time.sleep(0.04)

    def liq(vmin):
        return [c for c in S if vols[c] >= vmin]

    HYP = [
        ("H1 carry POS liq>=5M hold48", lambda c: carry(S[c], 1e-4, 48, "pos"), liq(5e6)),
        ("H2 carry POS majors>=50M hold48", lambda c: carry(S[c], 1e-4, 48, "pos"), liq(5e7)),
        ("H3 carry POS liq>=5M hold24", lambda c: carry(S[c], 1e-4, 24, "pos"), liq(5e6)),
        ("H4 funding FADE liq>=5M 24h", lambda c: fundsig(S[c], 3e-4, 24, -1), liq(5e6)),
        ("H5 funding FOLLOW liq>=5M 24h", lambda c: fundsig(S[c], 3e-4, 24, 1), liq(5e6)),
        ("H6 reversion move liq>=5M 24h", lambda c: movedir(S[c], 24, 0.25, 24, -1), liq(5e6)),
        ("H7 momentum move liq>=5M 24h", lambda c: movedir(S[c], 24, 0.25, 24, 1), liq(5e6)),
        ("H8 reversion move majors>=50M 24h", lambda c: movedir(S[c], 24, 0.25, 24, -1), liq(5e7)),
    ]

    res = []
    for nom, fn, cs in HYP:
        trades = []
        for c in cs:
            trades += fn(c)
        tr = [p for (t, p) in trades if t < cutoff]
        te = [p for (t, p) in trades if t >= cutoff]
        st_tr, st_te = stats(tr), stats(te)
        viable = (st_te[0] >= VIABLE_NMIN and st_te[2] >= VIABLE_T and st_te[1] > 0)
        res.append((nom, len(cs), st_tr, st_te, viable))

    viables = [r for r in res if r[4]]
    maj = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    verdict = ("VIABLE(S) TROUVE(S) : " + " ; ".join(r[0] for r in viables)) if viables \
        else "AUCUNE hypothese viable (net de frictions, t>=2,5 OOS). Continuer d'explorer."
    css = ("body{font-family:-apple-system,Segoe UI,sans-serif;background:#11141a;color:#e8eaed;padding:16px}"
           "table{border-collapse:collapse;width:100%;font-size:.84rem;margin-top:8px}"
           "th,td{border-bottom:1px solid #262c38;padding:5px 7px;text-align:right}th:first-child,td:first-child{text-align:left}"
           ".ok{color:#2ecc71;font-weight:700}.no{color:#e74c3c}"
           ".v{background:#2a1b1b;border:1px solid #5a2a2a;padding:12px;border-radius:8px;margin:10px 0;font-size:1.02rem}"
           ".v.good{background:#12261a;border-color:#2a5a3a}")
    rows = "".join(
        f"<tr><td>{nom}</td><td>{nc}</td><td>{tr[0]}</td><td>{tr[1]:+.3f}</td><td>{tr[2]:+.2f}</td>"
        f"<td>{te[0]}</td><td class='{'ok' if te[1]>0 else 'no'}'>{te[1]:+.3f}</td>"
        f"<td class='{'ok' if te[2]>=VIABLE_T else 'no'}'>{te[2]:+.2f}</td>"
        f"<td class='{'ok' if v else 'no'}'>{'VIABLE' if v else 'non'}</td></tr>"
        for (nom, nc, tr, te, v) in res)
    doc = (f"<!DOCTYPE html><html lang=fr><head><meta charset=utf-8>"
           f"<meta name=viewport content='width=device-width,initial-scale=1'>"
           f"<title>Explorateur d'hypotheses</title><style>{css}</style></head><body>"
           f"<h1>Explorateur — batterie d'hypothèses (net de frictions, OOS)</h1>"
           f"<div>Généré {maj} · {JOURS} j · {len(S)} coins · coûts baked : dir {COST_DIR*100:.2f} %, "
           f"carry {COST_CARRY*100:.2f} % · viable = t OOS &ge; {VIABLE_T}</div>"
           f"<div class='v {'good' if viables else ''}'><b>{verdict}</b></div>"
           f"<table><tr><th>Hypothèse</th><th>coins</th><th>n tr</th><th>esp tr</th><th>t tr</th>"
           f"<th>n te</th><th>esp te (net)</th><th>t te</th><th>OOS</th></tr>{rows}</table>"
           f"<p style='color:#9aa0a6;font-size:.8rem'>Net de coûts réalistes. Biais restants : survivance, "
           f"slippage moyen (pas pire-cas), régime unique. Viable ici = candidat à re-vérifier finement + "
           f"forward. Argent 100 % fictif, analyse factuelle.</p><script src=maj.js></script></body></html>")
    Path("docs").mkdir(parents=True, exist_ok=True)
    Path("docs/explore.html").write_text(doc, encoding="utf-8")

    print("\n=== EXPLORATEUR (net de frictions, OOS) ===", flush=True)
    for (nom, nc, tr, te, v) in res:
        print(f"{nom:36s} | train n={tr[0]:4d} t={tr[2]:+.2f} | test n={te[0]:4d} "
              f"esp={te[1]:+.3f} t={te[2]:+.2f} | {'VIABLE' if v else 'non'}", flush=True)
    print(f"\nVERDICT: {verdict}", flush=True)


if __name__ == "__main__":
    main()
