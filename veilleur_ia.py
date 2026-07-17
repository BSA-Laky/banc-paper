#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
veilleur_ia.py - le VEILLEUR de la station (Cadet Remy, Haiku 4.5, HEBDO).
==========================================================================
Etape B du plan Hermes (12/07/2026). Chaque SAMEDI 05:50 UTC, un appel Haiku
(~centimes) digere la semaine OPERATIONNELLE et depose une note factuelle que
le Superviseur (dimanche 06:30) relit dans son audit.

Perimetre STRICT (exploitation, pas prediction) :
  - frictions d'execution testnet (rejets d'ordres, causes, taux de fill) ;
  - consommation du budget d'avis LLM (avis_piece) ;
  - anomalies chiffrees du banc (ecarts esp vs reference si fournie, mdd etranges) ;
  - sante des automates (echecs arbitre, alertes gate).
INTERDIT : recommander un trade, predire un marche, promouvoir un bot.

Sorties : etat/note_veilleur.md (lu par superviseur_ia) + docs/veilleur.md (Pages)
+ etat/veilleur_echecs.json. Sans ANTHROPIC_API_KEY : dormant, sortie propre.
stdlib only. MAX_TOKENS 2500 (>= 2,5x la note demandee : lecon de la panne 04-08/07).
"""
from __future__ import annotations

import csv
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ETAT = Path("etat"); DOCS = Path("docs")
MODELE = os.environ.get("MODELE_VEILLEUR", "claude-haiku-4-5-20251001")
MAX_TOKENS = 4000   # 17/07 : marge (Haiku pense peu)
F_NOTE = ETAT / "note_veilleur.md"
F_NOTE_DOCS = DOCS / "veilleur.md"
F_ECHECS = ETAT / "veilleur_echecs.json"

SYSTEME = """Tu es « Cadet Remy », le Veilleur de la station banc-paper : un oeil froid
sur la MACHINE, pas sur les marches. Tu rediges la note hebdomadaire pour la Commandeure
(le Superviseur). Regles absolues : tout est 100 % fictif (paper/testnet) ; tu ne
recommandes JAMAIS un trade, une promotion de bot ou une direction de marche ; tu ne
parles que de ce qui est DANS les donnees fournies ; chiffres exacts, zero adjectif
inutile. Ta valeur : reperer les frictions d'execution, les derives de cout, les
anomalies chiffrees et les incoherences que les automates ne commentent pas.
Tu reponds EXCLUSIVEMENT en JSON valide, schema :
{"note_md":"note en markdown (<=900 caracteres) : ## Veille semaine <date> puis
3 sections courtes : Execution testnet / Couts LLM / Anomalies & attention",
 "alerte_humain":false}
