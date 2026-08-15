#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bot_32_carry_crossvenue.py - CARRY DE FUNDING CROISE HYPERLIQUID <-> NADO
=========================================================================
L'HYPOTHESE
-----------
Deux venues perpetuelles cotent la MEME piece avec des taux de funding
INDEPENDANTS. Si HL paie +30 %/an et Nado -10 %/an sur ARB, alors :

    SHORT ARB sur la venue au funding HAUT   -> on encaisse
    LONG  ARB sur la venue au funding BAS    -> on encaisse aussi
    notionnels egaux, meme piece             -> exposition prix ~ nulle

Le rendement est le SPREAD de funding, et il ne depend d'aucune prevision de
prix. C'est la seule famille du banc dont l'edge ne suppose rien sur le marche.

MESURE DU 15/08/2026 (snapshot, 45 pieces communes) :
    spread |median|  3,5 %/an     moyenne 7,8 %/an     max 48,8 % (ARB)
    17 pieces / 45 au-dessus du point mort de 9,4 %/an
Le snapshot ne dit RIEN de la PERSISTANCE du spread : c'est precisement ce que
ce bot mesure. Un spread qui s'inverse en 8 h ne se trade pas.

>>> AVERTISSEMENT EXECUTABILITE - LIRE AVANT DE PROMOUVOIR <<<
--------------------------------------------------------------
Le bot 24 a ete TUE le 29/07 pour avoir mesure un carry sur une venue ou nous
n'avons PAS DE COMPTE, et le bot 26 pour le meme motif sur Nado. Ce bot mesure
la meme classe de trade. Il est donc marque EXECUTABLE = False : la gate le
mesure mais NE PEUT PAS le promouvoir en argent reel.

Trois conditions LEVENT ce verrou, et aucune n'est acquise :
    1. un compte Nado finance (self-custody, cle dediee)
    2. l'audit de securite Nado CONFIRME (toujours non verifie au 15/08)
    3. min_size Nado = 100 $ par ordre (10x le plancher HL) -> il faut
       ~1 200 $ de notionnel pour 6 paires, soit tout le capital reel
Tant que ces trois points ne sont pas coches, ce bot produit une CONNAISSANCE
(le spread est-il persistant ?), pas une intention de trader.

COMPTABILITE
------------
Chaque jambe est une comptabilite.PositionReelle distincte, avec son propre
mark d'entree et de sortie. Consequence importante : le RISQUE DE BASE (les
deux venues qui divergent en prix) est capture EXACTEMENT, pas suppose nul.
C'est la difference avec le bot 25, dont le "t 3,56" etait un artefact.

Frais : la jambe Nado est facturee au tarif HL (4,5 bp) alors que Nado prend
3,5 bp taker. Le bot se penalise donc de 1 bp par jambe. Volontaire : on ne
touche pas a comptabilite.py, et l'erreur va dans le sens prudent.

