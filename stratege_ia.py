#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stratege_ia.py - le STRATEGE R&D de la station (Enseigne Nova, Sonnet 5, EVENEMENTIEL).
=======================================================================================
AMENDEMENT DE CHARTE (Commandant, 16/07/2026) : Nova ne se contente plus de PROPOSER,
elle CODE et MET EN SERVICE les bots PAPER de A a Z (parametres ADAPTATIFS au marche,
jamais cales sur le P&L passe), en autonomie, sans approbation
humaine. Justification : c'est du paper (0 EUR) ; un mauvais bot est TUE par la gate
(temoin + n/t/forward + kill auto du rd_runner) ; le GO reel reste la main humaine.

Ce que Nova fait a chaque invalidation (ROUGE/decrochage/kill), 1 bot par passe :
  1. concoit une fiche testable (mecanisme, signaux, seuils, frais, kill-criteres) ;
  2. ECRIT le code du bot : une fonction `step(marche, etat, now) -> list[trade]`,
     PUR CALCUL (imports limites a math/statistics/datetime/json), aucune I/O ;
  3. le code est valide par liste blanche AST (rd_runner.valider_code) ; si invalide,
     Nova a droit a 1 seule reecriture, sinon la fiche reste "proposee" (pas activee) ;
  4. si OK et < MAX_ACTIFS bots vivants : ACTIVATION directe (rd/bot_<id>.py + actifs.json) ;
  5. si l'hypothese exige une RESSOURCE que Nova ne peut pas fournir (cle/venue/endpoint
     prive), elle NE code pas : elle emet une DEMANDE Telegram detaillee (tuto) et laisse
     la fiche "en_attente_ressource".
Le rd_runner (workflow rd.yml SANS SECRETS) execute les bots vivants et les TUE selon la
fiche. Nova ne touche aucune cle : les secrets vivent dans d'autres workflows.

Sorties : etat/hypotheses.json + docs/hypotheses.md + rd/bot_<id>.py + rd/actifs.json
+ file Telegram. Sans ANTHROPIC_API_KEY : dormant. stdlib only. MAX_TOKENS 4000.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import rd_runner

ETAT = Path("etat"); DOCS = Path("docs"); RD = Path("rd")
MODELE = os.environ.get("MODELE_STRATEGE", "claude-sonnet-5")
MAX_TOKENS = 10000  # 17/07 : Nova Opus 4.8 pensant + ecrit du CODE (long)
F_HYP = ETAT / "hypotheses.json"
F_VU = ETAT / "stratege_vu.json"
F_ECHECS = ETAT / "stratege_echecs.json"
F_OUT = ETAT / "tresorier_out.json"
F_ACTIFS = RD / "actifs.json"
MAX_ACTIFS = rd_runner.MAX_ACTIFS

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
d'etre invalide ; tu concois UNE hypothese de remplacement ET tu ECRIS son code paper.
REGLES ABSOLUES :
- 100 % paper (0 EUR), aucun conseil d'argent reel, aucune cle a manipuler.
- L'hypothese doit etre FULL-AUTO sur les donnees deja fournies au bot (voir plus bas),
  frais 0,035 %/jambe integres. Pas de plateforme interdite en France (Polymarket exclu),
  pas de books sportifs. INTERDIT de recycler une hypothese deja tuee ou une variante
  cosmetique de celle qui vient de mourir.
- Mecanisme economique PLAUSIBLE, kill-criteres chiffres, prior honnete (la plupart meurent).

ADAPTATIVITE (regle de conception, decision Commandant 17/07) : PRIVILEGIE des parametres
ADAPTATIFS au marche plutot que des seuils FIXES, MAIS sans jamais les caler sur des gains
passes (ce serait du surajustement). Bon = parametre defini comme fonction d'un etat de
marche MESURE dans `marche`/`etat` : ex. seuil d'entree = percentile roulant de |funding|
ou de |ret24h| sur une fenetre que TU maintiens dans `etat` (accumule les observations,
calcule le percentile), taille modulee par la volatilite recente, sortie fonction du regime.
INTERDIT ABSOLU : ajuster un parametre pour que le P&L passe soit meilleur, tester plusieurs
jeux et garder le gagnant, ou coder une valeur 'magique' choisie parce qu'elle aurait marche.
Un parametre adaptatif ne doit ajouter AUCUN degre de liberte cale sur les resultats : il
reagit a l'etat du marche, pas au score. Si tu ne peux pas rendre un seuil adaptatif proprement,
garde-le fixe et documente-le : mieux vaut fixe et honnete qu'adaptatif et surajuste.

