#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
executeur_reel.py - EXECUTEUR MAINNET (ARGENT REEL) du bot 28, rails stricts.
============================================================================
Jumeau de executeur_testnet.py, mais :
  - REFUSE tout ce qui n'est pas mainnet + live arme (symetrique du verrou testnet).
  - PILOTES = ["28_carry_hold"] UNIQUEMENT (edge confirme t 2.52 ; pas les selecteurs).
  - Taille calee sur le capital reel via PORTEFEUILLE_CONFIG=portefeuille.reel.json
    (enveloppe ~12 $, levier force 1x sur mainnet tant que kelly non confirme).
  - Plafond d'exposition totale CAP_TOTAL_USD en plus du plafond par ordre HL_MAX_NOTIONAL.
  - KILL-SWITCH : etat/reel_stop.json {"stop": true} -> ferme tout, n'ouvre plus rien.
  - Etat + journal separes (etat/executeur_reel.json, etat/reel_trades.csv).
Le wallet AGENT (trade-only) ne peut PAS retirer : perte bornee au depot. Best-effort.
"""
from __future__ import annotations

import csv
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from bot_27e_arbitre import _parse_ctxs

ETAT = Path("etat")
F_STATE = ETAT / "executeur_reel.json"
LEDGER = ETAT / "reel_trades.csv"
F_STOP = ETAT / "reel_stop.json"
def _pilotes_reels():
    """SOURCE UNIQUE des bots reels = portefeuille.reel.json (cles 'bots'). Ajouter un bot
    reel = editer CE fichier UNIQUEMENT (synergie B, 23/07). Defaut sur 28 si illisible."""
    try:
        cfg = json.loads(Path(os.environ.get("PORTEFEUILLE_CONFIG", "portefeuille.reel.json"))
                         .read_text(encoding="utf-8"))
        return list((cfg.get("bots") or {}).keys()) or ["28_carry_hold"]
    except (OSError, ValueError):
        return ["28_carry_hold"]


PILOTES = _pilotes_reels()
FICHIER_ETAT = {"28_carry_hold": "etat_bot28.json"}
FRAIS = 0.00035
CAP_TOTAL_USD = 850.0   # exposition reelle totale plafonnee (marge de securite sous le depot)



def _positions_paper(bet: dict) -> dict:
    """Positions OUVERTES d'un bot paper, quel que soit le format de son etat.

    INCIDENT DU 26-29/07/2026 : la migration vers comptabilite.PositionReelle a
    change le format d'etat des bots 28 et 29, qui ecrivent desormais
        {"positions": {coin: {side, notionnel, mark_entree, ouverte_le, ...}}, ...}
    alors que les executeurs cherchaient l'ancien
        {coin: {"ouvert": true, "side": ..., "entree_ts": ...}}
    Resultat : 'ouverts' etait VIDE, les miroirs testnet et mainnet ne voyaient
    plus AUCUNE position, et le bot 28 reel est reste aveugle 3 jours sans que
    rien ne le signale (dernier fill reel : 26/07 10:31).

    Ce lecteur accepte les DEUX formats et normalise vers le format attendu
    (cle "side" + "entree_ts"), pour que l'ajout d'un bot ne puisse plus casser
    silencieusement l'execution.
    """
    pos = bet.get("positions")
    if isinstance(pos, dict) and pos:
        return {c: {"ouvert": True,
                    "side": v.get("side"),
                    "entree_ts": v.get("ouverte_le"),
                    "notionnel": v.get("notionnel")}
                for c, v in pos.items() if isinstance(v, dict)}
    return {c: v for c, v in bet.items() if isinstance(v, dict) and v.get("ouvert")}

def _lire_json(p, d):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return d


def _ecrire_json(p, d):
    try:
        Path(p).parent.mkdir(parents=True, exist_ok=True)
        Path(p).write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


def _log(row):
    try:
        ETAT.mkdir(parents=True, exist_ok=True)
        neuf = not LEDGER.exists()
        with LEDGER.open("a", newline="", encoding="utf-8") as fh:
            cols = ["ts", "bot", "coin", "action", "side", "notional_usd", "mark", "resp", "pnl_est_usd"]
            w = csv.DictWriter(fh, fieldnames=cols)
            if neuf:
                w.writeheader()
            w.writerow({k: row.get(k, "") for k in cols})
    except OSError:
        pass


def _info(base_url, body):
    try:
        req = urllib.request.Request(base_url + "/info", data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "banc-paper-reel"})
        with urllib.request.urlopen(req, timeout=12) as r:
            return json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, OSError):
        return None


def _ordre_reussi(resp):
    if isinstance(resp, dict) and resp.get("status") == "paper_simule":
        return True, "paper"
    try:
        st = resp["response"]["data"]["statuses"][0]
    except (KeyError, IndexError, TypeError):
        return False, "reponse inattendue"
    if isinstance(st, dict) and "error" in st:
        return False, st["error"]
    return True, st


def _positions_reelles(base_url, account):
    """Positions REELLES {coin: {szi, entry, valeur}}. None si reponse INCOMPLETE
    (24/07 : on ne purge JAMAIS sur un doute -- une purge a tort rouvre un ordre reel)."""
    if not account:
        return None
    d = _info(base_url, {"type": "clearinghouseState", "user": account})
    if not isinstance(d, dict) or "marginSummary" not in d:
        return None
    out = {}
    for p in d.get("assetPositions", []):
        pos = p.get("position", {})
        try:
            szi = float(pos.get("szi", 0))
            if abs(szi) > 0:
                out[pos.get("coin")] = {"szi": szi,
                                        "entry": float(pos.get("entryPx") or 0),
                                        "valeur": abs(float(pos.get("positionValue") or 0))}
        except (TypeError, ValueError):
            pass
    return out


def _entree_autorisee(v, d, now, seuil_f, age_max_h):
    """REGLE FIGEE 15/07 appliquee au reel (24/07) + anti-entree tardive.
    - trades RICHES seulement : |funding| courant >= seuil_funding_reel
      (l'addendum AUDIT_BOT28 : sans filtre, coef de survie ~0,31 -> le reel perdait) ;
    - episode paper FRAIS seulement : entrer > age_max_entree_h apres le signal =
      payer entree+sortie pour la fin d'un episode deja consomme (cause n1 des
      pertes reelles constatees, ex. JUP ouvert 46 min avant sa sortie)."""
    f = abs(float(d.get("funding") or 0.0))
    if f < seuil_f:
        return False, "funding %.4f%%/h < seuil reel %.4f%%/h (regle figee 15/07)" % (100 * f, 100 * seuil_f)
    try:
        age_h = (now - datetime.fromisoformat(str(v.get("entree_ts")))).total_seconds() / 3600.0
    except (ValueError, TypeError):
        return False, "entree_ts paper illisible -> pas d'entree a l'aveugle"
    if age_h > age_max_h:
        return False, "episode paper vieux de %.1f h > %.0f h (entree tardive interdite)" % (age_h, age_max_h)
    return True, "ok"


def _reconcilier_suivi(state, reelles, pilotes, now, log):
    """ADOPTION (24/07) : position presente sur HL mais suivie nulle part ->
    adoptee par le 1er pilote (redevient visible, fermable par age/kill-switch,
    comptee). Fin des positions invisibles du dashboard."""
    if reelles is None:
        return
    for coin, ph in reelles.items():
        if any(coin in (state.get(b) or {}) for b in state if b != "_rejets") or not pilotes:
            continue
        cible = pilotes[0]
        state.setdefault(cible, {})[coin] = {
            "side": 1 if ph["szi"] > 0 else -1, "notional": round(ph["valeur"], 2),
            "entry": ph["entry"], "ts": now.isoformat(), "adopte": True}
        log({"ts": now.isoformat(), "bot": cible, "coin": coin, "action": "adopt",
             "side": 1 if ph["szi"] > 0 else -1, "notional_usd": round(ph["valeur"], 2),
             "mark": ph["entry"], "resp": "position HL non suivie -> adoptee"})


def executer():
    from execution_hl import ExecutionHL
    from portefeuille import Portefeuille

    ex = ExecutionHL()
    # --- VERROUS MAINNET (symetriques du verrou testnet) ---
    if not ex.cfg.live_arme:
        print("[reel] live non arme (HL_MODE=live + HL_LIVE_CONFIRM) - dormant, aucun ordre.", flush=True)
        return
    if ex.cfg.net != "mainnet":
        print("[reel] SECURITE : cet executeur REFUSE hors mainnet (net=%s)." % ex.cfg.net, flush=True)
        return

    pf = Portefeuille(executor=ex)
    data = _parse_ctxs(_info(ex.cfg.base_url, {"type": "metaAndAssetCtxs"}) or [])
    if not data:
        print("[reel] pas de donnees marche mainnet.", flush=True)
        return
    now = datetime.now(timezone.utc)
    cfg_reel = _lire_json(Path(os.environ.get("PORTEFEUILLE_CONFIG", "portefeuille.reel.json")), {})
    seuil_f = float(cfg_reel.get("seuil_funding_reel", 0.0003))
    age_max_h = float(cfg_reel.get("age_max_entree_h", 2.0))
    hold_max_h = float(cfg_reel.get("hold_max_h", 50.0))
    state = _lire_json(F_STATE, {})
    rejets = state.setdefault("_rejets", {})
    stop = bool(_lire_json(F_STOP, {}).get("stop"))

    def _rejet_bloque(bot, coin):
        r = rejets.get(bot + ":" + coin)
        if not r or int(r.get("n", 0)) < 3:
            return False
        try:
            age_h = (now - datetime.fromisoformat(str(r.get("ts")))).total_seconds() / 3600
        except (ValueError, TypeError):
            return False
        return age_h < 24.0

    # RECONCILIATION : purge les fantomes (positions suivies non reelles)
    reelles = _positions_reelles(ex.cfg.base_url, ex.cfg.account)
    if reelles is not None:
        for bot in list(state):
            if bot == "_rejets":
                continue
            for coin in list(state.get(bot, {})):
                if coin not in reelles:
                    (_log({"ts": now.isoformat(), "bot": bot, "coin": coin, "action": "close", "side": state[bot][coin].get("side",0), "notional_usd": round(state[bot][coin].get("notional",0),2), "mark": (data.get(coin) or {}).get("mark",""), "resp": "purge externe (liquidation/fermeture)", "pnl_est_usd": round(state[bot][coin].get("side",0)*((data.get(coin) or {}).get("mark", state[bot][coin].get("entry",0))-state[bot][coin].get("entry",0))/(state[bot][coin].get("entry",1) or 1)*state[bot][coin].get("notional",0),3)}), state[bot].pop(coin))
    _reconcilier_suivi(state, reelles, PILOTES, now, _log)
    pf.expo = {b: round(sum(p.get("notional", 0.0) for p in m.values()), 4)
               for b, m in state.items() if b != "_rejets"}
    pf._sauver_expo()

    def _expo_totale():
        return sum(p.get("notional", 0.0) for b, m in state.items() if b != "_rejets" for p in m.values())

    for bot in PILOTES:
        bet = _lire_json(ETAT / FICHIER_ETAT.get(bot, "etat_%s.json" % bot), {})
        ouverts = {} if stop else _positions_paper(bet)
        mine = state.get(bot, {})

        # OUVRIR (jamais si kill-switch actif)
        for coin, v in ouverts.items():
            if coin in mine:
                continue
            d = data.get(coin)
            if not d:
                continue
            if _rejet_bloque(bot, coin):
                continue
            ok_entree, pourquoi = _entree_autorisee(v, d, now, seuil_f, age_max_h)
            if not ok_entree:
                print("[reel] %s %s NON ouvert : %s" % (bot, coin, pourquoi), flush=True)
                continue
            notion = pf.taille_entree(bot)
            if _expo_totale() + notion > CAP_TOTAL_USD + 1e-9:
                print("[reel] %s %s non ouvert : plafond total %.0f$ atteint (%.2f$ deployes)"
                      % (bot, coin, CAP_TOTAL_USD, _expo_totale()), flush=True)
                continue
            ok, raison = pf.peut_ouvrir(bot)
            if not ok:
                print("[reel] %s %s non ouvert : %s" % (bot, coin, raison), flush=True)
                continue
            side = int(v.get("side") or 0)
            if side == 0:
                continue
            lev = pf.levier(bot)          # force 1x sur mainnet (garde-fou portefeuille)
            if (ex.set_leverage(coin, lev) or {}).get("status") != "ok": print("[reel] %s %s NON ouvert : levier 1x non confirme -> skip (rail)" % (bot, coin), flush=True); continue
            try:
                r = pf.ouvrir(bot, coin, is_buy=(side > 0), prix_ref=d["mark"])
            except Exception as e:
                print("[reel] OUVRIR %s %s KO : %s" % (bot, coin, e), flush=True)
                continue
            reussi, detail = _ordre_reussi(r.get("exec"))
            if not reussi:
                pf.cloturer(bot)
                k = bot + ":" + coin
                rejets[k] = {"n": int(rejets.get(k, {}).get("n", 0)) + 1, "ts": now.isoformat()}
                _log({"ts": now.isoformat(), "bot": bot, "coin": coin, "action": "REJET",
                      "side": side, "notional_usd": round(notion, 2), "mark": d["mark"], "resp": str(detail)[:60]})
                print("[reel] REJET %s %s : %s" % (bot, coin, str(detail)[:80]), flush=True)
                continue
            rejets.pop(bot + ":" + coin, None)
            mine[coin] = {"side": side, "notional": notion, "entry": d["mark"], "ts": now.isoformat()}
            _log({"ts": now.isoformat(), "bot": bot, "coin": coin, "action": "open",
                  "side": side, "notional_usd": round(notion, 2), "mark": d["mark"], "resp": "ok"})
            print("[reel] OPEN MAINNET %s %s (%.2f$)" % (bot, coin, notion), flush=True)

        # FERMER : positions soldees par le bot, OU tout si kill-switch
        for coin in list(mine):
            st = mine[coin]
            try:
                age_reel_h = (now - datetime.fromisoformat(str(st.get("ts")))).total_seconds() / 3600.0
            except (ValueError, TypeError):
                age_reel_h = 0.0
            trop_vieux = age_reel_h >= hold_max_h
            if (not stop) and (coin in ouverts) and not trop_vieux:
                continue
            d = data.get(coin)
            mark = d["mark"] if d else st["entry"]
            side, entry, notion = st["side"], st["entry"], st["notional"]
            try:
                r = ex.market_close(coin)
            except Exception as e:
                print("[reel] FERMER %s %s KO : %s" % (bot, coin, e), flush=True)
                continue
            ret = side * (mark - entry) / entry if entry else 0.0
            pnl = notion * ret - 2 * FRAIS * notion
            _log({"ts": now.isoformat(), "bot": bot, "coin": coin, "action": "close",
                  "side": side, "notional_usd": round(notion, 2), "mark": mark,
                  "resp": "STOP" if stop else ("AGE %.0fh" % age_reel_h if trop_vieux else "ok"),
                  "pnl_est_usd": round(pnl, 3)})
            pf.cloturer(bot)
            del mine[coin]
            print("[reel] CLOSE MAINNET %s %s pnl~%.2f$%s" % (bot, coin, pnl, " (KILL-SWITCH)" if stop else ""), flush=True)

        state[bot] = mine
    _ecrire_json(F_STATE, state)
    if stop:
        print("[reel] KILL-SWITCH ACTIF (etat/reel_stop.json) : tout ferme, aucune ouverture.", flush=True)
    print("[reel] positions mainnet : " +
          " ".join("%s=%d" % (b, len(state.get(b, {}))) for b in PILOTES) +
          " | expo totale ~%.2f$" % _expo_totale(), flush=True)
    try:      # RECONCILIATION avec la verite HL -> etat/reel_hl.json (jamais bloquant)
        import reconcil_hl
        reconcil_hl.produire(ex.cfg.base_url, ex.cfg.account,
                             float(cfg_reel.get("depot_usdc", 0) or 0))
    except Exception as e:
        print("[reel] reconcil HL KO (non bloquant) : %s" % e, flush=True)


if __name__ == "__main__":
    executer()
