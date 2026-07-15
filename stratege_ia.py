#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stratege_ia.py - le STRATEGE R&D de la station (Enseigne Nova, Sonnet 5, EVENEMENTIEL).
=======================================================================================
Demande du Commandant (15/07/2026) : quand une hypothese est INVALIDEE par la gate,
un LLM en propose UNE nouvelle. Gouvernance stricte :
  - declenchement UNIQUEMENT sur invalidation NOUVELLE (ROUGE, decrochage, ou
    avertissement "KILL RECOMMANDE") -> zero appel API les semaines calmes ;
  - le Stratege NE CODE JAMAIS : il produit une FICHE testable (signal, seuils,
    frais, kill-criteres, prior honnete) dans docs/hypotheses.md ;
  - il ne recycle pas les hypotheses deja tuees (liste fournie) ;
  - circuit humain : interpellation Telegram -> "approve h<id>" du Commandant ->
    un humain code le bot -> le banc mesure. La fiche n'est qu'une candidate.
Sorties : etat/hypotheses.json (cap 20) + docs/hypotheses.md + file Telegram.
Sans ANTHROPIC_API_KEY : dormant. stdlib only. MAX_TOKENS 2500.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ETAT = Path("etat"); DOCS = Path("docs")
MODELE = os.environ.get("MODELE_STRATEGE", "claude-sonnet-5")
MAX_TOKENS = 2500
F_HYP = ETAT / "hypotheses.json"
F_VU = ETAT / "stratege_vu.json"
F_ECHECS = ETAT / "stratege_echecs.json"
F_OUT = ETAT / "tresorier_out.json"

DEJA_MORTES = (
    "arbitrage de latence BTC (Binance vs Polymarket)",
    "surebets sportifs full-auto (books FR fermes aux bots)",
    "achat de longshots 0,01-0,03",
    "suivi de tendance memecoins simple",
    "contrarian sur extremes Polymarket",
    "momentum BTC 5 min chaines de Markov",
    "market-making Polymarket (interdit FR/ANJ de toute facon)",
    "switch de regime 27b<->27c par tendance n-x (OOS t 0,24)",
    "intraday actions/futures (tue par les frais, veille 30 ans)",
    "toutes-cotes value paris (illusion hors cotes courtes)",
)

SYSTEME = """Tu es « Enseigne Nova », Stratege R&D de la station banc-paper. Un bot vient
d'etre invalide par la gate ; ta mission : proposer UNE SEULE hypothese de remplacement,
sous forme de fiche TESTABLE. Regles absolues :
- 100 % paper d'abord ; tu ne codes pas ; tu ne donnes aucun conseil d'argent reel.
- L'hypothese doit etre executable FULL-AUTO avec des donnees publiques GRATUITES
  (priorite : API Hyperliquid info deja utilisee par la station ; sinon API publique
  sans cle). Frais a integrer : 0,035 %/jambe perps. Pas de plateforme interdite en
  France (Polymarket exclu), pas de books sportifs.
- INTERDIT de recycler les hypotheses deja tuees (liste fournie) ou une variante
  cosmetique de l'hypothese qui vient de mourir.
- Sois froid : mecanisme economique PLAUSIBLE (qui paie qui, pourquoi ca persiste),
  kill-criteres chiffres, et un prior honnete (la plupart des hypotheses meurent).
Tu reponds EXCLUSIVEMENT en JSON valide, schema :
{"fiche":{"titre":"<=70 caracteres","famille":"carry|reversion|momentum|microstructure|autre",
 "mecanisme":"qui paie cette prime et pourquoi elle persiste (<=280)",
 "signal_entree":"regle chiffree precise (<=200)","signal_sortie":"regle chiffree (<=150)",
 "seuils":"parametres initiaux (<=150)","donnees_requises":"endpoints/champs exacts (<=150)",
 "frais_slippage":"cout aller-retour estime et impact (<=120)",
 "kill_criteres":"quand declarer l'hypothese morte (n, t, duree) (<=150)",
 "prior_honnete":"probabilite subjective de survivre au banc + justification (<=150)"},
 "resume_telegram":"<=180 caracteres"}"""


def _lire_json(p, defaut):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return defaut


def _ecrire_json(p, d):
    try:
        Path(p).parent.mkdir(parents=True, exist_ok=True)
        Path(p).write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        pass


def _invalidations(gate):
    """Cles d'invalidation presentes dans la gate (ROUGE / decrochage / kill recommande)."""
    out = []
    for b, v in (gate.get("bots", {}) or {}).items():
        if v.get("statut") == "ROUGE" or v.get("decrochage"):
            out.append(("rouge:%s" % b, b, "; ".join(v.get("raisons", [])) or "ROUGE/decrochage"))
        for av in v.get("avertissements", []):
            if "KILL RECOMMANDE" in av:
                out.append(("kill:%s" % b, b, av))
    return out


def _appel_api(cle, contenu):
    corps = {"model": MODELE, "max_tokens": MAX_TOKENS, "system": SYSTEME,
             "messages": [{"role": "user", "content": contenu}]}
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(corps).encode("utf-8"),
        headers={"x-api-key": cle, "anthropic-version": "2023-06-01",
                 "content-type": "application/json", "User-Agent": "banc-paper-stratege"})
    try:
        with urllib.request.urlopen(req, timeout=150) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError("HTTP %s : %s" % (e.code, e.read().decode("utf-8", "replace")[:300])) from None