UNITES - le piege a eviter
--------------------------
HL renvoie un funding HORAIRE. Nado renvoie un taux 24 HEURES (confirme par sa
doc : "the funding_rate returned by the API is the equivalent 24-hour rate,
three times the 8-hour rate"). On divise donc Nado par 24. Se tromper ici
fabrique un faux spread de 24x.

stdlib uniquement.
"""
from __future__ import annotations

import gzip
import json
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

from banc_essai_paper_trading import Strategy, Trade
from bots_cloud import _http_post_info, parse_ctxs, _now, _dt_h, ETAT_DIR
from comptabilite import FRAIS_PAR_JAMBE, Livre, notionnel_par_ligne

# --------------------------------------------------------------------------- #
# Acces Nado - lecture seule, aucun compte, aucune cle
# --------------------------------------------------------------------------- #
NADO_GATEWAY = "https://gateway.prod.nado.xyz/v1/query"
NADO_ARCHIVE = "https://archive.prod.nado.xyz/v1"
# Sans Accept-Encoding: gzip le gateway repond 403. Decouvert le 15/08.
_ENTETES = {
    "Accept": "application/json",
    "Accept-Encoding": "gzip",
    "Content-Type": "application/json",
    "User-Agent": "banc-paper/1.0",
}
X18 = 1e18
NADO_PERIODE_H = 24.0     # le taux Nado est un taux 24 h, pas horaire


def _nado(url: str, corps: dict | None = None, timeout: float = 20.0):
    """GET ou POST Nado. Renvoie None sur toute erreur (le bot doit survivre)."""
    try:
        req = urllib.request.Request(
            url,
            data=(json.dumps(corps).encode("utf-8") if corps is not None else None),
            headers=_ENTETES,
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            brut = r.read()
            if r.headers.get("Content-Encoding") == "gzip":
                brut = gzip.decompress(brut)
        return json.loads(brut.decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError, gzip.BadGzipFile) as e:
        print(f"[32] Nado injoignable ({type(e).__name__}) : {e}", flush=True)
        return None


def marche_nado(oi_min_usd: float = 300_000.0) -> dict[str, dict]:
    """{COIN: {funding horaire, markPx, oi_usd, taker}} pour les perps Nado.

    Trois appels : symbols (id + frais), all_products (prix + OI), archive
    (funding). Si l'un echoue, on renvoie {} - jamais de donnee partielle.
    """
    sym = _nado(NADO_GATEWAY + "?type=symbols")
    prod = _nado(NADO_GATEWAY + "?type=all_products")
    if not sym or not prod:
        return {}
    try:
        table = sym["data"]["symbols"] if "data" in sym else sym["symbols"]
        perps = prod["data"]["perp_products"]
    except (KeyError, TypeError):
        return {}

    # product_id -> (coin, taker)
    par_id: dict[int, tuple[str, float]] = {}
    for s, meta in table.items():
        if meta.get("type") != "perp" or meta.get("trading_status") != "live":
            continue
        coin = s.split("-")[0].upper()
        try:
            par_id[int(meta["product_id"])] = (
                coin, float(meta.get("taker_fee_rate_x18", 0)) / X18)
        except (KeyError, TypeError, ValueError):
            continue
    if not par_id:
        return {}

    # prix oracle + interet ouvert
    prix: dict[int, tuple[float, float]] = {}
    for p in perps:
        try:
            pid = int(p["product_id"])
            px = float(p["oracle_price_x18"]) / X18
            oi = float(p.get("state", {}).get("open_interest", 0)) / X18
        except (KeyError, TypeError, ValueError):
            continue
        if px > 0:
            prix[pid] = (px, oi * px)

    ids = [i for i in par_id if i in prix]
    if not ids:
        return {}
    rep = _nado(NADO_ARCHIVE, {"funding_rates": {"product_ids": ids}})
    if not rep:
        return {}

    out: dict[str, dict] = {}
    for cle, v in (rep.items() if isinstance(rep, dict) else []):
        try:
            pid = int(v.get("product_id", cle))
            f24 = float(v["funding_rate_x18"]) / X18
        except (KeyError, TypeError, ValueError):
            continue
        if pid not in par_id or pid not in prix:
            continue
        coin, taker = par_id[pid]
        px, oi_usd = prix[pid]
        if oi_usd < oi_min_usd:
            continue
        out[coin] = {"funding": f24 / NADO_PERIODE_H, "markPx": px,
                     "oi_usd": oi_usd, "taker": taker, "f24": f24}
    return out


# --------------------------------------------------------------------------- #
class CarryCrossVenue(Strategy):
    """Carry de funding croise HL <-> Nado, auto-neutre piece par piece."""

    name = "32_carry_crossvenue"
    EXECUTABLE = False        # <- verrou : la gate ne peut pas le promouvoir
    MOTIF_NON_EXECUTABLE = ("aucun compte Nado ; audit securite Nado non "
                            "confirme ; min_size Nado 100 $/ordre")

    # frais totaux d'une PAIRE, en fraction du notionnel d'une jambe :
    # 2 jambes x aller-retour = 4 traversees
    FRAIS_PAIRE = 4.0 * FRAIS_PAR_JAMBE      # 0,0018 = 18 bp

    def __init__(self, k_max: int = 6, hold_h: float = 168.0,
                 marge: float = 1.25, vol_min: float = 500_000.0,
                 oi_min: float = 300_000.0):
        super().__init__(stake_usd=1.0)
        self.k_max = int(k_max)
        self.hold_h = float(hold_h)
        self.marge = float(marge)
        self.vol_min = float(vol_min)
        self.oi_min = float(oi_min)
        self._f = ETAT_DIR / "etat_bot32.json"
        self.livre = Livre(self.name)
        self._etat = self._charger()
        self.livre.charger(self._etat.get("positions", {}))

    # -- seuil ---------------------------------------------------------------
    @property
    def seuil_horaire(self) -> float:
        """Spread horaire minimal pour couvrir `marge` fois les frais sur la tenue."""
        return self.marge * self.FRAIS_PAIRE / self.hold_h

    # -- persistance ---------------------------------------------------------
    def _charger(self) -> dict:
        try:
            return json.loads(self._f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _sauver(self) -> None:
        self._etat["positions"] = self.livre.vers_dict()
        try:
            ETAT_DIR.mkdir(parents=True, exist_ok=True)
            self._f.write_text(json.dumps(self._etat, ensure_ascii=False),
                               encoding="utf-8")
        except OSError:
            pass

    # -- donnees -------------------------------------------------------------
    def marches(self) -> tuple[dict, dict]:
        rep = _http_post_info({"type": "metaAndAssetCtxs"})
        hl = parse_ctxs(rep, ("*",)) if rep is not None else {}
        nd = marche_nado(self.oi_min)
        return hl, nd

    # -- selection -----------------------------------------------------------
    def selectionner(self, hl: dict, nd: dict) -> list[tuple[str, float]]:
        """[(coin, spread horaire signe)] : spread > 0 => HL paie plus."""
        cands = []
        for coin, dn in nd.items():
            dh = hl.get(coin)
            if not dh or dh.get("markPx", 0) <= 0:
                continue
            if dh.get("vol", 0) < self.vol_min:
                continue
            fh, fn = dh.get("funding"), dn.get("funding")
            if fh is None or fn is None:
                continue
            spread = float(fh) - float(fn)
            if abs(spread) >= self.seuil_horaire:
                cands.append((coin, spread))
        cands.sort(key=lambda x: -abs(x[1]))
        return cands[:self.k_max]

    # -- une passe -----------------------------------------------------------
    def step(self) -> list[Trade]:
        hl, nd = self.marches()
        if not hl or not nd:
            # Nado muet : on N'INVENTE PAS de prix. On accumule le funding HL sur
            # les jambes HL uniquement serait un biais -> on ne fait rien du tout.
            self._etat["derniere_panne"] = _now().isoformat()
            self._sauver()
            return []
        self._etat.pop("derniere_panne", None)

        # dictionnaire de marche a cles composites, consomme par le Livre
        marche = {}
        for c, d in hl.items():
            marche[c + "@HL"] = d
        for c, d in nd.items():
            marche[c + "@NADO"] = d

        now = _now()
        dt = _dt_h(self._etat.get("dernier_ts"))
        self._etat["dernier_ts"] = now.isoformat()

        # 1) funding SIGNE sur chaque jambe, avec le taux de SA venue
        self.livre.accumuler_tout(marche, dt)

        # 2) solder a l'echeance
        regles: list[Trade] = []
        if self.livre.positions:
            try:
                age = (now - datetime.fromisoformat(
                    str(self._etat.get("ouvert_le")))).total_seconds() / 3600.0
            except (ValueError, TypeError):
                age = 0.0
            if age >= self.hold_h:
                for cle in list(self.livre.positions):
                    d = marche.get(cle)
                    mark = (d["markPx"] if d
                            else self.livre.positions[cle].mark_entree)
                    tr = self.livre.fermer(cle, mark)
                    if tr:
                        regles.append(tr)
                self._etat["ouvert_le"] = None

        # 3) ouvrir un panier neuf si le livre est vide
        if not self.livre.positions:
            paires = self.selectionner(hl, nd)
            if paires:
                notionnel = notionnel_par_ligne(2 * len(paires))
                detail = []
                for coin, spread in paires:
                    # spread > 0 : HL paie plus -> SHORT HL, LONG Nado
                    s_hl = -1 if spread > 0 else +1
                    self.livre.ouvrir(coin + "@HL", s_hl, notionnel,
                                      hl[coin]["markPx"])
                    self.livre.ouvrir(coin + "@NADO", -s_hl, notionnel,
                                      nd[coin]["markPx"])
                    detail.append({
                        "coin": coin,
                        "spread_an_pct": round(spread * 8760 * 100, 2),
                        "f_hl_an_pct": round(hl[coin]["funding"] * 8760 * 100, 2),
                        "f_nado_an_pct": round(nd[coin]["funding"] * 8760 * 100, 2),
                        "base_pct": round(
                            (nd[coin]["markPx"] / hl[coin]["markPx"] - 1) * 100, 3),
                        "sens_hl": "short" if s_hl < 0 else "long",
                    })
                self._etat["ouvert_le"] = now.isoformat()
                self._etat["panier"] = detail
                print("[32] carry croise : %d paire(s), spread max %.1f %%/an"
                      % (len(detail), max(abs(d["spread_an_pct"]) for d in detail)),
                      flush=True)

        # 4) observatoire : le spread de TOUT l'univers commun, a chaque passe.
        #    C'est cette serie qui repondra a "le spread est-il persistant ?",
        #    independamment du P&L du bot.
        communs = [(c, hl[c]["funding"] - nd[c]["funding"])
                   for c in nd if c in hl and hl[c].get("funding") is not None]
        if communs:
            abs_sp = sorted(abs(s) for _, s in communs)
            m = abs_sp[len(abs_sp) // 2]
            self._etat["observatoire"] = {
                "ts": now.isoformat(),
                "n_communs": len(communs),
                "median_abs_an_pct": round(m * 8760 * 100, 2),
                "n_au_dessus_seuil": sum(1 for _, s in communs
                                         if abs(s) >= self.seuil_horaire),
                "seuil_an_pct": round(self.seuil_horaire * 8760 * 100, 2),
            }
            hist = self._etat.setdefault("serie", [])
            hist.append({"ts": now.isoformat(),
                         "spreads": {c: round(s * 8760 * 100, 3)
                                     for c, s in communs}})
            del hist[:-400]      # ~4 jours de passes, borne la taille du fichier

        self._etat["ecart_neutralite"] = round(self.livre.ecart_neutralite(), 6)
        self._sauver()
        if regles:
            print("[32] carry croise : %d jambe(s) soldee(s)" % len(regles),
                  flush=True)
        return regles


if __name__ == "__main__":
    b = CarryCrossVenue()
    print("seuil : %.2f %%/an  (marge %.2fx sur %.0f bp de frais, tenue %.0f h)"
          % (b.seuil_horaire * 8760 * 100, b.marge,
             b.FRAIS_PAIRE * 1e4, b.hold_h))
    hl, nd = b.marches()
    print("HL %d perps | Nado %d perps | communs %d"
          % (len(hl), len(nd), len({c for c in nd if c in hl})))
    for coin, sp in b.selectionner(hl, nd):
        print("  %-10s spread %+7.1f %%/an   HL %+7.1f  Nado %+7.1f   base %+6.3f %%"
              % (coin, sp * 8760 * 100, hl[coin]["funding"] * 8760 * 100,
                 nd[coin]["funding"] * 8760 * 100,
                 (nd[coin]["markPx"] / hl[coin]["markPx"] - 1) * 100))
