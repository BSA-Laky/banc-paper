# Memoire Arbitre — MAJ 2026-07-17

## Verdicts dates
- 09→17/07 : ret30 oscille -2%/-4.5%, baissier mou non tranche. 17/07 : 62906$ ret30 -2.43%.
- 25_conv : t 2.21(09/07)→2.41(12/07)→2.62(15/07)→2.83(17/07), n 413→581. Tendance haussiere continue = CREDIBLE, seule ref solide du banc.

## Bots — etat
- `25_conv` n=581 t=2.83 E=0.502 : reference principale, t TIENT/MONTE avec n.
- `23_carry` n=114 t=1.53 E=1.04 : ameliore (1.23→1.53) mais encore sous seuil solide.
- `28_carry_hold` n=44 t=2.31 E=4.27 : sort du bruit, t monte (2.05→2.31), n encore <60, surveiller.
- `24_funding` n=104 t=-0.83 : aucun edge, constant.
- `27b/27c` n=41 t=±2.0 : miroirs confirmes, somme PnL quasi nulle (-5.74), m2 en cours (seuil n=50 pas atteint).
- `27a/e/f/g10` n=10-22 GRIS : ignores (n<30).
- `27f10` n=85 t=0.67 : nul.
- Temoin 10 : n=293 t=0.42, sain, banc mesure bien le bruit.

## Lecons
- Jamais promouvoir n<30 quel que soit t.
- t qui MONTE avec n = credible (25_conv exemplaire) ; t qui baisse quand n monte = illusoire.
- Miroirs 27b/c : somme s'annule, ne jamais lire un seul cote (confirme a n=41).
- PnL isole d'un jour ne fait pas edge.
- Calibration arbitre n=7 taux 0.714 brier 0.217 : degeneree (n<20), aucune conclusion, plafond conf 0.5.
- ARBITRE EN PANNE signale (2 echecs) + avis perime 50h : humilite renforcee, pas d'escalade tant que gate=non suspect et alertes vides.

## A surveiller
- REV DYDX(02/07)/FARTCOIN(03/07) : issues toujours absentes des donnees (m1), relancer.
- 27b/c : confirmer somme nulle a n>50 (actuellement n=41).
- 28_carry_hold : t>1.5 a n>60 ?
- 23_carry : t continue-t-il de monter vers seuil credible ?
- Calibration arbitre : sortira-t-elle du regime degenere (n>=20) ?
- BTC : ret30 recreuse-t-il ou stabilise ?
- CASHCAT/KAITO : extremes recurrents, pattern REV a verifier.

## Divers
- Banc non suspect, temoin sain. Age avis regime 49.8h (perime, a renouveler).