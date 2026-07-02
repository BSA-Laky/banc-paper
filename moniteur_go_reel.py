#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
moniteur_go_reel.py - GATE "passage au reel" + surveillance decrochage (paper)
==============================================================================
Optimisation "logique OpenClaw" : la partie MESURABLE de la decision d'aller
en reel est calculee ici, froidement, a chaque passe du banc, et publiee dans
docs/go_reel.json. L'IA decideuse (Arbitre) lit ce fichier, tient a jour
vault_obsidian/GO_REEL.md et alerte sur ROUGE. Le feu vert final reste HUMAIN
(capital plancher, courtier, risque defini) : ce script ne recommande jamais
d'engager de l'argent reel, il dit seulement si les CRITERES chiffres du
projet sont remplis. stdlib only, lecture seule.

Statuts par bot :
  GRIS   n < n_lecture (30) -> rien a lire.
  ROUGE  decrochage : esperance glissante 20 trades < mu_ref - 2*sigma_ref/sqrt(20)
         (refs backtest si connues, sinon l'historique live complet du bot),
         OU drawdown live > 1,5x le pire drawdown de reference.
         -> action : COUPER LE BOT (jamais "elargir le stop").
  VERT   criteres GO chiffres remplis : n >= n_go, t >= 2, esp > 0,
         anciennete forward >= jours_min, pas de decrochage
         (+ bot 25 : doit battre le 23, delta d'esperance > 0 avec t_Welch >= 2).
  ORANGE tout le reste (mesure en cours, rien d'anormal).

Bonus : sante du temoin (|t| < 2 sinon le banc lui-meme est suspect), A/B 25
vs 23 (Welch), et scoring de calibration des avis de regime du bot 27e
(journal_arbitre.csv -> l'estimation haussier/baissier devient une prevision
NOTEE a J+7 sur le rendement BTC realise).
"""
from __future__ import annotations

import csv
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from banc_essai_paper_trading import charger_journal, evaluer, LEDGER_PATH

BOOK_LEDGER = Path("book_trades.csv")
ETAT_DIR = Path("etat")
JOURNAL_ARBITRE = ETAT_DIR / "journal_arbitre.csv"
CALIBRATION_CSV = ETAT_DIR / "calibration_arbitre.csv"
SORTIE_JSON = Path("docs") / "go_reel.json"
HL_INFO_URL = "https://api.hyperliquid.xyz/info"
USER_AGENT = "paper-trading-bench/1.0 (read-only research)"

N_LECTURE = 30          # en-dessous : GRIS (regle du projet, cf. verdicts du banc)
FEN_GLISSANTE = 20      # fenetre de detection du decrochage
HORIZON_SCORE_J = 7     # scoring des avis de regime a J+7

# References backtest par bot (mu/sigma par trade en $, mdd en $ ; None = inconnu
# -> auto-reference sur l'historique live complet du bot). jours_min = anciennete
# forward minimale avant qu'un VERT soit possible (regle projet : 4-8 semaines).
GATE = {
    "28_carry_hold":        {"n_go": 100, "jours_min": 28, "mu_ref": 1.26, "sigma_ref": 1.34, "mdd_ref": None},
    "25_convergence_basis": {"n_go": 300, "jours_min": 28, "mu_ref": None, "sigma_ref": None, "mdd_ref": None,
                             "exige_battre": "23_carry_funding"},
    "27b_rev_move":         {"n_go": 50,  "jours_min": 28, "mu_ref": None, "sigma_ref": None, "mdd_ref": None},
    "27e_arbitre":          {"n_go": 50,  "jours_min": 28, "mu_ref": None, "sigma_ref": None, "mdd_ref": None,
                             "exige_battre": "27b_rev_move"},
    "30_trend_following":   {"n_go": 4,   "jours_min": 120, "mu_ref": None, "sigma_ref": None, "mdd_ref": None},
    "31_variance_premium":  {"n_go": 4,   "jours_min": 120, "mu_ref": None, "sigma_ref": None, "mdd_ref": None},
}
DEFAUT = {"n_go": 100, "jours_min": 28, "mu_ref": None, "sigma_ref": None, "mdd_ref": None}
TEMOINS = ("10_controle_aleatoire", "10b_controle_book")


def _pnls_et_dates(lignes):
    """Par bot : liste chronologique des pnl + date du 1er trade ouvert."""
    par_bot, premiers = {}, {}
    for ln in lignes:
        if ln.get("status") != "closed" or ln.get("pnl") in (None, "", "None"):
            continue
        bot = ln["bot"]
        par_bot.setdefault(bot, []).append(float(ln["pnl"]))
        d = ln.get("opened_at") or ln.get("closed_at") or ""
        if d and (bot not in premiers or d < premiers[bot]):
            premiers[bot] = d
    return par_bot, premiers


def _moyenne_ecart(xs):
    n = len(xs)
    if n < 2:
        return (xs[0] if xs else 0.0), 0.0
    m = sum(xs) / n
    var = sum((x - m) ** 2 for x in xs) / (n - 1)
    return m, var ** 0.5


def _t_welch(a, b):
    ma, sa = _moyenne_ecart(a)
    mb, sb = _moyenne_ecart(b)
    na, nb = len(a), len(b)
    if na < 2 or nb < 2:
        return 0.0
    se = (sa * sa / na + sb * sb / nb) ** 0.5
    return (ma - mb) / se if se > 1e-9 else 0.0


def _jours_depuis(iso):
    try:
        d = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - d).total_seconds() / 86400.0
    except (ValueError, TypeError):
        return 0.0


def _statut_bot(bot, pnls, stats, premiers):
    cfg = GATE.get(bot, DEFAUT)
    n = len(pnls)
    res = {"n": n, "esperance": round(stats["esperance_par_trade"], 4),
           "t_stat": round(stats["t_stat"], 2),
           "mdd_live": round(stats["max_drawdown"], 2),
           "jours_forward": round(_jours_depuis(premiers.get(bot, "")), 1),
           "verdict_banc": stats["verdict"], "decrochage": False,
           "raisons": [], "avertissements": []}

    # -- decrochage (des que la fenetre existe, meme sous n_lecture on surveille)
    if n >= FEN_GLISSANTE + 5:
        esp20, _ = _moyenne_ecart(pnls[-FEN_GLISSANTE:])
        mu, sigma = cfg["mu_ref"], cfg["sigma_ref"]
        if mu is None or sigma is None:
            mu, sigma = _moyenne_ecart(pnls)
        borne = mu - 2.0 * sigma / (FEN_GLISSANTE ** 0.5)
        res["esp_glissante_20"] = round(esp20, 4)
        res["borne_decrochage"] = round(borne, 4)
        if esp20 < borne:
            if esp20 < 0:                 # sous la borne ET negatif -> couper
                res["decrochage"] = True
                res["raisons"].append(f"esp20 {esp20:.2f} < borne {borne:.2f} -> COUPER LE BOT")
            else:                          # sous la borne mais encore positif -> vigilance
                res["avertissements"].append(
                    f"esp20 {esp20:.2f} sous la borne {borne:.2f} mais > 0 -- surveiller")
    if cfg["mdd_ref"] and stats["max_drawdown"] > 1.5 * cfg["mdd_ref"]:
        res["decrochage"] = True
        res["raisons"].append("drawdown live > 1,5x reference -> COUPER LE BOT")

    # -- statut
    if res["decrochage"]:
        res["statut"] = "ROUGE"
        return res
    if n < N_LECTURE and cfg["n_go"] >= N_LECTURE:
        res["statut"] = "GRIS"
        return res
    go = (n >= cfg["n_go"] and stats["t_stat"] >= 2.0
          and stats["esperance_par_trade"] > 0
          and res["jours_forward"] >= cfg["jours_min"])
    if not go:
        res["statut"] = "ORANGE"
        if n < cfg["n_go"]:
            res["raisons"].append(f"n {n} < n_go {cfg['n_go']}")
        if stats["t_stat"] < 2.0:
            res["raisons"].append("t < 2")
        if res["jours_forward"] < cfg["jours_min"]:
            res["raisons"].append(f"forward {res['jours_forward']:.0f} j < {cfg['jours_min']} j")
    else:
        res["statut"] = "VERT"
    return res


# ---------------------------------------------------------------- calibration
def _http_post_info(body, timeout=12.0):
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(HL_INFO_URL, data=data,
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, OSError):
        return None


def _closes_btc_par_jour(depuis_ms):
    rep = _http_post_info({"type": "candleSnapshot",
                           "req": {"coin": "BTC", "interval": "1d",
                                   "startTime": depuis_ms,
                                   "endTime": int(time.time() * 1000)}})
    if not isinstance(rep, list):
        return {}
    out = {}
    for b in rep:
        try:
            jour = datetime.fromtimestamp(int(b["t"]) / 1000, tz=timezone.utc).date().isoformat()
            out[jour] = float(b["c"])
        except (TypeError, KeyError, ValueError):
            continue
    return out


def _scorer_calibration():
    """Note a J+7 les avis de regime du journal de l'arbitre. Append-only."""
    if not JOURNAL_ARBITRE.exists():
        return None
    try:
        with JOURNAL_ARBITRE.open(newline="", encoding="utf-8") as fh:
            lignes = list(csv.DictReader(fh))
    except OSError:
        return None
    deja = set()
    if CALIBRATION_CSV.exists():
        try:
            with CALIBRATION_CSV.open(newline="", encoding="utf-8") as fh:
                deja = {(r["ts"], r["coin"]) for r in csv.DictReader(fh)}
        except OSError:
            pass
    a_scorer = []
    for r in lignes:
        if (r["ts"], r["coin"]) in deja:
            continue
        if _jours_depuis(r["ts"]) < HORIZON_SCORE_J + 0.5:
            continue
        regime = (r.get("regime_ia") or r.get("regime_tendance") or "").strip()
        if regime not in ("haussier", "baissier"):
            continue                      # neutre/inconnu : pas une prevision directionnelle
        a_scorer.append((r, regime))
    if not a_scorer:
        return _resume_calibration()
    anciens = min(datetime.fromisoformat(r["ts"].replace("Z", "+00:00")) for r, _ in a_scorer)
    closes = _closes_btc_par_jour(int((anciens - timedelta(days=2)).timestamp() * 1000))
    if not closes:
        return _resume_calibration()
    nouveaux = []
    for r, regime in a_scorer:
        d0 = datetime.fromisoformat(r["ts"].replace("Z", "+00:00")).date()
        c0 = closes.get(d0.isoformat())
        c7 = closes.get((d0 + timedelta(days=HORIZON_SCORE_J)).isoformat())
        if not c0 or not c7:
            continue
        ret7 = c7 / c0 - 1.0
        correct = (regime == "haussier") == (ret7 > 0)
        try:
            conf = float(r.get("conf_ia") or 0.6)
        except ValueError:
            conf = 0.6
        p_haussier = conf if regime == "haussier" else 1.0 - conf
        brier = (p_haussier - (1.0 if ret7 > 0 else 0.0)) ** 2
        nouveaux.append([r["ts"], r["coin"], r.get("source", ""), regime,
                         round(ret7, 4), int(correct), round(brier, 4)])
    if nouveaux:
        try:
            ETAT_DIR.mkdir(parents=True, exist_ok=True)
            neuf = not CALIBRATION_CSV.exists()
            with CALIBRATION_CSV.open("a", encoding="utf-8", newline="") as fh:
                w = csv.writer(fh)
                if neuf:
                    w.writerow(["ts", "coin", "source", "regime_prevu",
                                "ret7_realise", "correct", "brier"])
                w.writerows(nouveaux)
        except OSError:
            pass
    return _resume_calibration()


def _resume_calibration():
    if not CALIBRATION_CSV.exists():
        return None
    try:
        with CALIBRATION_CSV.open(newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
    except OSError:
        return None
    if not rows:
        return None
    par_source = {}
    for r in rows:
        s = r.get("source") or "?"
        par_source.setdefault(s, []).append(r)
    out = {}
    for s, rs in par_source.items():
        n = len(rs)
        out[s] = {"n": n,
                  "taux_correct": round(sum(int(r["correct"]) for r in rs) / n, 3),
                  "brier_moyen": round(sum(float(r["brier"]) for r in rs) / n, 3)}
    return out


# ----------------------------------------------------------------- production
def produire_go_reel():
    lignes = charger_journal(LEDGER_PATH) + charger_journal(BOOK_LEDGER)
    stats = evaluer(lignes)
    par_bot, premiers = _pnls_et_dates(lignes)

    bots = {b: _statut_bot(b, par_bot[b], stats[b], premiers)
            for b in stats if b not in TEMOINS}

    # A/B et "exige_battre"
    for bot, cfg in GATE.items():
        rival = cfg.get("exige_battre")
        if not rival or bot not in bots or rival not in par_bot:
            continue
        delta = (stats[bot]["esperance_par_trade"]
                 - stats[rival]["esperance_par_trade"])
        t_d = _t_welch(par_bot[bot], par_bot[rival])
        bots[bot]["ab"] = {"contre": rival, "delta_esperance": round(delta, 4),
                           "t_welch": round(t_d, 2)}
        if bots[bot]["statut"] == "VERT" and not (delta > 0 and t_d >= 2.0):
            bots[bot]["statut"] = "ORANGE"
            bots[bot]["raisons"].append(f"ne bat pas {rival} (delta {delta:.2f}, t {t_d:.2f})")

    temoins = {b: {"n": stats[b]["trades"], "t_stat": round(stats[b]["t_stat"], 2),
                   "sain": abs(stats[b]["t_stat"]) < 2.0}
               for b in TEMOINS if b in stats}
    banc_suspect = any(not v["sain"] for v in temoins.values())

    doc = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "rappel": ("Criteres chiffres seulement. Le feu vert REEL reste humain : "
                   "capital >= plancher (3-10 k EUR), courtier IBKR, risque defini "
                   "(spreads) pour la variance, et jamais sans VERT stable."),
        "banc_suspect": banc_suspect,
        "temoins": temoins,
        "bots": bots,
        "alertes": sorted(f"{b}: {r}" for b, v in bots.items()
                          if v["statut"] == "ROUGE" for r in v["raisons"]),
        "avertissements": sorted(f"{b}: {r}" for b, v in bots.items()
                                 for r in v.get("avertissements", [])),
        "calibration_arbitre": _scorer_calibration(),
    }
    try:
        SORTIE_JSON.parent.mkdir(parents=True, exist_ok=True)
        with SORTIE_JSON.open("w", encoding="utf-8") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=1)
    except OSError:
        pass
    if doc["alertes"]:
        print(f"[go_reel] ALERTE ROUGE : {doc['alertes']}", flush=True)
    return doc


if __name__ == "__main__":
    d = produire_go_reel()
    for b, v in sorted(d["bots"].items()):
        print(f"{v['statut']:6} {b:22} n={v['n']:<4} esp={v['esperance']:<8} "
              f"t={v['t_stat']:<6} fwd={v['jours_forward']}j {';'.join(v['raisons'])}")
