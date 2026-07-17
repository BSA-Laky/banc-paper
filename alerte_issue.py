#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
alerte_issue.py - notification push PC eteint via issue GitHub (quotidien)
==========================================================================
Lit docs/go_reel.json et docs/brief.json ; s'il y a une ALERTE ROUGE, un banc
suspect ou un changement de statut, ouvre UNE issue GitHub datee (dedup par
titre). L'issue declenche la notification GitHub (appli mobile / e-mail) ->
alerte sur telephone sans PC ni service tiers. Token = GITHUB_TOKEN du
workflow (permissions: issues: write). stdlib only. Jamais bloquant.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = os.environ.get("GITHUB_REPOSITORY", "BSA-Laky/banc-paper")
API = f"https://api.github.com/repos/{REPO}/issues"
LABEL = "alerte-banc"


def _req(url, data=None, method="GET"):
    tok = os.environ.get("GITHUB_TOKEN", "")
    req = urllib.request.Request(url, method=method,
        data=(json.dumps(data).encode("utf-8") if data is not None else None),
        headers={"Authorization": f"Bearer {tok}",
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "banc-paper-alerte"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, OSError) as e:
        print(f"[alerte] API GitHub KO : {e}", flush=True)
        return None


def _lire(p):
    try:
        with Path(p).open(encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def main():
    gr = _lire("docs/go_reel.json")
    brief = _lire("docs/brief.json")
    alertes = list(gr.get("alertes", []))

    # ---- WATCHDOG 17/07 : verifications INDEPENDANTES de la fraicheur du brief
    # (lecon de la panne muette de 50 h : l'alerte ne doit dependre d'aucun des
    # organes qu'elle surveille). Lecture directe des fichiers d'etat commites.
    maintenant = datetime.now(timezone.utc)

    def _age_h(iso):
        try:
            d = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
            if d.tzinfo is None:
                d = d.replace(tzinfo=timezone.utc)
            return (maintenant - d).total_seconds() / 3600.0
        except (ValueError, TypeError):
            return None

    def _echecs(f):
        d = _lire(Path("etat") / f)
        return int(d.get("consecutifs", 0)) if isinstance(d, dict) else 0

    age_gate = _age_h(gr.get("ts"))
    if age_gate is not None and age_gate > 6:
        alertes.append(f"MOTEUR : aucune passe du banc depuis {age_gate:.0f} h "
                       "(famine cron ou panne sampler)")
    regime = _lire("etat/regime_ia.json")
    age_avis = _age_h(regime.get("date"))
    ea = _echecs("arbitre_echecs.json")
    if (ea >= 2 or (ea >= 1 and age_avis is not None and age_avis > 24)
            or (age_avis is not None and age_avis > 36)):
        alertes.append(f"ARBITRE : {ea} echec(s), avis vieux de "
                       f"{'?' if age_avis is None else round(age_avis)} h")
    for f, nom in (("superviseur_echecs.json", "SUPERVISEUR"),
                   ("veilleur_echecs.json", "VEILLEUR")):
        n_e = _echecs(f)
        if n_e >= 1:
            alertes.append(f"{nom} : {n_e} echec(s) (agent hebdo : 1 echec = 1 semaine muette)")
    cv = _lire("etat/cycle_vie.json")
    for b, v in (cv.get("bots", {}) or {}).items():
        if v.get("etat") == "kill":
            age_k = _age_h(v.get("ts"))
            if age_k is not None and age_k < 24:
                alertes.append(f"VERDICT EXECUTE : {b} au tapis — {v.get('raison', '')}")
    chg = brief.get("changements_statut", [])
    suspect = bool(gr.get("banc_suspect"))
    pannes = (brief.get("sante_equipage") or {}).get("problemes", [])
    alertes = alertes + [f"EQUIPAGE : {pb}" for pb in pannes]   # rappel quotidien tant que ca dure
    if not alertes and not suspect and not chg:
        print("[alerte] rien a signaler.", flush=True)
        return

    jour = datetime.now(timezone.utc).date().isoformat()
    titre = f"Alerte banc — {jour}"
    ouvertes = _req(f"{API}?state=open&per_page=50") or []   # dedup par TITRE (pas par label)
    if any(i.get("title") == titre for i in ouvertes if isinstance(i, dict)):
        print("[alerte] issue du jour deja ouverte.", flush=True)
        return

    corps = ["_Notification automatique (PC eteint). Constat, pas ordre — la gate decide._", ""]
    if suspect:
        corps.append("## 🔴 BANC SUSPECT : un temoin a |t| >= 2 — ne rien conclure tant que ce n'est pas resolu.")
    if alertes:
        corps.append("## 🔴 Decrochages (action : COUPER LE BOT, jamais elargir le stop)")
        corps += [f"- {a}" for a in alertes]
    if chg:
        corps.append("## Changements de statut")
        corps += [f"- {c.get('bot')} : {c.get('avant')} → **{c.get('apres')}**" for c in chg]
    corps += ["", "Brief complet : https://bsa-laky.github.io/banc-paper/brief.md",
              "Gate : https://bsa-laky.github.io/banc-paper/go_reel.json"]

    res = _req(API, data={"title": titre, "body": "\n".join(corps), "labels": [LABEL]}, method="POST")
    if not isinstance(res, dict):   # le label peut poser probleme -> reessai sans label
        res = _req(API, data={"title": titre, "body": "\n".join(corps)}, method="POST")
    print(f"[alerte] issue creee : {res.get('html_url') if isinstance(res, dict) else 'ECHEC'}", flush=True)


if __name__ == "__main__":
    main()
