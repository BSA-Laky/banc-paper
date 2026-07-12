# Memoire Arbitre — MAJ 2026-07-12

## Verdicts dates
- **2026-07-02/03** : neutre (BTC ~61800). 25_conv t 2.39→1.09.
- **2026-07-09** : neutre-haussier faible (BTC 63062). 25_conv n=413 t=2.21.
- **2026-07-10** : neutre-haussier mou (BTC 64189). n=429 t=2.34 E=0.52.
- **2026-07-11** : neutre (BTC 64243, ret mous). n=452 t=2.31 E=0.49. Conf 0.5.
- **2026-07-12** : neutre (BTC 63719, ret1 -0.16% ret7 +0.13% ret30 +0.25% plats). 25_conv n=478 t=2.41 E=0.50 → t REMONTE avec n. Conf 0.5.

## Bots — etat
- `25_convergence_basis` : n=478 t=2.41 E=0.50. t tient/remonte (2.34→2.31→2.41) avec n croissant → credible, seule ref.
- `23_carry_funding` : n=98 t=1.08 E=0.82 → E gonflee/t faible, douteux, stagne.
- `24_funding_multivenues` : n=86 t=-0.68 E<0 → aucun edge.
- `28_carry_hold` : n=36 t=1.81 E=3.94 → sort du bruit, n encore court, evaluer.
- `27b/27c` : n=36 t=±2.2 miroirs → PnL ~nul, ne pas croire un cote.
- `27f10_selecteur` : n=64 t=0.36 → nul.
- `27a/d/e/f` : n=15-30 sous/proche seuil. Ignorer.

## Lecons
- Jamais promouvoir n<30 quel que soit t.
- t qui BAISSE quand n MONTE = illusoire ; t qui TIENT/MONTE avec n eleve (25_conv 478) = credible.
- Bots miroirs (27b/c) : PnL s'annulent.
- PnL isole d'un jour (conv CASHCAT +11.12) ne fait pas edge : regarder t/n.
- ret7-ret30 mous = conf plafonnee ~0.5.

## A surveiller
- REV DYDX (02/07) & REV FARTCOIN (03/07) : echeances passees ~11-12/07, verifier issues.
- Serie MOM 06-08/07 (BLUR,HMSTR,BANANA,GRASS) : paye ou piege ? mi-juillet.
- REV VINE/JTO/BLUR (08/07) + MOM VINE (09/07) : ~19-21/07. MOM SYRUP (10/07). MOM CASHCAT (11/07) ~mi-aout.
- 25_conv : t tient-il au-dela de n=478 ?
- 28_carry_hold : n durable + t>1.5 ?
- Calibration arbitre TOUJOURS null → verdicts non scores, rester humble.

## Divers
- Temoin aleatoire 10 sain (t=0.37 n=222). Banc non suspect. Age avis 22.9h. Superviseur 1 echec (non bloquant).