def _rediger_md(hyps):
    lignes = ["# Registre R&D — hypotheses du Stratege (Enseigne Nova)",
              "_1 fiche par bot invalide. approve h<id> / rejette h<id> via Telegram._", ""]
    for h in reversed(hyps):
        f = h.get("fiche", {})
        lignes += ["## %s — %s  `[%s]`" % (h.get("id"), f.get("titre", "?"), h.get("statut", "proposee")),
                   "_Declencheur : %s (%s) — %s_" % (h.get("bot_mort"), h.get("cause", "")[:90], str(h.get("date", ""))[:10]),
                   "- **Mecanisme** : %s" % f.get("mecanisme", ""),
                   "- **Entree** : %s" % f.get("signal_entree", ""),
                   "- **Sortie** : %s" % f.get("signal_sortie", ""),
                   "- **Seuils** : %s · **Donnees** : %s" % (f.get("seuils", ""), f.get("donnees_requises", "")),
                   "- **Frais** : %s" % f.get("frais_slippage", ""),
                   "- **Kill** : %s" % f.get("kill_criteres", ""),
                   "- **Prior honnete** : %s" % f.get("prior_honnete", ""), ""]
    try:
        DOCS.mkdir(exist_ok=True)
        (DOCS / "hypotheses.md").write_text("\n".join(lignes), encoding="utf-8")
    except OSError:
        pass


def _echec(motif):
    d = _lire_json(F_ECHECS, {})
    n = int(d.get("consecutifs", 0)) + 1
    _ecrire_json(F_ECHECS, {"consecutifs": n, "motif": str(motif)[:200],
                            "maj": datetime.now(timezone.utc).isoformat()})
    print("[stratege] ECHEC (%d) : %s" % (n, motif), flush=True)


def main():
    gate = _lire_json(DOCS / "go_reel.json", {})
    vu = _lire_json(F_VU, {"traites": []})
    vu.setdefault("traites", [])
    nouvelles = [(k, b, c) for k, b, c in _invalidations(gate) if k not in vu["traites"]]
    if not nouvelles:
        print("[stratege] aucune invalidation nouvelle — 0 appel, 0 cout.", flush=True)
        return
    cle = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not cle:
        print("[stratege] invalidation detectee mais pas de cle API — dormant.", flush=True)
        return
    k, bot, cause = nouvelles[0]                      # UNE fiche par passe
    hyps = _lire_json(F_HYP, [])
    hyps = hyps if isinstance(hyps, list) else []
    deja_proposees = [h.get("fiche", {}).get("titre", "") for h in hyps]
    donnees = {
        "bot_invalide": {"nom": bot, "cause": cause,
                         "stats": (gate.get("bots", {}) or {}).get(bot, {})},
        "gate_resume": {b: {"statut": v.get("statut"), "n": v.get("n"),
                            "t": v.get("t_stat"), "esp": v.get("esperance"),
                            "rdt_j_pct": v.get("rendement_j_pct")}
                        for b, v in (gate.get("bots", {}) or {}).items()},
        "hypotheses_deja_mortes": list(DEJA_MORTES),
        "fiches_deja_proposees": deja_proposees,
        "competences_prouvees": ((ETAT / "competences.md").read_text(encoding="utf-8")[:2000]
                                 if (ETAT / "competences.md").exists() else "(vide)"),
        "note_veilleur": (ETAT / "note_veilleur.md").read_text(encoding="utf-8")[:800]
                         if (ETAT / "note_veilleur.md").exists() else "(vide)",
    }
    contenu = ("Un bot vient d'etre invalide. Propose UNE fiche (JSON) :\n" +
               json.dumps(donnees, ensure_ascii=False, default=str)[:12000] +
               "\n\nProduis ta reponse JSON maintenant.")
    try:
        rep = _appel_api(cle, contenu)
        texte = "".join(b_.get("text", "") for b_ in rep.get("content", [])
                        if b_.get("type") == "text").strip()
        if texte.startswith("```"):
            texte = texte.strip("`\n ")
            if texte.startswith("json"):
                texte = texte[4:]
        d = json.loads(texte)
        fiche = d.get("fiche") or {}
        if not fiche.get("titre") or not fiche.get("kill_criteres"):
            raise ValueError("fiche incomplete")
    except Exception as e:                            # noqa: BLE001 — jamais bloquant
        _echec(e)
        return
    hid = "h%d" % (len(hyps) + 1)
    hyps.append({"id": hid, "date": datetime.now(timezone.utc).isoformat(),
                 "bot_mort": bot, "cause": cause[:150], "statut": "proposee",
                 "fiche": fiche})
    _ecrire_json(F_HYP, hyps[-20:])
    _rediger_md(hyps[-20:])
    vu["traites"] = (vu["traites"] + [k])[-40:]
    _ecrire_json(F_VU, vu)
    out = _lire_json(F_OUT, {"pending": []})
    out.setdefault("pending", []).append(
        {"id": "hyp:%s" % hid,
         "texte": ("\U0001F9EA R&D — %s invalide (%s).\nNouvelle fiche %s : %s\n%s\n"
                   "Repondre « approve %s » pour la faire coder, "
                   "« rejette %s » sinon. Registre : "
                   "https://bsa-laky.github.io/banc-paper/hypotheses.md"
                   % (bot, cause[:60], hid, fiche.get("titre", "?"),
                      str(d.get("resume_telegram", ""))[:180], hid, hid)),
         "ts": datetime.now(timezone.utc).isoformat()})
    _ecrire_json(F_OUT, out)
    _ecrire_json(F_ECHECS, {"consecutifs": 0, "maj": datetime.now(timezone.utc).isoformat()})
    print("[stratege] OK — fiche %s deposee (%s), Telegram notifie." % (hid, fiche.get("titre", "")),
          flush=True)


if __name__ == "__main__":
    main()
