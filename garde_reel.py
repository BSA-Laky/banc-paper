#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
garde_reel.py - GARDE-FOUS DU LIVRE REEL + GATE PAR DECOMPOSITION (29/07/2026)
==============================================================================
Corrige les 5 defauts de l'audit du 29/07 SANS TOUCHER au chemin d'execution
reel ni aux bots. Ce module ne fait que LIRE, MESURER et ANNOTER. Il ne passe
aucun ordre, ne modifie aucun etat de bot, ne change aucun statut de gate de sa
propre autorite : il ajoute des alertes et un verdict de decomposition.

CE QU'IL CORRIGE
----------------
D1  Le dashboard reel affichait +17,07 $ pour un compte a -0,91 $ : docs/reel.json
    tirait "global" de la somme des pnl_est du ledger interne. Desormais "global"
    vient de etat/reel_hl.json (verite du compte) ; l'estimation interne reste
    publiee sous "global_estimation_interne", etiquetee comme telle.
D2  Le ledger interne perdait 20,43 $ (CASHCAT ferme hors executeur, jamais
    journalise). On ne repare pas le ledger (chemin d'execution reel = intouchable
    tant que le bot 28 est arme) : on MESURE l'ecart a chaque passe et on alerte
    des qu'il depasse le seuil. Un ecart silencieux devient un ecart bruyant.
D3  L'executeur reel est reste aveugle 3 jours sans un seul signal. Alarme :
      - reconciliation HL perimee  -> ROUGE (l'executeur ne tourne plus du tout)
      - executeur vivant mais aucun fill depuis N heures alors que le paper a des
        positions ouvertes -> AVERTISSEMENT (effet des filtres, pas une panne)
    La distinction evite l'alerte permanente : les filtres reels (seuil funding
    3x le paper, fraicheur 2 h) peuvent legitimement ne rien laisser passer.
D4  L'Arbitre citait "28_carry : n=83, t=3,73, sain" le 29/07, soit les statistiques
    d'AVANT la coupure comptable du 26/07 (n officiel : 1). Cause : sa memoire
    longue (etat/memoire_arbitre.md) est ecrite par lui-meme et il la recite.
    arbitre_ia.py passe docs/brief.json EN ENTIER au modele : on y injecte donc un
    avertissement de donnees explicite, lu a chaque appel, qui perime sa memoire.
D5  La gate n'opposait AUCUNE raison de blocage au bot 28 (n=1) : _statut_bot()
    sort en avance sur la branche GRIS, raisons vide, et rien ne verifie qu'un bot
    declare dans portefeuille.reel.json satisfait ses propres criteres. On remplit
    les raisons manquantes et on ajoute la verification qui n'existait pas.

LA GATE PAR DECOMPOSITION
-------------------------
Le critere historique (t >= 2 sur le P&L par trade) est inatteignable pour cette
famille : mesure sur le mainnet, carry net +0,2075 $/episode contre un bruit de
prix de 11,17 $ -> ratio 0,019 -> il faudrait ~11 600 episodes, soit ~24 ans.
Ce n'est pas un critere prudent, c'est un compteur casse.

On decompose donc, ce que la comptabilite du 26/07 rend possible :
    rendement_net = PRIX + FUNDING - FRAIS
  * FUNDING  : quasi deterministe -> t >= 2 atteignable en ~2 semaines
  * PRIX     : doit etre indiscernable de zero (c'est la definition d'un livre
               neutre). IC95 de la moyenne doit contenir 0.
  * FRAIS    : deterministes, on verifie seulement que E[funding] > E[frais].
  * NEUTRALITE : ecart_neutralite <= 0,10 (le bot 28 est a 1,00, le 29 a 0,00).

VERT_DECOMPOSITION exige les quatre. Un bot qui gagne parce que le PRIX est allé
dans son sens n'est PAS promu : c'est du directionnel deguise, et c'est
exactement ce qui a produit les 10 pertes sur 11 du mainnet.

RECONSTRUCTION DES COMPOSANTES, SANS TOUCHER AUX BOTS
-----------------------------------------------------
Trade ne transporte que le pnl agrege. Mais la decomposition est recuperable
EXACTEMENT, sans modifier comptabilite.py ni banc_essai_paper_trading.py :

    PositionReelle.cloturer() : net = r_prix + funding_cumule - frais
    Trade.close(1 + net)      : pnl = size_usd * net
    donc  net    = pnl / size_usd                      (paper_trades.csv)
    et    r_prix = net - funding_cumule + frais        (etat_bot<N>.json)

funding_cumule est lu dans l'etat du bot AVANT la fermeture : ce module
photographie les positions ouvertes a chaque passe (etat/snap_positions.json) et
apparie les fermetures constatees dans le journal. Aucune donnee de marche
supplementaire, aucune approximation.

