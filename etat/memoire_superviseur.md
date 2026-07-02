# Meta-memoire Superviseur — maj 2026-07-02 (semaine 1)

## Tendances de fond
- Marche : BTC 61839, ret7 +3.5% vs ret30 -7.3% → rebond court terme dans tendance mensuelle baissiere. Regime indecis.
- Banc fiable : temoin 10 sain (t=0.66, n=107), banc_suspect=false toute la semaine.

## Verdicts dates
- **2026-07-02** : aucun bot VERT. `25_convergence` seul candidat serieux (n=262, E=0.35, t=2.39, ORANGE, manque n_go=300 + fwd 28j). `23_carry` E=0.94 mais t=1.18 → non significatif, a surveiller pour degonflement. `24` t=0.47 nul. `27a-d` n<30 = bruit, statut GRIS correct.
- **2026-07-02** : extreme DYDX -23.6%. Arbitre a joue REV dessus (paper). Echeance de verification ~11/07.

## Qualite de l'Arbitre dans le temps
- Semaine 1 : calibration J+7 null → AUCUNE preuve de valeur. Consigne : plafond 1.0 (regle par defaut si inconnue).
- Signaux qualitatifs positifs : ses notes respectent la regle n<30=bruit, se plafonne lui-meme a ~0.55 en regime indecis, memoire coherente avec la gate. Pas de panne (0 consecutive).
- Point de vigilance : tant que calibration=null, sa prudence apparente ne vaut rien de prouve. Premier scoring attendu ~09-11/07.

## Echeances
- ~11/07 : resultat REV DYDX + premiers verdicts scorables J+7.
- `25_convergence` : franchissement n=300 probable sous 2-3 semaines au rythme actuel (~35 trades/j les jours actifs) ; forward 28j atteint ~20/07.
- Passage attendu des 27b/27c au-dessus de n=30 : verifier si leurs t extremes s'effondrent (hypothese : oui).

## Regles que je me fixe
- Ne jamais relever le plafond sur la base de notes bien ecrites : seule la calibration J+7 compte.
- Si calibration toujours null a la semaine 3, escalader (incoherence pipeline possible).
- A/B 25 vs 23 (t_welch=-0.73) : non concluant, ne pas trancher.