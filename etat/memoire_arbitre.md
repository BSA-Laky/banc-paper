# Mémoire Arbitre — MAJ 2026-07-29

## Verdicts datés
- 24_funding: n=168,t=-3.21,E=-0.5038 — IDENTIQUE au relevé 26-28/07. Suspicion de stagnation des données (3j sans update?). ORANGE maintenu (m1).
- 28_carry_hold: n=83,t=3.73,E=4.0066,pnl_j=14.334 — identique aux relevés precedents, pas de progression vers n=100. Sain, m2 actif.
- 27a_rev_premium: n=41,t=-0.27,E=-0.6486 — inchangé, suivi vers n=50 (m3), rien à signaler.
- 25_conv: VERT,n=1098,t=3.83,E=0.4257 — référence stable.
- 27b/27c miroirs: pattern -6/-8 DEFINITIF, ne plus requestionner.
- 23_carry_funding & 27e_arbitre: ROUGE résiduels post-KILL, clos, absents des dernières actions — avertissement 27e recyclé depuis 15/07 (>2 sem), toujours traité comme résiduel non-actif (pas de nouvelle action bot), donc pas d'escalade répétée tant que stats stagnantes et absentes des logs d'action.
- Témoin10: n=1157,t=-0.89, sain, hors plage historique sans rupture.
- Calibration arbitre: n=13,taux=0.538,brier=0.252 — toujours n<20, prudence conf≤0.55.

## Leçons
- t qui monte avec n croissant = crédible (25_conv,28_carry historique).
- Miroirs 27b/c définitif -6/-8.
- KILL 'exécuté' laisse stats résiduelles (23,27e): vérifier absence dans dernières_actions avant re-signalement.
- NOUVEAU 29/07: vérifier fraîcheur des données — brief daté 26/07 traité 29/07, stats missions identiques à J-3. Si répétition demain, escalader (donnees potentiellement figées).

## A surveiller
- Fraîcheur des relevés (priorité nouvelle)
- 24_funding: guetter reprise dégradation si nouvelle donnée arrive
- 27a: n=41→50
- 28_carry: n=83→100

## Divers
- Banc non suspect. Autofinancement: coût API 18.73$ (26/07), revenus réels 0€, reste 35€ (fictif).