Appel : une ligne dans run_once.py, APRES produire_go_reel().
stdlib uniquement, jamais bloquant, lecture seule sur les etats des bots.
"""
from __future__ import annotations

import csv
import json
import math
import statistics
from datetime import datetime, timezone
from pathlib import Path

ETAT = Path("etat")
DOCS = Path("docs")

F_SNAP = ETAT / "snap_positions.json"
F_API_CREDIT = ETAT / "api_credit.json"
F_REGIME = ETAT / "regime_ia.json"
F_ECHECS = ("arbitre_echecs.json", "superviseur_echecs.json", "veilleur_echecs.json")
F_COMPOSANTES = ETAT / "composantes.csv"
F_DECOMPO = DOCS / "decomposition.json"
# ECRITURE A L'EPREUVE DE LA STATION (constate le 05/08/2026) : run_once.py
# REGENERE docs/reel.json et docs/go_reel.json a chaque passe (~15 min), tandis
# que ce module tourne toutes les ~30 min et est en pratique throttle a ~3 h par
# GitHub. Les corrections ecrites dans ces deux fichiers etaient donc effacees
# en quelques minutes : le dashboard est reste a +10,66 $ pendant 3 jours alors
# que le compte etait a -35,21 $. La verite doit vivre dans un fichier que
# personne d'autre n'ecrit, et les alertes doivent partir SANS passer par un
# fichier partage. C'est la meme lecon que le 17/07 : une alarme ne doit
# dependre d'aucun organe qu'elle surveille.
F_VERITE = DOCS / "verite.json"
F_REEL_HL = ETAT / "reel_hl.json"
F_REEL_TRADES = ETAT / "reel_trades.csv"
F_GO_REEL = DOCS / "go_reel.json"
F_REEL_JSON = DOCS / "reel.json"
F_BRIEF = DOCS / "brief.json"
F_PORTEFEUILLE = Path("portefeuille.reel.json")
F_CORRECTION = ETAT / "correction_comptable.json"
LEDGER_PAPER = Path("paper_trades.csv")

# -- seuils, tous explicites et pre-enregistres -------------------------------
AGE_RECONCIL_ROUGE_H = 6.0     # au-dela : l'executeur ne tourne plus
AGE_FILL_AVERT_H = 24.0        # au-dela, paper ouvert et zero fill : a verifier
ECART_LEDGER_ABS = 2.0         # $ : ecart ledger interne vs compte HL tolere
ECART_LEDGER_PCT = 0.005       # ou 0,5 % du depot, le plus grand des deux
N_MIN_DECOMPO = 20             # jambes fermees avant tout verdict
T_FUNDING_MIN = 2.0            # le funding doit etre significatif
T_PRIX_MAX = 1.96              # le prix doit rester dans l'IC95 de zero
NEUTRALITE_MAX = 0.10          # |expo nette| / expo brute

COLS = ["ts_cloture", "bot", "coin", "sens", "notionnel_usd", "maker",
        "r_net", "r_prix", "r_funding", "r_frais",
        "pnl_usd", "prix_usd", "funding_usd", "frais_usd"]


# ============================================================ utilitaires bas
def _lire_json(p, defaut=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return defaut


def _ecrire_json(p, d):
    try:
        Path(p).parent.mkdir(parents=True, exist_ok=True)
        Path(p).write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        pass


def _f(x, d=0.0):
    try:
        return float(x)
    except (TypeError, ValueError):
        return d


def _age_h(iso, maintenant=None):
    """Age en heures d'un horodatage ISO. None si illisible."""
    if not iso:
        return None
    try:
        d = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    ref = maintenant or datetime.now(timezone.utc)
    return (ref - d).total_seconds() / 3600.0


def _t_stat(xs):
    """t de Student de la moyenne contre zero. 0.0 si non calculable."""
    n = len(xs)
    if n < 2:
        return 0.0
    m = statistics.mean(xs)
    sd = statistics.stdev(xs)
    if sd <= 1e-15:
        return 0.0 if abs(m) <= 1e-15 else math.copysign(99.99, m)
    return max(-99.99, min(99.99, m / (sd / math.sqrt(n))))


def _ic95(xs):
    """(borne_basse, borne_haute) de la moyenne. Approximation normale."""
    n = len(xs)
    if n < 2:
        return (0.0, 0.0)
    m = statistics.mean(xs)
    demi = 1.96 * statistics.stdev(xs) / math.sqrt(n)
    return (m - demi, m + demi)


def _bots_reels():
    cfg = _lire_json(F_PORTEFEUILLE, {}) or {}
    return list((cfg.get("bots") or {}).keys())


def _depot():
    return _f((_lire_json(F_PORTEFEUILLE, {}) or {}).get("depot_usdc"), 0.0)


