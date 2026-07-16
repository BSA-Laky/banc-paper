#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rd_runner.py - HARNAIS des bots R&D generes par Nova (deterministe, 0 LLM).
===========================================================================
Amendement de charte du 16/07/2026 (decision Commandant) : le Stratege code et met
en service les bots PAPER de A a Z sans approbation. Ce harnais rend ca sur :

  DEFENSE EN PROFONDEUR
  1. Ce runner tourne dans un workflow SANS AUCUN SECRET (rd.yml) : meme un code
     genere hostile n'a rien a voler.
  2. Les bots generes sont du PUR CALCUL : pas d'import reseau/fichier/process.
     La liste blanche AST est re-verifiee A CHAQUE passe (pas seulement a l'activation).
  3. Le runner fournit les donnees marche (1 fetch central) et persiste les etats :
     le bot ne touche ni disque ni reseau. Timeout 30 s par bot. Cap 2 bots actifs.
  4. Trades retournes VALIDES (champs, mise <= 200 $, |pnl| <= 50 % de la mise).
  5. KILL AUTOMATIQUE : ROUGE/decrochage a la gate, criteres de la fiche (n_max/t_min/
     jours_max) -> bot deplace dans rd/morts/, hypothese marquee, Telegram notifie.
     La mort alimente Nova (invalidation) -> nouvelle hypothese. Boucle fermee.

Ledger separe rd_trades.csv (memes colonnes que paper_trades.csv), charge par le
moniteur -> les bots R&D passent par LA MEME gate que les autres. GO reel = humain.
"""
from __future__ import annotations

import ast
import csv
import json
import signal
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RD = Path("rd"); MORTS = RD / "morts"
ETAT_RD = Path("etat") / "rd"
F_ACTIFS = RD / "actifs.json"
F_HYP = Path("etat") / "hypotheses.json"
F_OUT = Path("etat") / "tresorier_out.json"
LEDGER_RD = Path("rd_trades.csv")
GOREEL = Path("docs") / "go_reel.json"
CHAMPS = ["bot", "market", "side", "entry_price", "size_usd",
          "opened_at", "closed_at", "exit_price", "pnl", "status"]
MAX_ACTIFS = 2
TIMEOUT_S = 30
MISE_MAX = 200.0

IMPORTS_OK = {"math", "statistics", "datetime", "json", "typing", "__future__"}
NOMS_INTERDITS = {"open", "eval", "exec", "compile", "__import__", "globals", "locals",
                  "vars", "input", "breakpoint", "exit", "quit", "memoryview"}
ATTRS_INTERDITS = {"__globals__", "__builtins__", "__subclasses__", "__bases__",
                   "__code__", "__closure__", "__self__", "__dict__", "__class__",
                   "__mro__", "__init_subclass__", "__reduce__", "__getattribute__"}


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


def _notifier(mid, texte):
    out = _lire_json(F_OUT, {"pending": []})
    out.setdefault("pending", [])
    if any(m.get("id") == mid for m in out["pending"]):
        return
    out["pending"].append({"id": mid, "texte": texte,
                           "ts": datetime.now(timezone.utc).isoformat()})
    _ecrire_json(F_OUT, out)


def valider_code(source):
    """Liste blanche AST : pur calcul uniquement. Renvoie (ok, motif)."""
    try:
        arbre = ast.parse(source)
    except SyntaxError as e:
        return False, "syntaxe : %s" % e
    for noeud in ast.walk(arbre):
        if isinstance(noeud, (ast.Import, ast.ImportFrom)):
            mod = (noeud.module if isinstance(noeud, ast.ImportFrom)
                   else noeud.names[0].name) or ""
            if mod.split(".")[0] not in IMPORTS_OK:
                return False, "import interdit : %s" % mod
        elif isinstance(noeud, ast.Name) and noeud.id in NOMS_INTERDITS:
            return False, "nom interdit : %s" % noeud.id
        elif isinstance(noeud, ast.Attribute) and noeud.attr in ATTRS_INTERDITS:
            return False, "attribut interdit : %s" % noeud.attr
        elif isinstance(noeud, (ast.Global, ast.Nonlocal)):
            return False, "global/nonlocal interdit"
    if "def step" not in source:
        return False, "fonction step absente"
    return True, "ok"


def _fetch_marche():
    """1 fetch central metaAndAssetCtxs -> {coin: {mark, funding, vol, oi, ret24h}}."""
    try:
        req = urllib.request.Request(
            "https://api.hyperliquid.xyz/info",
            data=json.dumps({"type": "metaAndAssetCtxs"}).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "banc-paper-rd"})
        with urllib.request.urlopen(req, timeout=15) as r:
            rep = json.loads(r.read().decode("utf-8"))
        univers = rep[0]["universe"]; ctxs = rep[1]
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
            ValueError, KeyError, IndexError, OSError):
        return {}
    out = {}
    for meta, c in zip(univers, ctxs):
        try:
            mark = float(c.get("markPx") or 0)
            prev = float(c.get("prevDayPx") or 0)
            out[meta["name"]] = {
                "mark": mark,
                "funding": float(c.get("funding") or 0),
                "vol": float(c.get("dayNtlVlm") or 0),
                "oi": float(c.get("openInterest") or 0),
                "ret24h": (mark / prev - 1.0) if prev > 0 else 0.0,
            }
        except (TypeError, ValueError, KeyError):
            continue
    return out


def _import_restreint(nom, *a, **k):
    """__import__ n'autorisant QUE la liste blanche (l'AST l'a deja verifie, ceinture+bretelles)."""
    if nom.split(".")[0] in IMPORTS_OK:
        import importlib
        return importlib.import_module(nom)
    raise ImportError("import '%s' interdit dans un bot R&D" % nom)


class _Timeout(Exception):
    pass


def _alarme(signum, frame):
    raise _Timeout()


def _valider_trade(t):
    try:
        size = float(t["size_usd"]); pnl = float(t["pnl"])
    except (KeyError, TypeError, ValueError):
        return None
    if not (0 < size <= MISE_MAX) or abs(pnl) > 0.5 * size:
        return None
    entry = float(t.get("entry_price") or 1.0) or 1.0
    now_iso = datetime.now(timezone.utc).isoformat()
    return {"bot": "", "market": str(t.get("market", "?"))[:40],
            "side": str(t.get("side", "rd"))[:12],
            "entry_price": entry, "size_usd": size,
            "opened_at": str(t.get("opened_at") or now_iso),
            "closed_at": now_iso,
            "exit_price": entry * (1.0 + pnl / size),
            "pnl": round(pnl, 6), "status": "closed"}


def _journaliser(lignes):
    if not lignes:
        return
    neuf = not LEDGER_RD.exists()
    try:
        with LEDGER_RD.open("a", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=CHAMPS)
            if neuf:
                w.writeheader()
            w.writerows(lignes)
    except OSError:
        pass


def _tuer(bot_id, motif, actifs):
    """Retire un bot : fichier -> rd/morts/, hypothese marquee, Telegram notifie."""
    src = RD / ("bot_%s.py" % bot_id)
    try:
        MORTS.mkdir(parents=True, exist_ok=True)
        if src.exists():
            src.rename(MORTS / src.name)
    except OSError:
        pass
    actifs["bots"] = {k: v for k, v in actifs.get("bots", {}).items() if k != bot_id}
    hyps = _lire_json(F_HYP, [])
    for h in (hyps if isinstance(hyps, list) else []):
        if h.get("id") == bot_id:
            h["statut"] = "kill (%s)" % motif[:60]
    _ecrire_json(F_HYP, hyps)
    _notifier("rdkill:%s" % bot_id,
              "☠ R&D — bot rd_%s TUE (%s). Nova proposera une nouvelle hypothese." % (bot_id, motif))
    print("[rd] KILL %s : %s" % (bot_id, motif), flush=True)


def executer():
    actifs = _lire_json(F_ACTIFS, {"bots": {}})
    actifs.setdefault("bots", {})
    if not actifs["bots"]:
        print("[rd] aucun bot R&D actif.", flush=True)
        return
    gate = (_lire_json(GOREEL, {}) or {}).get("bots", {})
    now = datetime.now(timezone.utc)

    # ---- kills automatiques AVANT execution ----
    for bot_id, meta in list(actifs["bots"].items()):
        nom_gate = "rd_%s" % bot_id
        v = gate.get(nom_gate, {})
        kill = meta.get("kill", {})
        if v.get("statut") == "ROUGE" or v.get("decrochage"):
            _tuer(bot_id, "ROUGE/decrochage a la gate", actifs); continue
        n, t = v.get("n") or 0, v.get("t_stat")
        if n >= int(kill.get("n_max", 120)) and t is not None and t < float(kill.get("t_min", 0.5)):
            _tuer(bot_id, "critere fiche : n=%d t=%.2f < %.2f" % (n, t, float(kill.get("t_min", 0.5))), actifs); continue
        try:
            age_j = (now - datetime.fromisoformat(meta.get("active_depuis"))).days
        except (ValueError, TypeError):
            age_j = 0
        if age_j > int(kill.get("jours_max", 45)) and (t is None or t < 2):
            _tuer(bot_id, "timeout fiche : %d j sans verdict" % age_j, actifs)

    if not actifs["bots"]:
        _ecrire_json(F_ACTIFS, actifs)
        return

    donnees = _fetch_marche()
    if not donnees:
        print("[rd] pas de donnees marche — passe blanche.", flush=True)
        _ecrire_json(F_ACTIFS, actifs)
        return

    for bot_id in list(actifs["bots"]):
        chemin = RD / ("bot_%s.py" % bot_id)
        try:
            source = chemin.read_text(encoding="utf-8")
        except OSError:
            _tuer(bot_id, "fichier introuvable", actifs); continue
        ok, motif = valider_code(source)             # re-verification A CHAQUE passe
        if not ok:
            _tuer(bot_id, "validation AST : %s" % motif, actifs); continue
        etat_p = ETAT_RD / ("etat_%s.json" % bot_id)
        etat = _lire_json(etat_p, {})
        espace = {"__builtins__": {"abs": abs, "min": min, "max": max, "round": round,
                                   "len": len, "sum": sum, "sorted": sorted, "range": range,
                                   "float": float, "int": int, "str": str, "bool": bool,
                                   "dict": dict, "list": list, "tuple": tuple, "set": set,
                                   "enumerate": enumerate, "zip": zip, "isinstance": isinstance,
                                   "ValueError": ValueError, "TypeError": TypeError,
                                   "KeyError": KeyError, "Exception": Exception,
                                   "True": True, "False": False, "None": None,
                                   "abs": abs, "__import__": _import_restreint, "print": print}}
        try:
            signal.signal(signal.SIGALRM, _alarme)
            signal.alarm(TIMEOUT_S)
            exec(compile(source, chemin.name, "exec"), espace)   # noqa: S102 — source validee AST, espace clos, job sans secrets
            trades = espace["step"](donnees, etat, now)
            signal.alarm(0)
        except _Timeout:
            signal.alarm(0)
            _tuer(bot_id, "timeout %ds" % TIMEOUT_S, actifs); continue
        except Exception as e:                        # noqa: BLE001
            signal.alarm(0)
            meta = actifs["bots"][bot_id]
            meta["crashs"] = int(meta.get("crashs", 0)) + 1
            print("[rd] %s a leve : %s" % (bot_id, str(e)[:100]), flush=True)
            if meta["crashs"] >= 5:
                _tuer(bot_id, "5 crashs consecutifs (%s)" % str(e)[:40], actifs)
            continue
        actifs["bots"].get(bot_id, {}).pop("crashs", None)
        _ecrire_json(etat_p, etat)
        lignes = []
        for t in (trades or [])[:20]:                 # cap anti-spam
            lt = _valider_trade(t)
            if lt:
                lt["bot"] = "rd_%s" % bot_id
                lignes.append(lt)
        _journaliser(lignes)
        if lignes:
            print("[rd] %s : %d trade(s) soldes." % (bot_id, len(lignes)), flush=True)
    _ecrire_json(F_ACTIFS, actifs)
    print("[rd] passe terminee — %d bot(s) actif(s)." % len(actifs["bots"]), flush=True)


if __name__ == "__main__":
    executer()
