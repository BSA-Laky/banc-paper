#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scanner_dislocations.py - DETECTEUR D'OCCASIONS EPHEMERES (02/08/2026)
======================================================================
CE QU'IL CHERCHE, ET POURQUOI PAS AUTRE CHOSE
---------------------------------------------
Mesure du 02/08 : sur 7 ans, 80 pieces et 112 877 observations, l'hypothese
« funding anormal » plafonne a t = 2,99 dans sa MEILLEURE fenetre de 60 jours
sur 2 261 fenetres -- soit moins que le maximum produit par du bruit pur (3,65).
Elle est morte.

Le meme jour, le spread de funding Hyperliquid <-> Paradex a ete mesure a
t = 7,10 pendant 45 jours avant de se refermer (compression de 83 %). Reel,
exploitable, ephemere.

La difference n'est pas la finesse du signal, c'est la STRUCTURE :
    Carry Provider ...... le terme de prix RESTE, on tente de le predire  -> t <= 3
    spread inter-venues . le terme de prix S'ANNULE (meme actif, deux venues,
                          sens opposes) : il ne reste que le funding      -> t = 7,1

On n'atteint pas un t eleve en predisant mieux. On l'atteint en SUPPRIMANT le
bruit dominant par construction. Ce scanner ne surveille donc QUE des relations
mecaniquement contraintes, ou un ecart est une anomalie arithmetique et non une
prevision.

LE SEUIL, ET POURQUOI IL EST SI HAUT
------------------------------------
Scanner en continu, c'est faire des milliers de tests correles. Calibration par
simulation sous H0 (bruit pur, fenetre glissante 60 j sur 7 ans), p95 du max :
        1 relation  -> t 3,65      50 relations -> t 5,17
       10 relations -> t 4,56     200 relations -> t 5,37
Surveiller UNE seule relation pendant 7 ans produit deja un pic a 3,65 par
hasard. Un seuil a 3 sonnerait en permanence sur du vent.

    SEUIL RETENU : t >= 5,4  (calibre pour ~200 relations)

A ce niveau, la detection consomme (2/5,4)^2 = 14 % de la fenetre : il en reste
86 % d'exploitable. C'est ce qui rend la strategie des fenetres ephemeres
viable -- a condition de ne se declencher QUE sur des edges tres forts.

Il sonnera rarement. C'est le but. Une alarme qui sonne souvent ne dit rien.

AMORCAGE
--------
Le funding est historise publiquement sur les trois venues. Au premier passage,
le scanner REMPLIT son historique retroactivement au lieu d'attendre 30 jours de
calibration. Il peut donc alerter des le premier jour.

stdlib uniquement. Lecture seule, aucune cle, aucun ordre.
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

ETAT = Path("etat")
DOCS = Path("docs")
F_HIST = ETAT / "scanner_hist.json"
F_SORTIE = DOCS / "scanner.json"
UA = "banc-paper-scanner (read-only research)"

SEUIL_T = 5.4            # calibre sous H0 pour ~200 relations (voir en-tete)
FENETRE = 60             # observations retenues pour le t glissant
HIST_MAX = 400           # points conserves par relation
JOURS_AMORCAGE = 90

# Frais aller-retour sur les DEUX jambes, par venue (taker, hypothese prudente).
FRAIS = {"hyperliquid": 0.00045, "binance": 0.00045, "bybit": 0.00055}
TENUE_H = 24.0           # duree de detention de reference pour le seuil de frais


# --------------------------------------------------------------- utilitaires
def _get(url, essais=3):
    for i in range(essais):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (418, 429):
                time.sleep(1.5 * (i + 1)); continue
            return None
        except (urllib.error.URLError, TimeoutError, ValueError, OSError):
            time.sleep(0.5 * (i + 1))
    return None


def _post(url, corps, essais=3):
    data = json.dumps(corps).encode("utf-8")
    for i in range(essais):
        try:
            req = urllib.request.Request(url, data=data, headers={
                "Content-Type": "application/json", "User-Agent": UA})
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
                ValueError, OSError):
            time.sleep(0.5 * (i + 1))
    return None


def _f(x, d=0.0):
    try:
        return float(x)
    except (TypeError, ValueError):
        return d


def _lire(p, d):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return d


def _ecrire(p, d):
    try:
        Path(p).parent.mkdir(parents=True, exist_ok=True)
        Path(p).write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


# ------------------------------------------------- etat courant des venues
def hl_funding():
    """{coin: funding_horaire} sur Hyperliquid."""
    r = _post("https://api.hyperliquid.xyz/info", {"type": "metaAndAssetCtxs"})
    if not isinstance(r, list) or len(r) < 2:
        return {}
    out = {}
    for u, c in zip((r[0] or {}).get("universe", []), r[1] or []):
        if isinstance(c, dict) and _f(c.get("markPx")) > 0:
            out[u["name"]] = {"funding": _f(c.get("funding")), "mark": _f(c.get("markPx"))}
    return out


