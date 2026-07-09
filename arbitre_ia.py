#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
arbitre_ia.py - l'Arbitre LLM en autonomie (1 appel API/jour, PC eteint)
========================================================================
Test "pilote automatique 1 mois" : un LLM (Opus 4.8 / Fable 5 via l'API
Anthropic) remplace la session quotidienne du Commandant pour la couche
JUGEMENT uniquement :
  - lit la bibliotheque (brief.json, go_reel.json, journal arbitre, sa memoire)
  - ecrit la note de veille qualitative du jour (veille/AAAA-MM-JJ.md)
  - entretient SA memoire long-terme (etat/memoire_arbitre.md, bornee)
  - publie l'avis de regime consomme par le bot 27e (etat/regime_ia.json)
  - resume visible telephone (docs/arbitre.md)
  - ESCALADE au Commandant (issue GitHub -> notification) si necessaire

Ce que ce script NE PEUT PAS faire, par construction :
  - passer un ordre, toucher de l'argent (rien n'existe : paper only)
  - modifier le code ou les statuts de la gate (le moniteur deterministe decide)
  - depenser plus que : 1 appel/jour, max_tokens plafonne
Sans cle API (secret absent) : sort proprement, la station continue sans lui.
stdlib only.
"""
from __future__ import annotations

import csv
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API_URL = "https://api.anthropic.com/v1/messages"
MODELE = os.environ.get("MODELE_ARBITRE", "claude-sonnet-5")
MAX_TOKENS = 4000   # fix 09/07 : 1600 coupait le JSON des que la memoire grossissait
CAP_MEMOIRE = 7000          # caracteres max de la memoire persistante
ECHECS_AVANT_ESCALADE = 2

ETAT = Path("etat"); DOCS = Path("docs"); VEILLE = Path("veille")
F_MEMOIRE = ETAT / "memoire_arbitre.md"
F_ECHECS = ETAT / "arbitre_echecs.json"
F_REGIME = ETAT / "regime_ia.json"
REPO = os.environ.get("GITHUB_REPOSITORY", "BSA-Laky/banc-paper")

SYSTEME = """Tu es « l'Arbitre » de la station banc-paper : analyste froid, chiffre, sceptique.
REGLES ABSOLUES : tout est 100 % fictif (paper) ; tu ne donnes JAMAIS d'ordre de trade ni de
conseil d'argent reel ; la gate deterministe decide des statuts, l'humain tranche le reel ;
n<30 = bruit, meme seduisant ; tu cites les chiffres, tu dates, tu es bref.
Si ta calibration (fournie) montre taux_correct <= 0,5 avec n >= 20 : mets confiance <= 0,5.
ESCALADE (alerte_humain=true) UNIQUEMENT si : banc_suspect, alerte ROUGE non traitee depuis
>24h, donnees manifestement corrompues/absentes, ou decision qui engage argent reel/code.
Tu reponds EXCLUSIVEMENT en JSON valide, sans texte autour, schema :
{"regime":"haussier|baissier|neutre","confiance":0.0,"resume":"<=200 caracteres",
 "note_veille_md":"note du jour en markdown (<=800 caracteres), factuelle, chiffres du brief",
 "memoire_md":"TA memoire long-terme REECRITE en entier (<=2500 caracteres, sois dense) : verdicts dates, lecons, a surveiller",
 "alerte_humain":false,"raison_alerte":""}"""


def _lire_json(p):
    try:
        with Path(p).open(encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def _lire_texte(p, cap=8000):
    try:
        return Path(p).read_text(encoding="utf-8")[:cap]
    except OSError:
        return ""


def _tail_journal(n=15):
    try:
        with (ETAT / "journal_arbitre.csv").open(newline="", encoding="utf-8") as fh:
            return list(csv.DictReader(fh))[-n:]
    except OSError:
        return []


def _appel_api(cle, contenu):
    corps = {"model": MODELE, "max_tokens": MAX_TOKENS,
             "system": SYSTEME, "messages": [{"role": "user", "content": contenu}]}
    req = urllib.request.Request(API_URL, data=json.dumps(corps).encode("utf-8"),
        headers={"x-api-key": cle, "anthropic-version": "2023-06-01",
                 "content-type": "application/json", "User-Agent": "banc-paper-arbitre"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:600]
        raise RuntimeError(f"HTTP {e.code}: {detail}") from None


def _issue_escalade(titre, corps):
    tok = os.environ.get("GITHUB_TOKEN", "")
    if not tok:
        return
    data = {"title": titre, "body": corps, "labels": ["alerte-banc"]}
    req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/issues",
        data=json.dumps(data).encode("utf-8"), method="POST",
        headers={"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json",
                 "User-Agent": "banc-paper-arbitre"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            print(f"[arbitre] escalade : {json.loads(r.read()).get('html_url')}", flush=True)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, ValueError):
        print("[arbitre] escalade IMPOSSIBLE (API GitHub KO)", flush=True)


def _nb_echecs():
    d = _lire_json(F_ECHECS)
    return int(d.get("consecutifs", 0)) if isinstance(d, dict) else 0


def _ecrire_echecs(n):
    try:
        ETAT.mkdir(parents=True, exist_ok=True)
        F_ECHECS.write_text(json.dumps({"consecutifs": n,
            "maj": datetime.now(timezone.utc).isoformat()}), encoding="utf-8")
    except OSError:
        pass


def _echec(motif):
    n = _nb_echecs() + 1
    _ecrire_echecs(n)
    print(f"[arbitre] ECHEC ({n} consecutif(s)) : {motif}", flush=True)
    if n == ECHECS_AVANT_ESCALADE:
        _issue_escalade(
            f"Arbitre IA en panne — {datetime.now(timezone.utc).date().isoformat()}",
            f"_Escalade automatique._\n\nL'Arbitre IA a echoue {n} jours de suite.\n"
            f"Dernier motif : `{motif}`\n\nLa station continue en mode deterministe "
            f"(le bot 27e retombe sur la tendance n-x). A verifier : secret "
            f"ANTHROPIC_API_KEY, credit API, logs du workflow arbitre-ia.")


def main():
    cle = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not cle:
        print("[arbitre] pas de cle API (secret ANTHROPIC_API_KEY absent) — mode veille, rien a faire.", flush=True)
        return

    brief = _lire_json(DOCS / "brief.json")
    gate = _lire_json(DOCS / "go_reel.json")
    if not brief or not gate:
        _echec("brief.json ou go_reel.json introuvable")
        return

    donnees = {
        "date": datetime.now(timezone.utc).isoformat(),
        "brief": brief,
        "gate": {k: gate.get(k) for k in ("banc_suspect", "temoins", "alertes",
                                          "avertissements", "calibration_arbitre")},
        "mes_15_dernieres_decisions": _tail_journal(),
        "ma_memoire": _lire_texte(F_MEMOIRE, CAP_MEMOIRE) or "(vide — premier jour)",
    }
    contenu = ("Donnees du jour de la station (JSON) :\n" +
               json.dumps(donnees, ensure_ascii=False)[:24000] +
               "\n\nProduis ta reponse JSON maintenant.")

    try:
        rep = _appel_api(cle, contenu)
        texte = "".join(b.get("text", "") for b in rep.get("content", [])
                        if b.get("type") == "text").strip()
        if texte.startswith("```"):
            texte = texte.strip("`").lstrip("json").strip()
        d = json.loads(texte)
        regime = str(d["regime"]).lower()
        conf = max(0.0, min(1.0, float(d["confiance"])))
        assert regime in ("haussier", "baissier", "neutre")
        resume = str(d.get("resume", ""))[:300]
        note = str(d.get("note_veille_md", ""))[:4000]
        memoire = str(d.get("memoire_md", ""))[:CAP_MEMOIRE]
        alerte = bool(d.get("alerte_humain"))
        raison = str(d.get("raison_alerte", ""))[:500]
        consigne = _lire_json(ETAT / "consigne_arbitre.json")
        try:                                   # plafond fixe par le Superviseur (Fable 5)
            plafond = float(consigne.get("confiance_max", 1.0))
            age_j = (datetime.now(timezone.utc)
                     - datetime.fromisoformat(str(consigne.get("date")).replace("Z", "+00:00"))
                     ).total_seconds() / 86400.0
            if 0 <= age_j <= 8 and plafond < conf:
                print(f"[arbitre] confiance {conf:.2f} plafonnee a {plafond:.2f} (consigne superviseur)", flush=True)
                conf = plafond
        except (TypeError, ValueError, AttributeError):
            pass
    except Exception as e:                      # jamais bloquant, quel que soit l'echec
        _echec(f"{type(e).__name__}: {e}")
        return

    now = datetime.now(timezone.utc)
    jour = now.date().isoformat()
    try:
        ETAT.mkdir(exist_ok=True); DOCS.mkdir(exist_ok=True); VEILLE.mkdir(exist_ok=True)
        F_REGIME.write_text(json.dumps({"date": now.isoformat().replace("+00:00", "Z"),
            "regime": regime, "confiance": round(conf, 2), "resume": resume},
            ensure_ascii=False), encoding="utf-8")
        (VEILLE / f"{jour}.md").write_text(
            f"# Veille Arbitre — {jour}\n\n{note}\n\n_Regime : {regime} (confiance {conf:.2f})._\n",
            encoding="utf-8")
        if memoire:
            F_MEMOIRE.write_text(memoire, encoding="utf-8")
        (DOCS / "arbitre.md").write_text(
            f"# Arbitre IA — {jour}\n\n**Regime : {regime}** (confiance {conf:.2f})\n\n"
            f"{resume}\n\n[Note du jour](../veille/{jour}.md) — modele `{MODELE}`\n",
            encoding="utf-8")
    except OSError as e:
        _echec(f"ecriture: {e}")
        return

    _ecrire_echecs(0)
    u = rep.get("usage", {})
    print(f"[arbitre] OK regime={regime} conf={conf:.2f} "
          f"tokens={u.get('input_tokens','?')}/{u.get('output_tokens','?')}", flush=True)
    if alerte:
        _issue_escalade(f"Arbitre IA — escalade {jour}",
                        f"_L'Arbitre demande le Commandant._\n\n{raison}\n\n"
                        f"Resume du jour : {resume}\n"
                        f"Brief : https://bsa-laky.github.io/banc-paper/brief.md")


if __name__ == "__main__":
    main()