LE CODE QUE TU ECRIS ("code_step") — contraintes STRICTES, sinon rejet automatique :
- Tu ecris le CORPS d'un module Python definissant EXACTEMENT :  def step(marche, etat, now):
    * marche = dict {coin: {"mark":float, "funding":float, "vol":float, "oi":float, "ret24h":float}}
      (funding = taux horaire signe ; ret24h = rendement 24 h ; vol = volume notionnel jour).
    * etat = dict PERSISTANT entre les passes (tu y stockes tes positions ouvertes ; il t'est
      redonne tel quel a la passe suivante). now = datetime UTC de la passe (~toutes les 15 min).
    * RETOURNE une list de trades FERMES cette passe, chacun = dict
      {"market":str, "side":str, "size_usd":float (<=100), "entry_price":float, "pnl":float}.
      pnl = gain net en $ APRES frais (borne : |pnl| <= 50 % de size_usd). Mise 100 $ standard.
- IMPORTS AUTORISES UNIQUEMENT : math, statistics, datetime, json. AUCUN autre.
- INTERDIT : open, eval, exec, __import__, acces fichier, acces reseau, globals/locals,
  attributs __xxx__ (dunder). Pur calcul sur `marche` et `etat`. Robuste (try/except,
  .get avec defauts) : une exception tue ton bot.
- Modele de logique : a l'entree, stocke la position dans etat[coin] (mark d'entree, ts,
  side) ; a la sortie (seuil/temps), calcule le pnl funding/prix accumule MOINS 2*0.00035*mise,
  retire de etat, ajoute au resultat. Compte le temps via now - datetime.fromisoformat(ts).