# =================================================== 1. photographie des etats
def _etats_bots():
    """{bot: {"positions": {...}, "ecart_neutralite": x}} pour tout etat_bot*.json
    au format comptabilite (cle "positions")."""
    out = {}
    if not ETAT.is_dir():
        return out
    for p in sorted(ETAT.glob("etat_bot*.json")):
        d = _lire_json(p)
        if not isinstance(d, dict) or not isinstance(d.get("positions"), dict):
            continue
        # etat_bot28.json -> 28 ; le nom complet du bot vient du journal, on garde
        # le suffixe numerique comme cle d'appariement.
        suffixe = p.stem.replace("etat_bot", "")
        out[suffixe] = {"positions": d["positions"],
                        "ecart_neutralite": _f(d.get("ecart_neutralite"), 0.0),
                        "exposition_nette": _f(d.get("exposition_nette"), 0.0)}
    return out


def _photographier(etats):
    """Ecrit la photo courante et renvoie la PRECEDENTE (celle d'avant la passe)."""
    precedente = _lire_json(F_SNAP, {}) or {}
    courante = {"ts": datetime.now(timezone.utc).isoformat(), "bots": {}}
    for suffixe, e in etats.items():
        courante["bots"][suffixe] = {
            coin: {"funding_cumule": _f(v.get("funding_cumule")),
                   "notionnel": _f(v.get("notionnel")),
                   "mark_entree": _f(v.get("mark_entree")),
                   "side": int(_f(v.get("side"), 0)),
                   "maker": bool(v.get("maker")),
                   "ouverte_le": v.get("ouverte_le")}
            for coin, v in e["positions"].items() if isinstance(v, dict)}
        courante["bots"][suffixe]["_ecart_neutralite"] = e["ecart_neutralite"]
    _ecrire_json(F_SNAP, courante)
    return (precedente.get("bots") or {})


