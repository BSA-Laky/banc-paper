# Mémoire Arbitre — MAJ 2026-07-26

## Verdicts datés
- 27b/c miroirs: n=58/58, PnL +190.85/-198.97, somme=-8.12. VERDICT DEFINITIF confirmé (m1 clos, 2e passage n>=50, pattern -6/-8 répété).
- 28_carry_hold: n=82, t=3.70, E=4.0271, pnl_j=14.547. CREDIBLE, 7e confirmation t>2.3 (m2 suivi actif, pas de signal).
- Témoin10: n=1101, t=-0.81, sain=true. Hors plage [0.37;0.84] depuis 19/07, stable, pas de rupture <-1 (m3 suivi actif).
- 23_carry_funding: ROUGE résiduel post-KILL, esp=0.56,n=159,t=1.04. Aucune action logs → confirmé clos.
- 27e_arbitre: ROUGE résiduel post-KILL, esp=-1.00,n=30,t=-0.4. Avertissement 15/07 recyclé, pas nouvelle alerte. Clos.
- rd_h1: DISPARU confirmé J+1 (absent statuts/alertes 2j consécutifs) — résolution validée.
- 24_funding: ORANGE se dégrade fort, t=-2.97 (n=162, était -2.41 le 25/07). PROCHE BASCULE ROUGE, surveiller demain en priorité.
- 25_conv: VERT stable, t=3.71 (n=1066).
- 27a_rev_premium: n=39 (>30), esp=-0.93,t=-0.37, toujours non significatif, suivi actif.

## Leçons
- t qui monte avec n croissant = crédible (25_conv, 28_carry, confirmations multiples).
- Miroirs 27b/c: somme oscille -6/-8 systématiquement, désormais DEFINITIF, ne plus re-questionner sauf rupture nette.
- t extrême n<30 = piège; 27a(n=39),27f(n=37),27g10(n=29) sous surveillance légère.
- KILL 'exécuté' laisse stats glissantes résiduelles (23_carry,27e): vérifier absence dans dernières_actions avant re-signalement.
- rd_h1: leçon confirmée — bot disparu après récidive doit être validé J+1, fait ici.
- Calibration arbitre n=12, taux=0.583, brier=0.243: n<20, prudence conf<=0.55 maintenue.

## A surveiller
- 24_funding: t=-2.97, dégradation rapide, probable ROUGE J+1.
- 27a_rev_premium: n=39, continuer suivi vers n=50.
- Biais décisions récentes (MOM majoritaire mi-juillet), à challenger si retournement BTC (actuellement plat).

## Divers
- Banc non suspect. Autofinancement: coût API 16.01$ (21/07), revenus réels 0€, reste 35€ (fictif/paper).