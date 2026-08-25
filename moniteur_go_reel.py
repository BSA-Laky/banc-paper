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

from banc_essai_paper_trading import (charger_journal, evaluer, LEDGER_PATH,
                                      _coupure_comptable)


def _lignes_valides(lignes):
    """Ecarte les trades d'AVANT la correction comptable du 26/07/2026.

    CRITIQUE : ce gate autorise le passage en ARGENT REEL. Sans ce filtre, il
    calculait n, pnl_cumule et le decrochage sur le journal BRUT (evaluer() etait
    filtre, mais pas _pnls_et_dates) et publiait encore
    '25_convergence_basis : n=1098, t=3,83, statut=VERT' -- exactement la donnee
    fantasmee par l'ancienne comptabilite (abs(funding), aucun terme de prix).
    """
    bots, date = _coupure_comptable()
    if not bots or not date:
        return lignes
    return [l for l in lignes
            if not (l.get("bot") in bots and str(l.get("closed_at") or "") < date)]

BOOK_LEDGER = Path("book_trades.csv")
RD_LEDGER = Path("rd_trades.csv")   # bots generes par Nova (meme gate)
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
    "28_carry_hold":        {"n_go": 100, "jours_min": 28, "mu_ref": 1.26, "sigma_ref": 1.34, "mdd_ref": None,
                             "trop_beau_audite": "2026-07-15 : verifie vs funding reel HL (5/5 trades coherents, "
                                                 "BLUR 77$ = 83-90$ reels, 0 flip de signe) — regime juillet riche "
                                                 "+ queue droite (top3 = 63% du P&L). Voir Bot/AUDIT_BOT28."},
    "25_convergence_basis": {"n_go": 300, "jours_min": 28, "mu_ref": None, "sigma_ref": None, "mdd_ref": None,
                             "exige_battre": "23_carry_funding"},
    "27b_rev_move":         {"n_go": 50,  "jours_min": 28, "mu_ref": None, "sigma_ref": None, "mdd_ref": None},
    "27e_arbitre":          {"n_go": 50,  "jours_min": 28, "mu_ref": None, "sigma_ref": None, "mdd_ref": None,
                             "exige_battre": "27b_rev_move"},
    "30_trend_following":   {"n_go": 4,   "jours_min": 120, "mu_ref": None, "sigma_ref": None, "mdd_ref": None},
    "31_variance_premium":  {"n_go": 4,   "jours_min": 120, "mu_ref": None, "sigma_ref": None, "mdd_ref": None},
    # 30b ajoute le 25/08/2026, avec exige_battre. Mesure sur 143 mois de prix reels :
    # le bot rend +0,564 %/mois (Sharpe 0,67, t +2,30) mais son TEMOIN ALEATOIRE, qui
    # tient les memes instruments au hasard, rend deja +0,249 %/mois. L'apport du signal
    # est donc +0,315 %/mois avec t = +1,62 -- et sur 15 tirages du temoin, t depasse 2
    # dans 2 cas sur 15 seulement. Sans cette clause, 30b passerait VERT sur un t brut
    # gonfle par le simple fait d'etre long un marche haussier.
    "30b_trend_executable": {"n_go": 24,  "jours_min": 120, "mu_ref": None, "sigma_ref": None, "mdd_ref": None,
                             "exige_battre": "10c_controle_cfd"},
}
DEFAUT = {"n_go": 100, "jours_min": 28, "mu_ref": None, "sigma_ref": None, "mdd_ref": None}

# NON PROMOUVABLES (15/08) : bots dont le trade N'EST PAS EXECUTABLE avec les
# comptes dont nous disposons. Lecon des bots 24 et 26, tues le 29/07 pour avoir
# mesure finement un trade impossible. Ils sont MESURES (la connaissance a de la
# valeur) mais ne peuvent JAMAIS atteindre VERT.
NON_EXECUTABLES = {
    "32_carry_crossvenue": "aucun compte Nado ; audit securite Nado non confirme ; "
                           "min_size Nado 100 $/ordre",
}
TEMOINS = ("10_controle_aleatoire", "10b_controle_book")