alerte_humain=true UNIQUEMENT si un fait grave exige le Commandant (ex. rejets 100 %
persistants, budget explose, incoherence de donnees majeure)."""


def _lire_json(p, defaut):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return defaut


def _ecrire(p, txt):
    try:
        Path(p).parent.mkdir(parents=True, exist_ok=True)
        Path(p).write_text(txt, encoding="utf-8")
    except OSError:
        pass


def _semaine_testnet():
    """Resume deterministe des 7 derniers jours du ledger testnet."""
    seuil = datetime.now(timezone.utc) - timedelta(days=7)
    n_open = n_close = n_rejet = 0
    causes = {}
    pnl = 0.0
    try:
        with (ETAT / "testnet_trades.csv").open(encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                try:
                    ts = datetime.fromisoformat(str(r.get("ts", "")).replace("Z", "+00:00"))
                except ValueError:
                    continue
                if ts < seuil:
                    continue
                a = r.get("action", "")
                if a == "open":
                    n_open += 1
                elif a == "close":
                    n_close += 1
                    try:
                        pnl += float(r.get("pnl_est_usd") or 0)
                    except ValueError:
                        pass
                elif a == "REJET":
                    n_rejet += 1
                    c = str(r.get("resp", ""))[:45]
                    causes[c] = causes.get(c, 0) + 1
    except OSError:
        pass
    total = n_open + n_rejet
    return {"ordres_ouverts": n_open, "fermes": n_close, "rejets": n_rejet,
            "taux_fill_pct": round(100 * n_open / total) if total else None,
            "causes_rejet": causes, "pnl_est_cumule_usd": round(pnl, 2)}


def _resume_gate():
    gr = _lire_json(DOCS / "go_reel.json", {})
    bots = {}
    for b, v in (gr.get("bots", {}) or {}).items():
        bots[b] = {"statut": v.get("statut"), "n": v.get("n"),
                   "esp": v.get("esperance"), "t": v.get("t_stat"),
                   "mdd_usd": v.get("mdd_live")}
    return {"banc_suspect": gr.get("banc_suspect"), "alertes": gr.get("alertes", []),
            "temoin": (gr.get("temoins", {}) or {}).get("10_controle_aleatoire", {}),
            "bots": bots}


def _appel_api(cle, contenu):
    corps = {"model": MODELE, "max_tokens": MAX_TOKENS, "system": SYSTEME,
             "messages": [{"role": "user", "content": contenu}]}
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(corps).encode("utf-8"),
        headers={"x-api-key": cle, "anthropic-version": "2023-06-01",
                 "content-type": "application/json", "User-Agent": "banc-paper-veilleur"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode("utf-8")[:300]
        except OSError:
            detail = ""
        raise RuntimeError(f"HTTP {e.code} : {detail}") from e


def _echec(motif):
    d = _lire_json(F_ECHECS, {})
    n = int(d.get("consecutifs", 0)) + 1
    _ecrire(F_ECHECS, json.dumps({"consecutifs": n, "motif": str(motif)[:200],
                                  "maj": datetime.now(timezone.utc).isoformat()}))
    print(f"[veilleur] ECHEC ({n} consecutif(s)) : {motif}", flush=True)


def main():
    cle = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not cle:
        print("[veilleur] pas de cle API — dormant.", flush=True)
        return
    jour = datetime.now(timezone.utc).date().isoformat()
    donnees = {
        "date": jour,
        "execution_testnet_7j": _semaine_testnet(),
        "gate": _resume_gate(),
        "budget_avis_du_jour": _lire_json(ETAT / "avis_budget.json", {}),
        "echecs_arbitre": _lire_json(ETAT / "arbitre_echecs.json", {}),
        "tresorier": _lire_json(DOCS / "tresorier.json", {}),
        "rappel": "Note factuelle pour le Superviseur. Pas de reco de trade.",
    }
    contenu = ("Semaine operationnelle de la station (JSON) :\n" +
               json.dumps(donnees, ensure_ascii=False)[:14000] +
               "\n\nProduis ta reponse JSON maintenant.")
    try:
        rep = _appel_api(cle, contenu)
        texte = "".join(b.get("text", "") for b in rep.get("content", [])
                        if b.get("type") == "text").strip()
        if texte.startswith("```"):
            texte = texte.strip("`\n ")
            if texte.startswith("json"):
                texte = texte[4:]
        d = json.loads(texte)
        note = str(d.get("note_md", "")).strip()[:1400]
        if not note:
            raise ValueError("note vide")
    except Exception as e:                      # noqa: BLE001 — jamais bloquant
        _echec(e)
        return
    entete = f"_Note du Veilleur (Cadet Remy, {MODELE}) — {jour}_\n\n"
    _ecrire(F_NOTE, entete + note + "\n")
    _ecrire(F_NOTE_DOCS, entete + note + "\n")
    _ecrire(F_ECHECS, json.dumps({"consecutifs": 0,
                                  "maj": datetime.now(timezone.utc).isoformat()}))
    if d.get("alerte_humain"):
        alertes = _lire_json(ETAT / "tresorier_out.json", {"pending": []})
        alertes.setdefault("pending", []).append(
            {"id": f"veilleur:{jour}",
             "texte": "Le Veilleur signale un fait grave — lire docs/veilleur.md",
             "ts": datetime.now(timezone.utc).isoformat()})
        _ecrire(ETAT / "tresorier_out.json", json.dumps(alertes, ensure_ascii=False))
    print(f"[veilleur] OK — note deposee ({len(note)} car.), alerte={bool(d.get('alerte_humain'))}",
          flush=True)


if __name__ == "__main__":
    main()
