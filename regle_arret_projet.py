#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
regle_arret_projet.py - LA GATE DU PROJET LUI-MEME (figee le 15/08/2026)
=========================================================================
POURQUOI CE FICHIER EXISTE
--------------------------
Le banc tue ses bots selon une regle fixee d'avance. Le PROJET, lui, n'avait
aucune regle d'arret : il pouvait continuer indefiniment tant qu'une idee neuve
se presentait. C'est exactement l'angle mort que le dispositif est cense
prevenir, applique a l'echelle au-dessus.

CE QUE LA MESURE DU 15/08 A CHANGE
-----------------------------------
Le critere naturel aurait ete "une strategie a-t-elle passe la gate ?". La mesure
des couts d'execution du book (voir Bot fi/COUTS_EXECUTION_BOOK_2026-08-15.md)
montre que ce n'est PAS la bonne question :

    Bot 30 trend-following : Sharpe 0,82 sur 359 mois, t +4,47. L'edge tient.
    Mais a 900 $ les commissions mangent 63 % de l'edge (Sharpe 0,30, 16 $/an),
    et les 14 ETF sont interdits aux particuliers de l'UE (PRIIPs).
    Bot 31 prime de variance : a 900 $, deux spreads mettent 93 % du compte a
    risque sur une seule echeance.

Autrement dit : **ce qui bloque n'est pas l'edge, c'est le capital.** Le critere
d'arret doit donc porter sur le capital, pas sur la recherche.

LE CRITERE — REVISE LE 15/08/2026 (memes donnees, meilleure regle)
------------------------------------------------------------------
La v1 posait une DATE : arret au 31/12/2026 si le capital n'atteignait pas
4 500 $. Revise le jour meme, apres avoir chiffre honnetement les voies de
financement disponibles : aucune ne pouvait apporter 3 600 $ en 138 jours.

Une echeance qu'on ne peut pas tenir ne mesure rien. Elle fabrique un faux
echec, et surtout elle cree la MAUVAISE incitation : quand la date approche et
que le capital manque, la tentation est de compenser par du risque (levier,
strategie non validee, retour en reel "pour accelerer"). C'est le chemin le plus
court de 900 $ vers 0 $.

Donc le critere n'est plus une date. C'est un DECLENCHEUR de capital, en deux
paliers, sans limite de temps :

    PALIER 1 — 1 700 $  : le bot 31 (prime de variance) devient deployable
                          (perte maximale <= 10 % du compte, spreads de 2 $)
    PALIER 2 — 4 500 $  : le book complet 30+31 devient deployable
                          (= 2 800 $ pour le bot 30, frais <= 20 % de l'edge ;
                           confirme independamment par la taille de lot : 4 202 $)

Tant que le palier 1 n'est pas atteint : le banc MESURE, il ne DEPLOIE PAS, et
il ne coute rien (couche IA payante coupee le 15/08, 21,27 $/mois economises).

CE QUE CE FICHIER N'EST PAS
---------------------------
Ce n'est pas un abandon deguise. Le projet ne meurt pas d'un calendrier : il
attend, a cout nul, avec un plan d'execution pret (13 tickers UCITS verifies,
turnover mesure, planchers chiffres). Le jour ou le capital arrive, il n'y a
rien a redecouvrir.

La seule discipline qui reste, et elle est dure : AUCUN argent reel avant le
palier 1, quelle que soit la tentation.

MISE A JOUR DU CAPITAL
-----------------------
Ce module ne devine pas ton capital : les fonds ont ete retires le 07/08 et le
banc ne les voit plus. Il lit `etat/capital_declare.json` :

    {"capital_usd": 900, "maj": "2026-08-15", "note": "hors marche depuis le 07/08"}

Tant que ce fichier n'existe pas, il prend 900 $ (947,15 $ deposes - 35,21 $ de
P&L reel - retraits), ce qui est la meilleure estimation connue.

stdlib uniquement.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ETAT = Path("etat")
PUBLIC = Path("docs") / "regle_arret.json"

