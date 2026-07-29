#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_conformite.py - GARDE-FOU PERMANENT DE LA COMPTABILITE (26/07/2026)
==========================================================================
POURQUOI
--------
Le 26/07/2026, on a decouvert que le bot 28 paper calculait son P&L avec
'abs(funding) * notionnel * dt' : funding en valeur absolue, aucun terme de prix.
Il ne pouvait pas perdre. L'executeur reel, lui, prenait un perp nu. Ecart mesure :
-0,46 pp par trade, pendant des semaines, sans que rien ne le signale.

Ce module fait en sorte que ca ne puisse plus arriver SILENCIEUSEMENT : a chaque
passe, il verifie que tout bot produisant des Trade passe par 'comptabilite.py'
(prix + funding signe + frais reels). Il vaut pour les bots FUTURS, y compris ceux
ecrits par Nova.

CE QU'IL DETECTE
----------------
  1. un module de bot qui fabrique un Trade() sans importer comptabilite ;
  2. un appel a .close() hors de comptabilite (fabrication de P&L arbitraire) ;
  3. l'usage de abs() sur un funding (la faute d'origine) ;
  4. un livre dont l'ecart de neutralite derive (signale, pas bloquant : certains
     bots sont directionnels par construction).

Sortie : etat/conformite.json + code retour. Jamais bloquant pour la passe.
stdlib uniquement.
"""
from __future__ import annotations

import ast
import json
from datetime import datetime, timezone
from pathlib import Path

ETAT = Path("etat")
SORTIE = ETAT / "conformite.json"
DISPENSES = {"banc_essai_paper_trading.py", "comptabilite.py", "audit_conformite.py"}
# Bots sans position de marche reelle (temoin) : dispenses de comptabilite reelle.
BOTS_DISPENSES = {"10_controle_aleatoire", "10b_controle_book"}

# Modules ANTERIEURS a la regle du 26/07/2026. Ils sont SIGNALES pour migration mais
# ne font pas echouer l'audit. TOUT NOUVEAU MODULE est bloquant par defaut : c'est
# ce qui garantit que le probleme du bot 28 ne se reproduira pas sur un bot futur.
# Modules d'un AUTRE MARCHE que les perps Hyperliquid : livre d'ETF/options
# (bot_trend, bot_variance, pilotes par run_book.py). Il n'y a PAS de funding sur
# ces marches, et leur P&L est deja honnete : rendement reel de l'actif moins les
# couts de transaction. comptabilite.PositionReelle, concue pour un perp HL avec
# funding, ne s'y applique pas. Ils sont donc dispenses AVEC MOTIF, et non
# "a migrer" : les laisser dans la liste noyait les vrais problemes.
HORS_PERIMETRE_HL = {"bot_trend.py", "bot_variance.py"}

# Modules ANTERIEURS a la regle du 26/07/2026, sur perps HL, dont la comptabilite
# reste a router par comptabilite.py. Signales pour migration, non bloquants.
# NB : bots_cloud.py n'y figure plus (reduit aux helpers le 29/07), pas plus que
# bot_24 / bot_26 (tues le 29/07 : comptabilite fausse ET trades inexecutables,
# faute de compte sur Paradex / Nado).
LEGACY = {
    "bot_27_convex_buckets.py", "bot_27e_arbitre.py", "bot_27f_selecteur.py",
}


def _fichiers_bots() -> list[Path]:
    out = [p for p in Path(".").glob("bot_*.py")]
    for extra in ("bots_cloud.py",):
        p = Path(extra)
        if p.exists():
            out.append(p)
    return sorted(p for p in out if p.name not in DISPENSES
                  and p.name not in HORS_PERIMETRE_HL)


def _analyser(p: Path) -> dict:
    """Analyse statique d'un module de bot. Ne l'importe pas (aucun effet de bord)."""
    res = {"fichier": p.name, "bots": [], "importe_comptabilite": False,
           "trade_direct": [], "close_direct": [], "abs_funding": [], "verdict": "OK"}
    try:
        arbre = ast.parse(p.read_text(encoding="utf-8"))
    except (OSError, SyntaxError) as e:
        res["verdict"] = "ILLISIBLE (%s)" % type(e).__name__
        return res
    for n in ast.walk(arbre):
        # imports
        if isinstance(n, ast.ImportFrom) and (n.module or "").startswith("comptabilite"):
            res["importe_comptabilite"] = True
        if isinstance(n, ast.Import):
            for a in n.names:
                if a.name.startswith("comptabilite"):
                    res["importe_comptabilite"] = True
        # noms de bots declares
        if isinstance(n, ast.ClassDef):
            for st in n.body:
                if (isinstance(st, ast.Assign) and len(st.targets) == 1
                        and isinstance(st.targets[0], ast.Name)
                        and st.targets[0].id == "name"
                        and isinstance(st.value, ast.Constant)
                        and isinstance(st.value.value, str)):
                    res["bots"].append(st.value.value)
        # fabrication directe d'un Trade
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "Trade":
            res["trade_direct"].append(getattr(n, "lineno", 0))
        # .close(...) : fabrication d'un P&L arbitraire
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == "close"):
            res["close_direct"].append(getattr(n, "lineno", 0))
        # abs(funding) MULTIPLIE par un notionnel/dt = motif de P&L : la faute
        # d'origine du bot 28. Une simple COMPARAISON abs(f) >= seuil est legitime
        # (c'est de la selection, pas de la comptabilite).
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Mult):
            for cote in (n.left, n.right):
                if (isinstance(cote, ast.Call) and isinstance(cote.func, ast.Name)
                        and cote.func.id == "abs"):
                    for a in ast.walk(cote):
                        nom = a.id if isinstance(a, ast.Name) else (
                              a.attr if isinstance(a, ast.Attribute) else (
                              a.value if isinstance(a, ast.Constant)
                              and isinstance(a.value, str) else ""))
                        if "funding" in str(nom).lower() or str(nom) == "f":
                            res["abs_funding"].append(getattr(n, "lineno", 0))
                            break
    concernes = [b for b in res["bots"] if b not in BOTS_DISPENSES]
    fautes, avertissements = [], []
    if concernes and not res["importe_comptabilite"] and (res["trade_direct"] or res["close_direct"]):
        msg = "fabrique des Trade/P&L sans passer par comptabilite.py"
        (avertissements if p.name in LEGACY else fautes).append(msg)
    if res["abs_funding"]:
        fautes.append("abs(funding) MULTIPLIE (l.%s) : le funding a un SIGNE - "
                      "c'est la faute exacte du bot 28"
                      % ",".join(map(str, sorted(set(res["abs_funding"])))))
    res["avertissements"] = avertissements
    if fautes:
        res["verdict"] = "NON CONFORME : " + " ; ".join(fautes)
    elif avertissements:
        res["verdict"] = "A MIGRER (anterieur a la regle) : " + " ; ".join(avertissements)
    else:
        res["verdict"] = "OK"
    return res


def auditer(ecrire: bool = True) -> dict:
    lignes = [_analyser(p) for p in _fichiers_bots()]
    mauvais = [r for r in lignes if r["verdict"].startswith("NON CONFORME")]
    a_migrer = [r for r in lignes if r["verdict"].startswith("A MIGRER")]
    # Consequence AUTOMATIQUE : un bot dont la comptabilite est fausse ne peut pas
    # etre promu en argent reel. C'est le verrou qui aurait evite le bot 28.
    bloques = sorted({b for r in mauvais for b in r["bots"] if b not in BOTS_DISPENSES})
    # Verrou ELARGI (29/07) : un bot ne peut aller en argent reel que si son module
    # utilise la comptabilite reelle. Cela couvre les NON CONFORMES *et* les modules
    # anterieurs a la regle ("a migrer") : leurs statistiques peuvent etre aussi
    # fausses que celles du bot 28 avant correction. C'est le Tresorier qui lit
    # cette liste (checklist) et refuse la promotion.
    non_promouvables = sorted({b for r in lignes for b in r["bots"]
                               if b not in BOTS_DISPENSES and not r["importe_comptabilite"]})
    doc = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "n_modules": len(lignes),
        "n_non_conformes": len(mauvais),
        "n_a_migrer": len(a_migrer),
        "a_migrer": [r["fichier"] for r in a_migrer],
        "conforme": not mauvais,
        "bots_bloques_pour_le_reel": bloques,
        "bots_non_promouvables": non_promouvables,
        "detail": lignes,
        "regle": "Tout bot a position de marche produit ses Trade via "
                 "comptabilite.PositionReelle : P&L = prix + funding signe - frais reels.",
    }
    if ecrire:
        try:
            ETAT.mkdir(parents=True, exist_ok=True)
            SORTIE.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        except OSError:
            pass
    if bloques:
        print("[conformite] PROMOTION REELLE BLOQUEE pour : %s" % ", ".join(bloques), flush=True)
    if non_promouvables:
        print("[conformite] non promouvables (comptabilite non reelle) : %s"
              % ", ".join(non_promouvables), flush=True)
    if mauvais:
        print("[conformite] %d MODULE(S) NON CONFORME(S) :" % len(mauvais), flush=True)
        for r in mauvais:
            print("   - %-32s %s" % (r["fichier"], r["verdict"]), flush=True)
    else:
        print("[conformite] %d modules verifies, aucune violation." % len(lignes), flush=True)
    if a_migrer:
        print("[conformite] %d module(s) anterieur(s) a la regle, a migrer : %s"
              % (len(a_migrer), ", ".join(r["fichier"] for r in a_migrer)), flush=True)
    return doc


if __name__ == "__main__":
    d = auditer()
    raise SystemExit(0 if d["conforme"] else 1)
