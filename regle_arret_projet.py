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

LE CRITERE, FIGE, NON REVISABLE
--------------------------------
    Au 31/12/2026 :
      POURSUITE  si capital disponible >= 4 500 $
                    ET au moins une strategie a passe la gate
                    ET elle est executable a ce capital
      ARRET      sinon.

    4 500 $ = 2 800 $ (bot 30 : frais <= 20 % de l'edge)
            + 1 700 $ (bot 31 : perte maximale <= 10 % du compte)

L'arret n'est pas un constat d'echec. C'est un constat de PORTEE : une strategie
correcte hors d'atteinte du capital disponible n'est pas une source de revenu.

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
ECHEANCE = "2026-12-31"
CAPITAL_CIBLE_USD = 4500.0
DETAIL_CIBLE = {
    "30_trend_following": {"minimum_usd": 2800.0,
                           "motif": "frais <= 20 % de l'edge (2,17 ordres/mois x 1 $)"},
    "31_variance_premium": {"minimum_usd": 1700.0,
                            "motif": "perte maximale <= 10 % du compte (spreads 2 $)"},
}
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
    fin = datetime.fromisoformat(ECHEANCE + "T23:59:59+00:00")
    jours = (fin - now).total_seconds() / 86400.0

    manque = max(0.0, CAPITAL_CIBLE_USD - cap)
    cap_ok = cap >= CAPITAL_CIBLE_USD
    strat_ok = bool(vertes)

    if jours > 0:
        verdict = "EN COURS"
        lecture = ("echeance dans %.0f j — capital %.0f $ / %.0f $ (%s), "
                   "strategies VERTES : %s"
                   % (jours, cap, CAPITAL_CIBLE_USD,
                      "atteint" if cap_ok else "il manque %.0f $" % manque,
                      ", ".join(vertes) if vertes else "aucune"))
    elif cap_ok and strat_ok:
        verdict = "POURSUITE"
        lecture = ("capital %.0f $ suffisant et strategie(s) validee(s) : %s"
                   % (cap, ", ".join(vertes)))
    else:
        raisons = []
        if not cap_ok:
            raisons.append("capital %.0f $ < %.0f $" % (cap, CAPITAL_CIBLE_USD))
        if not strat_ok:
            raisons.append("aucune strategie n'a passe la gate")
        verdict = "ARRET"
        lecture = "; ".join(raisons) + " — la branche trading automatise se ferme"

    res = {
        "date_pose": DATE_POSE,
        "echeance": ECHEANCE,
        "jours_restants": round(jours, 1),
        "capital_usd": cap,
        "capital_maj": maj,
        "capital_cible_usd": CAPITAL_CIBLE_USD,
        "capital_manquant_usd": round(manque, 2),
        "detail_cible": DETAIL_CIBLE,
        "strategies_vertes": vertes,
        "verdict": verdict,
        "lecture": lecture,
        "rappel": ("L'arret n'est pas un echec de methode : c'est un constat de "
                   "portee. Une strategie correcte hors d'atteinte du capital "
                   "disponible n'est pas une source de revenu."),
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
    print("REGLE D'ARRET DU PROJET — echeance %s (%s j)"
          % (r["echeance"], r["jours_restants"]))
    print("  verdict : %s" % r["verdict"])
    print("  %s" % r["lecture"])
    if r["capital_manquant_usd"] > 0:
        print("  il manque %.0f $ (facteur %.1f sur le capital actuel)"
              % (r["capital_manquant_usd"], r["capital_cible_usd"] / max(r["capital_usd"], 1)))
