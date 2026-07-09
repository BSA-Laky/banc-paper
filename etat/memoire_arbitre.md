# Memoire Arbitre — MAJ 2026-07-09

## Verdicts dates
- **2026-07-02** : neutre (BTC 61839).
- **2026-07-03** : neutre (BTC 61800). t 25_conv chute 2.39→1.09.
- **2026-07-09** : neutre-haussier faible (BTC 63062, ret7+2.4% ret30+2.2% alignes). 25_conv redresse : n=413 t=2.21 E=0.50. Conf 0.5, hausse molle.

## Bots — etat
- `25_convergence_basis` : n=413, t=2.21, E=0.50. Rebond apres chute 03/07. Reference prudente, surveiller stabilite t.
- `23_carry_funding` : n=88, t=1.21, E=1.02. E gonflee/t faible → douteux.
- `24_funding_multivenues` : n=82, t=-0.55, E<0 → aucun edge.
- `28_carry_hold` : n=30, t=1.67 → sort du bruit, a evaluer.
- `27b/27c rev/mom_move` : n=31, t=±2.3 miroirs → PnL somme ~nulle (VINE +21.97/-22.11). NE PAS croire.
- `27a/d/e/f` : n=10-23, sous seuil. Ignorer.
- `27f10_selecteur` : n=39, t=-0.06 → nul.

## Lecons
- Jamais promouvoir n<30 quel que soit le t.
- t qui BAISSE quand n MONTE = edge illusoire (25_conv 03/07) ; rebond t avec n eleve (413) = credibilite prudente.
- Bots miroirs (27b/c) : PnL s'annulent, ne pas lire un cote isole.
- Faiblesse ret7-ret30 = confiance plafonnee ~0.5.

## A surveiller
- REV DYDX (02/07, -25.7%) ~11/07.
- REV FARTCOIN (03/07, +21.2%) ~12/07.
- Serie MOM 06-08/07 (BLUR, HMSTR, BANANA, GRASS) : echeances mi-juillet, momentum a paye ou piege ?
- REV VINE/JTO/BLUR (08/07) + MOM VINE (09/07) : issues ~19-21/07.
- 25_conv : t=2.21 tient-il au-dela de n=413 ?
- 28_carry_hold : n durable avec t>1.5 ?
- Calibration arbitre TOUJOURS null → verdicts non scores, rester humble.

## Divers
- Temoin aleatoire 10 sain (t=0.54, n=183). Banc non suspect, aucune alerte. Extreme VINE +32% le 09/07.