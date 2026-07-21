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
F_BUDGET = ETAT / "budget_reel.json"


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


_CLAVIER = [
    [{"text": "🛑 Stop réel", "callback_data": "stopreel"},
     {"text": "▶️ Reprendre", "callback_data": "reprends"}],
    [{"text": "📊 Statut", "callback_data": "statut"},
     {"text": "💰 Réel", "callback_data": "reel"}],
    [{"text": "❓ Aide", "callback_data": "aide"}],
]

_AIDE = (
    "🛰 Commandes de la station\n\n"
    "📊 VOIR\n"
    "• statut — état rapide des bots\n"
    "• reel — positions ARGENT RÉEL (bot 28) + P&L\n"
    "• arbitre — dernier avis de l'Arbitre\n"
    "• rapport — rapport du dimanche\n\n"
    "🟢 ARGENT RÉEL (mainnet)\n"
    "• stopreel — 🛑 coupe le réel : ferme tout, n'ouvre plus\n"
    "• reprends — ▶️ relance le réel\n\n"
    "⚙️ PROMOTION D'UN BOT\n"
    "• go <bot> puis confirme <bot> — mise en service (2 étapes, 90 min)\n"
    "• relance <bot> — ressuscite un bot tué\n\n"
    "📝 SUIVI\n"
    "• cout <usd> — note un relevé de coût API\n"
    "• revenu <eur> — note un revenu réel\n"
    "• approve <id> / rejette <id> — consigne pour le Superviseur\n\n"
    "👇 Ou utilise les boutons ci-dessous."
)


def _statut_reel():
    """Positions ARGENT REEL (bot 28) + P&L realise, pour la commande/bouton 'reel'."""
    etat = _lire_json(ETAT / "executeur_reel.json", {})
    stoppe = bool(_lire_json(ETAT / "reel_stop.json", {}).get("stop"))
    L = ["💰 ARGENT RÉEL (mainnet, bot 28)",
         "État : " + ("🛑 STOPPÉ" if stoppe else "▶️ actif")]
    pos = [(c, v) for b, m in etat.items() if b != "_rejets" and isinstance(m, dict)
           for c, v in m.items() if isinstance(v, dict)]
    if pos:
        for c, v in pos:
            sens = "short" if float(v.get("side", 0)) < 0 else "long"
            L.append("• %s %s %.2f$ (entrée %.6g)" % (c, sens, v.get("notional", 0), v.get("entry", 0)))
    else:
        L.append("Aucune position ouverte.")
    try:
        import csv as _csv
        p = ETAT / "reel_trades.csv"
        tot = 0.0; n = 0
        if p.exists():
            for r in _csv.DictReader(p.open(encoding="utf-8")):
                if r.get("action") == "close" and r.get("pnl_est_usd"):
                    tot += float(r["pnl_est_usd"]); n += 1
        L.append("P&L réalisé : %+.2f$ (%d trade(s) soldé(s))" % (tot, n))
    except Exception:                                  # noqa: BLE001
        pass
    return "\n".join(L)


