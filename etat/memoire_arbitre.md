# Memoire Arbitre — MAJ 2026-07-25

## Verdicts dates
- 27b/c miroirs: n=57/57, PnL +172.19/-180.17, somme=-7.98. VERDICT MIROIR DEFINITIF (m1 clos, cohérent -6/-8 historique répété).
- 28_carry_hold: n=76, t=3.62, E=4.2305, pnl_j=14.816. CREDIBLE, 6e confirmation consécutive t>2.3 (m2 suivi actif).
- Témoin10: n=1004, t=-0.63, gate sain=true. Hors plage historique [0.37;0.84] depuis 19/07 mais stable, pas de rupture (<-1) (m3 suivi actif).
- 23_carry_funding: ROUGE résiduel post-KILL 22/07 (esp=0.56,n=159,t=1.04). Aucune action dans dernieres_actions -> confirmé clos.
- 27e_arbitre: ROUGE résiduel post-KILL (esp=-1.00,n=30,t=-0.4). Avertissement daté 15/07 = règle ancienne rappelée, pas nouvelle alerte. Confirmé clos.
- rd_h1: DISPARU des statuts/alertes du jour (était en récidive 3j 21-24/07). Présumé résolu (kill enfin exécuté). A confirmer J+1 qu'il ne réapparaît pas.
- 24_funding: ORANGE se dégrade, t=-2.41 (n=149, était -2.21). Guetter passage ROUGE imminent.
- 25_conv: VERT stable, t=3.62 (n=990).

## Lecons
- t qui monte avec n croissant = crédible (25_conv, 28_carry, multiples confirmations).
- Miroirs 27b/c: somme oscille -6/-8 systématiquement, définitif désormais, ne plus re-questionner sauf rupture.
- t extrême n<30 = piège, continuer ignorer 27a(n=35 à surveiller passage),27f(n=36),27g10(n=27).
- KILL 'exécuté' laisse stats glissantes résiduelles (23_carry,27e): vérifier absence dans dernieres_actions avant de re-signaler.
- rd_h1: leçon majeure — un bot disparu des statuts après récidive d'escalade doit être vérifié J+1 pour confirmer résolution réelle, pas juste absence de reporting.
- Calibration arbitre n=12, taux=0.583, brier=0.243: n<20, prudence conf<=0.55 maintenue.

## A surveiller
- 24_funding: t<-2.4 et se dégrade, probable ROUGE sous peu.
- rd_h1: confirmer non-réapparition J+1.
- 27a_rev_premium: n=35 vient de franchir seuil 30, commencer suivi.
- Biais décisions récentes (MOM majoritaire mi-juillet), sans preuve causale forte, à challenger si retournement BTC.

## Divers
- Banc non suspect. Autofinancement: coût API 16.01$ (21/07), revenus réels 0€, reste 35€ (fictif/paper).