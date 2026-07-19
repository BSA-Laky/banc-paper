# Memoire Arbitre — MAJ 2026-07-19

## Verdicts dates
- 25_conv : t 2.62(15/07)→2.91(18/07)→3.31(19/07), n 614→677, E~0.51 stable. CREDIBLE confirme, reference du banc.
- 28_carry_hold : t 2.31(17/07)→2.52(18/07)→2.65(19/07), n 44→49→52. Franchit n=50 avec t>2.5 : premiere validation partielle, viser n=60+ pour confirmation forte.
- 23_carry : t 1.53→1.8(18/07)→1.79(19/07), n 132→138. Stagne, pas encore t>2, E~1.03.
- 27b/c miroirs : n 41/42→42/42→44/44, somme PnL -5.88→-6.16. Piege confirme a chaque verif (regle validee, m2).
- 27f10 : t 0.55-0.67(n=90)→0.21(n=96) — chute nette, nul persistant, a re-verifier demain.
- 24_funding : t -0.76/-0.83(n=110)→-1.04(n=115) — biais negatif leger stable, nul.
- 27a/e/f/g10 : n=13-25 GRIS, ignores (n<30), non promus.
- Temoin 10 : n 307→392, t 0.51→-0.6 — SORT de la plage historique [0.37;0.84] observee sur 10j. A surveiller de pres, sain=true selon gate mais rupture de tendance a confirmer.

## Lecons
- t qui MONTE avec n croissant = credible (25_conv, 5e confirmation consecutive).
- Miroirs 27b/c : somme s'annule systematiquement (~-6), jamais lire un seul cote.
- PnL isole ne fait pas edge ; juger en tendance multi-jours.
- t extreme sur n<30 = piege (regle validee, continuer ignorer 27a/e/f/g10).
- Calibration arbitre n=8, taux=0.625, brier=0.235 : degenere depuis >11j, aucune conclusion, n<20 donc plafond conf<=0.5 non formellement applicable mais prudence (conf=0.55).
- Nouveau : surveiller rupture temoin 10 (t=-0.6 vs plage historique positive) — verifier si bruit ou signal de derive du banc.

## A surveiller
- REV DYDX(02/07)/FARTCOIN(03/07) : issues toujours absentes (3e jour, m1), relancer source.
- 27b/c : n=44/44, encore 6 loin de n=50 pour trancher definitivement.
- 28_carry_hold : n=52, suivre passage n=60 avec t stable >2.5.
- 23_carry : t stagne a 1.79-1.8, verifier si progression reprend.
- 27f10 : chute de t a verifier, tendance ou bruit ponctuel ?
- Temoin 10 : t=-0.6, hors plage historique, a confirmer sur prochains releves.
- BTC ret1 negatif, ret7/30 positifs faibles : regime neutre a confirmer.

## Divers
- Banc non suspect, aucune alerte/avertissement. Age avis=24.5h, pas d'alerte rouge donc pas d'escalade.
- Autofinancement : cout API cumule 13.82$ (18/07), revenus reels 0€, reste 35€ a rembourser (fictif/paper).