# RETRAITS DU 15/08/2026 — la famille 27 est close. Motifs mesures, pas d'opinion :
# la somme 27b+27c vaut -14 bp CONSTANTS sur 92/92 trades apparies (ecart-type nul),
# donc 27c est une transformation deterministe de 27b et n'apporte aucun degre de
# liberte ; 27b et 27d ont epuise n_go ET la fenetre forward sans atteindre t=2 ;
# 27f a ete devance par son propre jumeau rapide 27f10 (n=175, t=-0,09, tue le 05/08).
# 27a est arrete non pour ses chiffres mais parce que meme a t=2 son rendement serait
# inexploitable au capital disponible (cf. Bot fi/COUTS_EXECUTION_BOOK_2026-08-15.md).
RETIRES = {
    "27c_mom_move":      "retrait 15/08 : miroir deterministe de 27b (somme -14 bp constants, 92/92) — zero information",
    "27b_rev_move":      "retrait 15/08 : n_go et forward atteints, t +0,52 — indiscernable du hasard",
    "27d_rev_move_stop": "retrait 15/08 : n_go et forward atteints, t -0,86 ; le stop detruit 221 $ sur 146 trades",
    "27f_selecteur":     "retrait 15/08 : question deja tranchee par le jumeau 27f10 (n=175, t -0,09)",
    "27a_rev_premium":   "retrait 15/08 : signal independant mais rendement inexploitable au capital disponible",
}


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


def _series_journalieres(lignes):
    """P&L somme PAR JOUR (cle date iso) et par bot, depuis les trades fermes."""
    out = {}
    for ln in lignes:
        if ln.get("status") != "closed" or ln.get("pnl") in (None, "", "None"):
            continue
        d = str(ln.get("closed_at") or ln.get("opened_at") or "")[:10]
        if not d:
            continue
        out.setdefault(ln["bot"], {})
        out[ln["bot"]][d] = out[ln["bot"]].get(d, 0.0) + float(ln["pnl"])
    return out


def _serie_alignee(jours_bot, depuis):
    """Liste des P&L quotidiens depuis une date (0 quand pas de trade ferme)."""
    from datetime import date, timedelta as _td
    try:
        d0 = date.fromisoformat(depuis)
    except ValueError:
        return list(jours_bot.values())
    fin = datetime.now(timezone.utc).date()
    xs, d = [], d0
    while d < fin:                        # jours complets uniquement
        xs.append(jours_bot.get(d.isoformat(), 0.0))
        d += _td(days=1)
    return xs


def _expo_moyenne(lignes):
    """$ moyens deployes par bot = somme(mise x duree) / periode totale."""
    contrib, bornes = {}, {}
    for ln in lignes:
        if ln.get("status") != "closed":
            continue
        try:
            o = datetime.fromisoformat(str(ln.get("opened_at")).replace("Z", "+00:00"))
            c = datetime.fromisoformat(str(ln.get("closed_at")).replace("Z", "+00:00"))
            sz = float(ln.get("size_usd") or 0)
        except (ValueError, TypeError):
            continue
        b = ln["bot"]
        contrib[b] = contrib.get(b, 0.0) + sz * max(0.0, (c - o).total_seconds())
        deb, fin = bornes.get(b, (o, c))
        bornes[b] = (min(deb, o), max(fin, c))
    out = {}
    for b, tot in contrib.items():
        deb, fin = bornes[b]
        periode = max(86400.0, (datetime.now(timezone.utc) - deb).total_seconds())
        out[b] = tot / periode
    # Fallback (16/07) : les trades anterieurs aux fixes opened_at ont duree 0 ->
    # estimation Little = (n/jours) x hold_defaut x mise moyenne, le temps que les
    # durees reelles peuplent le ledger. hold_defaut 1 j (28 : 2 j).
    holds = {"28_carry_hold": 2.0}
    n_par, mise_par, premiers_b = {}, {}, {}
    for ln in lignes:
        if ln.get("status") != "closed":
            continue
        b = ln["bot"]
        try:
            mise_par.setdefault(b, []).append(float(ln.get("size_usd") or 0))
        except (ValueError, TypeError):
            continue
        n_par[b] = n_par.get(b, 0) + 1
        d = str(ln.get("closed_at") or "")
        if d and (b not in premiers_b or d < premiers_b[b]):
            premiers_b[b] = d
    for b, n in n_par.items():
        if out.get(b, 0.0) > 1.0:
            continue                       # durees reelles disponibles
        jours = max(1.0, _jours_depuis(premiers_b.get(b, "")))
        mises = mise_par.get(b, [])
        mise_moy = (sum(mises) / len(mises)) if mises else 0.0
        out[b] = (n / jours) * holds.get(b, 1.0) * mise_moy
    return out


