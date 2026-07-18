#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
explore2.py - Vague 2 : hypotheses NOUVELLES (dont cross-sectional). Pipeline OOS + couts.
==========================================================================================
Flagship : CROSS-SECTIONAL funding (market-neutral) = chaque rebalance, LONG les coins au
funding le plus NEGATIF (les longs recoivent) / SHORT les plus POSITIFS (les shorts recoivent).
On capture la DISPERSION du funding, dollar-neutre. Plus : reversion court-horizon sur majors,
carry conditionne a la PERSISTANCE du funding, breakout de volatilite sur majors.
Meme crible : split TRAIN/TEST (OOS), NET de couts realistes. VIABLE = t OOS >= 2,5, esp>0, n>=20.
100 % fictif, lecture seule, stdlib.
"""
from __future__ import annotations

import json, math, statistics, time, urllib.error, urllib.request
from datetime import datetime, timezone
from pathlib import Path

HL = "https://api.hyperliquid.xyz/info"
UA = "paper-trading-bench/1.0 (read-only explore2)"
JOURS = 150
TOP_N = 90
VOL_MIN = 1_000_000.0
TRAIN_FRAC = 0.66
COST_DIR = 0.0010
COST_CARRY = 0.0018
COST_XS = 0.0015
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


def candles(coin, s, e):
    rep = _post({"type": "candleSnapshot", "req": {"coin": coin, "interval": "1h", "startTime": s, "endTime": e}})
    out = {}
    if isinstance(rep, list):
        for c in rep:
            try:
                out[int(c["t"]) // 3600000] = float(c["c"])
            except (TypeError, ValueError, KeyError):
                pass
    return out


def funding(coin, s, e):
    out, cur, g = {}, s, 0
    while g < 40:
        g += 1
        rep = _post({"type": "fundingHistory", "coin": coin, "startTime": cur, "endTime": e})
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


def stats(x):
    n = len(x)
    if n < 2:
        return (n, 0.0, 0.0)
    m = sum(x) / n
    sd = statistics.stdev(x)
    t = m / (sd / math.sqrt(n)) if sd > 0 else (99.0 if m > 0 else -99.0)
    return (n, m, max(-99.0, min(99.0, t)))


def movedir(series, lookback, thresh, horizon, side, notional=100.0):
    cl = [c for _, c, _ in series]; n = len(cl); out = []; libre = -1
    for i in range(lookback, n - 1):
        base = cl[i - lookback]
        if base <= 0 or i <= libre:
            continue
        mv = (cl[i] - base) / base
        if abs(mv) < thresh:
            continue
        pos = side * (1 if mv > 0 else -1)
        ex = min(i + horizon, n - 1)
        out.append((series[i][0], (pos * (cl[ex] - cl[i]) / cl[i] - COST_DIR) * notional))
        libre = ex
    return out


def persist_carry(series, seuil_avg, hold, notional=1000.0):
    n = len(series); out = []; i = 24; libre = -1
    while i < n - 1:
        if i > libre:
            avg = sum(series[j][2] for j in range(i - 24, i)) / 24
            if abs(avg) >= seuil_avg:
                end = min(i + hold, n)
                fp = sum(abs(series[j][2]) for j in range(i, end))
                out.append((series[i][0], (fp - COST_CARRY) * notional))
                libre = end
        i += 1
    return out


def xsect(panel, hours, H, kfrac, notional=100.0):
    out = []
    for idx in range(0, len(hours) - 1, H):
        h = hours[idx]; hex_ = h + H
        row = panel.get(h); exrow = panel.get(hex_)
        if not row or not exrow:
            continue
        coins = [c for c in row if c in exrow and row[c][0] > 0]
        if len(coins) < 8:
            continue
        coins.sort(key=lambda c: row[c][1])
        k = max(1, int(len(coins) * kfrac))
        longs, shorts = coins[:k], coins[-k:]
        def sf(c):
            return sum(panel[hh][c][1] for hh in range(h, hex_) if hh in panel and c in panel[hh])
        fund = sum(-sf(c) for c in longs) / k + sum(sf(c) for c in shorts) / k
        price = (sum((exrow[c][0] - row[c][0]) / row[c][0] for c in longs) / k
                 - sum((exrow[c][0] - row[c][0]) / row[c][0] for c in shorts) / k)
        out.append((h * 3600000, (fund + price - COST_XS) * notional))
    return out


def split(trades, cutoff):
    return ([p for (t, p) in trades if t < cutoff], [p for (t, p) in trades if t >= cutoff])


def main():
    now = int(time.time() * 1000); start = now - JOURS * 86400 * 1000
    cutoff = start + int((now - start) * TRAIN_FRAC)
    vols = univers(); coins = list(vols)
    print(f"[ex2] {len(coins)} coins", flush=True)
    S = {}; panel = {}
    for k, c in enumerate(coins):
        cl = candles(c, start, now); fu = funding(c, start, now)
        hs = sorted(set(cl) & set(fu))
        ser = [(h * 3600000, cl[h], fu[h]) for h in hs]
        if len(ser) > 100:
            S[c] = ser
            for h in hs:
                panel.setdefault(h, {})[c] = (cl[h], fu[h])
        if k % 20 == 0:
            print(f"[ex2] {k+1}/{len(coins)}", flush=True)
        time.sleep(0.04)
    hours = sorted(panel)

    def liq(v):
        return [c for c in S if vols[c] >= v]

    HYP = [
        ("H1 xsect funding H=8 K20%", lambda: xsect(panel, hours, 8, 0.20)),
        ("H2 xsect funding H=24 K20%", lambda: xsect(panel, hours, 24, 0.20)),
        ("H3 xsect funding H=8 K33%", lambda: xsect(panel, hours, 8, 0.33)),
        ("H4 reversion 6h majors>=20M", lambda: [t for c in liq(2e7) for t in movedir(S[c], 6, 0.08, 6, -1)]),
        ("H5 reversion 12h majors>=20M", lambda: [t for c in liq(2e7) for t in movedir(S[c], 12, 0.12, 12, -1)]),
        ("H6 persist-carry liq>=5M hold24", lambda: [t for c in liq(5e6) for t in persist_carry(S[c], 1e-4, 24)]),
        ("H7 breakout 6h momentum majors>=20M", lambda: [t for c in liq(2e7) for t in movedir(S[c], 6, 0.10, 6, 1)]),
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
        else "AUCUNE hypothese viable (vague 2). Espace largement arbitre."
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
           f"<title>Explorateur v2</title><style>{css}</style></head><body>"
           f"<h1>Explorateur v2 — cross-sectional & signaux neufs (OOS, net de coûts)</h1>"
           f"<div>Généré {maj} · {JOURS} j · {len(S)} coins · viable = t OOS &ge; {VIABLE_T}</div>"
           f"<div class='v {'good' if viables else ''}'><b>{verdict}</b></div>"
           f"<table><tr><th>Hypothèse</th><th>n tr</th><th>esp tr</th><th>t tr</th>"
           f"<th>n te</th><th>esp te (net)</th><th>t te</th><th>OOS</th></tr>{rows}</table>"
           f"<p style='color:#9aa0a6;font-size:.8rem'>Net de coûts réalistes. Biais restants : survivance, "
           f"slippage moyen, régime unique. Argent 100 % fictif.</p><script src=maj.js></script></body></html>")
    Path("docs").mkdir(parents=True, exist_ok=True)
    Path("docs/explore2.html").write_text(doc, encoding="utf-8")
    print("\n=== EXPLORATEUR v2 ===", flush=True)
    for (nom, tr, te, v) in res:
        print(f"{nom:34s} | train n={tr[0]:4d} t={tr[2]:+.2f} | test n={te[0]:4d} esp={te[1]:+.3f} t={te[2]:+.2f} | {'VIABLE' if v else 'non'}", flush=True)
    print(f"\nVERDICT: {verdict}", flush=True)


if __name__ == "__main__":
    main()
