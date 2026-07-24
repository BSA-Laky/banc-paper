#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""equipage.py - Tableau de bord de l'EQUIPAGE de LA STATION (deterministe, stdlib only).

Lit l'etat des agents IA (Arbitre, Superviseur) et des automates 24/7, puis ecrit
docs/equipage.html (mobile, PC eteint) + docs/equipage.json. AUCUN appel LLM, 0 cout.
Noms "Officiers de bord". Rafraichi a chaque passe (workflow equipage.yml, ~15 min).
"""
from __future__ import annotations

import html
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

ETAT = Path("etat"); DOCS = Path("docs")
NOW = datetime.now(timezone.utc)


# ---------- helpers ----------
def _json(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return {}


def _mtime(p):
    try:
        return datetime.fromtimestamp(Path(p).stat().st_mtime, timezone.utc)
    except Exception:
        return None


def _dt(s):
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except Exception:
        return None


def _il_y_a(dt):
    if not dt:
        return "jamais"
    s = (NOW - dt).total_seconds()
    if s < 0:
        return "a l'instant"
    if s < 90:
        return "il y a moins d'une minute"
    if s < 5400:
        return f"il y a {round(s/60)} min"
    if s < 172800:
        return f"il y a {round(s/3600)} h"
    return f"il y a {round(s/86400)} j"


def _dans(dt):
    if not dt:
        return "sur demande"
    s = (dt - NOW).total_seconds()
    if s < 0:
        return "imminent"
    if s < 5400:
        return f"dans {round(s/60)} min"
    if s < 172800:
        return f"dans {round(s/3600)} h"
    return f"dans {round(s/86400)} j"


def _next_daily(h, m):
    c = NOW.replace(hour=h, minute=m, second=0, microsecond=0)
    return c if c > NOW else c + timedelta(days=1)


def _next_weekly(py_weekday, h, m):   # py_weekday: lundi=0 ... dimanche=6
    c = NOW.replace(hour=h, minute=m, second=0, microsecond=0)
    c += timedelta(days=(py_weekday - NOW.weekday()) % 7)
    return c if c > NOW else c + timedelta(days=7)


def _next_quarter():
    add = (NOW.minute // 15 + 1) * 15 - NOW.minute
    return NOW.replace(second=0, microsecond=0) + timedelta(minutes=add)


def _hhmm(dt):
    return dt.strftime("%H:%M UTC") if dt else "-"


def esc(x):
    return html.escape(str(x))


# ---------- lecture de l'etat ----------
regime = _json(ETAT / "regime_ia.json")
consigne = _json(ETAT / "consigne_arbitre.json")
echecs = _json(ETAT / "arbitre_echecs.json")
brief = _json(DOCS / "brief.json")
gate = _json(DOCS / "go_reel.json")
treso = _json(DOCS / "tresorier.json")
note_veilleur = (ETAT / "note_veilleur.md").exists()
d_veille = _mtime(ETAT / "note_veilleur.md")

d_regime = _dt(regime.get("date"))
d_consigne = _dt(consigne.get("date"))
d_brief = _dt(brief.get("ts")) or _mtime(DOCS / "brief.json")
d_gate = _dt(gate.get("ts")) or _mtime(DOCS / "go_reel.json")
d_rapport = _mtime(DOCS / "rapport_semaine.md")
d_treso = _dt(treso.get("ts"))
n_echecs = int(echecs.get("consecutifs", 0)) if isinstance(echecs, dict) else 0

bots = gate.get("bots", {}) if isinstance(gate, dict) else {}
n_bots = len(bots)
statuts = [b.get("statut") for b in bots.values() if isinstance(b, dict)]
n_vert = statuts.count("VERT"); n_orange = statuts.count("ORANGE")
n_gris = statuts.count("GRIS"); n_rouge = statuts.count("ROUGE")
alertes = gate.get("alertes", []) if isinstance(gate, dict) else []
banc_suspect = bool(gate.get("banc_suspect"))
temoin = (gate.get("temoins", {}) or {}).get("10_controle_aleatoire", {})
btc = brief.get("tendances_btc", {}) if isinstance(brief, dict) else {}
extremes = brief.get("evenements_extremes", []) if isinstance(brief, dict) else []
actions = brief.get("dernieres_actions", []) if isinstance(brief, dict) else []
n_cand = len(treso.get("candidats", []) or [])
n_live = len(treso.get("live", []) or [])
n_pause = len(treso.get("pause", []) or [])


def _statut_ia(last_dt, incident=False, dormant=False):
    if dormant:
        return ("dormant", "Dormant (pas de cle)")
    if incident:
        return ("incident", "Incident signale")
    if last_dt and (NOW - last_dt).total_seconds() < 600:
        return ("actif", "A son poste")
    return ("repos", "Au repos")


# ---------- construction de l'equipage ----------
officiers = []

# Superviseur — Commandeure Ada (Fable 5, hebdo)
_next_ada = _next_weekly(6, 6, 30)
_cls, _lbl = _statut_ia(d_consigne or d_rapport)
officiers.append({
    "nom": "Commandeure Ada", "poste": "Supervision generale", "role": "Superviseur",
    "badge": "Fable 5", "type": "IA",
    "statut_cls": _cls, "statut": _lbl,
    "derniere": "Audit hebdomadaire + consigne posee", "derniere_dt": d_consigne or d_rapport,
    "prochain": "Prochain audit", "prochain_dt": _next_ada,
    "parole": (f"Consigne au Lt Hugo : plafond de confiance {consigne.get('confiance_max', '?')}"
               f" - {consigne.get('motif', 'en attente du 1er scoring')}"),
})

# Arbitre — Lieutenant Hugo (Opus 4.8, quotidien)
_next_hugo = _next_daily(5, 45)
_cls, _lbl = _statut_ia(d_regime, incident=(n_echecs > 0), dormant=not regime)
officiers.append({
    "nom": "Lieutenant Hugo", "poste": "Jugement quotidien", "role": "Arbitre",
    "badge": "Sonnet 5", "type": "IA",
    "statut_cls": _cls, "statut": (f"Incident ({n_echecs} echec(s))" if n_echecs else _lbl),
    "derniere": "Avis de regime rendu", "derniere_dt": d_regime,
    "prochain": "Prochain quart", "prochain_dt": _next_hugo,
    "parole": (f"Regime {regime.get('regime', '?')} (confiance {regime.get('confiance', '?')})"
               f" - {regime.get('resume', 'aucun avis encore')}"),
})

# Veilleur — Cadet Remy (Haiku 4.5, hebdo) : AFFECTE le 12/07 (etape B Hermes)
_next_remy = _next_weekly(5, 5, 50)
officiers.append({
    "nom": "Cadet Remy", "poste": "Veille hebdomadaire de la station", "role": "Veilleur",
    "badge": "Haiku 4.5", "type": "IA",
    "statut_cls": ("actif" if (d_veille and (NOW - d_veille).total_seconds() < 8*86400) else "repos"),
    "statut": ("Note de la semaine deposee" if note_veilleur else "En poste, 1re note samedi"),
    "derniere": "Note de veille pour la Commandeure", "derniere_dt": d_veille,
    "prochain": "Prochaine ronde", "prochain_dt": _next_remy,
    "parole": ("Chaque samedi 05:50 : frictions d'execution testnet, budget des avis, "
               "anomalies de la semaine -> note pour l'audit du dimanche d'Ada. Cout ~centimes."),
})

# Stratege R&D — Enseigne Nova (Opus 4.8, evenementiel) : code les bots (amendement 16/07)
_hyps = _json(ETAT / "hypotheses.json")
_n_hyp = len(_hyps) if isinstance(_hyps, list) else 0
# Date REELLE de la derniere fiche (fix 18/07) : dans le checkout Actions, le mtime
# vaut toujours "maintenant" -> fausse fraicheur affichee. On lit la date DES fiches.
_d_hyp = None
if isinstance(_hyps, list):
    for _h in _hyps:
        try:
            _cand = datetime.fromisoformat(str(_h.get("date", "")).replace("Z", "+00:00"))
            if _cand.tzinfo is None:
                _cand = _cand.replace(tzinfo=timezone.utc)
            if _d_hyp is None or _cand > _d_hyp:
                _d_hyp = _cand
        except (ValueError, TypeError):
            continue
if _d_hyp is None:
    _d_hyp = _mtime(ETAT / "hypotheses.json")
officiers.append({
    "nom": "Enseigne Nova", "poste": "R&D - code et active les bots paper (autonome)", "role": "Stratege",
    "badge": "Opus 4.8", "type": "IA",
    "statut_cls": ("actif" if (_d_hyp and (NOW - _d_hyp).total_seconds() < 8*86400) else "repos"),
    "statut": (f"{_n_hyp} fiche(s) au registre" if _n_hyp else "En poste, attend un kill"),
    "derniere": "Fiche d'hypothese deposee", "derniere_dt": _d_hyp,
    "prochain": "Ronde du dimanche (si invalidation)", "prochain_dt": _next_weekly(6, 6, 0),
    "parole": ("Quand la gate tue un bot, je concois ET CODE son remplacant paper de A a Z "
               "(sandbox sans secret, kill auto). Le GO reel reste au Commandant. Si je bute sur "
               "une ressource (cle, venue), je te la demande sur Telegram avec le tuto."),
})

# ---------- automates 24/7 ----------
automates = []; automates.append({"nom": "L'Exécuteur réel", "poste": "Trade le bot 28 en ARGENT RÉEL (mainnet HL)", "role": "executeur_reel.py", "badge": "Automate", "type": "SYS", "statut_cls": "actif", "statut": "Actif — rails 1× + garde-fou levier + kill-switch", "derniere": "Miroir mainnet du 28", "derniere_dt": d_gate, "prochain": "Prochaine passe", "prochain_dt": d_gate, "parole": "Je réplique les positions du bot 28 sur Hyperliquid mainnet : levier 1× forcé, coins non-1× refusés, plafond d'expo total, kill-switch stopreel. Perte bornée au dépôt (wallet agent trade-only)."})

# Le Sas — gate GO-reel (moniteur_go_reel.py)
automates.append({
    "nom": "Le Sas", "poste": "Controle GO-reel", "role": "moniteur_go_reel.py",
    "badge": "Automate", "type": "SYS",
    "statut_cls": ("incident" if banc_suspect or n_rouge else "actif"),
    "statut": ("Banc suspect" if banc_suspect else (f"{n_rouge} ROUGE" if n_rouge else "Sain")),
    "derniere": "Statuts GO-reel reevalues", "derniere_dt": d_gate,
    "prochain": "Prochain créneau", "prochain_dt": _next_quarter(),
    "parole": (f"Banc {'suspect' if banc_suspect else 'sain'}, temoin "
               f"{'sain' if temoin.get('sain') else 'a surveiller'} (t {temoin.get('t_stat', '?')}). "
               f"{n_bots} bots suivis : {n_vert} VERT / {n_orange} ORANGE / {n_gris} GRIS / {n_rouge} ROUGE. "
               f"{len(alertes)} alerte(s)."),
})

# La Salle des machines — sampler / bots (run_once.py)
_last_action = actions[0] if actions else {}
automates.append({
    "nom": "La Salle des machines", "poste": "Echantillonnage des bots", "role": "run_once.py",
    "badge": "Automate", "type": "SYS",
    "statut_cls": "actif", "statut": "En service",
    "derniere": "Passe d'echantillonnage", "derniere_dt": d_brief,
    "prochain": "Prochain créneau", "prochain_dt": _next_quarter(),
    "parole": (f"Bots echantillonnes (temoin, 23, 24, 25, 26, 27x, 28). Derniere action : "
               f"{_last_action.get('bot', '-')} sur {_last_action.get('marche', '-')} "
               f"(pnl {_last_action.get('pnl', '-')})." if _last_action
               else "Bots echantillonnes a chaque passe (creneau ~15 min, retards GitHub possibles)."),
})

# La Passerelle — brief (tour_de_controle.py)
automates.append({
    "nom": "La Passerelle", "poste": "Compilation du brief", "role": "tour_de_controle.py",
    "badge": "Automate", "type": "SYS",
    "statut_cls": "actif", "statut": "En service",
    "derniere": "Brief du jour compile", "derniere_dt": d_brief,
    "prochain": "Prochain créneau", "prochain_dt": _next_quarter(),
    "parole": (f"BTC {btc.get('prix', '?')} $ (7j {round(btc.get('ret7', 0)*100, 1)}%, "
               f"30j {round(btc.get('ret30', 0)*100, 1)}%). {len(extremes)} move(s) extreme(s), "
               f"{len(actions)} dernieres actions au journal."),
})

# Le Tresorier — enveloppes & promotions (tresorier.py)
automates.append({
    "nom": "Le Tresorier", "poste": "Enveloppes & promotions (300 EUR/bot)", "role": "tresorier.py",
    "badge": "Automate", "type": "SYS",
    "statut_cls": ("actif" if (n_cand or n_live) else "repos"),
    "statut": (f"{n_cand} candidat(s) / {n_live} live / {n_pause} pause"
               if (n_cand or n_live or n_pause) else "Aucun bot promu"),
    "derniere": "Checklist VERT-STABLE evaluee", "derniere_dt": d_treso,
    "prochain": "Prochain créneau", "prochain_dt": _next_quarter(),
    "parole": (f"Capital reel {treso.get('capital_dispo', 0):.0f} $, besoin alloue "
               f"{treso.get('besoin_alloue', 0):.0f} $. Checklist : VERT 5 j + t>=2 + P&L jamais "
               f"negatif + drawdown < 30 % de l'enveloppe + gagne son A/B. Mise en service = "
               f"go PUIS confirme (90 min), par le Commandant seul. Retrait = jamais."),
})

# La Vigie — alerte push (alerte_issue.py)
automates.append({
    "nom": "La Vigie", "poste": "Alertes push (issue GitHub)", "role": "alerte_issue.py",
    "badge": "Automate", "type": "SYS",
    "statut_cls": ("incident" if alertes or banc_suspect else "actif"),
    "statut": (f"{len(alertes)} alerte(s)" if alertes else "Rien a signaler"),
    "derniere": "Veille ROUGE / banc suspect", "derniere_dt": None,
    "prochain": "Ronde quotidienne", "prochain_dt": _next_daily(6, 15),
    "parole": ("Notifie le Commandant si un bot passe ROUGE, si le banc devient suspect "
               "ou en cas de changement de statut. Aucune alerte en cours."),
})

# ---------- journal des echanges ----------
evenements = []
if d_consigne:
    evenements.append((d_consigne, "Commandeure Ada", "Lieutenant Hugo",
                       f"Consigne transmise : plafond de confiance {consigne.get('confiance_max', '?')}"
                       f" ({consigne.get('motif', '')})"))
if d_regime:
    evenements.append((d_regime, "Lieutenant Hugo", "Les bots (27e)",
                       f"Avis de regime publie : {regime.get('regime', '?')} "
                       f"(conf {regime.get('confiance', '?')}) - {regime.get('resume', '')}"))
if d_veille:
    evenements.append((d_veille, "Cadet Remy", "Commandeure Ada",
                       "Note de veille hebdomadaire deposee (frictions, budget, anomalies)"))
if n_echecs:
    evenements.append((_dt(echecs.get("maj")) or NOW, "Lieutenant Hugo", "Commandant",
                       f"Incident API signale : {n_echecs} echec(s) consecutif(s)"))
if d_treso and (n_cand or n_live or n_pause):
    evenements.append((d_treso, "Le Tresorier", "Commandant",
                       f"Promotions : {n_cand} candidat(s), {n_live} live, {n_pause} en pause"))
if d_gate:
    evenements.append((d_gate, "Le Sas", "Station",
                       f"Statuts reevalues : banc {'suspect' if banc_suspect else 'sain'}, "
                       f"{n_orange} ORANGE / {n_gris} GRIS, {len(alertes)} alerte(s)"))
if d_brief:
    evenements.append((d_brief, "La Passerelle", "Station",
                       f"Brief compile : BTC {btc.get('prix', '?')} $, {len(extremes)} move(s) extreme(s)"))
evenements = [e for e in evenements if e[0]]
evenements.sort(key=lambda e: e[0], reverse=True)


# ---------- rendu HTML ----------
def carte(a):
    return f"""    <div class="carte {esc(a['statut_cls'])}">
      <div class="tete"><span class="nom">{esc(a['nom'])}</span><span class="badge b-{esc(a['type'])}">{esc(a['badge'])}</span></div>
      <div class="poste">{esc(a['poste'])} &middot; <span class="role">{esc(a['role'])}</span></div>
      <div><span class="pill p-{esc(a['statut_cls'])}">{esc(a['statut'])}</span></div>
      <div class="ligne"><b>Derniere tache :</b> {esc(a['derniere'])} <span class="muted">&middot; {_il_y_a(a['derniere_dt'])}</span></div>
      <div class="ligne"><b>{esc(a['prochain'])} :</b> {_dans(a['prochain_dt'])} <span class="muted">({_hhmm(a['prochain_dt'])})</span></div>
      <div class="parole">&laquo; {esc(a['parole'])} &raquo;</div>
    </div>"""


def ligne_journal(e):
    dt, de, vers, msg = e
    return (f'    <li><span class="jt">{esc(_hhmm(dt))}</span> '
            f'<b>{esc(de)}</b> <span class="fleche">&rarr;</span> {esc(vers)}<br>'
            f'<span class="jmsg">{esc(msg)}</span></li>')


resume = (f"Banc <b>{'suspect' if banc_suspect else 'sain'}</b> &middot; "
          f"{len(officiers)} officiers &middot; {len(automates)} automates &middot; "
          f"{len(alertes)} alerte(s) &middot; MAJ {esc(_hhmm(NOW))}")

html_doc = f"""<!doctype html>
<html lang="fr"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Equipage &middot; LA STATION</title>
<style>
:root {{ --bg:#0b1020; --card:#141b30; --card2:#101528; --line:#243050; --txt:#e6ecff;
  --muted:#8894b8; --actif:#28c76f; --repos:#5b7cff; --reserve:#8a93b0; --incident:#ff5b6e;
  --dormant:#54607f; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--txt);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  padding:14px; padding-bottom:40px; }}
h1 {{ font-size:20px; margin:2px 0 2px; letter-spacing:.5px; }}
.sub {{ color:var(--muted); font-size:12.5px; margin-bottom:12px; }}
.sub a {{ color:var(--repos); text-decoration:none; }}
h2 {{ font-size:13px; text-transform:uppercase; letter-spacing:1.5px; color:var(--muted);
  margin:20px 0 8px; border-bottom:1px solid var(--line); padding-bottom:6px; }}
.grille {{ display:grid; grid-template-columns:1fr; gap:10px; }}
@media(min-width:620px){{ .grille {{ grid-template-columns:1fr 1fr; }} }}
.carte {{ background:var(--card); border:1px solid var(--line); border-left:4px solid var(--repos);
  border-radius:12px; padding:12px 13px; }}
.carte.actif {{ border-left-color:var(--actif); }}
.carte.repos {{ border-left-color:var(--repos); }}
.carte.reserve {{ border-left-color:var(--reserve); background:var(--card2); }}
.carte.incident {{ border-left-color:var(--incident); }}
.carte.dormant {{ border-left-color:var(--dormant); opacity:.75; }}
.tete {{ display:flex; justify-content:space-between; align-items:center; gap:8px; }}
.nom {{ font-size:16px; font-weight:700; }}
.badge {{ font-size:11px; padding:2px 8px; border-radius:999px; white-space:nowrap;
  background:#1e2a4a; color:#b9c6f0; border:1px solid var(--line); }}
.badge.b-SYS {{ background:#20283f; color:#9fb0d8; }}
.poste {{ color:var(--txt); font-size:12.5px; margin:2px 0 8px; opacity:.9; }}
.role {{ color:var(--muted); font-family:ui-monospace,Menlo,Consolas,monospace; font-size:11px; }}
.pill {{ display:inline-block; font-size:11.5px; font-weight:600; padding:3px 9px;
  border-radius:999px; margin-bottom:8px; }}
.p-actif {{ background:rgba(40,199,111,.15); color:var(--actif); }}
.p-repos {{ background:rgba(91,124,255,.15); color:#9fb0ff; }}
.p-reserve {{ background:rgba(138,147,176,.15); color:var(--reserve); }}
.p-incident {{ background:rgba(255,91,110,.15); color:var(--incident); }}
.p-dormant {{ background:rgba(84,96,127,.15); color:var(--dormant); }}
.ligne {{ font-size:12.5px; margin:3px 0; }}
.ligne b {{ color:#c7d2f7; font-weight:600; }}
.muted {{ color:var(--muted); }}
.parole {{ margin-top:9px; padding-top:8px; border-top:1px dashed var(--line);
  font-size:12.5px; color:#cdd6f4; font-style:italic; line-height:1.45; }}
ul.journal {{ list-style:none; padding:0; margin:0; }}
ul.journal li {{ background:var(--card2); border:1px solid var(--line); border-radius:10px;
  padding:9px 12px; margin-bottom:8px; font-size:12.5px; line-height:1.45; }}
.jt {{ font-family:ui-monospace,Menlo,Consolas,monospace; color:var(--muted); font-size:11px;
  margin-right:6px; }}
.fleche {{ color:var(--actif); }}
.jmsg {{ color:#c3cdec; }}
footer {{ color:var(--muted); font-size:11px; margin-top:22px; text-align:center; }}
</style></head><body>
<h1>&#128737; LA STATION &mdash; &Eacute;quipage</h1>
<div class="sub">{resume} &middot; <a href="./index.html">&larr; tableau de bord</a></div>

<h2>Officiers (IA)</h2>
<div class="grille">
{chr(10).join(carte(a) for a in officiers)}
</div>

<h2>Automates de bord (24/7)</h2>
<div class="grille">
{chr(10).join(carte(a) for a in automates)}
</div>

<h2>Journal des &eacute;changes</h2>
<ul class="journal">
{chr(10).join(ligne_journal(e) for e in evenements) if evenements else '    <li>Aucun &eacute;change enregistr&eacute; pour le moment.</li>'}
</ul>

<footer>Page d&eacute;terministe &middot; 0 appel LLM &middot; g&eacute;n&eacute;r&eacute;e le {esc(NOW.strftime('%Y-%m-%d %H:%M UTC'))} &middot; rafra&icirc;chie &agrave; chaque passe du banc</footer>
</body></html>"""

# ---------- localisation heure (UTC -> heure locale de l'appareil, cote client) ----------
_LOCALIZER = (
    "<script>(function(){"
    "function p(n){return String(n).padStart(2,'0');}"
    "function loc(d){return p(d.getDate())+'/'+p(d.getMonth()+1)+' '+p(d.getHours())+':'+p(d.getMinutes());}"
    "var reF=/(\\d{4})-(\\d{2})-(\\d{2})[ T](\\d{2}):(\\d{2})(?::\\d{2})?\\s*(?:UTC|Z)/g;"
    "var reH=/\\b(\\d{2}):(\\d{2})\\s*UTC\\b/g;"
    "function cv(t){"
    "t=t.replace(reF,function(m,Y,Mo,D,H,Mi){var d=new Date(Date.UTC(+Y,+Mo-1,+D,+H,+Mi));return isNaN(d)?m:loc(d);});"
    "t=t.replace(reH,function(m,H,Mi){var n=new Date();var d=new Date(Date.UTC(n.getUTCFullYear(),n.getUTCMonth(),n.getUTCDate(),+H,+Mi));return isNaN(d)?m:p(d.getHours())+':'+p(d.getMinutes());});"
    "return t;}"
    "function sw(){var w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT,null),a=[],n;"
    "while(n=w.nextNode()){var v=n.nodeValue||'';if(v.indexOf('UTC')>-1||/\\d{2}:\\d{2}(:\\d{2})?Z/.test(v))a.push(n);}"
    "a.forEach(function(nd){var v=cv(nd.nodeValue);if(v!==nd.nodeValue)nd.nodeValue=v;});}"
    "if(document.body)sw();else document.addEventListener('DOMContentLoaded',sw);"
    "setInterval(sw,60000);})();</script>"
)
html_doc = html_doc.replace('<meta charset="utf-8">',
                            '<meta charset="utf-8">\n<meta http-equiv="refresh" content="900">', 1)
html_doc = html_doc.replace("</body></html>", _LOCALIZER + "</body></html>", 1)

# ---------- ecriture ----------
DOCS.mkdir(exist_ok=True)
(DOCS / "equipage.html").write_text(html_doc, encoding="utf-8")
(DOCS / "equipage.json").write_text(json.dumps({
    "genere": NOW.isoformat(),
    "officiers": [{k: v for k, v in a.items() if k not in ("derniere_dt", "prochain_dt")} for a in officiers],
    "automates": [{k: v for k, v in a.items() if k not in ("derniere_dt", "prochain_dt")} for a in automates],
    "journal": [{"ts": e[0].isoformat(), "de": e[1], "vers": e[2], "message": e[3]} for e in evenements],
}, ensure_ascii=False, indent=1), encoding="utf-8")

print(f"[equipage] OK - {len(officiers)} officiers, {len(automates)} automates, "
      f"{len(evenements)} echanges -> docs/equipage.html", flush=True)
