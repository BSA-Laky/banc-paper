#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sweep.py - RECHERCHE d'edge rigoureuse (train/test, anti-overfitting). Runner GitHub.
=====================================================================================
Balaye des familles de strategies sur l'HISTORIQUE Hyperliquid, sur une fenetre TRAIN,
puis CONFIRME les meilleurs candidats en OUT-OF-SAMPLE (TEST, jamais vu). Un edge n'est
declare VALIDE que s'il est significatif (t) sur TRAIN *et* TEST, meme signe, esp > 0.

Familles :
  - CARRY-HOLD : entre si |funding| >= seuil, tient `hold` h en accumulant, sort. (anti-churn)
  - DIRECTIONNEL : sur un move `lookback`h >= `thresh`, parie reversion (side=-1) ou
    momentum (side=+1), tenu `horizon` h.
Protocole anti-p-hacking : on choisit le MEILLEUR combo par famille sur le TRAIN, puis on
ne confirme QUE ces quelques candidats sur le TEST (peu de tests OOS -> barre t>=2, ideal 2.5).

BIAIS (comme backtest) : survivance (coins delistes absents), pas de slippage, regime unique.
100 % fictif, lecture seule. stdlib.
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
UA = "paper-trading-bench/1.0 (read-only research sweep)"

JOURS = 150
TOP_N = 100
VOL_MIN = 1_000_000.0
FEE = 0.00035
NOTIONAL = 100.0        # directionnel
NOTIONAL_C = 1000.0     # carry
MIN_TRAIN = 25
MIN_TEST = 15
TRAIN_FRAC = 0.66

CARRY_SEUILS = [1e-4, 2e-4, 3e-4, 5e-4, 8e-4]
CARRY_HOLDS = [8, 24, 48]
DIR_LOOKBACKS = [12, 24, 48]
DIR_THRESH = [0.15, 0.25, 0.40]
DIR_HORIZONS = [12, 24, 48]
DIR_SIDES = [(-1, "rev"), (1, "mom")]


