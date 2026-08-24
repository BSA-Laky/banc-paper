#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
jalon_29.py - JALON DE CONTROLE A UN MOIS POUR LA FAMILLE 29 (15/08/2026)
=========================================================================
LE PROBLEME QU'IL RESOUT
------------------------
La gate du bot 29 exige n >= 100 paniers. A 6 jambes par semaine, elle rendra
son verdict en ~5 mois. Or son t-stat, lui, atteindrait 2 en un mois. Le goulot
n'est pas la statistique, c'est la REGLE.

On ne touche PAS a n_go (decision du 15/08). A la place on pose un JALON :
un critere fige A PRIORI, evalue le 15/09/2026, qui ne peut que RACCOURCIR
l'attente, jamais autoriser de l'argent reel.

    JALON REUSSI  -> on continue jusqu'a n_go, en confiance
    JALON ECHOUE  -> l'hypothese est morte, on arrete d'attendre 4 mois de plus
    ENTRE LES DEUX-> on continue, sans conclusion

CE QUE LE JALON MESURE, ET POURQUOI PAS LE P&L
-----------------------------------------------
Le P&L d'un panier = prix + funding - frais. Le terme de PRIX a un ecart-type
de 3,4 %/semaine contre une esperance nulle : c'est du bruit pur, et il ecrase
tout. C'est lui, et lui seul, qui impose n = 100.

L'edge du bot 29 n'a jamais ete un edge de prix. Il a ete prouve par
DECOMPOSITION sur 7 mois d'historique HL :

    funding capte : +0,4602 %/sem  t=+5,67 (TRAIN)   +0,3075 %/sem  t=+5,20 (OOS)
    prix          : indiscernable de zero (t +0,26 / +0,71)
    frais         : deterministes

Donc on mesure le FUNDING CAPTE, pas le P&L. Sur la composante funding, dont
l'ecart-type hebdomadaire vaut ~0,21 %, quatre paniers suffisent a atteindre
t ~ 3 si l'effet historique tient. C'est ca, le jalon.

CRITERE — CORRIGE LE 24/08/2026 (le critere du 15/08 etait FAUX)
-----------------------------------------------------------------
La v1 declarait REUSSI sur la seule capture de funding, au motif que le terme de
prix est "du bruit d'esperance nulle". Le 24/08, les donnees ont montre que c'est
faux en pratique : le bot 29c capte +0,671 %/panier de funding avec t = +9,71 et
affiche pourtant **t = -0,78 sur son P&L reel** (n=120, P&L -6,40 $).

Le jalon allait donc rendre un verdict REUSSI sur un bot perdant. C'est exactement
le faux vert que le bot 25 avait produit le 05/08 (t 3,56 annonce, -3,32 reel) et
que tout ce dispositif existe pour empecher. La capture de funding est une
CONDITION NECESSAIRE, jamais suffisante.

Au 15/09/2026, sur les paniers CLOS depuis le 15/08 :
    REUSSI    : t(funding) CORRIGE >= 2,0  ET  funding moyen > frais
                ET  P&L cumule >= 0  ET  t(P&L) >= 0      <-- ajoutes le 24/08
    ECHOUE    : t(funding) corrige < 1,0  OU  P&L cumule < 0  OU  t(P&L) < 0
    POURSUITE : entre les deux
Minimum de 3 paniers clos, sinon DONNEES INSUFFISANTES.

AVERTISSEMENT SUR L'INDEPENDANCE
---------------------------------
Le bot 29c ouvre un panier toutes les 48 h et les tient 168 h : ses paniers se
CHEVAUCHENT d'un facteur 3,5. Son t brut est donc surestime d'environ racine(3,5).
Le module publie les deux, et c'est le t CORRIGE qui fait foi.

COMMENT LA MESURE EST PRISE
----------------------------
En LECTURE SEULE sur etat/etat_bot29*.json. On ne touche pas a comptabilite.py
(coeur audite) ni au ledger. A chaque passe on photographie le funding_cumule
des positions ouvertes ; quand le panier tourne (la cle 'ouvert_le' change), on
archive la derniere photo comme resultat du panier clos.

