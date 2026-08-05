#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_29bc.py - runner des deux jumeaux du carry neutre (29b et 29c).
====================================================================
Remplace run_29b.py : un seul workflow fait tourner les deux, ils partagent la
meme passe de marche et le meme journal.

    29  (existant) ...  6 jambes, panier unique, tenue 168 h
    29b .............. 20 jambes, panier unique, tenue 168 h
    29c .............. 20 jambes, paniers DECALES toutes les 48 h, tenue 168 h

Le trio isole exactement deux variables : le nombre de jambes (29 -> 29b) et
le decalage des paniers (29b -> 29c). Rien d'autre ne change : meme signal,
meme tenue, meme comptabilite, meme gate, meme journal.

Un bot qui leve n'empeche jamais l'autre de tourner.
stdlib uniquement.
"""
from __future__ import annotations

from banc_essai_paper_trading import journaliser


def lancer() -> None:
    nouveaux = []
    for nom, importer in (("29b", _b), ("29c", _c)):
        try:
            bot = importer()
        except Exception as e:  # noqa: BLE001
            print("[%s] construction KO : %s" % (nom, e), flush=True)
            continue
        try:
            tr = bot.step()
        except Exception as e:  # noqa: BLE001
            print("[%s] step a leve : %s" % (nom, e), flush=True)
            continue
        nouveaux.extend(tr)
        etat = getattr(bot, "_etat", {}) or {}
        if nom == "29c":
            print("[29c] %d panier(s), %d jambe(s), neutralite %.3f"
                  % (etat.get("n_paniers", 0), etat.get("n_jambes", 0),
                     etat.get("ecart_neutralite", 0.0)), flush=True)
        else:
            n = len(getattr(bot, "livre").positions) if hasattr(bot, "livre") else 0
            print("[29b] %d jambe(s) ouverte(s)." % n, flush=True)
    if nouveaux:
        journaliser(nouveaux)
        print("[29bc] %d jambe(s) soldee(s) au total." % len(nouveaux), flush=True)


def _b():
    from bot_29b_large import CarryNeutreLarge
    return CarryNeutreLarge()


def _c():
    from bot_29c_decale import CarryNeutreDecale
    return CarryNeutreDecale()


if __name__ == "__main__":
    lancer()
