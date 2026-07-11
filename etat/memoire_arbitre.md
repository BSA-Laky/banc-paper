# Memoire Arbitre — MAJ 2026-07-11

## Verdicts dates
- **2026-07-02/03** : neutre (BTC ~61800). 25_conv t 2.39→1.09.
- **2026-07-09** : neutre-haussier faible (BTC 63062). 25_conv n=413 t=2.21.
- **2026-07-10** : neutre-haussier mou (BTC 64189). 25_conv n=429 t=2.34 E=0.52.
- **2026-07-11** : neutre (BTC 64243, ret7+1.8% ret30+1.0% mous, momentum s'essouffle). 25_conv n=452 t=2.31 E=0.49. Conf 0.5.

## Bots — etat
- `25_convergence_basis` : n=452 t=2.31 E=0.49. t tient (2.34→2.31) avec n+23 → credibilite prudente confirmee. Seule ref.
- `23_carry_funding` : n=94 t=1.12 E=0.88. E gonflee/t faible → douteux, t stagne.
- `24_funding_multivenues` : n=82 t=-0.55 E<0 → aucun edge.
- `28_carry_hold` : n=34 t=1.81 E=4.16 → sort du bruit, evaluer (n encore court).
- `27b/27c rev/mom_move` : n=35 t=±2.2 miroirs → PnL ~nul. NE PAS croire un cote.
- `27f10_selecteur` : n=60 t=0.42 → nul (PnL +8.58 du jour = bruit).
- `27a/d/e/f` : n=14-29 sous seuil. Ignorer.

## Lecons
- Jamais promouvoir n<30 quel que soit le t.
- t qui BAISSE quand n MONTE = illusoire ; t qui TIENT avec n eleve (25_conv 452) = credible.
- Bots miroirs (27b/c) : PnL s'annulent.
- PnL isole d'un jour (27f10 +8.58) ne fait pas edge : regarder t/n.
- ret7-ret30 mous = conf plafonnee ~0.5.

## A surveiller
- REV DYDX (02/07) echeance ~11/07 — verifier issue AUJOURD'HUI.
- REV FARTCOIN (03/07 +21.2%) ~12/07.
- Serie MOM 06-08/07 (BLUR,HMSTR,BANANA,GRASS) : paye ou piege ? mi-juillet.
- REV VINE/JTO/BLUR (08/07) + MOM VINE (09/07) : ~19-21/07. MOM SYRUP (10/07).
- 25_conv : t tient-il au-dela de n=452 ?
- 28_carry_hold : n durable + t>1.5 ?
- Calibration arbitre TOUJOURS null → verdicts non scores, rester humble.

## Divers
- Temoin aleatoire 10 sain (t=0.84 n=204). Banc non suspect. Age avis 21.8h. Superviseur 1 echec (non bloquant).