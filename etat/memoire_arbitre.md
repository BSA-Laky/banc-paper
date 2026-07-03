# Mémoire Arbitre — MAJ 2026-07-03

## Verdicts datés
- **2026-07-02** : neutre (BTC 61839, ret7 +3.5% vs ret30 -7.3%). Convergence basis (25) seul crédible (n=262, t=2.39).
- **2026-07-03** : neutre (BTC 61800, ret7 +2.9% vs ret30 -3.6%). ATTENTION : t de 25_conv chute 2.39→1.09 alors que n monte 262→275. Edge se dégrade, E 0.35→0.24. À surveiller de près.

## Bots — état
- `25_convergence_basis` : n=275, t=1.09, E=0.24. Était réf de qualité, mais t s'effondre. Douter désormais.
- `23_carry_funding` : n=52, t=1.03, E=0.77 → E gonflée par peu de trades, t faible. Douteux.
- `24_funding_multivenues` : n=57, t=0.36 → aucun edge démontré.
- `27a-d rev/mom_move` : n=7 à 20, sous seuil bruit (n<30). 27b/27c t=±2.6 sur n=20 = piège classique. NE PAS croire. 27b et 27c sont miroirs → PnL somme ~nulle sur DYDX/HEMI le 03/07.

## Leçons
- Ne jamais promouvoir un signal n<30, peu importe le t-stat.
- Un t-stat qui BAISSE quand n MONTE = signe d'edge illusoire (cas 25_conv). Ne pas confondre maturité et solidité.
- Divergence ret7/ret30 = marché indécis → confiance plafonnée ~0.5.

## À surveiller
- Résultat REV DYDX (décidé 02/07, move -25.7%) vers ~2026-07-11.
- Résultat REV FARTCOIN (décidé 03/07, move +21.2%) vers ~2026-07-12.
- 25_conv : t continue-t-il de chuter ? Si t<1 durablement → déclasser mentalement.
- 23_carry : E=0.77 tiendra-t-elle si n grandit et t reste faible ?
- Passage éventuel 27x au-dessus de n=30 → statut réel à réévaluer.
- Calibration arbitre encore null : mes verdicts non scorés, rester humble.

## Divers
- Témoin aléatoire 10 sain (t=0.53, n=114) → banc non biaisé.
- Banc non suspect. Aucune alerte ouverte ni événement extrême.