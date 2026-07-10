#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
superviseur_ia.py - le Superviseur (Fable 5) : salle de controle, 1 appel/semaine
=================================================================================
Le haut de la hierarchie LLM de la station. Une fois par semaine :
  - audite la semaine : gate, brief, notes de veille de l'Arbitre, SA calibration
    (scoring J+7 deterministe), pannes eventuelles
  - ecrit le rapport hebdo lisible telephone (docs/rapport_semaine.md)
  - entretient SA meta-memoire (etat/memoire_superviseur.md, bornee)
  - PILOTE l'Arbitre quotidien par consigne : etat/consigne_arbitre.json
    {"confiance_max": 0-1} — si la calibration de l'Arbitre est mauvaise, le
    Superviseur plafonne sa confiance => le bot 27e retombe sur la tendance n-x.
    C'est un controle LLM-sur-LLM par DONNEES uniquement, jamais par code.
  - ESCALADE au Commandant (issue GitHub) si necessaire.
Memes garde-fous que l'Arbitre : paper only, aucun ordre, fichiers de donnees
uniquement, 1 appel plafonne, sortie propre sans cle. stdlib only.
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
MODELE = os.environ.get("MODELE_SUPERVISEUR", "claude-fable-5")
MAX_TOKENS = 4000   # fix 09/07 : idem arbitre, JSON tronque sinon
CAP_MEMOIRE = 6000
ECHECS_AVANT_ESCALADE = 2

ETAT = Path("etat"); DOCS = Path("docs"); VEILLE = Path("veille")
F_MEMOIRE = ETAT / "memoire_superviseur.md"
F_CONSIGNE = ETAT / "consigne_arbitre.json"
F_ECHECS = ETAT / "superviseur_echecs.json"
REPO = os.environ.get("GITHUB_REPOSITORY", "BSA-Laky/banc-paper")

SYSTEME = """Tu es « le Superviseur » de la station banc-paper : le controle general. Froid,
chiffre, sceptique, econome en mots. Tu audites la semaine ecoulee et tu pilotes l'Arbitre
quotidien (un LLM moins cher) par une CONSIGNE de plafond de confiance.
REGLES ABSOLUES : tout est 100 % fictif (paper) ; jamais d'ordre de trade ni de conseil
d'argent reel ; la gate deterministe decide des statuts ; l'humain tranche le reel ;
n<30 = bruit ; la calibration J+7 fournie est la SEULE preuve de la valeur de l'Arbitre.
COMPETENCES : tu entretiens la bibliotheque de la station (regles PROUVEES par les donnees
uniquement : seuils qui marchent, pieges verifies, heuristiques validees par la calibration).
MISSIONS : tu peux emettre 0 a 3 missions courtes a l'Arbitre pour la semaine (id + texte),
et tu relis ses reponses de la semaine ecoulee (fournies).
COMMANDANT : decisions_du_commandant contient d'eventuels approve/rejette envoyes par
l'humain via Telegram (cible = id de mission ou sujet). Respecte-les : une mission rejetee
n'est pas reconduite ; un approve leve le doute. S'il est vide, poursuis normalement.
CONSIGNE : confiance_max=1.0 si calibration bonne ou inconnue (n<20) ; 0.55 si taux_correct
<= 0.55 avec n>=20 ; 0.4 si <= 0.45 avec n>=20 (l'Arbitre passe alors sous le seuil 0.6 et
le bot 27e retombe sur la tendance pure — c'est le but).
ESCALADE (escalade=true) UNIQUEMENT si : banc_suspect persistant, ROUGE non traite, pannes
repetees de l'Arbitre, incoherence grave des donnees, ou decision humaine requise (reel,
code, depense).
Tu reponds EXCLUSIVEMENT en JSON valide, schema :
{"rapport_md":"rapport hebdo en markdown (<=1400 caracteres) : etat des salles, verdicts en
cours (n, t), calibration de l'Arbitre, cout/pannes, 3 points pour la semaine",
 "memoire_superviseur_md":"TA meta-memoire REECRITE (<=2200 caracteres, dense) : tendances de fond,
verdicts dates, qualite de l'Arbitre dans le temps",
 "competences_md":"bibliotheque de competences REECRITE (<=2000 caracteres, uniquement du PROUVE, date chaque regle)",
 "missions":[{"id":"m1","texte":"<=140 caracteres"}],
 "confiance_max_arbitre":1.0,"motif_consigne":"<=140 caracteres",
 "escalade":false,"raison_escalade":""}"""


