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
    chg = brief.get("changements_statut", [])
    suspect = bool(gr.get("banc_suspect"))
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