def _statut_bot(bot, pnls, stats, premiers):
    cfg = GATE.get(bot, DEFAUT)
    n = len(pnls)
    res = {"n": n, "esperance": round(stats["esperance_par_trade"], 4),
           "t_stat": round(stats["t_stat"], 2),
           "mdd_live": round(stats["max_drawdown"], 2),
           "jours_forward": round(_jours_depuis(premiers.get(bot, "")), 1),
           "verdict_banc": stats["verdict"], "decrochage": False,
           "raisons": [], "avertissements": []}
    res["mu_ref"] = cfg.get("mu_ref")
    res["pnl_cumule"] = round(sum(pnls), 2)
    res["pnl_par_jour"] = round(sum(pnls) / max(res["jours_forward"], 0.5), 3)
    # garde TROP-BEAU (15/07) : un edge se degrade du backtest au forward, il ne
    # triple pas. Au-dela de 2x la reference -> a expliquer avant toute promotion.
    # Une fois l'ecart AUDITE (cle trop_beau_audite dans GATE), la garde devient
    # une note informative et ne bloque plus (audit du 28 : 15/07/2026).
    res["trop_beau_audite"] = cfg.get("trop_beau_audite")
    if cfg.get("mu_ref") and n >= 20 and stats["esperance_par_trade"] > 2.0 * cfg["mu_ref"]:
        if cfg.get("trop_beau_audite"):
            res.setdefault("notes", []).append(
                "esp %.1fx la ref backtest — ecart AUDITE (%s)"
                % (stats["esperance_par_trade"] / cfg["mu_ref"], cfg["trop_beau_audite"][:60]))
        else:
            res["avertissements"].append(
                "esp %.2f = %.1fx la ref backtest (%.2f) -- TROP BEAU : a expliquer "
                "(P&L par piece, funding recalcule) avant toute promotion"
                % (stats["esperance_par_trade"],
                   stats["esperance_par_trade"] / cfg["mu_ref"], cfg["mu_ref"]))

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
    # verrou d'executabilite : un trade impossible ne devient jamais VERT
    motif = NON_EXECUTABLES.get(bot)
    if motif:
        res["non_executable"] = motif
        if res["statut"] == "VERT":
            res["statut"] = "ORANGE"
            res["raisons"].append("NON EXECUTABLE : " + motif)
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
    lignes = charger_journal(LEDGER_PATH) + charger_journal(BOOK_LEDGER) + charger_journal(RD_LEDGER)
    lignes = _lignes_valides(lignes)     # meme perimetre pour TOUT ce qui suit
    stats = evaluer(lignes)
    par_bot, premiers = _pnls_et_dates(lignes)

    bots = {b: _statut_bot(b, par_bot[b], stats[b], premiers)
            for b in stats if b not in TEMOINS}

    # debit et rendement du capital (15/07 : l'esperance/trade ne suffit pas
    # quand les frequences different -- comparer aussi P&L/jour et P&L/jour/$expo)
    jours_series = _series_journalieres(lignes)
    expos = _expo_moyenne(lignes)
    for b, v in bots.items():
        e = expos.get(b, 0.0)
        v["expo_moyenne_usd"] = round(e, 1)
        v["rendement_j_pct"] = (round(100.0 * v["pnl_par_jour"] / e, 3) if e > 1 else None)

    # A/B et "exige_battre" -- verdict rendu A CAPITAL EGAL (rendement/jour/$),
    # avec Welch sur les series JOURNALIERES alignees ; l'esp/trade reste affichee.
    for bot, cfg in GATE.items():
        rival = cfg.get("exige_battre")
        # 'rival not in stats' : un rival SUPPRIME (bot 23, retire le 29/07) ou dont
        # tous les trades sont ecartes par la coupure comptable ne figure plus dans
        # stats. Sans ce garde, produire_go_reel() levait un KeyError, run_once
        # l'attrapait en silence, et go_reel.json restait FIGE sur des donnees
        # perimees -- le gate du reel gelait sur '25 VERT t=3,83'.
        if (not rival or bot not in bots or rival not in par_bot
                or rival not in stats or bot not in stats):
            continue
        delta = (stats[bot]["esperance_par_trade"]
                 - stats[rival]["esperance_par_trade"])
        t_d = _t_welch(par_bot[bot], par_bot[rival])
        depuis = max(str(premiers.get(bot, ""))[:10], str(premiers.get(rival, ""))[:10])
        sa = _serie_alignee(jours_series.get(bot, {}), depuis)
        sb = _serie_alignee(jours_series.get(rival, {}), depuis)
        ea, eb = expos.get(bot, 0.0), expos.get(rival, 0.0)
        if ea > 1 and eb > 1 and len(sa) >= 10:
            ra = [100.0 * x / ea for x in sa]          # rendement quotidien %
            rb = [100.0 * x / eb for x in sb]
            d_r = (sum(ra) / len(ra)) - (sum(rb) / len(rb))
            t_r = _t_welch(ra, rb)
        else:                                          # fallback : par-trade
            d_r, t_r = delta, t_d
        bots[bot]["ab"] = {"contre": rival, "delta_esperance": round(delta, 4),
                           "t_welch": round(t_d, 2),
                           "delta_rendement_j_pct": round(d_r, 4),
                           "t_welch_jour": round(t_r, 2),
                           "jours_compares": len(sa)}
        if bots[bot]["statut"] == "VERT" and not (d_r > 0 and t_r >= 2.0):
            bots[bot]["statut"] = "ORANGE"
            bots[bot]["raisons"].append(
                f"ne bat pas {rival} a capital egal (delta rendement/j {d_r:.3f} pt, t {t_r:.2f})")

    # regle 15/07 : l'arbitrage de regime (27e) doit battre 27b avant n=30, sinon kill
    v27 = bots.get("27e_arbitre")
    if v27 and isinstance(v27.get("ab"), dict) and v27["n"] >= 30             and v27["ab"].get("delta_esperance", 0) < 0:
        v27["avertissements"].append(
            "REGLE 15/07 : Delta<0 vs 27b a n>=30 -- KILL RECOMMANDE (prior negatif confirme)")

    # ------------------------------------------------------------ cycle de vie
    # VERDICTS PRE-ENREGISTRES (17/07) : la station exécute elle-même les règles
    # écrites A L'AVANCE — aucun jugement nouveau ici, le GO réel reste humain.
    #   R1  ROUGE/décrochage -> KILL (texte de la gate : « COUPER LE BOT »)
    #   R2  25_convergence_basis : à l'échéance (n>=n_go ET forward>=jours_min),
    #       s'il ne bat pas le 23 à capital égal (delta>0 et t>=2) -> KILL (règle 22/06)
    #   R3  27e_arbitre : n>=30 et delta<0 vs 27b -> KILL (règle du 15/07)
    # Buckets 27a-27d EXCLUS (expérience appariée : le miroir doit tourner).
    # Un kill est STICKY ; réactivation humaine via « relance <bot> » (gateway),
    # qui pose relance=ts -> plus jamais d'auto-kill sur ce bot (main humaine).
    CYCLE = ETAT_DIR / "cycle_vie.json"
    try:
        cv = json.loads(CYCLE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cv = {}
    cv.setdefault("bots", {})
    # --- RETRAITS DECIDES LE 15/08/2026 -------------------------------------
    # Declares ICI plutot qu'edites a la main dans cycle_vie.json : le fichier
    # d'etat est reecrit a chaque passe, une edition manuelle serait ecrasee ou
    # entrerait en collision. Un kill est sticky, donc une seule ecriture suffit.
    for _b, _r in RETIRES.items():
        if _b not in cv["bots"] and not cv["bots"].get(_b, {}).get("relance"):
            cv["bots"][_b] = {"etat": "kill", "raison": _r,
                              "ts": datetime.now(timezone.utc).isoformat()}
    KILLABLES = {"23_carry_funding", "24_funding_multivenues", "25_convergence_basis",
                 "26_carry_nado", "27e_arbitre", "27f_selecteur", "27f10_selecteur",
                 "27g10_selecteur", "28_carry_hold"}
    for b, v in bots.items():
        deja = cv["bots"].get(b, {})
        if deja.get("etat") == "kill":
            v["statut"] = "ROUGE"          # sticky : reste ROUGE, mais ALERTE NETTOYEE
            # 23/07 : un bot tué ne crache plus TOUTES ses raisons de gate (n<50, t<2...) :
            # une seule ligne pendant 3 j, puis SILENCE (kill acquitte). Anti-accumulation.
            if _jours_depuis(deja.get("ts", "")) < 3.0:
                v["raisons"] = ["KILL exécuté (%s) : %s" % (str(deja.get("ts", ""))[:10],
                                                           deja.get("raison", ""))]
            else:
                v["raisons"] = []
            continue
        if b not in KILLABLES or deja.get("relance"):
            continue
        raison = None
        etat_verdict = "kill"
        cfgb = GATE.get(b, DEFAUT)
        ab = v.get("ab") or {}
        if v["statut"] == "ROUGE" and v.get("decrochage"):
            raison = "R1 décrochage : " + " ; ".join(v.get("raisons", [])[:2])
        elif b == "25_convergence_basis" and ab:
            if (v["n"] >= cfgb.get("n_go", 300)
                    and v["jours_forward"] >= cfgb.get("jours_min", 28)
                    and not (ab.get("delta_rendement_j_pct", 0) > 0
                             and ab.get("t_welch_jour", 0) >= 2.0)):
                raison = ("R2 échéance A/B : ne bat pas 23 à capital égal "
                          "(delta %.3f pt/j, t %.2f)"
                          % (ab.get("delta_rendement_j_pct", 0), ab.get("t_welch_jour", 0)))
                etat_verdict = "retrograde"   # 21/07 : redondance n'est pas nullite -> garder (paper 0 cout), trancher au reel
        elif b == "27e_arbitre" and ab:
            if v["n"] >= 30 and ab.get("delta_esperance", 0) < 0:
                raison = ("R3 règle 15/07 : delta %.2f $ < 0 vs 27b à n>=30"
                          % ab.get("delta_esperance", 0))
        if raison:
            cv["bots"][b] = {"etat": etat_verdict, "raison": raison,
                             "ts": datetime.now(timezone.utc).isoformat()}
            if etat_verdict == "kill":
                v["statut"] = "ROUGE"
                v.setdefault("raisons", []).append("VERDICT PRÉ-ENREGISTRÉ -> KILL : " + raison)
            else:
                v.setdefault("raisons", []).append(
                    "RÉTROGRADÉ (redondant vs 23, à trancher au réel — reste en paper) : " + raison)
    try:
        CYCLE.parent.mkdir(parents=True, exist_ok=True)
        CYCLE.write_text(json.dumps(cv, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        pass

    # --- Sante des temoins (revu le 13/08/2026) -------------------------------
    # Un temoin qui paie un spread DOIT perdre : son t-stat vaut -s*racine(n) et
    # part vers le rouge a mesure que n grandit, sans qu'aucune anomalie n'existe.
    # On retire donc cette derive AVANT de juger. Le t corrige est exactement le
    # test "le taux de reussite vaut-il 50 % ?" -- la seule question qui compte.
    #
    # Deux corrections apportees a l'ancienne version :
    #  (a) la valeur 0,02 etait ecrite en dur ici alors que le spread est defini
    #      dans banc_essai_paper_trading. Un changement de spread aurait rendu la
    #      gate silencieusement fausse. Chaque temoin declare desormais sa derive.
    #  (b) la meme correction de 2 % etait appliquee au temoin du BOOK, qui ne
    #      paie aucun spread construit : on lui offrait 2 %*racine(n) de mauvaise
    #      performance gratuite, ce qui aurait masque un temoin reellement casse.
    derives = {}
    for nom, mod, cls in (("10_controle_aleatoire", "banc_essai_paper_trading", "ControleAleatoire"),
                          ("10b_controle_book", "bot_trend", "ControleBook")):
        try:
            derives[nom] = float(getattr(__import__(mod), cls).DERIVE_ATTENDUE)
        except Exception:
            derives[nom] = 0.02 if nom == "10_controle_aleatoire" else 0.0

    temoins = {}
    for b in TEMOINS:
        if b not in stats:
            continue
        n, t = stats[b]["trades"], stats[b]["t_stat"]
        d = derives.get(b, 0.0)
        t_corr = t + d * n ** 0.5
        temoins[b] = {"n": n, "t_stat": round(t, 2),
                      "derive_attendue": d,
                      "t_corrige": round(t_corr, 2),
                      "sain": abs(t_corr) < 2.0,
                      "lecture": (f"t brut {t:+.2f} dont {-d * n ** 0.5:+.2f} de spread "
                                  f"par construction -> t corrige {t_corr:+.2f} "
                                  f"({'sain' if abs(t_corr) < 2.0 else 'SUSPECT'})")
                      if d else (f"t {t:+.2f} ({'sain' if abs(t_corr) < 2.0 else 'SUSPECT'}) "
                                 "-- aucun spread construit, derive attendue nulle")}
    banc_suspect = any(not v["sain"] for v in temoins.values())
    # --- Bots reellement en ARGENT REEL (corrige le 10/08/2026) -----------------
    # Trois verrous, du plus fort au plus faible. Un seul suffit a vider la liste :
    #   (a) etat/reel_stop.json {"stop": true}  -> kill-switch, plus rien ne trade ;
    #   (b) portefeuille.reel.json reel_suspendu -> fonds retires, equity 0 ;
    #   (c) cycle_vie[bot].etat == "kill"        -> le bot est mort, meme s'il traine
    #       encore dans le registre.
    # Defaut d'origine : la liste tombait sur ["28_carry_hold"] en dur, si bien que le
    # 28 -- tue le 09/08 et desargente depuis le 07/08 -- restait annonce "en ARGENT
    # REEL" sur station.html et equipage.html. Un fallback en dur qui ressuscite un bot
    # mort est pire que pas de fallback du tout : ici, en cas de doute, la liste est VIDE.
    reel_suspendu, reel_motif = False, ""
    try:
        _stop = json.loads((Path("etat") / "reel_stop.json").read_text(encoding="utf-8"))
        if _stop.get("stop"):
            reel_suspendu = True
            reel_motif = _stop.get("motif") or "kill-switch etat/reel_stop.json actif"
    except (OSError, ValueError):
        pass
    try:
        _cfg = json.loads(Path("portefeuille.reel.json").read_text(encoding="utf-8"))
        if _cfg.get("reel_suspendu"):
            reel_suspendu = True
            reel_motif = reel_motif or "reel_suspendu dans portefeuille.reel.json"
        reels_list = [] if reel_suspendu else list((_cfg.get("bots") or {}).keys())
    except (OSError, ValueError):
        reels_list = []
    reels_list = [b for b in reels_list
                  if (cv["bots"].get(b) or {}).get("etat") != "kill"]

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
        "cycle_vie": cv["bots"],
        "reels": reels_list,
        "reel_suspendu": reel_suspendu,
        "reel_motif": reel_motif,
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