def _post(body, timeout=20.0, essais=3):
    data = json.dumps(body).encode()
    for k in range(essais):
        try:
            req = urllib.request.Request(HL, data=data,
                headers={"Content-Type": "application/json", "User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, OSError):
            time.sleep(0.6 * (k + 1))
    return None


def univers():
    rep = _post({"type": "metaAndAssetCtxs"})
    out = []
    try:
        univ, ctxs = rep[0]["universe"], rep[1]
    except (TypeError, KeyError, IndexError):
        return []
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


def candles(coin, start, end):
    rep = _post({"type": "candleSnapshot",
                 "req": {"coin": coin, "interval": "1h", "startTime": start, "endTime": end}})
    if not isinstance(rep, list):
        return []
    out = []
    for c in rep:
        try:
            out.append((int(c["t"]), float(c["c"])))
        except (TypeError, ValueError, KeyError):
            pass
    return out


def funding(coin, start, end):
    out, cur, g = [], start, 0
    while g < 40:
        g += 1
        rep = _post({"type": "fundingHistory", "coin": coin, "startTime": cur, "endTime": end})
        if not isinstance(rep, list) or not rep:
            break
        for r in rep:
            try:
                out.append((int(r["time"]), float(r["fundingRate"])))
            except (TypeError, ValueError, KeyError):
                pass
        if len(rep) < 500:
            break
        cur = int(rep[-1]["time"]) + 1
    return out


def stats(pnls):
    n = len(pnls)
    if n < 2:
        return (n, 0.0, 0.0)
    m = sum(pnls) / n
    sd = statistics.stdev(pnls)
    t = m / (sd / math.sqrt(n)) if sd > 0 else (99.0 if m > 0 else -99.0)
    return (n, m, max(-99.0, min(99.0, t)))


def replay_carry(fund, seuil, hold):
    pnls, i, n = [], 0, len(fund)
    while i < n:
        if abs(fund[i][1]) >= seuil:
            end = min(i + hold, n)
            acc = sum(abs(fund[j][1]) * NOTIONAL_C for j in range(i, end)) - 2 * FEE * NOTIONAL_C
            pnls.append(acc)
            i = end
        else:
            i += 1
    return pnls


def replay_dir(closes, lookback, thresh, horizon, side):
    cl = [c for _, c in closes]
    n = len(cl)
    pnls, libre = [], -1
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
        pnls.append(NOTIONAL * ret - 2 * FEE * NOTIONAL)
        libre = ex
    return pnls


def agg_carry(fund_by, seuil, hold):
    out = []
    for f in fund_by.values():
        out += replay_carry(f, seuil, hold)
    return out


def agg_dir(cl_by, lb, th, hz, side):
    out = []
    for c in cl_by.values():
        out += replay_dir(c, lb, th, hz, side)
    return out


def split(series, cutoff):
    tr = [x for x in series if x[0] < cutoff]
    te = [x for x in series if x[0] >= cutoff]
    return tr, te


def main():
    now = int(time.time() * 1000)
    start = now - JOURS * 86400 * 1000
    cutoff = start + int((now - start) * TRAIN_FRAC)
    coins = univers()
    print(f"[sweep] {len(coins)} coins, fenetre {JOURS}j, cutoff train/test", flush=True)

    cl_tr, cl_te, fu_tr, fu_te = {}, {}, {}, {}
    for i, c in enumerate(coins):
        cc = candles(c, start, now)
        if cc:
            a, b = split(cc, cutoff)
            if len(a) > 60:
                cl_tr[c] = a
            if len(b) > 40:
                cl_te[c] = b
        ff = funding(c, start, now)
        if ff:
            a, b = split(ff, cutoff)
            if len(a) > 60:
                fu_tr[c] = a
            if len(b) > 40:
                fu_te[c] = b
        if i % 15 == 0:
            print(f"[sweep] {i+1}/{len(coins)} {c}", flush=True)
        time.sleep(0.04)

    n_combos = 0
    cands = []   # (famille, label, params, train_stats)

    # CARRY
    best_carry = None
    for s in CARRY_SEUILS:
        for h in CARRY_HOLDS:
            n_combos += 1
            st = stats(agg_carry(fu_tr, s, h))
            if st[0] >= MIN_TRAIN and (best_carry is None or st[2] > best_carry[3][2]):
                best_carry = ("carry", f"seuil={s:.0e} hold={h}h", (s, h), st)
    if best_carry:
        cands.append(best_carry)

    # DIRECTIONNEL : meilleur par side (rev / mom)
    for side, nom in DIR_SIDES:
        best = None
        for lb in DIR_LOOKBACKS:
            for th in DIR_THRESH:
                for hz in DIR_HORIZONS:
                    n_combos += 1
                    st = stats(agg_dir(cl_tr, lb, th, hz, side))
                    if st[0] >= MIN_TRAIN and (best is None or st[2] > best[3][2]):
                        best = (nom, f"lookback={lb}h thresh={int(th*100)}% horizon={hz}h",
                                (lb, th, hz, side), st)
        if best:
            cands.append(best)

    # Confirmation OUT-OF-SAMPLE des candidats retenus
    lignes = []
    valide = []
    for fam, label, params, tr in cands:
        if fam == "carry":
            te = stats(agg_carry(fu_te, params[0], params[1]))
        else:
            te = stats(agg_dir(cl_te, params[0], params[1], params[2], params[3]))
        ok = (tr[2] >= 2 and te[2] >= 2 and te[1] > 0 and tr[1] > 0 and te[0] >= MIN_TEST)
        if ok:
            valide.append((fam, label))
        lignes.append((fam, label, tr, te, ok))

    maj = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    verdict = ("EDGE VALIDE OOS : " + " ; ".join(f"{f} ({l})" for f, l in valide)) if valide \
        else "AUCUN edge valide hors-echantillon (train+test, t>=2, meme signe)."
    css = ("body{font-family:-apple-system,Segoe UI,sans-serif;background:#11141a;color:#e8eaed;"
           "padding:16px}table{border-collapse:collapse;width:100%;font-size:.85rem;margin-top:8px}"
           "th,td{border-bottom:1px solid #262c38;padding:6px 8px;text-align:right}"
           "th:first-child,td:first-child{text-align:left}.ok{color:#2ecc71;font-weight:700}"
           ".no{color:#e74c3c}.v{font-size:1.05rem;padding:10px;border-radius:8px;background:#1b2230;margin:10px 0}")
    tr_html = ""
    for fam, label, tr, te, ok in lignes:
        cls = "ok" if ok else "no"
        tr_html += (f"<tr><td>{fam} — {label}</td>"
                    f"<td>{tr[0]}</td><td>{tr[1]:+.3f}</td><td>{tr[2]:+.2f}</td>"
                    f"<td>{te[0]}</td><td>{te[1]:+.3f}</td><td>{te[2]:+.2f}</td>"
                    f"<td class='{cls}'>{'VALIDE' if ok else 'non'}</td></tr>")
    doc = (f"<!DOCTYPE html><html lang=fr><head><meta charset=utf-8>"
           f"<meta name=viewport content='width=device-width,initial-scale=1'>"
           f"<title>Sweep edge</title><style>{css}</style></head><body>"
           f"<h1>Recherche d'edge — train/test (out-of-sample)</h1>"
           f"<div>Généré {maj} · {JOURS} j · {len(cl_tr)} coins candles / {len(fu_tr)} funding · "
           f"{n_combos} combos testés · train {int(TRAIN_FRAC*100)}% / test {100-int(TRAIN_FRAC*100)}%</div>"
           f"<div class=v><b>Verdict : {verdict}</b></div>"
           f"<table><tr><th>Meilleur candidat / famille</th><th>n tr</th><th>esp tr</th><th>t tr</th>"
           f"<th>n te</th><th>esp te</th><th>t te</th><th>OOS</th></tr>{tr_html}</table>"
           f"<p style='color:#9aa0a6;font-size:.8rem'>Meilleur combo par famille choisi sur le TRAIN, "
           f"confirmé sur le TEST jamais vu. Biais restants : survivance, pas de slippage, régime unique. "
           f"Avec plusieurs candidats confirmés, viser t&ge;2.5. Argent 100% fictif.</p></body></html>")
    Path("docs").mkdir(parents=True, exist_ok=True)
    Path("docs/sweep.html").write_text(doc, encoding="utf-8")

    print("\n=== SWEEP (train -> test OOS) ===", flush=True)
    for fam, label, tr, te, ok in lignes:
        print(f"{fam:6s} {label:34s} | train n={tr[0]:4d} esp={tr[1]:+.3f} t={tr[2]:+.2f} "
              f"| test n={te[0]:4d} esp={te[1]:+.3f} t={te[2]:+.2f} | {'VALIDE' if ok else 'non'}",
              flush=True)
    print(f"\nVERDICT: {verdict}", flush=True)


if __name__ == "__main__":
    main()
