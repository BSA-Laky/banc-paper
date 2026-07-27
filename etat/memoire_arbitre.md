# Mémoire Arbitre — MAJ 2026-07-27

## Verdicts datés
- 24_funding: n=168,t=-3.21 (25/07:-2.41→26/07:-2.97→27/07:-3.21). Dégradation monotone 3e jour confirmée, structurelle. PROCHE ROUGE, surveiller m1 en priorité demain.
- 28_carry_hold: n=83,t=3.73,E=4.0066,pnl_j=14.334. CREDIBLE, 8e confirmation t>2.3 (m2 actif, sain).
- 25_conv: VERT, n=1098,t=3.83,E=0.4257. Stable, référence de crédibilité.
- 27a_rev_premium: n=41(>30),t=-0.27,E=-0.6486. Toujours non significatif, suivi vers n=50 (m3).
- 27b/27c miroirs: pattern -6/-8 DEFINITIF, ne plus requestionner sauf rupture nette.
- 23_carry_funding: ROUGE résiduel post-KILL, n=159,t=1.04. Confirmé clos, aucune action logs.
- 27e_arbitre: ROUGE résiduel post-KILL, n=30,t=-0.4. Avertissement 15/07 recyclé (>24h) mais résiduel connu, pas nouvelle alerte, clos.
- Témoin10: n=1157,t=-0.89,sain=true. Stable hors plage historique sans rupture.
- Calibration arbitre: n=13,taux=0.538,brier=0.252. n<20, prudence conf≤0.55 maintenue.

## Leçons
- t qui monte avec n croissant = crédible (25_conv,28_carry).
- Dégradation monotone t sur 3+ relevés = structurelle (24_funding), pas du bruit.
- Miroirs 27b/c: somme -6/-8 systématique, définitif.
- t extrême n<30 = piège; 27a,27f,27g10 sous surveillance légère.
- KILL 'exécuté' laisse stats résiduelles (23,27e): vérifier absence dans dernières_actions avant re-signalement — toujours vrai.
- Calibration arbitre reste n<20 depuis semaines: aucune règle prouvable, prudence permanente requise.

## A surveiller
- 24_funding: t=-3.21, dégradation 3e jour, probable bascule ROUGE J+1 ou J+2.
- 27a_rev_premium: n=41, continuer vers n=50.
- BTC plat (ret7=-0.15%), pas de signal directionnel fort.

## Divers
- Banc non suspect. Autofinancement: coût API 18.73$ (26/07), revenus réels 0€, reste 35€ (fictif/paper).