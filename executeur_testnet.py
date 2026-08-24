#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
executeur_testnet.py - MIROIR TESTNET des bots selecteurs (validation machine + frais).
=======================================================================================
Reflete les positions des bots PILOTES (paper) sur Hyperliquid TESTNET via le portefeuille
(enveloppe 300 EUR) + execution_hl. Verifie le VRAI statut de chaque ordre (pas seulement
le "ok" de l'API), se reconcilie avec les positions reelles (nettoie les fantomes), et
prend prix + univers depuis le TESTNET. Testnet = argent FICTIF. Best-effort, non bloquant.
"""
from __future__ import annotations

import csv
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from bot_27e_arbitre import _parse_ctxs

ETAT = Path("etat")
F_STATE = ETAT / "executeur_testnet.json"
LEDGER = ETAT / "testnet_trades.csv"
PILOTES = ["28_carry_hold", "29_carry_neutre", "29b_carry_neutre_large", "29c_carry_decale"]
FICHIER_ETAT = {"28_carry_hold": "etat_bot28.json", "29_carry_neutre": "etat_bot29.json", "29b_carry_neutre_large": "etat_bot29b.json", "29c_carry_decale": "etat_bot29c.json"}  # noms non standards
FRAIS = 0.00035



def _positions_paper(bet: dict) -> dict:
    """Positions OUVERTES d'un bot paper, quel que soit le format de son etat.

    INCIDENT DU 26-29/07/2026 : la migration vers comptabilite.PositionReelle a
    change le format d'etat des bots 25, 28 et 29, qui ecrivent desormais
        {"positions": {coin: {side, notionnel, mark_entree, ouverte_le, ...}}, ...}
    alors que les executeurs cherchaient l'ancien
        {coin: {"ouvert": true, "side": ..., "entree_ts": ...}}
    Resultat : 'ouverts' etait VIDE et les miroirs ne voyaient plus AUCUNE
    position, sans que rien ne le signale.

    TROISIEME FORMAT (14/08/2026) : le bot 29c tient des PANIERS qui se
    chevauchent, et ecrit
        {"paniers": {"p002": {"ouvert_le": ..., "positions": {coin: {...}}}, ...}}
    Ce lecteur renvoyait donc 0 position pour lui -- exactement la panne muette
    decrite ci-dessus, deuxieme edition. Les jambes de tous les paniers ouverts
    sont desormais fusionnees. Un meme coin peut apparaitre dans plusieurs
    paniers : on AGREGE les notionnels et on garde le sens dominant, parce que
    l'executeur ne tient qu'UNE position par coin sur la venue. Si les deux sens
    s'annulent, la jambe nette est nulle et le coin est simplement omis.

    Ce lecteur accepte les TROIS formats et normalise vers le format attendu.
    """
    paniers = bet.get("paniers")
    if isinstance(paniers, dict) and paniers:
        net = {}
        for pan in paniers.values():
            if not isinstance(pan, dict):
                continue
            for c, v in (pan.get("positions") or {}).items():
                if not isinstance(v, dict):
                    continue
                a = net.setdefault(c, {"n": 0.0, "ts": None})
                a["n"] += float(v.get("side") or 0) * float(v.get("notionnel") or 0)
                ts = v.get("ouverte_le")
                if ts and (a["ts"] is None or ts < a["ts"]):
                    a["ts"] = ts                      # la plus ancienne jambe
        return {c: {"ouvert": True,
                    "side": 1 if a["n"] > 0 else -1,
                    "entree_ts": a["ts"],
                    "notionnel": abs(a["n"])}
                for c, a in net.items() if abs(a["n"]) > 1e-9}

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
            headers={"Content-Type": "application/json", "User-Agent": "banc-paper-executeur"})
        with urllib.request.urlopen(req, timeout=12) as r:
            return json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, OSError):
        return None


# --- LIQUIDITE DU CARNET TESTNET (ajoute le 24/08/2026) ---------------------
# Constat : le testnet n'a pas de contrepartie sur beaucoup de pieces. Mesure du
# 24/08 : CASHCAT cote 21,78 % de spread avec 3 $ de profondeur (0,14 % et
# 1 107 $ sur le mainnet) ; PURR et ZEC ont un carnet VIDE ; HYPE cote 73,16 %.
# Les ordres IOC partaient quand meme et se faisaient refuser avec
# "could not immediately match against any resting orders".
# On refuse donc EN AMONT, et on le journalise comme ILLIQUIDE (pas comme REJET) :
# ce n'est pas un echec de la strategie, c'est une absence de marche.
SPREAD_MAX = 0.01          # 1 % ; au-dela le testnet ne cote plus rien de reel
_BOOK = {}


def _carnet(base_url, coin):
    """{bid, ask, spread, prof_bid, prof_ask} ou None si le carnet est vide."""
    if coin in _BOOK:
        return _BOOK[coin]
    b = _info(base_url, {"type": "l2Book", "coin": coin})
    r = None
    try:
        lv = b["levels"]
        bid, ask = float(lv[0][0]["px"]), float(lv[1][0]["px"])
        if bid > 0 and ask > 0:
            r = {"bid": bid, "ask": ask, "spread": (ask - bid) / bid,
                 "prof_bid": sum(float(x["sz"]) * float(x["px"]) for x in lv[0][:5]),
                 "prof_ask": sum(float(x["sz"]) * float(x["px"]) for x in lv[1][:5])}
    except (KeyError, IndexError, TypeError, ValueError, ZeroDivisionError):
        r = None
    _BOOK[coin] = r
    return r


def _negociable(base_url, coin, notional, side):
    """(bool, motif). side>0 = on achete -> on consomme le cote ASK."""
    c = _carnet(base_url, coin)
    if not c:
        return False, "carnet testnet vide"
    if c["spread"] > SPREAD_MAX:
        return False, "spread testnet %.1f %% (> %.0f %%)" % (c["spread"] * 100, SPREAD_MAX * 100)
    prof = c["prof_ask"] if side > 0 else c["prof_bid"]
    if prof < notional:
        return False, "profondeur %.0f $ < mise %.0f $" % (prof, notional)
    return True, ""


# Bots dont la NEUTRALITE DOLLAR est l'edge : un panier a moitie rempli n'est pas
# une version degradee de la strategie, c'est un pari directionnel. Constat du
# 24/08 : le bot 29 tenait 1 short pour 3 longs sur le testnet (au lieu de 3/3),
# et 29c 9 shorts pour 15 longs. On n'ouvre donc que des PAIRES appariees.
NEUTRES = {"29_carry_neutre", "29b_carry_neutre_large", "29c_carry_decale"}


def _ordre_reussi(resp):
    """Vrai statut d'un ordre HL. (ok: bool, detail). Gere aussi le paper."""
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
    """Set des coins avec une position perp reelle. None si requete impossible (on ne purge pas)."""
    if not account:
        return None
    d = _info(base_url, {"type": "clearinghouseState", "user": account})
    if not isinstance(d, dict):
        return None
    out = set()
    for p in d.get("assetPositions", []):
        pos = p.get("position", {})
        try:
            if abs(float(pos.get("szi", 0))) > 0:
                out.add(pos.get("coin"))
        except (TypeError, ValueError):
            pass
    return out


def executer():
    from execution_hl import ExecutionHL
    from portefeuille import Portefeuille

    ex = ExecutionHL()
    if not ex.cfg.live_arme:
        print("[executeur] live non arme (paper) - dormant.", flush=True)
        return
    if ex.cfg.net != "testnet":
        print("[executeur] SECURITE : refuse hors testnet.", flush=True)
        return
    pf = Portefeuille(executor=ex)

    # prix + univers depuis le TESTNET (coherent avec l'execution)
    data = _parse_ctxs(_info(ex.cfg.base_url, {"type": "metaAndAssetCtxs"}) or [])
    if not data:
        print("[executeur] pas de donnees marche testnet.", flush=True)
        return
    now = datetime.now(timezone.utc)
    state = _lire_json(F_STATE, {})
    rejets = state.setdefault("_rejets", {})   # cle "bot:coin" -> {"n":int,"ts":iso}

    def _rejet_bloque(bot, coin):
        r = rejets.get(bot + ":" + coin)
        if not r or int(r.get("n", 0)) < 3:
            return False
        try:
            age_h = (now - datetime.fromisoformat(str(r.get("ts")))).total_seconds() / 3600
        except (ValueError, TypeError):
            return False
        return age_h < 24.0                    # re-essai autorise apres 24 h

    # RECONCILIATION : purge les positions suivies qui n'existent pas vraiment (fantomes)
    reelles = _positions_reelles(ex.cfg.base_url, ex.cfg.account)
    if reelles is not None:
        for bot in list(state):
            if bot in ("_rejets", "_mises", "_neutralite"):
                # BUG CORRIGE LE 24/08/2026 : "_mises" n'etait pas exclu de la
                # reconciliation. Ses cles sont des NOMS DE BOTS, jamais des coins
                # ouverts, donc elles etaient toutes supprimees a chaque passe.
                # Consequence : `_mises.get(bot) != _mise_now` etait TOUJOURS vrai,
                # la purge des penalites de rejet se declenchait a chaque passe, et
                # `_rejet_bloque` n'atteignait jamais 3. Resultat mesure : 497 rejets
                # CASHCAT en 7 jours sur 449 passes, la ou le garde-fou en autorisait
                # ~1 par jour. Le garde-fou existait, il etait desarme par ce bug.
                continue
            for coin in list(state.get(bot, {})):
                if coin not in reelles:
                    del state[bot][coin]
    # recalcule l'exposition du portefeuille depuis l'etat reconcilie
    pf.expo = {b: round(sum(p.get("notional", 0.0) for p in m.values()), 4)
               for b, m in state.items() if not b.startswith("_")}
    pf._sauver_expo()

    # Cycle de vie : un bot TUE n'a plus personne pour solder ses positions.
    # Constat du 13/08/2026 : le bot 28, tue le 09/08, gardait 7 positions
    # ouvertes sur le testnet, datees du 07/08. Personne ne les fermait parce que
    # son etat paper etait fige : elles n'apparaissaient jamais comme "soldees".
    # En forcant ouverts = {} pour un bot mort, la boucle de fermeture ci-dessous
    # les solde a la passe suivante, et la boucle d'ouverture ne peut rien rouvrir.
    _cv = (_lire_json(ETAT / "cycle_vie.json", {}).get("bots") or {})
    _tues = set(b for b, v in _cv.items() if (v or {}).get("etat") == "kill")

    for bot in PILOTES:
        bet = _lire_json(ETAT / FICHIER_ETAT.get(bot, "etat_%s.json" % bot), {})
        ouverts = {} if bot in _tues else _positions_paper(bet)
        if bot in _tues and state.get(bot):
            print("[executeur] %s est TUE : fermeture de ses %d position(s) testnet."
                  % (bot, len(state[bot])), flush=True)
        mine = state.get(bot, {})

        # GARDE DE CONFIGURATION (14/08/2026). Un bot mal configure partait
        # autrefois a l'ordre coin par coin et remplissait le journal de rejets
        # identiques : 192 lignes "taille arrondie a 0" pour 29b en six jours,
        # sans que rien ne s'allume. On teste UNE fois avant la boucle, on
        # journalise UNE ligne, et on passe au bot suivant. Le journal dit
        # desormais pourquoi, au lieu de repeter le symptome.
        # PURGE DES PENALITES APRES CORRECTION DE CONFIG (14/08/2026).
        # Le compteur de rejets met un coin en pause 24 h apres 3 echecs. Utile
        # quand c'est LE COIN qui refuse ; injuste quand c'est le bot qui etait
        # mal configure : 29b a garde 20 coins sur 29 en pause alors que sa cause
        # (mise a 0,00 $) venait d'etre reparee. Le compteur confondait "ce coin
        # me refuse" et "j'etais mal regle". On memorise donc la mise du bot : si
        # elle change, ses penalites sont effacees -- corriger une config doit
        # prendre effet tout de suite, pas 24 h plus tard.
        _mises = state.setdefault("_mises", {})
        _mise_now = round(pf.taille_entree(bot), 4)
        if _mises.get(bot) != _mise_now:
            _purges = [k for k in list(rejets) if k.startswith(bot + ":")]
            for k in _purges:
                rejets.pop(k, None)
            _mises[bot] = _mise_now
            if _purges:
                print("[executeur] %s : mise passee a %.2f$ -> %d penalite(s) de rejet purgee(s)."
                      % (bot, _mise_now, len(_purges)), flush=True)

        if ouverts:
            _ok, _raison = pf.peut_ouvrir(bot)
            if not _ok and ("ABSENT" in _raison or "mise nulle" in _raison
                            or "plancher" in _raison):
                _log({"ts": now.isoformat(), "bot": bot, "coin": "-",
                      "action": "CONFIG", "side": 0, "notional_usd": 0.0,
                      "mark": 0.0, "resp": _raison[:120]})
                print("[executeur] %s NON EXECUTABLE : %s" % (bot, _raison), flush=True)
                state[bot] = mine
                continue

        # HARMONISATION DU LEVIER SUR LES POSITIONS DEJA OUVERTES (15/08/2026).
        # set_leverage n'etait appele qu'a l'OUVERTURE. Une position ouverte avant
        # un changement de levier gardait donc l'ancien, et immobilisait la marge
        # correspondante jusqu'a sa cloture -- jusqu'a 7 jours (tenue 168 h).
        # Constat du 15/08 : 727 $ de notionnel consommaient 339 $ de marge, soit
        # un levier effectif de 2,1x au lieu de 3x, et le compte saturait a 100 %.
        # Resultat : 34 jambes ouvertes sur les 68 attendues, donc des livres
        # dollar-neutres A MOITIE REMPLIS -- qui ne sont plus neutres du tout.
        # Ce n'est pas un probleme d'argent (testnet), c'est un probleme de MESURE.
        # On aligne donc le levier a chaque passe, y compris sur l'existant :
        # l'operation ne touche pas les positions, elle ne fait que liberer la
        # marge initiale immobilisee a tort.
        if mine:
            _lev = pf.levier(bot)
            for _coin in list(mine):
                try:
                    ex.set_leverage(_coin, _lev)
                except Exception as _e:
                    print("[executeur] levier %s %s KO : %s" % (bot, _coin, _e), flush=True)

        # OUVRIR — en deux temps depuis le 24/08/2026 : on PLANIFIE, puis on execute.
        # Avant, chaque jambe partait seule ; celles dont le carnet testnet etait vide
        # se faisaient refuser et le livre finissait dollar-DESEQUILIBRE, ce qui detruit
        # precisement l'edge que la famille 29 est censee mesurer.
        base_url = ex.cfg.base_url
        candidats = []
        for coin, v in ouverts.items():
            if coin in mine:
                continue
            d = data.get(coin)
            if not d:                       # coin absent du testnet
                continue
            if _rejet_bloque(bot, coin):    # 3 rejets consecutifs -> pause 24 h
                continue
            side = int(v.get("side") or 0) or (-1 if (v.get("premium_entree") or 0) > 0 else (1 if v.get("premium_entree") else 0))
            if side == 0:                   # position sans direction connue (ex. 28 pre-16/07)
                continue
            notion = pf.taille_entree(bot)
            negoc, motif = _negociable(base_url, coin, notion, side)
            if not negoc:
                _log({"ts": now.isoformat(), "bot": bot, "coin": coin, "action": "ILLIQUIDE",
                      "side": side, "notional_usd": round(notion, 2), "mark": d["mark"],
                      "resp": motif[:60]})
                continue
            candidats.append((coin, side))

        # APPARIEMENT : pour un bot dollar-neutre, on n'ouvre que des paires, et on
        # utilise les jambes en trop pour corriger un desequilibre deja present.
        if bot in NEUTRES:
            net = sum(int(p.get("side", 0)) for p in mine.values())   # >0 = trop de longs
            courts = [c for c in candidats if c[1] < 0]
            longs = [c for c in candidats if c[1] > 0]
            k = min(len(courts), len(longs))
            plan = courts[:k] + longs[:k]
            if net > 0:
                plan += courts[k:k + net]
            elif net < 0:
                plan += longs[k:k - net]
            ecarte = len(candidats) - len(plan)
            if ecarte:
                _log({"ts": now.isoformat(), "bot": bot, "coin": "-", "action": "NON_APPARIE",
                      "side": 0, "notional_usd": 0.0, "mark": 0.0,
                      "resp": "%d jambe(s) ecartee(s) : %d courts / %d longs negociables, net %+d"
                              % (ecarte, len(courts), len(longs), net)})
        else:
            plan = candidats

        for coin, side in plan:
            ok, raison = pf.peut_ouvrir(bot)
            if not ok:
                print("[executeur] %s %s non ouvert : %s" % (bot, coin, raison), flush=True)
                break
            d = data.get(coin)
            notion = pf.taille_entree(bot)
            lev = pf.levier(bot)
            ex.set_leverage(coin, lev)     # fixe le levier voulu (1x tant que non promu)
            try:
                r = pf.ouvrir(bot, coin, is_buy=(side > 0), prix_ref=d["mark"])
            except Exception as e:
                print("[executeur] OUVRIR %s %s KO : %s" % (bot, coin, e), flush=True)
                continue
            reussi, detail = _ordre_reussi(r.get("exec"))
            if not reussi:
                pf.cloturer(bot)            # revert l'expo : l'ordre n'est pas passe
                k = bot + ":" + coin
                rejets[k] = {"n": int(rejets.get(k, {}).get("n", 0)) + 1, "ts": now.isoformat()}
                _log({"ts": now.isoformat(), "bot": bot, "coin": coin, "action": "REJET",
                      "side": side, "notional_usd": round(notion, 2), "mark": d["mark"], "resp": str(detail)[:60]})
                print("[executeur] REJET %s %s : %s" % (bot, coin, str(detail)[:80]), flush=True)
                continue
            rejets.pop(bot + ":" + coin, None)
            mine[coin] = {"side": side, "notional": notion, "entry": d["mark"], "ts": now.isoformat()}
            _log({"ts": now.isoformat(), "bot": bot, "coin": coin, "action": "open",
                  "side": side, "notional_usd": round(notion, 2), "mark": d["mark"], "resp": "ok"})
            print("[executeur] OPEN testnet %s %s (%.0f$)" % (bot, coin, notion), flush=True)

        # FERMER : mes positions dont le bot a solde
        for coin in list(mine):
            if coin in ouverts:
                continue
            st = mine[coin]
            d = data.get(coin)
            mark = d["mark"] if d else st["entry"]
            side, entry, notion = st["side"], st["entry"], st["notional"]
            # 24/08/2026 : la cloture ne verifiait PAS son statut. Un ordre refuse
            # (carnet vide) etait soit avale par le except (retente a l'infini sans
            # trace), soit journalise comme "close ok" alors que la position restait
            # ouverte sur la venue. Symptome trouve : AERO tenu 9,8 jours a l'ancienne
            # taille de 16,05 $, tres au-dela de la tenue de 168 h.
            try:
                r = ex.market_close(coin)
            except Exception as e:
                _log({"ts": now.isoformat(), "bot": bot, "coin": coin, "action": "REJET_CLOSE",
                      "side": side, "notional_usd": round(notion, 2), "mark": mark,
                      "resp": str(e)[:60]})
                print("[executeur] FERMER %s %s KO : %s" % (bot, coin, e), flush=True)
                continue
            ferme, det_c = _ordre_reussi(r)
            if not ferme:
                # on GARDE la position dans `mine` : elle sera retentee a la passe
                # suivante. Et on crie si elle traine au-dela de 2x la tenue.
                try:
                    age_h = (now - datetime.fromisoformat(str(st.get("ts")))).total_seconds() / 3600
                except (ValueError, TypeError):
                    age_h = 0.0
                _log({"ts": now.isoformat(), "bot": bot, "coin": coin, "action": "REJET_CLOSE",
                      "side": side, "notional_usd": round(notion, 2), "mark": mark,
                      "resp": ("%s | ouverte depuis %.0f h" % (str(det_c)[:40], age_h))})
                print("[executeur] CLOTURE REFUSEE %s %s (%.0f h) : %s"
                      % (bot, coin, age_h, str(det_c)[:60]), flush=True)
                continue
            ret = side * (mark - entry) / entry if entry else 0.0
            pnl = notion * ret - 2 * FRAIS * notion
            _log({"ts": now.isoformat(), "bot": bot, "coin": coin, "action": "close",
                  "side": side, "notional_usd": round(notion, 2), "mark": mark,
                  "resp": "ok", "pnl_est_usd": round(pnl, 3)})
            pf.cloturer(bot)
            del mine[coin]
            print("[executeur] CLOSE testnet %s %s pnl~%.2f$" % (bot, coin, pnl), flush=True)

        # TRACE DE NEUTRALITE (24/08/2026) : c'est la mesure qui manquait. Un livre
        # cense etre dollar-neutre et qui ne l'est pas ne mesure plus la strategie.
        if bot in NEUTRES and mine:
            brut = sum(p.get("notional", 0.0) for p in mine.values())
            netv = sum(int(p.get("side", 0)) * p.get("notional", 0.0) for p in mine.values())
            ecart = abs(netv) / brut if brut else 0.0
            state.setdefault("_neutralite", {})[bot] = {
                "jambes": len(mine), "brut_usd": round(brut, 2),
                "net_usd": round(netv, 2), "ecart": round(ecart, 4),
                "ts": now.isoformat()}
            if ecart > 0.20:
                print("[executeur] ALERTE neutralite %s : net %+.0f $ sur %.0f $ brut (%.0f %%)"
                      % (bot, netv, brut, 100 * ecart), flush=True)
        state[bot] = mine
    _ecrire_json(F_STATE, state)
    print("[executeur] positions testnet : " +
          " ".join("%s=%d" % (b, len(state.get(b, {}))) for b in PILOTES), flush=True)


if __name__ == "__main__":
    executer()
