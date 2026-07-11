#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
telegram_gateway.py - le gateway messagerie de la station (pattern Hermes)
==========================================================================
Toutes les ~15 min (workflow telegram.yml), deterministe, 0 token LLM :

SORTANT (notifications push iPhone, dedupliquees) :
  - nouvelles ALERTES du brief (gate + pannes d'equipage, rappel 1x/jour max)
  - nouveau verdict quotidien de l'Arbitre (regime + confiance + resume)
  - nouveau rapport hebdo du Superviseur

ENTRANT (commandes du Commandant UNIQUEMENT — chat_id verifie, liste blanche
a correspondance exacte, jamais d'ordre de trade ni d'execution de texte) :
  statut | arbitre | rapport | aide
  approve <id> / rejette <id>  -> consigne dans etat/decisions_commandant.json
                                  (relu par le Superviseur chaque dimanche)

Sans secrets TELEGRAM_TOKEN / TELEGRAM_CHAT_ID : sortie propre, station intacte.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import tg

ETAT = Path("etat"); DOCS = Path("docs")
F_NOTIF = ETAT / "tg_notifie.json"
F_DECISIONS = ETAT / "decisions_commandant.json"
F_TRESO_OUT = ETAT / "tresorier_out.json"
F_PROMO = Path("promotions.json")


def _lire_json(p, defaut):
    try:
        with Path(p).open(encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return defaut


def _lire_texte(p, cap=3500):
    try:
        return Path(p).read_text(encoding="utf-8")[:cap]
    except OSError:
        return ""


def _ecrire_json(p, d):
    try:
        Path(p).parent.mkdir(parents=True, exist_ok=True)
        Path(p).write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        pass


# ------------------------------------------------------------------ sortant
def notifier(st, brief, regime):
    jour = datetime.now(timezone.utc).date().isoformat()
    envoyes = 0

    # alertes gate + pannes equipage (cle jour:texte -> rappel 1x/jour)
    alertes = list(brief.get("alertes", []))
    alertes += [f"EQUIPAGE : {p}" for p in
                (brief.get("sante_equipage") or {}).get("problemes", [])]
    if brief.get("banc_suspect"):
        alertes.append("BANC SUSPECT : temoin |t| >= 2 — ne rien conclure")
    deja = st.setdefault("alertes_envoyees", [])
    for a in alertes:
        cle = f"{jour}:{a}"
        if cle not in deja:
            if tg.envoyer(f"🔴 STATION — ALERTE\n{a}\n\n"
                          f"Brief : https://bsa-laky.github.io/banc-paper/brief.md"):
                deja.append(cle); envoyes += 1
    st["alertes_envoyees"] = deja[-60:]

    # verdict quotidien de l'Arbitre
    date_avis = str(regime.get("date", ""))
    if date_avis and date_avis != st.get("dernier_avis"):
        if tg.envoyer(f"🤖 Arbitre — regime {regime.get('regime','?').upper()} "
                      f"(confiance {regime.get('confiance','?')})\n"
                      f"{regime.get('resume','')}"):
            st["dernier_avis"] = date_avis; envoyes += 1

    # rapport hebdo du Superviseur
    rapport = _lire_texte(DOCS / "rapport_semaine.md", 1200)
    entete = rapport.split("\n", 1)[0] if rapport else ""
    if entete and entete != st.get("dernier_rapport"):
        if tg.envoyer(f"📋 {entete}\n\n{rapport[len(entete):900].strip()}\n\n"
                      f"Complet : https://bsa-laky.github.io/banc-paper/rapport_semaine.md"):
            st["dernier_rapport"] = entete; envoyes += 1
    return envoyes


def notifier_tresorier(st):
    """Draine la file d'interpellations du Tresorier (etat/tresorier_out.json)."""
    q = _lire_json(F_TRESO_OUT, {"pending": []})
    pend = q.get("pending", []) if isinstance(q, dict) else []
    restant = []
    envoyes = 0
    for m in pend:
        if tg.envoyer("\U0001F4B0 TRESORIER\n" + str(m.get("texte", ""))):
            envoyes += 1
        else:
            restant.append(m)
    if pend:
        _ecrire_json(F_TRESO_OUT, {"pending": restant})
    return envoyes


# ------------------------------------------------------------------ entrant
def _statut_court(brief):
    s = brief.get("statuts", {})
    comptes = {}
    for v in s.values():
        comptes[v.get("statut", "?")] = comptes.get(v.get("statut", "?"), 0) + 1
    lignes = [f"⬢ STATION — {str(brief.get('ts',''))[:16]} UTC",
              f"Bots {len(s)} : " + " · ".join(f"{k} {n}" for k, n in sorted(comptes.items())),
              f"Alertes : {len(brief.get('alertes', []))}"]
    sante = brief.get("sante_equipage") or {}
    lignes.append("Equipage : " + ("⚠ " + " ; ".join(sante.get("problemes", []))
                                   if sante.get("problemes") else "OK"))
    tb = brief.get("tendances_btc")
    if tb:
        lignes.append(f"BTC {tb.get('prix','?')} $ (7j {tb.get('ret7',0)*100:+.1f} %)")
    interessants = [f"{b} {v.get('statut')} n={v.get('n')} t={v.get('t')}"
                    for b, v in sorted(s.items())
                    if v.get('statut') in ('VERT', 'ROUGE') or abs(v.get('t') or 0) >= 2]
    if interessants:
        lignes.append("A l'oeil : " + " | ".join(interessants[:5]))
    return "\n".join(lignes)


def repondre(st, brief):
    offset = int(st.get("offset", 0))
    traites = 0
    for u in tg.maj(offset):
        offset = max(offset, int(u.get("update_id", 0)) + 1)
        msg = u.get("message") or {}
        if str((msg.get("chat") or {}).get("id", "")) != tg.CHAT_ID:
            continue                                   # on ignore tout autre chat
        texte = str(msg.get("text", "")).strip()
        mots = texte.lower().split()
        if not mots:
            continue
        cmd = mots[0]
        traites += 1
        if cmd in ("statut", "status"):
            tg.envoyer(_statut_court(brief))
        elif cmd == "arbitre":
            tg.envoyer(_lire_texte(DOCS / "arbitre.md") or "Pas encore d'avis.")
        elif cmd == "rapport":
            tg.envoyer(_lire_texte(DOCS / "rapport_semaine.md") or "Pas encore de rapport.")
        elif cmd in ("approve", "rejette") and len(mots) >= 2:
            decisions = _lire_json(F_DECISIONS, [])
            decisions = decisions if isinstance(decisions, list) else []
            decisions.append({"date": datetime.now(timezone.utc).isoformat(),
                              "commande": cmd, "cible": mots[1][:24]})
            _ecrire_json(F_DECISIONS, decisions[-30:])
            tg.envoyer(f"✔ Consigne « {cmd} {mots[1]} » enregistree — "
                       f"le Superviseur la lira dimanche.")
        elif cmd in ("go", "confirme", "valide") and len(mots) >= 2:
            bot = mots[1]
            promo = _lire_json(F_PROMO, {"bots": {}})
            promo.setdefault("bots", {})
            cur = promo["bots"].get(bot, {}).get("etat")
            if cur in ("candidat", "pause"):
                promo["bots"][bot] = {"etat": "live",
                                      "confirme": datetime.now(timezone.utc).isoformat()}
                _ecrire_json(F_PROMO, promo)
                tg.envoyer(f"\u2705 {bot} MIS EN SERVICE (live). Le Tresorier lui alloue son "
                           f"enveloppe ; il trade desormais en autonomie. Retrait = ta main.")
            else:
                tg.envoyer(f"\u26a0 {bot} n'est pas 'candidat' (etat: {cur or 'inconnu'}). "
                           f"Mise en service refusee.")
        else:
            tg.envoyer("Commandes : statut · arbitre · rapport · "
                       "approve <id> · rejette <id> · go <bot>\n"
                       "(lecture seule — aucun ordre de trade possible par ici)")
    st["offset"] = offset
    return traites


def main():
    if not tg.actif():
        print("[gateway] secrets Telegram absents — mode veille.", flush=True)
        return
    st = _lire_json(F_NOTIF, {})
    st = st if isinstance(st, dict) else {}
    premiere = not st
    brief = _lire_json(DOCS / "brief.json", {})
    regime = _lire_json(ETAT / "regime_ia.json", {})
    if premiere:
        tg.envoyer("🛰 STATION CONNECTEE — le gateway Telegram est actif.\n"
                   "Tape « aide » pour les commandes. Les alertes, le verdict "
                   "quotidien de l'Arbitre et le rapport du dimanche arriveront ici.")
    n = notifier(st, brief, regime)
    notifier_tresorier(st)
    c = repondre(st, brief)
    _ecrire_json(F_NOTIF, st)
    print(f"[gateway] {n} notification(s), {c} commande(s) traitee(s).", flush=True)


if __name__ == "__main__":
    main()