def binance_funding():
    """{BASE: funding_horaire} — Binance publie un taux par 8 h, on ramene a l'heure."""
    r = _get("https://fapi.binance.com/fapi/v1/premiumIndex")
    if not isinstance(r, list):
        return {}
    out = {}
    for x in r:
        s = str(x.get("symbol") or "")
        if not s.endswith("USDT"):
            continue
        out[s[:-4]] = {"funding": _f(x.get("lastFundingRate")) / 8.0,
                       "mark": _f(x.get("markPrice"))}
    return out


def bybit_funding():
    r = _get("https://api.bybit.com/v5/market/tickers?category=linear")
    lst = ((r or {}).get("result") or {}).get("list") or []
    out = {}
    for x in lst:
        s = str(x.get("symbol") or "")
        if not s.endswith("USDT"):
            continue
        out[s[:-4]] = {"funding": _f(x.get("fundingRate")) / 8.0,
                       "mark": _f(x.get("markPrice"))}
    return out


# --------------------------------------------------------- le catalogue
def relations(hl, bn, by):
    """Les relations MECANIQUEMENT CONTRAINTES. Rien d'autre n'a sa place ici.

    Pour chacune : long sur la venue au funding le plus bas, short sur celle au
    funding le plus haut, MEME actif, notionnels egaux. Le terme de prix
    s'annule par construction : il ne reste que le differentiel de funding,
    moins les frais des deux venues.
    """
    out = {}
    paires = (("HL-BINANCE", hl, bn, "hyperliquid", "binance"),
              ("HL-BYBIT", hl, by, "hyperliquid", "bybit"),
              ("BINANCE-BYBIT", bn, by, "binance", "bybit"))
    for nom, A, B, va, vb in paires:
        for coin in set(A) & set(B):
            fa, fb = A[coin]["funding"], B[coin]["funding"]
            if A[coin]["mark"] <= 0 or B[coin]["mark"] <= 0:
                continue
            spread = fa - fb                       # capturable par heure
            # seuil de rentabilite : aller-retour sur les deux venues, amorti
            # sur la duree de detention de reference
            seuil = (2 * FRAIS[va] + 2 * FRAIS[vb]) / TENUE_H
            out["%s:%s" % (nom, coin)] = {
                "spread_h": spread, "abs_spread_h": abs(spread),
                "seuil_frais_h": seuil,
                "ratio_frais": abs(spread) / seuil if seuil > 0 else 0.0,
                "ecart_prix_bp": round(1e4 * (A[coin]["mark"] - B[coin]["mark"])
                                       / B[coin]["mark"], 2)}
    return out


