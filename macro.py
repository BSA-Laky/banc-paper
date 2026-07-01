#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
macro.py - Source EXTERNE : sentiment (Fear&Greed) + liquidite on-chain (masse stablecoins).
============================================================================================
Nouvelle piste, hors prix/funding : signaux MACRO tenus en regime (faible turnover -> frictions
negligeables, le contraire des edges rapides deja tues). Testes sur BTC ET ETH (coherence
cross-actif = garde-fou anti-overfit). Chaque REGIME tenu = un trade independant (compte honnete).
Split TRAIN/TEST (OOS), net de couts. VIABLE = test t>=2,5, esp>0, n>=15, ET BTC & ETH tous deux >0.
Sources gratuites : alternative.me (F&G), CoinGecko (prix), DeFiLlama (stablecoins). 100% fictif.
"""
from __future__ import annotations

import json, math, statistics, time, urllib.error, urllib.request
from datetime import datetime, timezone
from pathlib import Path

UA = "paper-trading-bench/1.0 (read-only macro research)"
TRAIN_FRAC = 0.66
COST = 0.0010      # BTC/ETH round-trip perp taker ~2 jambes
VIABLE_T = 2.5
VIABLE_N = 15


def _get(url, timeout=25.0, essais=3):
    for k in range(essais):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8", errors="replace"))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, OSError) as e:
            print(f"[get] echec {url[:60]} : {e}", flush=True)
            time.sleep(1.2 * (k + 1))
    return None


def day(ts_s):
    return datetime.fromtimestamp(int(ts_s), tz=timezone.utc).strftime("%Y-%m-%d")


def fetch_fng():
    j = _get("https://api.alternative.me/fng/?limit=0&format=json")
    out = {}
    if isinstance(j, dict):
        for d in j.get("data", []):
            try:
                out[day(d["timestamp"])] = int(d["value"])
            except (KeyError, ValueError, TypeError):
                pass
    return out


def fetch_price(coin):
    j = _get(f"https://api.coingecko.com/api/v3/coins/{coin}/market_chart?vs_currency=usd&days=1400&interval=daily")
    out = {}
    if isinstance(j, dict):
        for ms, p in j.get("prices", []):
            try:
                out[day(ms / 1000)] = float(p)
            except (ValueError, TypeError):
                pass
    return out


def fetch_stables():
    j = _get("https://stablecoins.llama.fi/stablecoincharts/all")
    out = {}
    if isinstance(j, list):
        for r in j:
            try:
                v = r.get("totalCirculatingUSD") or r.get("totalCirculating") or {}
                val = v.get("peggedUSD") if isinstance(v, dict) else v
                out[day(r["date"])] = float(val)
            except (KeyError, ValueError, TypeError):
                pass
    return out


def stats(x):
    n = len(x)
    if n < 2:
        return (n, 0.0, 0.0)
    m = sum(x) / n
    sd = statistics.stdev(x)
    t = m / (sd / math.sqrt(n)) if sd > 0 else (99.0 if m > 0 else -99.0)
    return (n, m, max(-99.0, min(99.0, t)))


def episodes(dates, price, pos):
    """Chaque regime (position non nulle) tenu = 1 trade. Renvoie [(date_entree, pnl_frac)]."""
    out, cur, entry, edate, eside = [], 0, None, None, 0
    for d in dates:
        if d not in price:
            continue
        p = pos.get(d, 0)
        if p != cur:
            if cur != 0 and entry:
                out.append((edate, eside * (price[d] / entry - 1) - COST))
            if p != 0:
                entry, edate, eside = price[d], d, p
            cur = p
    if cur != 0 and entry:
        last = [d for d in dates if d in price][-1]
        out.append((edate, eside * (price[last] / entry - 1) - COST))
    return out


def pos_fng_contra(fng, lo, hi):
    return lambda dates: {d: (1 if fng[d] <= lo else (-1 if fng[d] >= hi else 0)) for d in dates if d in fng}


def pos_fng_long(fng, lo):
    return lambda dates: {d: (1 if fng[d] <= lo else 0) for d in dates if d in fng}


def pos_stable_mom(stab):
    dl = sorted(stab)
    idx = {d: i for i, d in enumerate(dl)}
    def f(dates):
        p = {}
        for d in dates:
            i = idx.get(d)
            if i is not None and i >= 30:
                p[d] = 1 if stab[d] > stab[dl[i - 30]] else 0
        return p
    return f


def main():
    fng = fetch_fng()
    stab = fetch_stables()
    px = {"BTC": fetch_price("bitcoin"), "ETH": fetch_price("ethereum")}
    print(f"[macro] F&G={len(fng)}j stables={len(stab)}j BTC={len(px['BTC'])}j ETH={len(px['ETH'])}j", flush=True)

    dates_all = sorted(set(fng) | set(px["BTC"]))
    if not dates_all:
        print("[macro] pas de donnees F&G/prix.", flush=True); 
    cut_i = int(len(dates_all) * TRAIN_FRAC)
    cutoff = dates_all[cut_i] if dates_all else "9999"

    SIG = [
        ("M1 F&G contrarian 25/75", pos_fng_contra(fng, 25, 75)),
        ("M2 F&G long fear<=25", pos_fng_long(fng, 25)),
        ("M3 F&G long fear<=35", pos_fng_long(fng, 35)),
        ("M4 F&G contrarian 30/70", pos_fng_contra(fng, 30, 70)),
        ("M5 stablecoins momentum 30j", pos_stable_mom(stab)),
    ]

    res = []
    for nom, mkpos in SIG:
        allep = []
        by = {}
        for coin in ("BTC", "ETH"):
            price = px[coin]
            dts = sorted(set(price) & (set(fng) | set(stab)))
            pos = mkpos(dts)
            ep = episodes(dts, price, pos)
            by[coin] = [p for (d, p) in ep if d >= cutoff]   # test par actif
            allep += ep
        tr = [p for (d, p) in allep if d < cutoff]
        te = [p for (d, p) in allep if d >= cutoff]
        st_tr, st_te = stats(tr), stats(te)
        btc_te = stats(by["BTC"]); eth_te = stats(by["ETH"])
        v = (st_te[0] >= VIABLE_N and st_te[2] >= VIABLE_T and st_te[1] > 0
             and btc_te[1] > 0 and eth_te[1] > 0)
        res.append((nom, st_tr, st_te, btc_te[1], eth_te[1], v))

    viables = [r for r in res if r[5]]
    maj = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    verdict = ("VIABLE(S) : " + " ; ".join(r[0] for r in viables)) if viables \
        else "AUCUN signal macro viable (net de couts, OOS, coherent BTC+ETH)."
    css = ("body{font-family:-apple-system,Segoe UI,sans-serif;background:#11141a;color:#e8eaed;padding:16px}"
           "table{border-collapse:collapse;width:100%;font-size:.84rem;margin-top:8px}"
           "th,td{border-bottom:1px solid #262c38;padding:5px 7px;text-align:right}th:first-child,td:first-child{text-align:left}"
           ".ok{color:#2ecc71;font-weight:700}.no{color:#e74c3c}"
           ".v{background:#2a1b1b;border:1px solid #5a2a2a;padding:12px;border-radius:8px;margin:10px 0}"
           ".v.good{background:#12261a;border-color:#2a5a3a}")
    rows = "".join(
        f"<tr><td>{nom}</td><td>{tr[0]}</td><td>{tr[2]:+.2f}</td>"
        f"<td>{te[0]}</td><td class='{'ok' if te[1]>0 else 'no'}'>{te[1]*100:+.2f}%</td>"
        f"<td class='{'ok' if te[2]>=VIABLE_T else 'no'}'>{te[2]:+.2f}</td>"
        f"<td class='{'ok' if b>0 else 'no'}'>{b*100:+.2f}%</td>"
        f"<td class='{'ok' if e>0 else 'no'}'>{e*100:+.2f}%</td>"
        f"<td class='{'ok' if v else 'no'}'>{'VIABLE' if v else 'non'}</td></tr>"
        for (nom, tr, te, b, e, v) in res)
    doc = (f"<!DOCTYPE html><html lang=fr><head><meta charset=utf-8>"
           f"<meta name=viewport content='width=device-width,initial-scale=1'>"
           f"<title>Macro externe</title><style>{css}</style></head><body>"
           f"<h1>Source externe — sentiment (F&G) + liquidité (stablecoins), régimes BTC/ETH</h1>"
           f"<div>Généré {maj} · net de coûts {COST*100:.2f}% · 1 régime tenu = 1 trade · viable = t OOS &ge; {VIABLE_T} & BTC+ETH &gt; 0</div>"
           f"<div class='v {'good' if viables else ''}'><b>{verdict}</b></div>"
           f"<table><tr><th>Signal macro</th><th>n tr</th><th>t tr</th><th>n te</th>"
           f"<th>esp/trade te</th><th>t te</th><th>BTC te</th><th>ETH te</th><th>OOS</th></tr>{rows}</table>"
           f"<p style='color:#9aa0a6;font-size:.8rem'>Régimes tenus (faible turnover). BTC+ETH partagent le "
           f"signal (épisodes corrélés) : la cohérence cross-actif est un garde-fou, pas 2 preuves. "
           f"Argent 100 % fictif, analyse factuelle.</p></body></html>")
    Path("docs").mkdir(parents=True, exist_ok=True)
    Path("docs/macro.html").write_text(doc, encoding="utf-8")
    print("\n=== MACRO EXTERNE ===", flush=True)
    for (nom, tr, te, b, e, v) in res:
        print(f"{nom:28s} | train n={tr[0]:3d} t={tr[2]:+.2f} | test n={te[0]:3d} esp={te[1]*100:+.2f}% t={te[2]:+.2f} | BTC {b*100:+.2f}% ETH {e*100:+.2f}% | {'VIABLE' if v else 'non'}", flush=True)
    print(f"\nVERDICT: {verdict}", flush=True)


if __name__ == "__main__":
    main()
