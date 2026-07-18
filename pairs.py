#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pairs.py - STAT-ARB de paires (cointegration), en DISCIPLINE STRICTE anti-p-hacking. OOS + couts.
=================================================================================================
Long un coin / short son partenaire cointegre ; on trade la reversion du SPREAD (z-score).
Anti-p-hacking : paires PRE-SPECIFIEES (economiquement liees, pas de balayage N^2), hedge ratio
beta + stats du spread estimes sur le TRAIN SEUL, trades comptes UNIQUEMENT sur le TEST (vrai OOS,
zero look-ahead). Net de couts 4-jambes (0,18 %). VIABLE (barre relevee, ~12 paires testees) =
test t >= 3,0, esp>0, n>=20, ET >=60 % des paires a esperance positive. 100% fictif, stdlib.
"""
from __future__ import annotations

import json, math, statistics, time, urllib.error, urllib.request
from datetime import datetime, timezone
from pathlib import Path

HL = "https://api.hyperliquid.xyz/info"
UA = "paper-trading-bench/1.0 (read-only pairs)"
JOURS = 150
TRAIN_FRAC = 0.66
NOT = 100.0
COST = 0.0018          # 2 actifs x aller-retour
Z_ENTRY, Z_EXIT, Z_STOP = 2.0, 0.5, 4.0
VIABLE_T = 3.0         # barre relevee (tests multiples)
VIABLE_N = 20

PAIRES = [("BTC","ETH"),("ETH","SOL"),("SOL","AVAX"),("AVAX","NEAR"),("BNB","ETH"),
          ("ARB","OP"),("LTC","BCH"),("LINK","UNI"),("ATOM","DOT"),("APT","SUI"),
          ("INJ","TIA"),("DOGE","WIF")]


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


def closes(coin, s, e):
    rep = _post({"type": "candleSnapshot", "req": {"coin": coin, "interval": "1h", "startTime": s, "endTime": e}})
    out = {}
    if isinstance(rep, list):
        for c in rep:
            try:
                out[int(c["t"]) // 3600000] = float(c["c"])
            except (TypeError, ValueError, KeyError):
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


def ols(la, lb):
    n = len(lb)
    mb = sum(lb) / n; ma = sum(la) / n
    cov = sum((la[i] - ma) * (lb[i] - mb) for i in range(n))
    var = sum((lb[i] - mb) ** 2 for i in range(n))
    beta = cov / var if var > 0 else 1.0
    alpha = ma - beta * mb
    return beta, alpha


def simulate(merged, cutoff):
    """merged: [(h, logA, logB)] ; params estimes sur train ; trades comptes en test seulement."""
    tr = [x for x in merged if x[0] < cutoff]
    if len(tr) < 150:
        return []
    la = [x[1] for x in tr]; lb = [x[2] for x in tr]
    beta, alpha = ols(la, lb)
    spr_tr = [la[i] - beta * lb[i] - alpha for i in range(len(la))]
    mu = sum(spr_tr) / len(spr_tr)
    sd = statistics.stdev(spr_tr) if len(spr_tr) > 1 else 0.0
    if sd <= 0:
        return []
    out, pos, entry_s, et = [], 0, None, None
    for (h, a, b) in merged:
        s = a - beta * b - alpha
        z = (s - mu) / sd
        if pos == 0:
            if z >= Z_ENTRY:
                pos, entry_s, et = -1, s, h
            elif z <= -Z_ENTRY:
                pos, entry_s, et = 1, s, h
        else:
            hit = (pos == -1 and (z <= Z_EXIT or z >= Z_STOP)) or (pos == 1 and (z >= -Z_EXIT or z <= -Z_STOP))
            if hit:
                pnl = (pos * (s - entry_s) - COST) * NOT
                if et >= cutoff:
                    out.append((et, pnl))
                pos = 0
    return out


def main():
    now = int(time.time() * 1000); start = now - JOURS * 86400 * 1000
    coins = sorted({c for p in PAIRES for c in p})
    px = {}
    for c in coins:
        d = closes(c, start, now)
        if len(d) > 200:
            px[c] = d
        time.sleep(0.05)
    print(f"[pairs] coins dispo : {sorted(px)}", flush=True)

    # cutoff temporel commun
    allh = sorted({h for c in px for h in px[c]})
    cutoff = allh[int(len(allh) * TRAIN_FRAC)] if allh else 0

    res = []; pooled = []
    for A, B in PAIRES:
        if A not in px or B not in px:
            res.append((f"{A}-{B}", None)); continue
        hs = sorted(set(px[A]) & set(px[B]))
        merged = [(h, math.log(px[A][h]), math.log(px[B][h])) for h in hs if px[A][h] > 0 and px[B][h] > 0]
        tr = simulate(merged, cutoff)
        res.append((f"{A}-{B}", stats([p for (t, p) in tr])))
        pooled += tr

    te = [p for (t, p) in pooled]
    st = stats(te)
    npos = sum(1 for (nom, s) in res if s and s[0] >= 3 and s[1] > 0)
    ntest = sum(1 for (nom, s) in res if s and s[0] >= 3)
    frac_pos = (npos / ntest) if ntest else 0.0
    viable = (st[0] >= VIABLE_N and st[2] >= VIABLE_T and st[1] > 0 and frac_pos >= 0.60)

    maj = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    verdict = ("VIABLE : stat-arb de paires (t OOS %.2f, esp %+.3f$, %d/%d paires +)" % (st[2], st[1], npos, ntest)) if viable \
        else "AUCUN stat-arb de paires viable (net de couts, OOS strict, barre t>=3)."
    css = ("body{font-family:-apple-system,Segoe UI,sans-serif;background:#11141a;color:#e8eaed;padding:16px}"
           "table{border-collapse:collapse;width:100%;font-size:.84rem;margin-top:8px}"
           "th,td{border-bottom:1px solid #262c38;padding:5px 7px;text-align:right}th:first-child,td:first-child{text-align:left}"
           ".ok{color:#2ecc71;font-weight:700}.no{color:#e74c3c}"
           ".v{background:#2a1b1b;border:1px solid #5a2a2a;padding:12px;border-radius:8px;margin:10px 0}"
           ".v.good{background:#12261a;border-color:#2a5a3a}")
    rows = ""
    for nom, s in res:
        if s is None:
            rows += f"<tr><td>{nom}</td><td colspan=3>coin absent</td></tr>"
        else:
            rows += (f"<tr><td>{nom}</td><td>{s[0]}</td>"
                     f"<td class='{'ok' if s[1]>0 else 'no'}'>{s[1]:+.3f}$</td>"
                     f"<td class='{'ok' if s[2]>=VIABLE_T else 'no'}'>{s[2]:+.2f}</td></tr>")
    doc = (f"<!DOCTYPE html><html lang=fr><head><meta charset=utf-8>"
           f"<meta name=viewport content='width=device-width,initial-scale=1'>"
           f"<title>Stat-arb paires</title><style>{css}</style></head><body>"
           f"<h1>Stat-arb de paires (cointégration) — OOS strict, net de coûts</h1>"
           f"<div>Généré {maj} · {JOURS} j · Z {Z_ENTRY}/{Z_EXIT} · pré-spécifié · beta sur train, trades sur test</div>"
           f"<div class='v {'good' if viable else ''}'><b>POOLED test : n={st[0]}, esp {st[1]:+.3f}$, t {st[2]:+.2f} · {npos}/{ntest} paires positives</b></div>"
           f"<div class='v {'good' if viable else ''}'><b>VERDICT : {verdict}</b></div>"
           f"<table><tr><th>Paire</th><th>n test</th><th>esp/trade</th><th>t</th></tr>{rows}</table>"
           f"<p style='color:#9aa0a6;font-size:.8rem'>Paires pré-spécifiées (anti-data-mining). Params train, "
           f"trades test (zéro look-ahead). Barre t&ge;3 (tests multiples). Argent 100 % fictif.</p><script src=maj.js></script></body></html>")
    Path("docs").mkdir(parents=True, exist_ok=True)
    Path("docs/pairs.html").write_text(doc, encoding="utf-8")
    print("\n=== STAT-ARB PAIRES (OOS) ===", flush=True)
    for nom, s in res:
        print(f"{nom:12s} " + ("absent" if s is None else f"n={s[0]:3d} esp={s[1]:+.3f} t={s[2]:+.2f}"), flush=True)
    print(f"POOLED: n={st[0]} esp={st[1]:+.3f} t={st[2]:+.2f} | {npos}/{ntest} paires + | frac={frac_pos:.2f}", flush=True)
    print(f"VERDICT: {verdict}", flush=True)


if __name__ == "__main__":
    main()
