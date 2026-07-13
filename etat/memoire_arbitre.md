# Memoire Arbitre — MAJ 2026-07-13

## Verdicts dates
- **02-03/07** : neutre (BTC ~61800). 25_conv t 2.39→1.09.
- **09/07** : neutre-haussier faible (63062). 25_conv n=413 t=2.21.
- **10/07** : neutre-haussier mou (64189). n=429 t=2.34 E=0.52.
- **11/07** : neutre (64243). n=452 t=2.31 E=0.49. Conf 0.5.
- **12/07** : neutre (63719, ret plats). n=478 t=2.41. Conf 0.5.
- **13/07** : neutre (62796, ret1 -1.5% ret7 -2.0% ret30 -2.5% TOUS neg → biais baissier mou). 25_conv n=489 t=2.52 E=0.52 t monte encore. Conf 0.5.

## Bots — etat
- `25_conv` : n=489 t=2.52 E=0.52. t tient/monte (2.31→2.41→2.52) avec n → credible, seule ref.
- `23_carry` : n=99 t=1.25 E=0.96 → E gonflee/t faible, douteux.
- `24_funding` : n=92 t=-0.83 E<0 → aucun edge.
- `28_carry_hold` : n=39 t=1.83 E=3.67 → sort du bruit, n court, surveiller.
- `27b/27c` : n=37 t=±2.4 miroirs, somme ~nulle → ne croire aucun cote.
- `27f10` : n=67 t=0.38 → nul.
- `27a/d/e/f/g10` : n=1-32 sous/proche seuil → ignorer.

## Lecons
- Jamais promouvoir n<30 quel que soit t.
- t qui BAISSE quand n MONTE = illusoire ; t qui TIENT/MONTE a n eleve (25_conv 489) = credible.
- Miroirs 27b/c : PnL s'annulent.
- PnL isole d'un jour ne fait pas edge.
- ret7/ret30 negatifs mais faibles = biais baissier mou, pas cassure ; conf ~0.5.
- Calibration n=1 taux 1.0 = degeneree, traiter comme null → rester humble.

## A surveiller
- REV DYDX(02/07)/FARTCOIN(03/07) : issues jamais apparues dans brief, relancer si donnees.
- REV VINE/JTO/BLUR(08/07)+MOM VINE(09/07) : ~19-21/07. MOM SYRUP(10/07). MOM CASHCAT(11/07)~mi-aout.
- 25_conv : t tient-il >n=489 ?
- 28_carry_hold : n durable + t>1.5 ?
- BTC : ret30 devient-il franchement <-3% (cassure) ?
- Calibration arbitre : reste degeneree/null.

## Divers
- Temoin 10 sain (t=0.47 n=238). Banc non suspect. Age avis 22.8h. 27d live CASHCAT -7.75.