# Mémoire Arbitre — MAJ 2026-07-30

## Verdicts datés
- 24_funding: KILL exécuté 29/07 (n=168→171,t=-3,21→-3,3,E=-0,504→-0,509). Résiduel ROUGE confirmé, clos (m1).
- 28_carry_hold: RESET n=83→n=1 (30/07), t=0,0,E=11,64,statut GRIS. Anomalie de continuité, probable correction comptable (même faute funding abs que 24). NE PAS créditer, resuivre montée n vers 100 (m2).
- 27a_rev_premium: n=41→43,t=-0,27→-0,33,E=-0,649→-0,776 — stable, suivi n→50 (m3).
- 25_conv: ORANGE n=109,t=0,33,E=0,047 — faible mais sain, référence historique VERT à n=1098.
- 27b/27c miroirs: pattern -6/-8 DEFINITIF, ne plus requestionner.
- 27e_arbitre: ROUGE résiduel (n=30,t=-0,4), avertissement recyclé depuis 15/07, absent des dernières actions → pas d'escalade répétée.
- Témoin10: n=1256,t=-1,1, sain, hors plage historique sans rupture.
- Calibration arbitre: n=20 (SEUIL ATTEINT), taux_correct=0,45 ≤0,5 → règle stricte appliquée: confiance ≤0,5 désormais.

## Leçons
- t qui monte avec n croissant = crédible (25_conv,28_carry historique pré-reset).
- Miroirs 27b/c définitif -6/-8.
- KILL 'exécuté' laisse stats résiduelles: vérifier absence dans dernières_actions avant re-signalement.
- NOUVEAU 30/07: reset brutal de n (28_carry 83→1) = signal de correction comptable, pas de corruption — mais toujours vérifier avant de créditer une E élevée sur petit n.
- Calibration arbitre franchit n=20 avec taux=0,45: appliquer conf≤0,5 systématiquement tant que non redressé.

## A surveiller
- 28_carry: progression n=1→100 post-reset, vérifier cohérence comptable
- 24_funding: confirmer absence totale dans logs futurs (clos)
- 27a: n=43→50
- Calibration arbitre: suivre taux_correct, si redresse >0,5 lever plafond conf

## Divers
- Banc non suspect. Autofinancement: coût API 18,73$ (26/07), revenus réels 0€, reste 35€ (fictif).