# --- le critere. Modifier ces constantes invaliderait la regle. -------------
DATE_POSE = "2026-08-15"
DATE_REVISION = "2026-08-15"      # date -> declencheur, cf. en-tete
PALIERS = [
    (1700.0, "31_variance_premium",
     "bot 31 deployable : perte maximale <= 10 % du compte (spreads de 2 $)"),
    (4500.0, "book 30+31",
     "book complet : 2 800 $ (frais <= 20 % de l'edge du bot 30) + 1 700 $"),
]
CAPITAL_CIBLE_USD = PALIERS[-1][0]
CAPITAL_DEFAUT = 900.0


def _lire(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def capital_declare() -> tuple[float, str]:
    d = _lire(ETAT / "capital_declare.json")
    try:
        return float(d["capital_usd"]), str(d.get("maj", "?"))
    except (KeyError, TypeError, ValueError):
        return CAPITAL_DEFAUT, "defaut (947,15 $ deposes - 35,21 $ de P&L reel)"


def _strategies_vertes() -> list[str]:
    """Bots au statut VERT dans le dernier verdict de la gate."""
    for p in (Path("docs") / "go_reel.json", ETAT / "go_reel.json"):
        g = _lire(p)
        if g:
            return sorted(b for b, v in (g.get("bots") or {}).items()
                          if v.get("statut") == "VERT")
    return []


def evaluer(ecrire: bool = True) -> dict:
    cap, maj = capital_declare()
    vertes = _strategies_vertes()
    now = datetime.now(timezone.utc)

    atteints = [p for p in PALIERS if cap >= p[0]]
    prochain = next((p for p in PALIERS if cap < p[0]), None)

    if prochain is None:
        verdict = "CAPITAL SUFFISANT"
        lecture = ("capital %.0f $ : tous les paliers sont franchis. Le deploiement "
                   "reste conditionne a une gate VERTE (%s)."
                   % (cap, ", ".join(vertes) if vertes else "aucune a ce jour"))
    else:
        seuil, quoi, motif = prochain
        verdict = "EN ATTENTE DE CAPITAL"
        lecture = ("capital %.0f $ — il manque %.0f $ (x%.1f) pour le palier %.0f $ : %s"
                   % (cap, seuil - cap, seuil / max(cap, 1), seuil, motif))

    res = {
        "date_pose": DATE_POSE,
        "date_revision": DATE_REVISION,
        "regle": "declencheur de capital, SANS date — une echeance intenable "
                 "fabrique un faux echec et pousse a compenser par du risque",
        "capital_usd": cap,
        "capital_maj": maj,
        "paliers": [{"seuil_usd": s_, "debloque": q, "motif": m,
                     "atteint": cap >= s_} for s_, q, m in PALIERS],
        "prochain_palier_usd": prochain[0] if prochain else None,
        "manque_usd": round(prochain[0] - cap, 2) if prochain else 0.0,
        "paliers_atteints": len(atteints),
        "strategies_vertes": vertes,
        "verdict": verdict,
        "lecture": lecture,
        "interdit": "AUCUN argent reel avant le palier 1, quelle que soit la tentation. "
                    "Le risque ne remplace pas le capital manquant.",
        "cout_du_banc": "0 $/mois depuis le 15/08 (couche IA payante coupee, "
                        "21,27 $/mois economises) — le projet peut attendre indefiniment",
        "ts": now.isoformat(),
    }
    if ecrire:
        for p in (ETAT / "regle_arret.json", PUBLIC):
            try:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(json.dumps(res, ensure_ascii=False, indent=1),
                             encoding="utf-8")
            except OSError:
                pass
    return res


if __name__ == "__main__":
    r = evaluer()
    print("REGLE D'ARRET DU PROJET — declencheur de capital (revise le %s)"
          % r["date_revision"])
    print("  verdict : %s" % r["verdict"])
    print("  %s" % r["lecture"])
    for p in r["paliers"]:
        print("    [%s] %6.0f $  %s" % ("x" if p["atteint"] else " ",
                                        p["seuil_usd"], p["debloque"]))
    print("  %s" % r["interdit"])
