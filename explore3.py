#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
explore3.py - Vague 3 : MICROSTRUCTURE INTRA-BARRE (mèches / amplitudes OHLC). OOS + couts.
===========================================================================================
Source NOUVELLE (dimension jamais testee : je n'utilisais que les clotures). Une casacade de
liquidation laisse une SIGNATURE dans la bougie horaire : longue MECHE (le prix plonge/pique
intra-heure puis revient) + grosse AMPLITUDE (h-l). Hypothese : apres un tel pic de flux
FORCE, le prix sur-reagit puis mean-revert -> on FADE (long apres grosse meche basse, short
apres grosse meche haute), tenu quelques heures. Exploitable APRES le pic (pas de course a la
latence). Sur coins liquides (cout faible). Meme crible : TRAIN/TEST OOS, net de couts.
VIABLE = t OOS >= 2,5 ET esp > 0 ET n_test >= 20. 100 % fictif, lecture seule, stdlib.
"""
from __future__ import annotations

import json, math, statistics, time, urllib.error, urllib.request
from datetime import datetime, timezone
from pathlib import Path

HL = "https://api.hyperliquid.xyz/info"
UA = "paper-trading-bench/1.0 (read-only explore3)"
JOURS = 150
TOP_N = 90
VOL_MIN = 1_000_000.0
TRAIN_FRAC = 0.66
COST = 0.0010
VIABLE_T = 2.5
VIABLE_N = 20


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


def ohlc(coin, s, e):
    rep = _post({"type": "candleSnapshot", "req": {"coin": coin, "interval": "1h", "startTime": s, "endTime": e}})
    out = []
    if isinstance(rep, list):
        for c in rep:
            try:
                out.append((int(c["t"]), float(c["o"]), float(c["h"]), float(c["l"]), float(c["c"])))
            except (TypeError, ValueError, KeyError):
                pass
    out.sort(key=lambda x: x[0])
    return out


def stats(x):
    n = len(x)
    if n < 2:
        return (n, 0.0, 0.0)
    m = sum(x) / n
    sd = statistics.stdev(x)
    t = m / (sd / math.sqrt(n)) if sd > 0 else (99.0 if m > 0 else -99.0)
    return (n, m, max(-99.0, min(99.0, t)))


def wickfade(series, thr, H, notional=100.0):
    out, n, libre = [], len(series), -1
    for i in range(n - 1):
        t, o, h, l, c = series[i]
        if c <= 0 or i <= libre:
            continue
        lw = (min(o, c) - l) / c
        uw = (h - max(o, c)) / c
        side = 0
        if lw >= thr and lw >= uw:
            side = 1
        elif uw >= thr and uw > lw:
            side = -1
        if side == 0:
            continue
        ex = min(i + H, n - 1)
        out.append((t, (side * (series[ex][4] - c) / c - COST) * notional))
        libre = ex
    return out


def rangerev(series, thr, H, notional=100.0):
    out, n, libre = [], len(series), -1
    for i in range(n - 1):
        t, o, h, l, c = series[i]
        if c <= 0 or o <= 0 or i <= libre:
            continue
        if (h - l) / c < thr:
            continue
        side = 1 if (c - o) / o < 0 else -1
        ex = min(i + H, n - 1)
        out.append((t, (side * (series[ex][4] - c) / c - COST) * notional))
        libre = ex
    return out


def split(trades, cutoff):
    return ([p for (t, p) in trades if t < cutoff], [p for (t, p) in trades if t >= cutoff])


def main():
    now = int(time.time() * 1000); start = now - JOURS * 86400 * 1000
    cutoff = start + int((now - start) * TRAIN_FRAC)
    vols = univers(); coins = list(vols)
    print(f"[ex3] {len(coins)} coins", flush=True)
    S = {}
    for k, c in enumerate(coins):
        o = ohlc(c, start, now)
        if len(o) > 100:
            S[c] = o
        if k % 20 == 0:
            print(f"[ex3] {k+1}/{len(coins)}", flush=True)
        time.sleep(0.04)

    def liq(v):
        return [c for c in S if vols[c] >= v]

    HYP = [
        ("H1 wick-fade 8% H6 liq>=5M", lambda: [x for c in liq(5e6) for x in wickfade(S[c], 0.08, 6)]),
        ("H2 wick-fade 12% H6 liq>=5M", lambda: [x for c in liq(5e6) for x in wickfade(S[c], 0.12, 6)]),
        ("H3 wick-fade 8% H3 liq>=5M", lambda: [x for c in liq(5e6) for x in wickfade(S[c], 0.08, 3)]),
        ("H4 wick-fade 8% H12 liq>=5M", lambda: [x for c in liq(5e6) for x in wickfade(S[c], 0.08, 12)]),
        ("H5 wick-fade 8% H6 majors>=20M", lambda: [x for c in liq(2e7) for x in wickfade(S[c], 0.08, 6)]),
        ("H6 range-rev 8% H6 liq>=5M", lambda: [x for c in liq(5e6) for x in rangerev(S[c], 0.08, 6)]),
        ("H7 range-rev 12% H12 liq>=5M", lambda: [x for c in liq(5e6) for x in rangerev(S[c], 0.12, 12)]),
        ("H8 range-rev 5% H24 majors>=20M", lambda: [x for c in liq(2e7) for x in rangerev(S[c], 0.05, 24)]),
    ]

    res = []
    for nom, fn in HYP:
        tr, te = split(fn(), cutoff)
        st_tr, st_te = stats(tr), stats(te)
        v = (st_te[0] >= VIABLE_N and st_te[2] >= VIABLE_T and st_te[1] > 0)
        res.append((nom, st_tr, st_te, v))

    viables = [r for r in res if r[3]]
    maj = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    verdict = ("VIABLE(S) : " + " ; ".join(r[0] for r in viables)) if viables \
        else "AUCUNE hypothese viable (microstructure intra-barre)."
    css = ("body{font-family:-apple-system,Segoe UI,sans-serif;background:#11141a;color:#e8eaed;padding:16px}"
           "table{border-collapse:collapse;width:100%;font-size:.84rem;margin-top:8px}"
           "th,td{border-bottom:1px solid #262c38;padding:5px 7px;text-align:right}th:first-child,td:first-child{text-align:left}"
           ".ok{color:#2ecc71;font-weight:700}.no{color:#e74c3c}"
           ".v{background:#2a1b1b;border:1px solid #5a2a2a;padding:12px;border-radius:8px;margin:10px 0}"
           ".v.good{background:#12261a;border-color:#2a5a3a}")
    rows = "".join(
        f"<tr><td>{nom}</td><td>{tr[0]}</td><td>{tr[1]:+.3f}</td><td>{tr[2]:+.2f}</td>"
        f"<td>{te[0]}</td><td class='{'ok' if te[1]>0 else 'no'}'>{te[1]:+.3f}</td>"
        f"<td class='{'ok' if te[2]>=VIABLE_T else 'no'}'>{te[2]:+.2f}</td>"
        f"<td class='{'ok' if v else 'no'}'>{'VIABLE' if v else 'non'}</td></tr>"
        for (nom, tr, te, v) in res)
    doc = (f"<!DOCTYPE html><html lang=fr><head><meta charset=utf-8>"
           f"<meta name=viewport content='width=device-width,initial-scale=1'>"
           f"<title>Explorateur v3</title><style>{css}</style></head><body>"
           f"<h1>Explorateur v3 — microstructure intra-barre (mèches/amplitudes)</h1>"
           f"<div>Généré {maj} · {JOURS} j · {len(S)} coins · net de coûts {COST*100:.2f}% · viable = t OOS &ge; {VIABLE_T}</div>"
           f"<div class='v {'good' if viables else ''}'><b>{verdict}</b></div>"
           f"<table><tr><th>Hypothèse</th><th>n tr</th><th>esp tr</th><th>t tr</th>"
           f"<th>n te</th><th>esp te (net)</th><th>t te</th><th>OOS</th></tr>{rows}</table>"
           f"<p style='color:#9aa0a6;font-size:.8rem'>Net de coûts. Biais restants : survivance, slippage moyen, "
           f"régime unique. Argent 100 % fictif.</p><script src=maj.js></script></body></html>")
    Path("docs").mkdir(parents=True, exist_ok=True)
    Path("docs/explore3.html").write_text(doc, encoding="utf-8")
    print("\n=== EXPLORATEUR v3 (microstructure) ===", flush=True)
    for (nom, tr, te, v) in res:
        print(f"{nom:34s} | train n={tr[0]:5d} t={tr[2]:+.2f} | test n={te[0]:5d} esp={te[1]:+.3f} t={te[2]:+.2f} | {'VIABLE' if v else 'non'}", flush=True)
    print(f"\nVERDICT: {verdict}", flush=True)


if __name__ == "__main__":
    main()
