#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
trend.py - TIME-SERIES MOMENTUM (trend-following) multi-actifs. Hors crypto. OOS + couts.
=========================================================================================
L'edge systematique le plus REPLIQUE (Moskowitz-Ooi-Pedersen ; les CTA/managed-futures).
Sur un panier DIVERSIFIE (actions US/intl/EM, obligs, or/argent/petrole/commodities, USD, REIT),
chaque mois : position = signe du rendement des N derniers mois ; on capte le mois suivant.
Faible turnover (mensuel) -> frictions negligeables (le contraire des perps crypto).
Anti-p-hacking : signaux CANONIQUES (lookback 3/6/12 mois), panier pre-specifie. Split TRAIN/TEST
(OOS). VIABLE = test t>=2,5, esp>0, n>=30. Le 12 mois long-short est LA version canonique.
Donnees gratuites : Stooq (CSV). 100 % fictif, lecture seule, stdlib.
"""
from __future__ import annotations

import math, statistics, time, urllib.error, urllib.request
from datetime import datetime, timezone
from pathlib import Path

UA = "Mozilla/5.0 (paper-trading-bench research)"
TRAIN_FRAC = 0.60
COST = 0.0005          # ETF liquide, aller-retour ~5 bps, applique aux changements de position
VIABLE_T = 2.5
VIABLE_N = 30
LOOKBACKS = [3, 6, 12]
ACTIFS = ["SPY", "QQQ", "IWM", "EFA", "EEM", "TLT", "IEF",
          "GLD", "SLV", "USO", "UUP", "VNQ", "HYG", "DBC"]


def _get_json(url, timeout=25.0, essais=3):
    import json as _json
    for k in range(essais):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return _json.loads(r.read().decode("utf-8", errors="replace"))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, OSError) as e:
            print(f"[get] {url[:55]} : {e}", flush=True)
            time.sleep(1.0 * (k + 1))
    return None


def fetch_monthly(tk):
    """{'YYYY-MM': close de fin de mois} depuis Yahoo Finance (chart JSON, sans cle)."""
    now = int(time.time())
    for host in ("query1", "query2"):
        j = _get_json(f"https://{host}.finance.yahoo.com/v8/finance/chart/{tk}"
                      f"?period1=946684800&period2={now}&interval=1d")
        try:
            res = j["chart"]["result"][0]
            ts = res["timestamp"]
            cl = res["indicators"]["quote"][0]["close"]
        except (TypeError, KeyError, IndexError):
            continue
        monthly = {}
        for t, c in zip(ts, cl):
            if c is None:
                continue
            d = datetime.fromtimestamp(int(t), tz=timezone.utc).strftime("%Y-%m")
            monthly[d] = float(c)
        if len(monthly) > 40:
            return monthly
    return {}


def stats(x):
    n = len(x)
    if n < 2:
        return (n, 0.0, 0.0)
    m = sum(x) / n
    sd = statistics.stdev(x)
    t = m / (sd / math.sqrt(n)) if sd > 0 else (99.0 if m > 0 else -99.0)
    return (n, m, max(-99.0, min(99.0, t)))


def tsmom(monthly, N, longshort):
    """Renvoie [(mois, strat_ret)] : position=signe(rendement N mois), capture le mois suivant."""
    ms = sorted(monthly)
    out, prev = [], 0
    for i in range(N, len(ms) - 1):
        past = monthly[ms[i]] / monthly[ms[i - N]] - 1 if monthly[ms[i - N]] > 0 else 0
        sig = (1 if past > 0 else (-1 if longshort else 0))
        nxt = monthly[ms[i + 1]] / monthly[ms[i]] - 1 if monthly[ms[i]] > 0 else 0
        r = sig * nxt - (COST if sig != prev else 0.0)
        out.append((ms[i + 1], r))
        prev = sig
    return out


def main():
    data = {}
    for s in ACTIFS:
        m = fetch_monthly(s)
        if len(m) > 40:
            data[s] = m
        time.sleep(0.2)
    print(f"[trend] actifs charges : {sorted(data)}", flush=True)
    allm = sorted({m for s in data for m in data[s]})
    cutoff = allm[int(len(allm) * TRAIN_FRAC)] if allm else "9999"

    res = []
    for N in LOOKBACKS:
        for ls, tag in [(True, "long-short"), (False, "long-flat")]:
            pooled = []
            for s in data:
                pooled += tsmom(data[s], N, ls)
            tr = [r for (mo, r) in pooled if mo < cutoff]
            te = [r for (mo, r) in pooled if mo >= cutoff]
            st_tr, st_te = stats(tr), stats(te)
            shar = (st_te[1] / statistics.stdev(te) * math.sqrt(12)) if len(te) > 1 and statistics.stdev(te) > 0 else 0.0
            v = (st_te[0] >= VIABLE_N and st_te[2] >= VIABLE_T and st_te[1] > 0)
            res.append((f"{N}m {tag}", st_tr, st_te, shar, v))

    viables = [r for r in res if r[4]]
    maj = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    verdict = ("VIABLE : " + " ; ".join(f"{r[0]} (t OOS {r[2][2]:+.2f}, Sharpe {r[3]:.2f})" for r in viables)) if viables \
        else "AUCUN signal trend viable (net de couts, OOS)."
    css = ("body{font-family:-apple-system,Segoe UI,sans-serif;background:#11141a;color:#e8eaed;padding:16px}"
           "table{border-collapse:collapse;width:100%;font-size:.85rem;margin-top:8px}"
           "th,td{border-bottom:1px solid #262c38;padding:5px 8px;text-align:right}th:first-child,td:first-child{text-align:left}"
           ".ok{color:#2ecc71;font-weight:700}.no{color:#e74c3c}"
           ".v{background:#2a1b1b;border:1px solid #5a2a2a;padding:12px;border-radius:8px;margin:10px 0}"
           ".v.good{background:#12261a;border-color:#2a5a3a}")
    rows = "".join(
        f"<tr><td>{nom}</td><td>{tr[0]}</td><td>{tr[2]:+.2f}</td>"
        f"<td>{te[0]}</td><td class='{'ok' if te[1]>0 else 'no'}'>{te[1]*100:+.3f}%</td>"
        f"<td class='{'ok' if te[2]>=VIABLE_T else 'no'}'>{te[2]:+.2f}</td>"
        f"<td>{sh:.2f}</td><td class='{'ok' if v else 'no'}'>{'VIABLE' if v else 'non'}</td></tr>"
        for (nom, tr, te, sh, v) in res)
    doc = (f"<!DOCTYPE html><html lang=fr><head><meta charset=utf-8>"
           f"<meta name=viewport content='width=device-width,initial-scale=1'>"
           f"<title>Trend-following</title><style>{css}</style></head><body>"
           f"<h1>Time-series momentum (trend) — panier multi-actifs, OOS, net de coûts</h1>"
           f"<div>Généré {maj} · {len(data)} actifs · mensuel · net {COST*100:.2f}%/rotation · viable = t OOS &ge; {VIABLE_T}</div>"
           f"<div class='v {'good' if viables else ''}'><b>VERDICT : {verdict}</b></div>"
           f"<table><tr><th>Stratégie</th><th>n tr</th><th>t tr</th><th>n te</th>"
           f"<th>ret/mois te</th><th>t te</th><th>Sharpe te</th><th>OOS</th></tr>{rows}</table>"
           f"<p style='color:#9aa0a6;font-size:.8rem'>Signaux canoniques (lookback 3/6/12 mois), panier "
           f"pré-spécifié (actions/obligs/matières premières/USD/REIT). Le 12 mois long-short est LA version "
           f"académique. Frictions faibles (mensuel). Argent 100 % fictif, analyse factuelle.</p></body></html>")
    Path("docs").mkdir(parents=True, exist_ok=True)
    Path("docs/trend.html").write_text(doc, encoding="utf-8")
    print("\n=== TREND-FOLLOWING (OOS) ===", flush=True)
    for (nom, tr, te, sh, v) in res:
        print(f"{nom:16s} | train n={tr[0]:4d} t={tr[2]:+.2f} | test n={te[0]:4d} ret={te[1]*100:+.3f}%/mois t={te[2]:+.2f} Sharpe={sh:.2f} | {'VIABLE' if v else 'non'}", flush=True)
    print(f"\nVERDICT: {verdict}", flush=True)


if __name__ == "__main__":
    main()