def repondre(st, brief):
    offset = int(st.get("offset", 0))
    traites = 0
    for u in tg.maj(offset):
        offset = max(offset, int(u.get("update_id", 0)) + 1)
        cb = u.get("callback_query")
        if cb:                                         # tap de bouton inline
            chat_id = str(((cb.get("message") or {}).get("chat") or {}).get("id", ""))
            texte = str(cb.get("data", "")).strip()
            tg.accuser_bouton(cb.get("id", ""))
        else:
            msg = u.get("message") or {}
            chat_id = str((msg.get("chat") or {}).get("id", ""))
            texte = str(msg.get("text", "")).strip()
        if chat_id != tg.CHAT_ID:
            continue                                   # on ignore tout autre chat
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
        elif cmd in ("cout", "revenu") and len(mots) >= 2:
            try:
                montant = float(mots[1].replace(",", ".").replace("$", "").replace("e", ""))
            except ValueError:
                tg.envoyer("Format : cout 11.54  (releve console, $)  ou  revenu 12.50 (EUR reels)")
                continue
            b = _lire_json(F_BUDGET, {})
            b = b if isinstance(b, dict) else {}
            cle_b = "releves_api_usd" if cmd == "cout" else "revenus_eur"
            b.setdefault(cle_b, []).append(
                {"date": datetime.now(timezone.utc).isoformat(), "montant": montant})
            b[cle_b] = b[cle_b][-120:]
            b.setdefault("cible_eur", 35.0)
            _ecrire_json(F_BUDGET, b)
            if cmd == "cout":
                tg.envoyer("💸 Releve API enregistre : %.2f $. Le brief suit "
                           "l'autofinancement (cible %.0f EUR)." % (montant, b["cible_eur"]))
            else:
                tot = sum(float(r.get("montant", 0)) for r in b["revenus_eur"])
                reste = max(0.0, float(b["cible_eur"]) - tot)
                tg.envoyer("💰 Revenu REEL enregistre : %.2f EUR. Total %.2f EUR / "
                           "cible %.0f EUR — reste %.2f EUR." % (montant, tot, b["cible_eur"], reste))
        elif cmd == "go" and len(mots) >= 2:
            # DOUBLE GATE (audit 11/07) : "go" ARME seulement ; la mise en service
            # exige un second message distinct "confirme <bot>" sous 90 minutes
            # (17/07 : 30 -> 90, aligné sur la latence réelle des passes GitHub).
            bot = mots[1]
            promo = _lire_json(F_PROMO, {"bots": {}})
            promo.setdefault("bots", {})
            cur = promo["bots"].get(bot, {}).get("etat")
            if cur in ("candidat", "pause"):
                promo["bots"][bot] = {"etat": "arme", "etat_avant": cur,
                                      "arme": datetime.now(timezone.utc).isoformat()}
                _ecrire_json(F_PROMO, promo)
                tg.envoyer("\u23f3 %s ARME (rien ne tourne encore). Pour le mettre en "
                           "service, reponds \u00ab confirme %s \u00bb dans les 90 minutes. "
                           "Sans confirmation, il redeviendra %s." % (bot, bot, cur))
            else:
                tg.envoyer("\u26a0 %s n'est pas 'candidat' (etat: %s). Armement refuse : "
                           "seul le Tresorier fabrique des candidats (checklist VERT-STABLE)."
                           % (bot, cur or "inconnu"))
        elif cmd in ("confirme", "valide") and len(mots) >= 2:
            bot = mots[1]
            promo = _lire_json(F_PROMO, {"bots": {}})
            promo.setdefault("bots", {})
            b = promo["bots"].get(bot, {})
            if b.get("etat") != "arme":
                tg.envoyer("\u26a0 %s n'est pas arme (etat: %s). Envoie d'abord "
                           "\u00ab go %s \u00bb." % (bot, b.get("etat") or "inconnu", bot))
            else:
                try:
                    age_min = (datetime.now(timezone.utc) -
                               datetime.fromisoformat(str(b.get("arme")))).total_seconds() / 60
                except (ValueError, TypeError):
                    age_min = 9999.0
                if age_min > 90:
                    promo["bots"][bot] = {"etat": b.get("etat_avant", "candidat")}
                    _ecrire_json(F_PROMO, promo)
                    tg.envoyer("\u23f0 Armement de %s expire (%.0f min > 90). Redevenu %s. "
                               "Recommence par \u00ab go %s \u00bb."
                               % (bot, age_min, b.get("etat_avant", "candidat"), bot))
                else:
                    promo["bots"][bot] = {"etat": "live",
                                          "confirme": datetime.now(timezone.utc).isoformat()}
                    _ecrire_json(F_PROMO, promo)
                    tg.envoyer("\u2705 %s MIS EN SERVICE (live). Le Tresorier lui alloue "
                               "son enveloppe ; il trade en autonomie sur la venue armee "
                               "(TESTNET aujourd'hui, argent fictif). Retrait = ta main." % bot)
        elif cmd == "relance" and len(mots) >= 2:
            bot = mots[1]
            cv = _lire_json(ETAT / "cycle_vie.json", {})
            cv = cv if isinstance(cv, dict) else {}
            cv.setdefault("bots", {})
            if cv["bots"].get(bot, {}).get("etat") == "kill":
                cv["bots"][bot] = {"etat": "actif",
                                   "relance": datetime.now(timezone.utc).isoformat()}
                _ecrire_json(ETAT / "cycle_vie.json", cv)
                tg.envoyer("\u267b %s RELANCE par le Commandant : de nouveau "
                           "echantillonne des la prochaine passe (paper). L'auto-kill "
                           "ne s'appliquera plus a ce bot (main humaine)." % bot)
            else:
                tg.envoyer("%s n'est pas au tapis (cycle de vie : %s)."
                           % (bot, cv["bots"].get(bot, {}).get("etat", "actif")))
        elif cmd in ("stopreel", "stop", "coupe"):
            _ecrire_json(ETAT / "reel_stop.json",
                         {"stop": True, "ts": datetime.now(timezone.utc).isoformat()})
            tg.envoyer("\ud83d\uded1 STOP R\u00c9EL activ\u00e9. \u00c0 la prochaine passe (~15 min), l'ex\u00e9cuteur "
                       "mainnet ferme toutes les positions r\u00e9elles et n'en ouvre plus. "
                       "Pour relancer : \u00ab reprends \u00bb.", boutons=_CLAVIER)
        elif cmd in ("reprends", "repars", "reprendsreel"):
            _ecrire_json(ETAT / "reel_stop.json",
                         {"stop": False, "ts": datetime.now(timezone.utc).isoformat()})
            tg.envoyer("\u25b6\ufe0f R\u00e9el RELANC\u00c9. L'ex\u00e9cuteur mainnet reprend le miroir du bot 28 "
                       "d\u00e8s la prochaine passe.", boutons=_CLAVIER)
        elif cmd in ("reel", "mainnet"):
            tg.envoyer(_statut_reel(), boutons=_CLAVIER)
        elif cmd in ("aide", "menu", "help", "start", "commandes"):
            tg.envoyer(_AIDE, boutons=_CLAVIER)
        else:
            tg.envoyer("Commande inconnue. Tape \u00ab aide \u00bb ou utilise les boutons \ud83d\udc47",
                       boutons=_CLAVIER)
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
    if not st.get("aide_v2"):
        tg.envoyer("🆕 Nouveau : contrôle du RÉEL depuis Telegram + boutons.\n\n" + _AIDE,
                   boutons=_CLAVIER)
        st["aide_v2"] = True
    n = notifier(st, brief, regime)
    notifier_tresorier(st)
    c = repondre(st, brief)
    _ecrire_json(F_NOTIF, st)
    print(f"[gateway] {n} notification(s), {c} commande(s) traitee(s).", flush=True)


if __name__ == "__main__":
    main()