Biais connu et assume : la photo a au plus une passe de retard (15 min sur
168 h = 0,15 % du funding), donc elle SOUS-ESTIME legerement la capture. Le
jalon est donc conservateur.

stdlib uniquement.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ETAT = Path("etat")
SORTIE = ETAT / "jalon_29.json"
PUBLIC = Path("docs") / "jalon_29.json"

# --- le critere, fige. Modifier ces constantes invaliderait le jalon. --------
DATE_POSE = "2026-08-15"
DATE_ECHEANCE = "2026-09-15"
T_REUSSI = 2.0
T_ECHEC = 1.0
N_MIN = 3
T_PNL_MIN = 0.0           # ajoute le 24/08 : un t(P&L) negatif interdit le REUSSI
CHEVAUCHEMENT = {"29c_carry_decale": 168.0/48.0}   # tenue / cadence

BOTS = {
    "29_carry_neutre": "etat_bot29.json",
    "29b_carry_neutre_large": "etat_bot29b.json",
    "29c_carry_decale": "etat_bot29c.json",
}
FRAIS_PANIER = 2 * 0.00045      # aller-retour par jambe, cf. comptabilite


def _lire(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _positions(etat: dict) -> dict:
    """Rend {cle: position} quel que soit le format d'etat (3 formats existent)."""
    pos = etat.get("positions")
    if isinstance(pos, dict) and pos:
        return pos
    out = {}
    for pid, pan in (etat.get("paniers") or {}).items():
        for c, p in (pan.get("positions") or {}).items():
            if isinstance(p, dict):
                out["%s/%s" % (pid, c)] = p
    return out


def _capture(etat: dict) -> tuple[float, int]:
    """Funding capte du panier ouvert, pondere par notionnel. (%, nb jambes)."""
    pos = _positions(etat)
    num = som = 0.0
    for p in pos.values():
        try:
            n = float(p.get("notionnel", 0.0))
            f = float(p.get("funding_cumule", 0.0))
        except (TypeError, ValueError):
            continue
        if n > 0:
            num += f * n
            som += n
    return (num / som if som > 0 else 0.0), len(pos)


def _t_stat(xs: list[float]) -> float | None:
    n = len(xs)
    if n < 2:
        return None
    m = sum(xs) / n
    v = sum((x - m) ** 2 for x in xs) / (n - 1)
    if v <= 0:
        return None
    return m / ((v / n) ** 0.5)


def _pnl_gate() -> dict:
    """{bot: (n, t_stat, pnl_total)} depuis le dernier verdict de la gate."""
    for p in (Path("docs") / "go_reel.json", ETAT / "go_reel.json"):
        g = _lire(p)
        if g:
            return {b: (v.get("n"), v.get("t_stat"), v.get("pnl_cumule"))
                    for b, v in (g.get("bots") or {}).items()}
    return {}


def observer() -> dict:
    """Une passe : photographie, detecte les rotations, evalue le jalon."""
    hist = _lire(SORTIE)
    hist.setdefault("date_pose", DATE_POSE)
    hist.setdefault("echeance", DATE_ECHEANCE)
    hist.setdefault("critere", {"t_reussi": T_REUSSI, "t_echec": T_ECHEC,
                                "n_min": N_MIN,
                                "mesure": "funding capte par panier, pondere notionnel"})
    bots = hist.setdefault("bots", {})
    now = datetime.now(timezone.utc).isoformat()
    gate = _pnl_gate()

    for bot, fichier in BOTS.items():
        etat = _lire(ETAT / fichier)
        if not etat:
            continue
        b = bots.setdefault(bot, {"paniers": [], "photo": None, "ouvert_le": None})
        # identite du panier courant : 'ouvert_le' (29/29b) ou la liste des paniers (29c)
        cle = etat.get("ouvert_le") or ",".join(sorted((etat.get("paniers") or {})))
        cap, jambes = _capture(etat)

        if b.get("ouvert_le") and cle != b["ouvert_le"] and b.get("photo"):
            # rotation : la derniere photo devient le resultat du panier clos
            ph = b["photo"]
            if ph.get("jambes", 0) > 0 and ph.get("cap") is not None:
                b["paniers"].append({"clos_le": now, "ouvert_le": b["ouvert_le"],
                                     "funding_pct": round(ph["cap"] * 100, 5),
                                     "jambes": ph["jambes"]})
                del b["paniers"][:-200]
        b["ouvert_le"] = cle or None
        b["photo"] = {"cap": cap, "jambes": jambes, "ts": now}
        b["funding_courant_pct"] = round(cap * 100, 5)
        b["jambes_ouvertes"] = jambes

        # --- evaluation du jalon, sur les paniers clos DEPUIS la pose ---
        serie = [p["funding_pct"] for p in b["paniers"]
                 if p.get("clos_le", "") >= DATE_POSE]
        t = _t_stat(serie)
        moy = (sum(serie) / len(serie)) if serie else None
        k = CHEVAUCHEMENT.get(bot, 1.0)
        t_corr = (t / (k ** 0.5)) if t is not None else None
        n_pnl, t_pnl, pnl_tot = gate.get(bot, (None, None, None))
        # un bot ne peut pas etre declare REUSSI si son P&L reel va dans le mauvais sens
        perdant = (t_pnl is not None and t_pnl < T_PNL_MIN) or \
                  (pnl_tot is not None and pnl_tot < 0)
        if len(serie) < N_MIN:
            verdict, lecture = "DONNEES_INSUFFISANTES", (
                "%d panier(s) clos sur %d requis" % (len(serie), N_MIN))
        elif perdant:
            verdict, lecture = "ECHOUE", (
                "funding capte %+.3f %%/panier (t corrige %+.2f) MAIS le bot PERD : "
                "t(P&L) %+.2f sur n=%s, P&L %+.2f $ — capter le funding ne suffit pas"
                % (moy or 0.0, t_corr or 0.0, t_pnl or 0.0, n_pnl, pnl_tot or 0.0))
        elif (t_corr is not None and t_corr >= T_REUSSI and moy is not None
              and moy / 100 > FRAIS_PANIER):
            verdict, lecture = "REUSSI", (
                "funding %+.3f %%/panier, t corrige %+.2f, et le P&L ne contredit pas "
                "(t %+.2f, %+.2f $)" % (moy, t_corr, t_pnl or 0.0, pnl_tot or 0.0))
        elif t_corr is not None and t_corr < T_ECHEC:
            verdict, lecture = "ECHOUE", (
                "funding %+.3f %%/panier, t corrige %+.2f — la selection ne capte rien"
                % (moy, t_corr))
        else:
            verdict, lecture = "POURSUITE", (
                "funding %+.3f %%/panier, t corrige %+.2f — non concluant"
                % (moy or 0.0, t_corr or 0.0))
        b["t_funding_corrige"] = round(t_corr, 3) if t_corr is not None else None
        b["chevauchement"] = k
        b["pnl_gate"] = {"n": n_pnl, "t": t_pnl, "pnl": pnl_tot}
        b["n_paniers_clos"] = len(serie)
        b["funding_moyen_pct"] = round(moy, 5) if moy is not None else None
        b["t_funding"] = round(t, 3) if t is not None else None
        b["verdict"] = verdict
        b["lecture"] = lecture

    hist["maj"] = now
    reste = (datetime.fromisoformat(DATE_ECHEANCE + "T00:00:00+00:00")
             - datetime.now(timezone.utc)).total_seconds() / 86400.0
    hist["jours_restants"] = round(reste, 1)
    hist["echu"] = reste <= 0

    for p in (SORTIE, PUBLIC):
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(hist, ensure_ascii=False, indent=1),
                         encoding="utf-8")
        except OSError:
            pass
    return hist


if __name__ == "__main__":
    h = observer()
    print("Jalon famille 29 — echeance %s (%s j)"
          % (h["echeance"], h["jours_restants"]))
    for bot, b in h.get("bots", {}).items():
        print("  %-24s %-22s %s" % (bot, b.get("verdict", "?"), b.get("lecture", "")))
        print("      panier ouvert : %d jambes, funding courant %+.4f %%"
              % (b.get("jambes_ouvertes", 0), b.get("funding_courant_pct", 0.0)))
