# Meta-memoire Superviseur — maj 2026-07-12 (semaine 2)

## Tendances de fond
- Marche : BTC 61839→63719 sur la semaine, ret7/ret30 devenus plats (12/07 : +0.13%/+0.25%). Regime neutre stable.
- Banc fiable en continu : temoin 10 sain (t 0.37-0.84, n 193→222), banc_suspect=false depuis le debut.

## Verdicts dates
- **02/07** : 25_conv n=262 t=2.39 seul candidat. 27a-d GRIS bruit.
- **03/07** : chute t 25_conv 2.39→1.09 (n=275) — alerte fausse : t est remonte ensuite.
- **09-12/07** : 25_conv n 413→478, t 2.21→2.41, E ~0.50 stable. t qui tient/remonte avec n = signal credible. Manque fwd 28j (atteint ~20/07) — seul chemin vers VERT visible.
- **12/07** : 23_carry n=98 t=1.08 stagne (E gonflee confirmee vs 02/07). 24 nul (t<0). 27b/c a n=36 : t ±2.2 mais miroirs, hypothese semaine 1 CONFIRMEE (PnL s'annulent). 28_carry_hold emerge (n=36 t=1.81), trop court. 27c MDD 217 = perdant significatif.

## Qualite de l'Arbitre dans le temps
- Semaine 1-2 : calibration J+7 TOUJOURS null → zero preuve. Plafond maintenu 1.0 (regle par defaut).
- Qualitatif : 0 panne, notes quotidiennes coherentes avec la gate, respecte n<30=bruit, auto-conf 0.5 en regime plat. Non probant tant que non score.
- Aucune mission emise semaine 1 (oubli) → 3 missions emises cette semaine.

## Echeances
- ~13-15/07 : REV DYDX/FARTCOIN echues, exiger verification par l'Arbitre.
- ~20/07 : 25_conv fwd 28j. Si t>=2 tient → candidat VERT, decision humaine.
- Semaine 3 : si calibration null persiste → ESCALADE (pipeline casse probable).
- 27b/c vers n=50 : verifier effondrement des t miroirs.

## Regles que je me fixe
- Seule la calibration J+7 justifie de baisser/valider le plafond.
- Ne jamais lire un seul cote d'une paire miroir.
- Chute ponctuelle de t (03/07) ne condamne pas : juger sur tendance multi-semaines.