def _lire_json(p):
    try:
        with Path(p).open(encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def _lire_texte(p, cap=6000):
    try:
        return Path(p).read_text(encoding="utf-8")[:cap]
    except OSError:
        return ""


def _calibration():
    """Stats deterministes du scoring J+7 (la preuve, pas l'opinion)."""
    try:
        with (ETAT / "calibration_arbitre.csv").open(newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
    except OSError:
        return None
    if not rows:
        return None
    out = {}
    for r in rows:
        s = r.get("source") or "?"
        out.setdefault(s, []).append(r)
    return {s: {"n": len(rs),
                "taux_correct": round(sum(int(x["correct"]) for x in rs) / len(rs), 3),
                "brier_moyen": round(sum(float(x["brier"]) for x in rs) / len(rs), 3)}
            for s, rs in out.items()}


def _notes_semaine(n=7, cap=700):
    try:
        fichiers = sorted(VEILLE.glob("*.md"), reverse=True)[:n]
    except OSError:
        return []
    return [{"fichier": f.name, "contenu": _lire_texte(f, cap)} for f in fichiers]


def _appel_api(cle, contenu):
    corps = {"model": MODELE, "max_tokens": MAX_TOKENS,
             "system": SYSTEME, "messages": [{"role": "user", "content": contenu}]}
    req = urllib.request.Request(API_URL, data=json.dumps(corps).encode("utf-8"),
        headers={"x-api-key": cle, "anthropic-version": "2023-06-01",
                 "content-type": "application/json", "User-Agent": "banc-paper-superviseur"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:600]
        raise RuntimeError(f"HTTP {e.code}: {detail}") from None


def _issue(titre, corps):
    tok = os.environ.get("GITHUB_TOKEN", "")
    if not tok:
        return
    req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/issues",
        data=json.dumps({"title": titre, "body": corps, "labels": ["alerte-banc"]}).encode("utf-8"),
        method="POST",
        headers={"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json",
                 "User-Agent": "banc-paper-superviseur"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            print(f"[superviseur] escalade : {json.loads(r.read()).get('html_url')}", flush=True)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, ValueError):
        print("[superviseur] escalade IMPOSSIBLE (API GitHub KO)", flush=True)


def _echec(motif):
    d = _lire_json(F_ECHECS)
    n = (int(d.get("consecutifs", 0)) if isinstance(d, dict) else 0) + 1
    try:
        ETAT.mkdir(parents=True, exist_ok=True)
        F_ECHECS.write_text(json.dumps({"consecutifs": n,
            "maj": datetime.now(timezone.utc).isoformat()}), encoding="utf-8")
    except OSError:
        pass
    print(f"[superviseur] ECHEC ({n}) : {motif}", flush=True)
    if n == ECHECS_AVANT_ESCALADE:
        _issue(f"Superviseur IA en panne — {datetime.now(timezone.utc).date().isoformat()}",
               f"_Escalade automatique._\n\nLe Superviseur a echoue {n} semaines de suite.\n"
               f"Dernier motif : `{motif}`\n\nL'Arbitre quotidien continue sans consigne.")


def main():
    cle = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not cle:
        print("[superviseur] pas de cle API — mode veille.", flush=True)
        return

    brief = _lire_json(DOCS / "brief.json")
    gate = _lire_json(DOCS / "go_reel.json")
    if not brief or not gate:
        _echec("brief/gate introuvables")
        return

    donnees = {
        "date": datetime.now(timezone.utc).isoformat(),
        "brief_du_jour": brief,
        "gate": gate,
        "calibration_arbitre_J7": _calibration(),
        "pannes_arbitre": _lire_json(ETAT / "arbitre_echecs.json"),
        "notes_veille_7_derniers_jours": _notes_semaine(),
        "memoire_arbitre": _lire_texte(ETAT / "memoire_arbitre.md", 3000),
        "rapports_quotidiens_arbitre": _lire_json(ETAT / "rapport_arbitre.json"),
        "competences_actuelles": _lire_texte(ETAT / "competences.md", 2500) or "(vide)",
        "mes_missions_precedentes": (_lire_json(F_CONSIGNE) or {}).get("missions", []),
        "decisions_du_commandant": _lire_json(ETAT / "decisions_commandant.json") or [],
        "ma_meta_memoire": _lire_texte(F_MEMOIRE, CAP_MEMOIRE) or "(vide — premiere semaine)",
    }
    contenu = ("Audit hebdomadaire de la station (JSON) :\n" +
               json.dumps(donnees, ensure_ascii=False)[:30000] +
               "\n\nProduis ta reponse JSON maintenant.")

    try:
        rep = _appel_api(cle, contenu)
        texte = "".join(b.get("text", "") for b in rep.get("content", [])
                        if b.get("type") == "text").strip()
        if texte.startswith("```"):
            texte = texte.strip("`").lstrip("json").strip()
        d = json.loads(texte)
        rapport = str(d["rapport_md"])[:6000]
        memoire = str(d.get("memoire_superviseur_md", ""))[:CAP_MEMOIRE]
        plafond = max(0.0, min(1.0, float(d.get("confiance_max_arbitre", 1.0))))
        competences = str(d.get("competences_md", ""))[:2400]
        missions = d.get("missions") or []
        missions = [{"id": str(m.get("id", f"m{i+1}"))[:24], "texte": str(m.get("texte", ""))[:160]}
                    for i, m in enumerate(missions) if isinstance(m, dict)][:3]
        motif = str(d.get("motif_consigne", ""))[:200]
        escalade = bool(d.get("escalade"))
        raison = str(d.get("raison_escalade", ""))[:600]
    except Exception as e:
        _echec(f"{type(e).__name__}: {e}")
        return

    now = datetime.now(timezone.utc)
    jour = now.date().isoformat()
    try:
        ETAT.mkdir(exist_ok=True); DOCS.mkdir(exist_ok=True)
        (DOCS / "rapport_semaine.md").write_text(
            f"# Rapport du Superviseur — semaine du {jour}\n\n{rapport}\n\n"
            f"_Consigne Arbitre : confiance_max {plafond:.2f} ({motif or 'calibration OK'}). "
            f"Modele `{MODELE}`._\n", encoding="utf-8")
        if memoire:
            F_MEMOIRE.write_text(memoire, encoding="utf-8")
        if competences:
            (ETAT / "competences.md").write_text(competences, encoding="utf-8")
        F_CONSIGNE.write_text(json.dumps({"confiance_max": round(plafond, 2),
            "date": now.isoformat().replace("+00:00", "Z"), "motif": motif,
            "missions": missions}, ensure_ascii=False), encoding="utf-8")
        F_ECHECS.write_text(json.dumps({"consecutifs": 0, "maj": now.isoformat()}),
                            encoding="utf-8")
    except OSError as e:
        _echec(f"ecriture: {e}")
        return

    u = rep.get("usage", {})
    print(f"[superviseur] OK consigne={plafond:.2f} "
          f"tokens={u.get('input_tokens','?')}/{u.get('output_tokens','?')}", flush=True)
    if escalade:
        _issue(f"Superviseur — escalade {jour}",
               f"_Le Superviseur demande le Commandant._\n\n{raison}\n\n"
               f"Rapport : https://bsa-laky.github.io/banc-paper/rapport_semaine.md")


if __name__ == "__main__":
    main()
