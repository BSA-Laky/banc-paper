#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify.py - VERIFICATION "argent reel" du bot 28 (carry-hold). Runner GitHub.
=============================================================================
Le sweep a valide l'edge sur la COMPOSANTE FUNDING (net d'un frais jouet 0,07 %).
Ici on teste s'il survit NET DES FRICTIONS REELLES d'un carry delta-neutre exploite
pour de vrai :
  - 4 jambes de frais (short perp + long spot a l'entree, inverse a la sortie),
  - slippage (le funding eleve vit sur des alts FINS -> slippage plus fort),
  - cout de break-even : a quel cout total l'esperance passe a 0 ?
On calcule, sur TEST (out-of-sample), l'esperance NETTE et le t sous une GRILLE de couts
round-trip realistes, on trouve le break-even, on regarde la LIQUIDITE des coins qui
declenchent, la part funding positif/negatif (le negatif exige de shorter le spot = borrow),
la queue (pire trade, drawdown) et une estimation d'APY sur capital deploye.
Sortie : docs/verify.html + verdict clair. 100 % fictif, lecture seule, stdlib.
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
UA = "paper-trading-bench/1.0 (read-only verify)"

JOURS = 150
TOP_N = 120
VOL_MIN = 1_000_000.0
SEUIL = 1e-4
HOLD = 48
NOTIONAL = 1000.0
TRAIN_FRAC = 0.66
# grille de couts ROUND-TRIP (fraction du notionnel) : 0,07 % (jouet) -> 0,60 %
COUTS = [0.0007, 0.0010, 0.0015, 0.0018, 0.0022, 0.0030, 0.0040, 0.0050, 0.0060]
COUT_REALISTE_BAS = 0.0018   # 4 jambes taker HL ~4,5 bps, sans slippage (majors)
COUT_REALISTE_HAUT = 0.0035  # + slippage alts fins


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


def stats(x):
    n = len(x)
    if n < 2:
        return (n, 0.0, 0.0)
    m = sum(x) / n
    sd = statistics.stdev(x)
    t = m / (sd / math.sqrt(n)) if sd > 0 else (99.0 if m > 0 else -99.0)
    return (n, m, max(-99.0, min(99.0, t)))


def maxdd(pnls):
    cum = sommet = dd = 0.0
    for p in pnls:
        cum += p
        sommet = max(sommet, cum)
        dd = max(dd, sommet - cum)
    return dd


def replay(fund):
    """Rejoue carry-hold. Renvoie liste de trades : (t_entree, gross_frac, signe)."""
    out, i, n = [], 0, len(fund)
    while i < n:
        t0, rate = fund[i]
        if abs(rate) >= SEUIL:
            end = min(i + HOLD, n)
            gross = sum(abs(fund[j][1]) for j in range(i, end))  # fraction du notionnel
            out.append((t0, gross, 1 if rate > 0 else -1))
            i = end
        else:
            i += 1
    return out


def pct(vals, q):
    if not vals:
        return 0.0
    s = sorted(vals)
    return s[min(len(s) - 1, int(q * len(s)))]


def main():
    now = int(time.time() * 1000)
    start = now - JOURS * 86400 * 1000
    cutoff = start + int((now - start) * TRAIN_FRAC)
    vols = univers()
    coins = list(vols)
    print(f"[verify] {len(coins)} coins", flush=True)

    trades = []   # (t, gross, signe, coin, vol)
    for k, c in enumerate(coins):
        ff = funding(c, start, now)
        for (t0, gross, sg) in replay(ff):
            trades.append((t0, gross, sg, c, vols[c]))
        if k % 20 == 0:
            print(f"[verify] {k+1}/{len(coins)}", flush=True)
        time.sleep(0.04)

    test = [x for x in trades if x[0] >= cutoff]
    tr = [x for x in trades if x[0] < cutoff]
    gross_te = [x[1] for x in test]
    print(f"[verify] trades total={len(trades)} train={len(tr)} test={len(test)}", flush=True)

    # esperance/t NET sur TEST pour chaque cout
    grille = []
    for c in COUTS:
        net = [(g - c) * NOTIONAL for g in gross_te]
        n, m, t = stats(net)
        grille.append((c, n, m, t))
    breakeven = statistics.mean(gross_te) if gross_te else 0.0   # cout ou esp net = 0

    # net a couts realistes
    def net_at(c):
        return stats([(g - c) * NOTIONAL for g in gross_te])
    nb = net_at(COUT_REALISTE_BAS)
    nh = net_at(COUT_REALISTE_HAUT)

    # liquidite des coins declencheurs (test)
    tvols = [x[4] for x in test]
    liq = {"p25": pct(tvols, .25), "median": pct(tvols, .50), "p75": pct(tvols, .75)}
    part_thin = (sum(1 for v in tvols if v < 5_000_000) / len(tvols)) if tvols else 0.0

    # part funding positif vs negatif (negatif = shorter le spot = borrow)
    part_neg = (sum(1 for x in test if x[2] < 0) / len(test)) if test else 0.0

    # queue au cout realiste bas
    net_pnls_bas = [(g - COUT_REALISTE_BAS) * NOTIONAL for g in gross_te]
    pire = min(net_pnls_bas) if net_pnls_bas else 0.0
    dd = maxdd(net_pnls_bas)
    # APY sur capital deploye (une position dure HOLD h) au cout realiste bas
    apy_bas = (nb[1] / NOTIONAL) * (8760.0 / HOLD) if nb[0] else 0.0
    gross_pct = statistics.mean(gross_te) * 100 if gross_te else 0.0

    verdict_ok = (nb[3] >= 2 and nb[2] > 0 and part_thin < 0.5)
    if verdict_ok:
        verdict = ("SURVIT a l'execution IDEALE (majors, sans slippage) mais reste FRAGILE : "
                   "a confirmer en forward + slippage reel.")
    else:
        verdict = ("PAS PRET pour l'argent reel : l'edge funding (~{:.3f} %/trade) est du meme "
                   "ordre ou INFERIEUR aux frictions reelles (~{:.2f}-{:.2f} %) ; net d'execution, "
                   "l'esperance n'est plus significative.").format(gross_pct, COUT_REALISTE_BAS*100, COUT_REALISTE_HAUT*100)

    # --- rapport HTML ---
    css = ("body{font-family:-apple-system,Segoe UI,sans-serif;background:#11141a;color:#e8eaed;padding:16px}"
           "table{border-collapse:collapse;width:100%;font-size:.85rem;margin:8px 0}"
           "th,td{border-bottom:1px solid #262c38;padding:5px 8px;text-align:right}th:first-child,td:first-child{text-align:left}"
           ".ok{color:#2ecc71}.no{color:#e74c3c}.v{background:#2a1b1b;border:1px solid #5a2a2a;padding:12px;border-radius:8px;font-size:1.02rem;margin:10px 0}"
           ".v.good{background:#12261a;border-color:#2a5a3a}")
    gr = "".join(f"<tr><td>{c*100:.2f} %</td><td>{n}</td><td class='{'ok' if m>0 else 'no'}'>{m:+.3f} $</td>"
                 f"<td class='{'ok' if t>=2 else 'no'}'>{t:+.2f}</td></tr>" for (c, n, m, t) in grille)
    maj = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    doc = (f"<!DOCTYPE html><html lang=fr><head><meta charset=utf-8>"
           f"<meta name=viewport content='width=device-width,initial-scale=1'>"
           f"<title>Vérification argent réel</title><style>{css}</style></head><body>"
           f"<h1>Bot 28 — vérification « argent réel »</h1>"
           f"<div>Généré {maj} · {JOURS} j · {len(coins)} coins · {len(test)} trades OOS (test)</div>"
           f"<div class='v {'good' if verdict_ok else ''}'><b>VERDICT : {verdict}</b></div>"
           f"<h3>Espérance NETTE (test OOS) selon le coût round-trip réel</h3>"
           f"<table><tr><th>Coût round-trip</th><th>n</th><th>Espérance/trade</th><th>t-stat</th></tr>{gr}</table>"
           f"<p>Funding brut moyen capté : <b>{gross_pct:.3f} % / trade</b> (sur 48 h). "
           f"Coût de <b>break-even = {breakeven*100:.3f} %</b> round-trip : au-dessus, l'edge disparaît.</p>"
           f"<h3>Réalités d'exécution</h3><ul>"
           f"<li>Coût réaliste 4 jambes taker HL (majors, <b>sans</b> slippage) ≈ <b>{COUT_REALISTE_BAS*100:.2f} %</b> "
           f"→ net {nb[2]:+.3f} $/trade, t {nb[3]:+.2f}.</li>"
           f"<li>+ slippage alts fins ≈ <b>{COUT_REALISTE_HAUT*100:.2f} %</b> → net {nh[2]:+.3f} $/trade, t {nh[3]:+.2f}.</li>"
           f"<li>Liquidité des coins qui déclenchent (volume 24 h) : médiane {liq['median']/1e6:.1f} M$ ; "
           f"<b>{part_thin*100:.0f} %</b> des trades sur des coins &lt; 5 M$ (slippage élevé probable).</li>"
           f"<li><b>{part_neg*100:.0f} %</b> des trades sont sur funding NÉGATIF → il faut SHORTER le spot "
           f"(borrow, souvent indispo/coûteux en self-custody) : cette part est difficilement capturable.</li>"
           f"<li>Queue (au coût {COUT_REALISTE_BAS*100:.2f} %) : pire trade {pire:+.1f} $, max drawdown {dd:.1f} $ "
           f"(sur notionnel {NOTIONAL:.0f} $).</li>"
           f"<li>APY sur capital déployé (coût {COUT_REALISTE_BAS*100:.2f} %) ≈ <b>{apy_bas*100:+.0f} %</b> "
           f"— mais uniquement quand une position est ouverte, hors tail-risk.</li>"
           f"</ul>"
           f"<h3>Ce que ça ne couvre toujours pas</h3><ul>"
           f"<li>Risque de queue non tarifé : depeg stablecoin, liquidation de la jambe perp, panne d'API "
           f"laissant une jambe non couverte.</li>"
           f"<li>Survivance : coins délistés absents (biais optimiste).</li>"
           f"<li>Échelle 30 € : à 30 $ de notionnel au lieu de 1000 $, l'edge/trade est divisé par ~33 et "
           f"les coûts fixes (taille min d'ordre, gas) dominent → non capturable à ce capital.</li></ul>"
           f"<p style='color:#9aa0a6;font-size:.8rem'>Argent 100 % fictif. Ceci est une analyse factuelle, "
           f"pas un conseil d'investissement.</p></body></html>")
    Path("docs").mkdir(parents=True, exist_ok=True)
    Path("docs/verify.html").write_text(doc, encoding="utf-8")

    print("\n=== VERIFICATION ARGENT REEL (bot 28) ===", flush=True)
    print(f"funding brut moyen: {gross_pct:.3f} %/trade | break-even cout: {breakeven*100:.3f} %", flush=True)
    for (c, n, m, t) in grille:
        print(f"  cout {c*100:.2f}% -> net esp {m:+.3f}$ t {t:+.2f} (n={n})", flush=True)
    print(f"part trades coins <5M$: {part_thin*100:.0f}% | part funding negatif: {part_neg*100:.0f}%", flush=True)
    print(f"VERDICT: {verdict}", flush=True)


if __name__ == "__main__":
    main()
