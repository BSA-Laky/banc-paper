# Memoire Arbitre — MAJ 2026-07-09

## Verdicts dates
- **2026-07-02** : neutre (BTC 61839).
- **2026-07-03** : neutre (BTC 61800). t de 25_conv chute 2.39→1.09.
- **2026-07-09** : neutre-haussier faible (BTC 63062, ret7+2.4% ret30+2.2% alignes). 25_conv se REDRESSE : n=413 t=2.21 E=0.50. Confiance 0.5, hausse trop molle.

## Bots — etat
- `25_convergence_basis` : n=413, t=2.21, E=0.50. Redressement apres chute 03/07. Redevient reference, mais surveiller stabilite du t.
- `23_carry_funding` : n=88, t=1.21, E=1.02. E gonflee, t faible → douteux.
- `24_funding_multivenues` : n=82, t=-0.55, E<0 → aucun edge, negatif.
- `28_carry_hold` : n=30, t=1.67 → franchit seuil bruit, a evaluer.
- `27b/27c rev/mom_move` : n=31, t=±2.3 miroirs → PnL somme ~nulle (VINE +21.97/-22.11). NE PAS croire.
- `27a/d/e/f` : n=10-23, sous seuil bruit. Ignorer.
- `27f10_selecteur` : n=39, t=-0.06 → nul.

## Lecons
- Jamais promouvoir signal n<30 quel que soit le t.
- t qui BAISSE quand n MONTE = edge illusoire (cas 25_conv 03/07) ; MAIS un rebond du t avec n eleve (413) redonne credibilite prudente.
- Bots miroirs (27b/c) : PnL s'annulent, ne pas lire un cote isole.
- Divergence/faiblesse ret7-ret30 = confiance plafonnee ~0.5.

## A surveiller
- Resultat REV DYDX (02/07, move -25.7%) ~2026-07-11.
- Resultat REV FARTCOIN (03/07, move +21.2%) ~2026-07-12.
- Serie MOM 06-08/07 (BLUR, HMSTR, BANANA, GRASS) : echeances mi-juillet, verifier si momentum haussier a paye ou piege.
- REV VINE/JTO/BLUR (08/07) et MOM VINE (09/07) : issues ~19-21/07.
- 25_conv : le t=2.21 tient-il au-dela de n=413 ?
- 28_carry_hold : franchira-t-il n durablement avec t>1.5 ?
- Calibration arbitre TOUJOURS null → verdicts non scores, rester humble.

## Divers
- Temoin aleatoire 10 sain (t=0.54, n=183) → banc non biaise.
- Banc non suspect, aucune alerte ouverte. Evenement extreme VINE +32% le 09/07.