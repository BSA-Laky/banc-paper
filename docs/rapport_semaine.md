# Rapport du Superviseur — semaine du 2026-07-12

# Audit hebdo — 2026-07-12 (semaine 2)

## Etat des salles
- Banc sain : temoin 10 t=0.37 (n=222), banc_suspect=false toute la semaine. 0 alerte, 0 ROUGE.
- BTC 63719, ret1/7/30 quasi plats → regime neutre confirme.

## Verdicts en cours
- **25_conv** : n=478, t=2.41, E=0.50 — seule reference. t a tenu puis remonte (2.34→2.31→2.41) avec n croissant. Reste ORANGE (fwd 20j<28j). Franchira fwd 28j ~20/07.
- **28_carry_hold** : n=36, t=1.81, E=3.94 — sort du bruit, court, a suivre.
- **23_carry** : n=98, t=1.08 — E gonflee, non significatif. **24** : t=-0.68, nul.
- **27b/27c** : n=36, t=±2.2 miroirs, PnL ~somme nulle — piege confirme. **27c** MDD 217, perdant.
- **27a/e/f** n<20, **27f10** t=0.36 : bruit.

## Arbitre
- Calibration J+7 : **toujours null** → aucune preuve de valeur. 0 panne. Notes coherentes avec la gate, auto-plafonnement 0.5 correct mais NON prouve. 3 rapports/7j, missions vides (aucune emise).
- Superviseur : 1 echec non bloquant.

## 3 points pour la semaine
1. Calibration J+7 doit apparaitre : si toujours null au prochain audit (semaine 3), escalade pipeline.
2. 25_conv atteint fwd 28j ~20/07 : premier candidat verdict serieux.
3. Verifier issues REV DYDX (02/07) et REV FARTCOIN (03/07), echeances passees.

_Consigne Arbitre : confiance_max 1.00 (Calibration J+7 inconnue (null, n<20) : plafond par defaut 1.0 conforme a la regle.). Modele `claude-fable-5`._