Si l'hypothese EXIGE une donnee/cle/venue que le bot n'a PAS dans `marche` (ex. carnet
d'ordres profond, funding d'une autre venue, cle privee) : ne fournis PAS de code, mets
"code_step":"" et remplis "besoin_ressource" (ce qu'il te faut + tuto precis pour le Commandant).

Tu reponds EXCLUSIVEMENT en JSON valide, schema :
{"fiche":{"titre":"<=70","famille":"carry|reversion|momentum|microstructure|autre",
 "mecanisme":"<=280","signal_entree":"<=200","signal_sortie":"<=150","seuils":"<=150",
 "donnees_requises":"<=150","frais_slippage":"<=120","kill_criteres":"<=150","prior_honnete":"<=150"},
 "code_step":"le corps complet du module python (def step...), ou \\"\\" si ressource manquante",
 "kill":{"n_max":120,"t_min":0.5,"jours_max":45},
 "besoin_ressource":"vide si code fourni ; sinon description + tuto pour le Commandant",
 "resume_telegram":"<=180"}"""


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
    out = []
    for b, v in (gate.get("bots", {}) or {}).items():
        if v.get("statut") == "ROUGE" or v.get("decrochage"):
            out.append(("rouge:%s" % b, b, "; ".join(v.get("raisons", [])) or "ROUGE/decrochage"))
        for av in v.get("avertissements", []):
            if "KILL RECOMMANDE" in av:
                out.append(("kill:%s" % b, b, av))
    return out


def _cible_simulation():
    """Seam de galop d'essai (Commandant) : fait croire a Nova qu'un bot est invalide,
    SANS toucher a la vraie gate (go_reel.json) ni declencher de fausse alerte. Priorite
    env STRATEGE_SIM_KILL, sinon fichier one-shot sim_kill.txt (auto-supprime pour ne pas
    se re-declencher au cron suivant). Dormant par defaut : ni env ni fichier -> "" -> normal."""
    cible = os.environ.get("STRATEGE_SIM_KILL", "").strip()
    if cible:
        return cible
    p = Path("sim_kill.txt")
    try:
        cible = p.read_text(encoding="utf-8").strip()
    except OSError:
        return ""
    try:
        p.unlink()  # one-shot
    except OSError:
        pass
    return cible


def _appel_api(cle, contenu):
    corps = {"model": MODELE, "max_tokens": MAX_TOKENS, "system": SYSTEME,
             "messages": [{"role": "user", "content": contenu}]}
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(corps).encode("utf-8"),
        headers={"x-api-key": cle, "anthropic-version": "2023-06-01",
                 "content-type": "application/json", "User-Agent": "banc-paper-stratege"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError("HTTP %s : %s" % (e.code, e.read().decode("utf-8", "replace")[:300])) from None


def _extraire_json(rep):
    texte = "".join(b.get("text", "") for b in rep.get("content", [])
                    if b.get("type") == "text").strip()
    if texte.startswith("```"):
        texte = texte.strip("`\n ")
        if texte.startswith("json"):
            texte = texte[4:]
    return json.loads(texte)


def _rediger_md(hyps):
    lignes = ["# Registre R&D — hypotheses & bots de Nova (Stratege)",
              "_Nova code et met en service les bots paper en autonomie. Kill auto par la gate._", ""]
    for h in reversed(hyps):
        f = h.get("fiche", {})
        lignes += ["## %s — %s  `[%s]`" % (h.get("id"), f.get("titre", "?"), h.get("statut", "proposee")),
                   "_Declencheur : %s (%s) — %s_" % (h.get("bot_mort"), h.get("cause", "")[:80], str(h.get("date", ""))[:10]),
                   "- **Mecanisme** : %s" % f.get("mecanisme", ""),
                   "- **Entree** : %s · **Sortie** : %s" % (f.get("signal_entree", ""), f.get("signal_sortie", "")),
                   "- **Seuils** : %s · **Frais** : %s" % (f.get("seuils", ""), f.get("frais_slippage", "")),
                   "- **Kill** : %s · **Prior** : %s" % (f.get("kill_criteres", ""), f.get("prior_honnete", "")), ""]
        if h.get("besoin_ressource"):
            lignes.append("- ⛔ **En attente ressource** : %s" % h["besoin_ressource"]); lignes.append("")
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


def _notifier(mid, texte):
    out = _lire_json(F_OUT, {"pending": []})
    out.setdefault("pending", [])
    if not any(m.get("id") == mid for m in out["pending"]):
        out["pending"].append({"id": mid, "texte": texte,
                               "ts": datetime.now(timezone.utc).isoformat()})
        _ecrire_json(F_OUT, out)


def _activer(bot_id, code, kill, fiche):
    """Ecrit rd/bot_<id>.py + inscrit dans actifs.json (le rd_runner l'executera)."""
    try:
        RD.mkdir(parents=True, exist_ok=True)
        (RD / ("bot_%s.py" % bot_id)).write_text(code, encoding="utf-8")
    except OSError:
        return False
    actifs = _lire_json(F_ACTIFS, {"bots": {}})
    actifs.setdefault("bots", {})
    actifs["bots"][bot_id] = {"titre": fiche.get("titre", "?"),
                              "active_depuis": datetime.now(timezone.utc).isoformat(),
                              "kill": kill}
    _ecrire_json(F_ACTIFS, actifs)
    return True


def main():
    gate = _lire_json(DOCS / "go_reel.json", {})
    vu = _lire_json(F_VU, {"traites": []}); vu.setdefault("traites", [])
    nouvelles = [(k, b, c) for k, b, c in _invalidations(gate) if k not in vu["traites"]]
    sim = _cible_simulation()
    if sim:
        k_sim = "sim:%s:%s" % (sim, datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
        nouvelles.insert(0, (k_sim, sim,
                             "SIMULATION galop d'essai (Commandant) : bot repute juge perdant"))
        print("[stratege] SIMULATION demandee sur %s (seam de test)." % sim, flush=True)
    if not nouvelles:
        print("[stratege] aucune invalidation nouvelle — 0 appel, 0 cout.", flush=True)
        return
    actifs = _lire_json(F_ACTIFS, {"bots": {}})
    if len(actifs.get("bots", {})) >= MAX_ACTIFS:
        print("[stratege] %d bots R&D actifs (max) — on attend un kill." % MAX_ACTIFS, flush=True)
        return
    cle = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not cle:
        print("[stratege] invalidation detectee mais pas de cle API — dormant.", flush=True)
        return

    k, bot, cause = nouvelles[0]
    hyps = _lire_json(F_HYP, []); hyps = hyps if isinstance(hyps, list) else []
    donnees = {
        "bot_invalide": {"nom": bot, "cause": cause, "stats": (gate.get("bots", {}) or {}).get(bot, {})},
        "gate_resume": {b: {"statut": v.get("statut"), "n": v.get("n"), "t": v.get("t_stat"),
                            "esp": v.get("esperance")} for b, v in (gate.get("bots", {}) or {}).items()},
        "hypotheses_deja_mortes": list(DEJA_MORTES),
        "fiches_deja_proposees": [h.get("fiche", {}).get("titre", "") for h in hyps],
        "competences": ((ETAT / "competences.md").read_text(encoding="utf-8")[:1500]
                        if (ETAT / "competences.md").exists() else "(vide)"),
    }
    contenu = ("Un bot est invalide. Concois UNE hypothese ET code son step() (JSON) :\n" +
               json.dumps(donnees, ensure_ascii=False, default=str)[:12000] +
               "\n\nProduis ta reponse JSON maintenant.")
    try:
        d = _extraire_json(_appel_api(cle, contenu))
        fiche = d.get("fiche") or {}
        if not fiche.get("titre") or not fiche.get("kill_criteres"):
            raise ValueError("fiche incomplete")
    except Exception as e:                            # noqa: BLE001
        _echec(e); return

    hid = "h%d" % (len(hyps) + 1)
    entree = {"id": hid, "date": datetime.now(timezone.utc).isoformat(),
              "bot_mort": bot, "cause": cause[:150], "fiche": fiche,
              "besoin_ressource": str(d.get("besoin_ressource") or "").strip()}
    code = str(d.get("code_step") or "").strip()
    kill = d.get("kill") if isinstance(d.get("kill"), dict) else {}

    if not code and entree["besoin_ressource"]:
        entree["statut"] = "en_attente_ressource"
        _notifier("rdbesoin:%s" % hid,
                  "🧪 R&D — %s invalide. Nova propose « %s » mais a besoin d'une ressource :\n%s\n"
                  "Reponds via Telegram quand c'est pret." % (bot, fiche.get("titre", "?"),
                                                              entree["besoin_ressource"][:600]))
    elif code:
        ok, motif = rd_runner.valider_code(code)
        if not ok:                                    # 1 seule reecriture autorisee
            try:
                d2 = _extraire_json(_appel_api(
                    cle, contenu + "\n\nTON CODE A ETE REJETE (%s). Reecris `code_step` "
                    "en respectant STRICTEMENT la liste blanche." % motif))
                code = str(d2.get("code_step") or "").strip()
                ok, motif = rd_runner.valider_code(code)
            except Exception:                         # noqa: BLE001
                ok = False
        if ok and _activer(hid, code, kill, fiche):
            entree["statut"] = "actif"
            _notifier("rdactif:%s" % hid,
                      "🧪 R&D — nouveau bot rd_%s EN SERVICE (paper) : « %s »\n%s\n"
                      "Il passe par la meme gate ; s'il est nul il sera tue tout seul. "
                      "Registre : https://bsa-laky.github.io/banc-paper/hypotheses.md"
                      % (hid, fiche.get("titre", "?"), str(d.get("resume_telegram", ""))[:180]))
        else:
            entree["statut"] = "code_rejete (%s)" % motif[:50]
            _notifier("rdrejet:%s" % hid,
                      "🧪 R&D — fiche « %s » retenue mais code auto-rejete (%s). "
                      "Reste a l'etude." % (fiche.get("titre", "?"), motif[:60]))
    else:
        entree["statut"] = "proposee"

    hyps.append(entree)
    _ecrire_json(F_HYP, hyps[-20:])
    _rediger_md(hyps[-20:])
    vu["traites"] = (vu["traites"] + [k])[-40:]
    _ecrire_json(F_VU, vu)
    _ecrire_json(F_ECHECS, {"consecutifs": 0, "maj": datetime.now(timezone.utc).isoformat()})
    print("[stratege] %s -> %s (%s)" % (hid, entree.get("statut"), fiche.get("titre", "")[:50]), flush=True)


if __name__ == "__main__":
    main()
