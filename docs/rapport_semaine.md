# Rapport du Superviseur — semaine du 2026-07-19

# Audit hebdo — 2026-07-19

## Salles
- Banc sain, banc_suspect=false, 0 alerte. Temoin 10 : n=395 t=-0.65 sain, mais SORT de la plage historique [0.37;0.84] — a suivre, pas d'action.
- **25_conv** : n=681 t=3.33 E=0.51 — 5e hausse consecutive de t. fwd 26.6j : franchit 28j vers le 21/07 → candidat VERT imminent, decision humaine a preparer.
- **28_carry_hold** : n=52 t=2.65 E=4.22 (3.4x mu_ref, AUDITE 15/07 : 5/5 trades coherents funding reel). Viser n=60.
- **23_carry** t=1.79 stagne. **24** nul (t=-1.04). **27b/c** miroirs reconfirmes (somme -6.16 a n=44). 27a/e/f/g10 : n<30, bruit.

## Arbitre
- Calibration J+7 : n=8, taux=0.625, brier=0.235 — n<20, non probante. Plafond 1.0 (regle par defaut). 0 panne cette semaine (2 echecs le 17/07, resolus). Missions m1-m3 executees avec rigueur ; m1 (issues DYDX/FARTCOIN) bloquee cote donnees depuis 3 releves — lacune de flux, pas de l'Arbitre.

## Cout / machine
- API 13.82$ (18/07), revenus 0€, reste 35€. Veilleur : fill testnet 28.6%, 111/143 rejets = absence contrepartie — friction connue, stable.

## 3 points semaine
1. 25_conv atteint fwd 28j (~21/07) : si t>=2 tient, dossier VERT au Commandant.
2. 28_carry_hold : confirmer t>2.5 a n=60.
3. h1 (carry percentile) en attente d'approbation Commandant (approve h1).

_Consigne Arbitre : confiance_max 1.00 (Calibration J+7 n=8 <20 : non probante, plafond par defaut 1.0.). Modele `claude-fable-5`._
