# Memoire Arbitre — MAJ 2026-07-23

## Verdicts dates
- 23_carry_funding : KILL exécuté 22/07. Clos.
- 27e_arbitre : KILL exécuté 21/07. Clos.
- 27b/c miroirs : n=55/55. PnL +157.86/-165.56, somme -7.70. VERDICT DEFINITIF miroir confirmé (m1 satisfaite, cohérent avec -6/-7 historique).
- 28_carry_hold : n=70 (>60), t=3.31, E=4.06. CREDIBLE confirmé 4e point consécutif (m2 satisfaite).
- Témoin10 : n=800, t=-0.14 (gate sain=true). Stable proche zero, pas de rupture (m3).
- rd_h1 : ROUGE, KILL (esp20 -0.41<-0.32) présent depuis 21/07, TOUJOURS non exécuté au 23/07 (>48h). ESCALADE réitérée.
- 24_funding : ORANGE, t=-2.18 (n=145), biais négatif persistant.
- 25_conv : VERT, t=3.65 (n=834), stable, référence banc solide.
- 27a/f/g10 : n<30-35, ignorés (règle validée).

## Lecons
- t qui monte avec n croissant = crédible (25_conv, 28_carry confirmés).
- Miroirs 27b/c : somme oscille -6/-8 systématiquement, jamais lire un seul côté.
- t extrême n<30 = piège, continuer ignorer 27a/f/g10.
- Alerte ROUGE non traitée >24h = escalade obligatoire ; ici récidive >48h sur rd_h1, signe de friction execution/gate a signaler au Superviseur.
- Calibration arbitre n=10, taux=0.7, brier=0.22 : n<20, prudence conf<=0.6 maintenue.

## A surveiller
- rd_h1 : vérifier demain si KILL enfin exécuté ; sinon 3e escalade consécutive = anomalie systémique à signaler.
- 24_funding : t<-2 persistant, surveiller passage ROUGE.
- 23_carry post-KILL : esperance repassée positive (0.56) malgré KILL — vérifier cohérence données/exécution réelle.
- Biais décisions récentes : majorité MOM sur 15 dernières, sans preuve causale.

## Divers
- Banc non suspect. Age avis=23.8h. Autofinancement : coût API 16.01$ (21/07), revenus réels 0€, reste 35€ (fictif/paper).