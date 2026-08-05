#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_29b.py - runner du bot 29b (carry neutre LARGE, 20 jambes).
================================================================
Tourne a cote de run_once.py plutot que dedans, pour la meme raison que
garde_reel.py et run_book_30b.py : editer un fichier existant dans l'editeur
web GitHub est impossible sans risque (CodeMirror ne rend que 36 lignes sur 96
et un collage duplique le fichier -- c'est ce qui a casse la station 24 h).
Tant que le Commandant ne peut pas editer lui-meme, on n'ajoute QUE des
fichiers neufs. C'est plus verbeux, c'est sans risque, et ca marche.

Le bot 29b journalise dans le MEME paper_trades.csv que les autres : il est
donc evalue par la meme gate, avec les memes regles, sans traitement de faveur.

stdlib uniquement.
"""
from __future__ import annotations

from banc_essai_paper_trading import journaliser


def lancer() -> None:
    try:
        from bot_29b_large import CarryNeutreLarge
    except Exception as e:  # noqa: BLE001
        print("[29b] import impossible : %s" % e, flush=True)
        return
    try:
        bot = CarryNeutreLarge()
    except Exception as e:  # noqa: BLE001
        print("[29b] construction KO : %s" % e, flush=True)
        return
    try:
        trades = bot.step()
    except Exception as e:  # noqa: BLE001
        print("[29b] step a leve : %s" % e, flush=True)
        return
    if trades:
        journaliser(trades)
        print("[29b] %d jambe(s) soldee(s)." % len(trades), flush=True)
    else:
        n = len(getattr(bot, "livre", None).positions) if getattr(bot, "livre", None) else 0
        print("[29b] rien a solder ; %d jambe(s) ouverte(s)." % n, flush=True)


if __name__ == "__main__":
    lancer()