# ------------------------------------------------------------- amorcage
def amorcer(hist, coins_hl, budget_s=180.0):
    """Remplit l'historique retroactivement : le funding est public et historise.

    Sans ca il faudrait 30 jours avant que le scanner puisse dire quoi que ce
    soit. Avec, il est operationnel des le premier passage.

    BUDGET DE TEMPS OBLIGATOIRE : un incident du 02/08 a montre qu'une venue
    momentanement lente, multipliee par les reessais et 40 pieces, fait pendre
    la passe indefiniment. Un module qui tourne en cron ne doit JAMAIS pouvoir
    pendre : il fait ce qu'il peut dans son budget, marque ou il s'est arrete,
    et reprend a la passe suivante. L'amorcage est incremental.
    """
    if hist.get("_amorce"):
        return hist
    debut = time.time()
    faits = set(hist.get("_amorce_faits") or [])
    print("[scanner] amorcage sur %d jours (budget %.0f s, reprise possible)..."
          % (JOURS_AMORCAGE, budget_s), flush=True)
    t1 = int(time.time() * 1000)
    t0 = t1 - JOURS_AMORCAGE * 86400 * 1000
    n = 0
    restants = [c for c in list(coins_hl)[:40] if c not in faits]
    for coin in restants:
        if time.time() - debut > budget_s:
            hist["_amorce_faits"] = sorted(faits)
            print("[scanner] budget atteint : %d/%d pieces, reprise a la prochaine passe."
                  % (len(faits), 40), flush=True)
            return hist
        faits.add(coin)
        h = _post("https://api.hyperliquid.xyz/info",
                  {"type": "fundingHistory", "coin": coin, "startTime": t0, "endTime": t1})
        b = _get("https://fapi.binance.com/fapi/v1/fundingRate?symbol=%sUSDT&startTime=%d&limit=1000"
                 % (coin, t0))
        if not isinstance(h, list) or not isinstance(b, list) or not h or not b:
            continue
        H = {int(x["time"]) // 3600000: _f(x["fundingRate"]) for x in h}
        B = {int(x["fundingTime"]) // 3600000: _f(x["fundingRate"]) / 8.0 for x in b}
        serie = []
        for k in sorted(B):
            for d in (0, -1, 1):
                if k + d in H:
                    serie.append(round(H[k + d] - B[k], 10)); break
        if len(serie) >= 30:
            hist.setdefault("rel", {})["HL-BINANCE:%s" % coin] = serie[-HIST_MAX:]
            n += 1
        time.sleep(0.05)
    hist["_amorce"] = datetime.now(timezone.utc).isoformat()
    hist["_amorce_faits"] = sorted(faits)
    print("[scanner] amorcage TERMINE : %d relation(s) pre-remplie(s)" % n, flush=True)
    return hist


# ----------------------------------------------------------------- passe
def executer():
    now = datetime.now(timezone.utc)
    hl, bn, by = hl_funding(), binance_funding(), bybit_funding()

    # DEGRADATION PROPRE (constate le 05/08/2026) : Binance geo-bloque les IP des
    # runners GitHub (situes aux Etats-Unis) et renvoie 451. Exiger les trois
    # venues faisait donc echouer chaque passe en 2 s, en silence. Un scanner
    # doit fonctionner avec ce qu'il a : deux venues suffisent a former une
    # relation. On journalise ce qui manque au lieu de rendre la main.
    dispo = {"hyperliquid": len(hl), "binance": len(bn), "bybit": len(by)}
    vivantes = [k for k, v in dispo.items() if v > 0]
    if len(vivantes) < 2:
        print("[scanner] moins de 2 venues joignables %s -> aucune relation possible."
              % dispo, flush=True)
        _ecrire(F_SORTIE, {"ts": now.isoformat(timespec="seconds"),
                           "erreur": "moins de 2 venues joignables",
                           "venues": dispo, "n_relations": 0, "n_alertes": 0,
                           "alertes": [], "top20": []})
        return None
    if len(vivantes) < 3:
        print("[scanner] venues joignables : %s (manquantes : %s) -- on continue."
              % (", ".join(vivantes),
                 ", ".join(k for k in dispo if k not in vivantes)), flush=True)
    rels = relations(hl, bn, by)
    hist = _lire(F_HIST, {})
    hist = amorcer(hist, list(hl))
    H = hist.setdefault("rel", {})

    for k, v in rels.items():
        H.setdefault(k, []).append(round(v["spread_h"], 10))
        if len(H[k]) > HIST_MAX:
            H[k] = H[k][-HIST_MAX:]

    # t glissant : le rendement capturable par heure, net de frais, sur FENETRE points
    resultats = []
    for k, serie in H.items():
        if len(serie) < 30 or k not in rels:
            continue
        s = serie[-FENETRE:]
        net = [abs(x) - rels[k]["seuil_frais_h"] for x in s]
        m = statistics.mean(net)
        sd = statistics.stdev(net) if len(net) > 1 else 0.0
        t = (m / (sd / math.sqrt(len(net)))) if sd > 1e-15 else 0.0
        resultats.append({
            "relation": k, "n": len(s),
            "spread_actuel_pct_h": round(100 * rels[k]["spread_h"], 5),
            "seuil_frais_pct_h": round(100 * rels[k]["seuil_frais_h"], 5),
            "ratio_frais": round(rels[k]["ratio_frais"], 2),
            "ecart_prix_bp": rels[k]["ecart_prix_bp"],
            "gain_net_moyen_pct_h": round(100 * m, 5),
            "t": round(max(-99.0, min(99.0, t)), 2),
            "alerte": bool(t >= SEUIL_T and m > 0)})
    resultats.sort(key=lambda r: -r["t"])
    alertes = [r for r in resultats if r["alerte"]]

    doc = {"ts": now.isoformat(timespec="seconds"),
           "seuil_t": SEUIL_T, "fenetre": FENETRE,
           "n_relations": len(resultats), "n_alertes": len(alertes),
           "calibration": ("seuil calibre sous H0 par simulation : le bruit pur "
                           "produit un max de t glissant de 3,65 (1 relation) a "
                           "5,37 (200 relations) sur 7 ans. En dessous de 5,4, "
                           "une alerte n'est pas distinguable du hasard."),
           "alertes": alertes,
           "top20": resultats[:20],
           "rappel": ("Detection seule. Aucune position n'est ouverte par ce module. "
                      "Une alerte signifie : relation mecanique dont l'ecart depasse "
                      "les frais de facon significative -- a verifier a la main avant "
                      "tout engagement, et un second compte est necessaire.")}
    _ecrire(F_SORTIE, doc)
    _ecrire(F_HIST, hist)
    if alertes:
        for a in alertes:
            print("[scanner] *** ALERTE *** %s : t=%.2f, spread %.5f %%/h "
                  "(%.1fx les frais)" % (a["relation"], a["t"],
                                         a["spread_actuel_pct_h"], a["ratio_frais"]), flush=True)
    else:
        meilleur = resultats[0] if resultats else None
        print("[scanner] %d relations, 0 alerte (seuil t>=%.1f). Meilleure : %s t=%.2f"
              % (len(resultats), SEUIL_T,
                 meilleur["relation"] if meilleur else "-",
                 meilleur["t"] if meilleur else 0), flush=True)
    return doc


if __name__ == "__main__":
    executer()
