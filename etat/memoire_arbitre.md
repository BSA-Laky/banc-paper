# Memoire Arbitre — MAJ 2026-07-18

## Verdicts dates
- 25_conv : t 2.21(09/07)→2.62(15/07)→2.83(17/07)→2.91(18/07), n 413→614. Tendance MONTANTE continue = CREDIBLE, reference principale du banc.
- 23_carry : t 1.18(pre-09)→1.53(17/07)→1.8(18/07), n 98→132, E=1.08. Progresse mais pas encore seuil fort (viser t>2).
- 28_carry_hold : t 2.05→2.31(17/07)→2.52(18/07), n=44→49, E=4.22. Sort du bruit, n encore <60.
- 27b/c miroirs : n=41→42/42, somme PnL -5.74→-5.88 quasi nulle. Confirme piege a chaque verif (m2), seuil n=50 pas atteint.
- 27f10 n=85→90 t=0.55-0.67 : nul persistant. 24_funding n=104→110 t=-0.76 a -0.83 : nul persistant.
- 27a/e/f/g10 n=12-24 GRIS : ignores (n<30), non promus.
- Temoin 10 : n=293→307, t=0.42→0.51, sain, mesure correctement le bruit.

## Lecons
- t qui MONTE avec n croissant = credible (25_conv exemplaire, confirme sur 4+ points).
- Miroirs 27b/c : somme s'annule systematiquement (~-6), jamais lire un seul cote.
- PnL isole d'un jour ne fait pas edge ; juger en tendance multi-jours.
- t extreme sur n<30 = piege (regle validee historiquement, continuer a ignorer 27a/e/f/g10).
- Calibration arbitre n=8 taux=0.625 brier=0.235 : TOUJOURS n<20, degenere depuis >10j. Aucune conclusion sur validite predictive Arbitre. Regle plafond conf<=0.5 ne s'applique pas formellement (n<20) mais prudence maintenue.
- Age avis 20h (<24h) : pas d'escalade requise sur ce point.

## A surveiller
- REV DYDX(02/07)/FARTCOIN(03/07) : issues toujours absentes (m1), relancer aupres source de donnees.
- 27b/c : n=42/42, verifier passage n=50 pour trancher somme nulle definitivement.
- 28_carry_hold : n a-t-il depasse 60 avec t>2.5 stable ?
- 23_carry : t continue de monter vers 2.0+ ?
- Calibration arbitre : n depassera-t-il 20 pour juger serieusement ?
- BTC ret30=+1.63% (18/07) : leger haussier, a confirmer ou s'estomper.
- CASHCAT/KAITO : pattern REV recurrent sur move_pct extremes -20/-40%, a continuer de tracker (7 occurrences en 15 decisions).

## Divers
- Banc non suspect, temoin sain (n=307, t=0.51, sain=true). Gate: aucune alerte/avertissement.
- Autofinancement : cout API cumule, revenus reels toujours 0€, reste 35€ a rembourser (fictif/paper).