# ============================================ 2. reconstruction des composantes
def _composantes_deja_vues():
    vues = set()
    if not F_COMPOSANTES.exists():
        return vues
    try:
        with F_COMPOSANTES.open(newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                vues.add((r.get("ts_cloture"), r.get("bot"), r.get("coin")))
    except OSError:
        pass
    return vues


def _fermetures_recentes(limite=400):
    """Derniers trades FERMES du journal paper, les plus recents en dernier."""
    if not LEDGER_PAPER.exists():
        return []
    try:
        with LEDGER_PAPER.open(newline="", encoding="utf-8") as fh:
            lignes = [r for r in csv.DictReader(fh)
                      if r.get("status") == "closed"
                      and str(r.get("pnl") or "") not in ("", "None")]
    except OSError:
        return []
    return lignes[-limite:]


def _coin_et_sens(market):
    """'CASHCAT-short' -> ('CASHCAT', -1). Renvoie (None, 0) si non reconnu."""
    s = str(market or "")
    if s.endswith("-short"):
        return s[:-6], -1
    if s.endswith("-long"):
        return s[:-5], 1
    return None, 0


def _frais_de(maker):
    # memes constantes que comptabilite.py (FRAIS_PAR_JAMBE / FRAIS_MAKER), x2 (A-R)
    return 2.0 * (0.00015 if maker else 0.00045)


def _reconstruire(snap_precedent):
    """Apparie les fermetures du journal avec la photo d'avant et ecrit les
    composantes exactes. Renvoie le nombre de lignes ajoutees."""
    vues = _composantes_deja_vues()
    nouvelles = []
    for r in _fermetures_recentes():
        bot = r.get("bot") or ""
        ts = r.get("closed_at") or ""
        coin, sens = _coin_et_sens(r.get("market"))
        if not coin or (ts, bot, coin) in vues:
            continue
        # le suffixe d'etat : '28_carry_hold' -> '28'
        suffixe = bot.split("_", 1)[0]
        pos = (snap_precedent.get(suffixe) or {}).get(coin)
        if not isinstance(pos, dict):
            continue  # position jamais photographiee : on ne devine pas
        taille = _f(r.get("size_usd"))
        pnl = _f(r.get("pnl"))
        if taille <= 0:
            continue
        r_net = pnl / taille
        r_funding = _f(pos.get("funding_cumule"))
        r_frais = _frais_de(pos.get("maker"))
        r_prix = r_net - r_funding + r_frais       # identite exacte, cf. docstring
        nouvelles.append({
            "ts_cloture": ts, "bot": bot, "coin": coin,
            "sens": "short" if sens < 0 else "long",
            "notionnel_usd": round(taille, 4),
            "maker": int(bool(pos.get("maker"))),
            "r_net": round(r_net, 8), "r_prix": round(r_prix, 8),
            "r_funding": round(r_funding, 8), "r_frais": round(r_frais, 8),
            "pnl_usd": round(pnl, 6),
            "prix_usd": round(r_prix * taille, 6),
            "funding_usd": round(r_funding * taille, 6),
            "frais_usd": round(-r_frais * taille, 6)})
        vues.add((ts, bot, coin))
    if not nouvelles:
        return 0
    try:
        ETAT.mkdir(parents=True, exist_ok=True)
        neuf = not F_COMPOSANTES.exists()
        with F_COMPOSANTES.open("a", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=COLS)
            if neuf:
                w.writeheader()
            w.writerows(nouvelles)
    except OSError:
        return 0
    return len(nouvelles)


# ================================================ 3. la gate par decomposition
def _charger_composantes():
    par_bot = {}
    if not F_COMPOSANTES.exists():
        return par_bot
    try:
        with F_COMPOSANTES.open(newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                par_bot.setdefault(r["bot"], []).append(r)
    except (OSError, KeyError):
        pass
    return par_bot


def gate_decomposition(etats):
    """Verdict par bot sur la decomposition. Ne modifie aucun statut existant :
    publie un verdict PARALLELE, que l'humain et la gate peuvent lire."""
    par_bot = _charger_composantes()
    neutralites = {s: e["ecart_neutralite"] for s, e in etats.items()}
    out = {}
    for bot, rows in sorted(par_bot.items()):
        fund = [_f(r["r_funding"]) for r in rows]
        prix = [_f(r["r_prix"]) for r in rows]
        frais = [_f(r["r_frais"]) for r in rows]
        n = len(rows)
        t_f = _t_stat(fund)
        t_p = _t_stat(prix)
        lo, hi = _ic95(prix)
        e_fund = statistics.mean(fund) if fund else 0.0
        e_frais = statistics.mean(frais) if frais else 0.0
        neutre = neutralites.get(bot.split("_", 1)[0])

        raisons = []
        if n < N_MIN_DECOMPO:
            raisons.append("n %d < %d jambes fermees" % (n, N_MIN_DECOMPO))
        if t_f < T_FUNDING_MIN:
            raisons.append("funding t %.2f < %.1f (capture non significative)" % (t_f, T_FUNDING_MIN))
        if abs(t_p) >= T_PRIX_MAX:
            raisons.append("prix t %.2f : IC95 [%.4f ; %.4f] ne contient pas 0 "
                           "-> directionnel deguise" % (t_p, lo, hi))
        if e_fund <= e_frais:
            raisons.append("E[funding] %.5f <= E[frais] %.5f" % (e_fund, e_frais))
        if neutre is None:
            raisons.append("neutralite inconnue (etat du bot illisible)")
        elif neutre > NEUTRALITE_MAX:
            raisons.append("ecart de neutralite %.2f > %.2f (livre nu)" % (neutre, NEUTRALITE_MAX))

        out[bot] = {
            "n_jambes": n,
            "funding": {"moyenne_pct": round(100 * e_fund, 5), "t": round(t_f, 2)},
            "prix": {"moyenne_pct": round(100 * statistics.mean(prix), 5) if prix else 0.0,
                     "t": round(t_p, 2),
                     "ic95_pct": [round(100 * lo, 5), round(100 * hi, 5)]},
            "frais": {"moyenne_pct": round(100 * e_frais, 5)},
            "esperance_nette_pct": round(100 * (e_fund - e_frais), 5),
            "ecart_neutralite": neutre,
            "verdict": "VERT_DECOMPOSITION" if not raisons else "EN COURS",
            "raisons": raisons,
        }
    return out


# ================================================== 4. garde-fous du livre reel
def _estimation_interne():
    """Somme des pnl_est du LEDGER D'EXECUTION (etat/reel_trades.csv).

    C'est ce chiffre-la qui etait publie en titre du dashboard reel (+17,07 $).
    On le recalcule TOUJOURS depuis sa source, jamais depuis docs/reel.json :
    sinon, des la premiere reecriture, on comparerait la verite a elle-meme et
    l'ecart disparaitrait silencieusement -- exactement le defaut qu'on corrige.
    """
    if not F_REEL_TRADES.exists():
        return None, 0
    total, n = 0.0, 0
    try:
        with F_REEL_TRADES.open(newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                if r.get("action") != "close":
                    continue
                v = str(r.get("pnl_est_usd") or "").strip()
                if v in ("", "None"):
                    continue
                total += _f(v)
                n += 1
    except OSError:
        return None, 0
    return total, n


def _garde_d1_d2(alertes):
    """D1 : la verite du compte devient le chiffre affiche.
       D2 : l'ecart ledger interne vs compte devient bruyant, a CHAQUE passe."""
    hl = _lire_json(F_REEL_HL)
    reel = _lire_json(F_REEL_JSON)
    if not isinstance(hl, dict) or hl.get("pnl_compte") is None:
        return
    verite = _f(hl.get("pnl_compte"))
    interne, n_closes = _estimation_interne()
    if isinstance(reel, dict) and isinstance(reel.get("global"), dict):
        seuil = max(ECART_LEDGER_ABS, ECART_LEDGER_PCT * _depot())
        ecart = (interne - verite) if interne is not None else 0.0
        # D1 : on retitre. L'estimation interne reste, explicitement etiquetee.
        reel["global_estimation_interne"] = {
            "source": "etat/reel_trades.csv (journal de l'executeur)",
            "n_fermetures": n_closes,
            "pnl_total": (round(interne, 3) if interne is not None else None),
            "_note": "ESTIMATION interne au mark : hors frais, hors funding, aveugle "
                     "aux fermetures hors executeur. NE PAS lire comme le P&L du compte.",
        }
        reel["global"] = {
            "source": "etat/reel_hl.json (compte Hyperliquid)",
            "n": int(_f(hl.get("n_fills"))),
            "pnl_total": round(verite, 2),
            "prix_realise": _f(hl.get("realized_fills")),
            "funding": _f(hl.get("funding_net")),
            "frais": -abs(_f(hl.get("fees_total"))),
            "latent": _f(hl.get("unrealized_total")),
            "equity": _f(hl.get("equity")),
            "depot": _f(hl.get("depot_usdc")),
            "esp": None, "t_stat": None, "taux_reussite": None,
            "_note": "P&L du COMPTE = equity - depots nets. Verifie par identite "
                     "prix + funding - frais + latent.",
        }
        reel["ecart_interne_vs_hl"] = round(-ecart, 2)
        _ecrire_json(F_REEL_JSON, reel)
        if interne is not None and abs(ecart) > seuil:
            alertes.append(
                "LEDGER REEL FAUX de %+.2f $ : le journal d'execution totalise %+.2f $ "
                "sur %d fermeture(s), le compte Hyperliquid est a %+.2f $ (seuil %.2f $). "
                "Des fermetures hors executeur ne sont pas journalisees. La verite "
                "affichee est etat/reel_hl.json ; le journal reste une estimation."
                % (ecart, interne, n_closes, verite, seuil))
    # residu d'identite comptable : si HL ne se boucle pas, on veut le savoir
    residu = hl.get("residu_identite")
    if residu is not None and abs(_f(residu)) > 1.0:
        alertes.append("RECONCILIATION HL : residu d'identite %+.2f $ (depot/retrait "
                       "non reporte, ou champ mal lu)." % _f(residu))


def _garde_d3(alertes, avertissements, etats):
    """D3 : l'executeur reel ne peut plus se taire sans que rien ne le dise."""
    hl = _lire_json(F_REEL_HL, {}) or {}
    age_reconcil = _age_h(hl.get("ts"))
    if age_reconcil is None or age_reconcil > AGE_RECONCIL_ROUGE_H:
        alertes.append(
            "EXECUTEUR REEL MUET : derniere reconciliation HL il y a %s. "
            "L'executeur ne tourne plus (secret, verrou live, ou exception silencieuse) "
            "-- le livre reel n'est plus surveille."
            % ("jamais" if age_reconcil is None else "%.0f h" % age_reconcil))
        return

    # l'executeur tourne : un long silence est alors un effet de FILTRE, pas une panne
    dernier = None
    if F_REEL_TRADES.exists():
        try:
            with F_REEL_TRADES.open(newline="", encoding="utf-8") as fh:
                for r in csv.DictReader(fh):
                    if r.get("ts"):
                        dernier = r["ts"]
        except OSError:
            pass
    age_fill = _age_h(dernier)
    reels = _bots_reels()
    paper_ouvert = {}
    for b in reels:
        suffixe = b.split("_", 1)[0]
        pos = (etats.get(suffixe) or {}).get("positions") or {}
        if pos:
            paper_ouvert[b] = sorted(pos)
    if paper_ouvert and (age_fill is None or age_fill > AGE_FILL_AVERT_H):
        avertissements.append(
            "EXECUTEUR REEL SILENCIEUX : aucun ordre depuis %s alors que le paper tient "
            "%s. L'executeur tourne (reconciliation il y a %.0f h) : ce sont les filtres "
            "reels (seuil funding %.4f vs paper, fraicheur %.0f h) qui bloquent. "
            "Le livre reel n'est donc PAS un miroir du paper."
            % ("jamais" if age_fill is None else "%.0f h" % age_fill,
               " ; ".join("%s=%s" % (b, ",".join(c)) for b, c in paper_ouvert.items()),
               age_reconcil,
               _f((_lire_json(F_PORTEFEUILLE, {}) or {}).get("seuil_funding_reel"), 0.0),
               _f((_lire_json(F_PORTEFEUILLE, {}) or {}).get("age_max_entree_h"), 0.0)))


def _garde_d5(alertes, gate, decompo):
    """D5 : un bot en argent reel doit satisfaire ses propres criteres, et une
    branche de sortie anticipee ne doit plus produire un dossier vide."""
    bots = (gate.get("bots") or {})
    # (a) raisons manquantes : la branche GRIS de _statut_bot sort avant de les ecrire
    try:
        from moniteur_go_reel import GATE, DEFAUT
    except Exception:  # noqa: BLE001
        GATE, DEFAUT = {}, {"n_go": 100, "jours_min": 28}
    for b, v in bots.items():
        if v.get("raisons") or v.get("statut") == "VERT":
            continue
        cfg = GATE.get(b, DEFAUT)
        manque = []
        n = int(_f(v.get("n")))
        fwd = _f(v.get("jours_forward"))
        if n < int(cfg.get("n_go", 100)):
            manque.append("n %d < n_go %d" % (n, int(cfg.get("n_go", 100))))
        if _f(v.get("t_stat")) < 2.0:
            manque.append("t %.2f < 2" % _f(v.get("t_stat")))
        if fwd < _f(cfg.get("jours_min", 28)):
            manque.append("forward %.0f j < %.0f j" % (fwd, _f(cfg.get("jours_min", 28))))
        if manque:
            v["raisons"] = manque

    # (b) LA VERIFICATION QUI MANQUAIT : bot declare reel mais statut non VERT
    for b in _bots_reels():
        v = bots.get(b)
        if not isinstance(v, dict):
            alertes.append(
                "ARGENT REEL NON COUVERT : %s est declare dans portefeuille.reel.json "
                "mais la gate ne le mesure pas (aucune statistique). Capital engage sans "
                "critere applicable." % b)
            continue
        if v.get("statut") != "VERT":
            d = decompo.get(b) or {}
            alertes.append(
                "ARGENT REEL NON JUSTIFIE : %s est en mainnet avec statut %s "
                "(n=%s, t=%s, forward=%s j) -- raisons : %s. Decomposition : %s. "
                "Aucun critere chiffre du projet n'autorise ce capital engage."
                % (b, v.get("statut"), v.get("n"), v.get("t_stat"), v.get("jours_forward"),
                   " ; ".join(v.get("raisons") or ["(aucune)"]),
                   d.get("verdict", "pas encore mesuree")))


def mode_economie(avertissements):
    """MODE ATTENTE DE RECHARGE (02/08/2026).

    Sans credit API, les agents LLM n'entrent PAS dans leur branche dormante :
    ils appellent l'API, prennent une erreur HTTP, et incrementent leur compteur
    d'echecs. Consequences si on ne fait rien :
      - arbitre_ia.py ouvre une issue GitHub a 2 echecs consecutifs ;
      - alerte_issue.py en ouvre une PAR JOUR tant que echecs >= 1 et avis > 24 h.
    Le Commandant recevrait une alerte quotidienne pour une situation connue,
    volontaire et sans gravite. L'alerte perdrait tout son sens (c'est le defaut
    exact qu'on a corrige le 29/07 : une alarme qui crie tout le temps ne dit rien).

    Ce mode ne MASQUE pas une panne : il la REQUALIFIE. Tant que
    etat/api_credit.json porte {"epuise": true}, l'absence d'avis IA est un etat
    ATTENDU, pas un incident. Les compteurs sont remis a zero avec un motif
    explicite, l'avis de regime est maintenu a NEUTRE (les bots qui le lisent
    retombent sur leur regle deterministe), et l'etat est publie sur les
    dashboards. Des que le fichier repasse a {"epuise": false}, tout redevient
    normal et un vrai echec redeviendra une vraie alerte.
    """
    d = _lire_json(F_API_CREDIT, {}) or {}
    if not d.get("epuise"):
        return None
    depuis = str(d.get("depuis") or "")[:10]
    motif = "API sans credit depuis le %s - EN ATTENTE DE RECHARGE (etat voulu)" % depuis
    now = datetime.now(timezone.utc)
    for f in F_ECHECS:
        _ecrire_json(ETAT / f, {"consecutifs": 0, "motif": motif,
                                "maj": now.isoformat(), "mode": "attente_recharge"})
    # avis de regime maintenu NEUTRE et frais : les bots qui le lisent (27e/27f)
    # retombent proprement sur leur signal deterministe au lieu de rejouer un
    # avis perime, et le garde-fou "avis vieux de X h" ne se declenche plus.
    _ecrire_json(F_REGIME, {"date": now.isoformat().replace("+00:00", "Z"),
                            "regime": "neutre", "confiance": 0.0,
                            "resume": "Agents IA dormants - en attente de recharge API. "
                                      "Aucun avis produit : regime force a neutre.",
                            "mode": "attente_recharge"})
    msg = ("STATION EN MODE ECONOMIE : agents IA (Arbitre, Superviseur, Veilleur, "
           "avis par piece) dormants faute de credit API depuis le %s. Le banc "
           "deterministe tourne normalement. Ce n'est PAS une panne." % depuis)
    avertissements.append(msg)
    return msg


def _garde_d4(decompo):
    """D4 : perimer la memoire de l'Arbitre par une donnee qu'il lit chaque jour.

    arbitre_ia.py transmet docs/brief.json EN ENTIER au modele, mais ne transmet
    PAS gate['bots']. On injecte donc l'avertissement dans le brief, ou il sera lu."""
    corr = _lire_json(F_CORRECTION, {}) or {}
    brief = _lire_json(F_BRIEF)
    if not isinstance(brief, dict) or not corr:
        return
    statuts = brief.get("statuts") or {}
    officiels = {b: {"n": v.get("n"), "t": v.get("t"), "esperance": v.get("esperance")}
                 for b, v in statuts.items() if isinstance(v, dict)}
    brief["avertissement_donnees"] = {
        "coupure_comptable": str(corr.get("date"))[:10],
        "bots_concernes": corr.get("bots"),
        "regle": ("Toute statistique de ces bots ANTERIEURE a la coupure est INVALIDE : "
                  "elle mesurait abs(funding) sans terme de prix. Ne JAMAIS la citer, "
                  "meme si elle figure dans ta memoire longue."),
        "n_officiels_post_coupure": officiels,
        "exemple_de_donnee_perimee": ("28_carry_hold n=83 t=3,73 E=4,01 -- ce sont "
                                      "exactement les 83 trades ECARTES le 26/07. "
                                      "Si tu lis cela quelque part, c'est perime."),
        "verdicts_decomposition": {b: d.get("verdict") for b, d in decompo.items()},
    }
    _ecrire_json(F_BRIEF, brief)


def _alerter_github(alertes):
    """Ouvre UNE issue par jour si une alerte rouge est active.

    Volontairement redondant avec alerte_issue.py : celui-ci lit go_reel.json,
    que la station reecrit. Si nos alertes n'y survivent pas, elles ne sont
    jamais notifiees. Ici on parle directement a l'API GitHub.
    Dedup par titre : une seule issue par jour, jamais de spam.
    """
    import os
    import urllib.error
    import urllib.request
    tok = os.environ.get("GITHUB_TOKEN", "")
    if not tok:
        return
    depot = os.environ.get("GITHUB_REPOSITORY", "BSA-Laky/banc-paper")
    api = "https://api.github.com/repos/%s/issues" % depot
    titre = "Garde du livre reel — %s" % datetime.now(timezone.utc).date().isoformat()

    def _req(url, data=None, methode="GET"):
        r = urllib.request.Request(
            url, method=methode,
            data=(json.dumps(data).encode("utf-8") if data is not None else None),
            headers={"Authorization": "Bearer " + tok,
                     "Accept": "application/vnd.github+json",
                     "User-Agent": "banc-paper-garde"})
        try:
            with urllib.request.urlopen(r, timeout=15) as rep:
                return json.loads(rep.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
                ValueError, OSError) as e:
            print("[garde_reel] API GitHub KO : %s" % e, flush=True)
            return None

    ouvertes = _req(api + "?state=open&per_page=50") or []
    if any(isinstance(i, dict) and i.get("title") == titre for i in ouvertes):
        return
    corps = ["_Constat automatique du garde. La gate decide, pas ce message._", "",
             "## Alertes actives"] + ["- " + a for a in alertes] + [
        "", "Verite du compte : https://bsa-laky.github.io/banc-paper/verite.json",
        "", "_docs/reel.json est regenere par la station et perd ces corrections :",
        "s'y fier pour le P&L reel serait une erreur._"]
    _req(api, data={"title": titre, "body": "\n".join(corps),
                    "labels": ["alerte-banc"]}, methode="POST")


# ============================================================== point d'entree
def executer():
    """Une passe complete. Jamais bloquant : toute exception est capturee ici."""
    etats = _etats_bots()
    snap_precedent = _photographier(etats)
    ajoutees = _reconstruire(snap_precedent)
    decompo = gate_decomposition(etats)

    alertes, avertissements = [], []
    try:
        eco = mode_economie(avertissements)
    except Exception as e:  # noqa: BLE001
        eco = None
        print("[garde_reel] mode economie a leve : %s" % e, flush=True)
    try:
        _garde_d1_d2(alertes)
    except Exception as e:  # noqa: BLE001
        print("[garde_reel] D1/D2 a leve : %s" % e, flush=True)
    try:
        _garde_d3(alertes, avertissements, etats)
    except Exception as e:  # noqa: BLE001
        print("[garde_reel] D3 a leve : %s" % e, flush=True)

    gate = _lire_json(F_GO_REEL)
    if isinstance(gate, dict):
        try:
            _garde_d5(alertes, gate, decompo)
        except Exception as e:  # noqa: BLE001
            print("[garde_reel] D5 a leve : %s" % e, flush=True)
        gate["decomposition"] = decompo
        gate["alertes"] = sorted(set(list(gate.get("alertes") or []) + alertes))
        gate["avertissements"] = sorted(set(list(gate.get("avertissements") or [])
                                            + avertissements))
        gate["mode_station"] = ("attente_recharge_api" if eco else "normal")
        gate["garde_reel"] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "mode_station": ("attente_recharge_api" if eco else "normal"),
            "composantes_ajoutees": ajoutees,
            "n_alertes": len(alertes),
            "n_avertissements": len(avertissements),
            "criteres": {"t_funding_min": T_FUNDING_MIN, "t_prix_max": T_PRIX_MAX,
                         "neutralite_max": NEUTRALITE_MAX, "n_min": N_MIN_DECOMPO},
        }
        _ecrire_json(F_GO_REEL, gate)

    _ecrire_json(F_DECOMPO, {"ts": datetime.now(timezone.utc).isoformat(),
                             "criteres": {"funding_t_min": T_FUNDING_MIN,
                                          "prix_ic95_contient_0": True,
                                          "neutralite_max": NEUTRALITE_MAX,
                                          "n_min_jambes": N_MIN_DECOMPO},
                             "bots": decompo})
    try:
        _garde_d4(decompo)
    except Exception as e:  # noqa: BLE001
        print("[garde_reel] D4 a leve : %s" % e, flush=True)

    # le mode station doit etre LISIBLE sur les tableaux de bord, pas seulement
    # dans les logs : brief.json alimente la Station et l'Equipage.
    try:
        b = _lire_json(F_BRIEF)
        if isinstance(b, dict):
            b["mode_station"] = {
                "mode": "attente_recharge_api" if eco else "normal",
                "message": eco or "Agents IA operationnels.",
                "banc_deterministe": "actif",
                "maj": datetime.now(timezone.utc).isoformat()}
            if eco:
                b["sante_equipage"] = {**(b.get("sante_equipage") or {}),
                                       "problemes": [], "mode": "attente_recharge_api"}
            _ecrire_json(F_BRIEF, b)
    except Exception as e:  # noqa: BLE001
        print("[garde_reel] mode_station brief a leve : %s" % e, flush=True)

    # --- SORTIE A L'EPREUVE DE LA STATION -----------------------------------
    hl = _lire_json(F_REEL_HL, {}) or {}
    interne, n_cl = _estimation_interne()
    _ecrire_json(F_VERITE, {
        "ts": datetime.now(timezone.utc).isoformat(),
        "_lire_ceci": ("Fichier ecrit UNIQUEMENT par garde_reel.py. docs/reel.json "
                       "et docs/go_reel.json sont regeneres par la station toutes "
                       "les 15 min et perdent ces corrections : ne pas s'y fier "
                       "pour le P&L reel."),
        "pnl_compte_reel": hl.get("pnl_compte"),
        "equity": hl.get("equity"), "depot": hl.get("depot_usdc"),
        "prix_realise": hl.get("realized_fills"), "funding": hl.get("funding_net"),
        "frais": hl.get("fees_total"),
        "estimation_interne_journal": (round(interne, 3) if interne is not None else None),
        "ecart_journal_vs_compte": (round(interne - _f(hl.get("pnl_compte")), 2)
                                    if interne is not None else None),
        "mode_station": "attente_recharge_api" if eco else "normal",
        "decomposition": decompo, "alertes": alertes, "avertissements": avertissements})

    # alerte directe : ne transite par AUCUN fichier que la station reecrit
    if alertes:
        _alerter_github(alertes)
    for a in alertes:
        print("[garde_reel] ALERTE : %s" % a, flush=True)
    for a in avertissements:
        print("[garde_reel] avertissement : %s" % a, flush=True)
    print("[garde_reel] %d composante(s) ajoutee(s) ; %d bot(s) en decomposition ; "
          "%d alerte(s)" % (ajoutees, len(decompo), len(alertes)), flush=True)
    return {"decomposition": decompo, "alertes": alertes,
            "avertissements": avertissements, "composantes_ajoutees": ajoutees}


if __name__ == "__main__":
    r = executer()
    for b, d in sorted(r["decomposition"].items()):
        print("%-22s n=%-4d funding t=%-6.2f prix t=%-6.2f neutralite=%-5s %s"
              % (b, d["n_jambes"], d["funding"]["t"], d["prix"]["t"],
                 d["ecart_neutralite"], d["verdict"]))
        for x in d["raisons"]:
            print("    - %s" % x)
