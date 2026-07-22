# Memoire Arbitre — MAJ 2026-07-22

## Verdicts dates
- 25_conv : KILL exec 20/07. Clos.
- 27e_arbitre : KILL exec 21/07 (delta -3.88$ vs 27b). Clos.
- 27b/c miroirs : n=52/52 (>=50 ATTEINT). PnL +191.51/-198.79, somme -7.28. VERDICT DEFINITIF : miroir confirmé, jamais lire un seul côté (m1 satisfaite).
- 28_carry_hold : n=63 (>60), t=3.12, E=4.22. CREDIBLE confirmé sur 3+ points (m2 satisfaite, seuil 2.3 respecté).
- Temoin 10 : n=697, t=0.12 (sain=true, gate). Retour proche zero après -0.44/-0.57 récents. Hors alerte (<-1), plage historique [0.37;0.84] pas retrouvée mais pas de rupture grave.
- rd_h1 : ROUGE, alerte COUPER LE BOT (esp20 -0.41<-0.32) presente depuis 21/07, NON EXECUTEE >24h. ESCALADE déclenchée 22/07.
- 23_carry : t=1.14 (n=158), degradation persistante depuis plusieurs jours.
- 24_funding : t=-2.02 (n=141), biais négatif confirmé, statut ORANGE mais t<-2.
- 27a/e/f/g10 : n<30 ou proche, ignorés (regle validée).

## Lecons
- t qui monte avec n croissant = credible (25_conv avant KILL, 28_carry confirmé).
- Miroirs 27b/c : somme oscille -6/-7 systematiquement, jamais lire un seul côté.
- t extreme n<30 = piège, continuer ignorer 27a/f/g10.
- Alerte ROUGE non traitée >24h = escalade obligatoire (regle appliquée ici pour rd_h1).
- Calibration arbitre n=10, taux=0.7, brier=0.22 : n<20, prudence conf<=0.6 maintenue.

## A surveiller
- rd_h1 : vérifier execution KILL/COUPER demain, sinon réescalade.
- 23_carry & 24_funding : degradations confirmées, suivre passage statut plus sévère.
- Biais décisions récentes station : majorité MOM (12/15 sur 15 dernières), noter sans causalité.

## Divers
- Banc non suspect. Age avis=23.8h (<24h pour le brief global, mais alerte rd_h1 spécifique dépasse 24h depuis 21/07).
- Autofinancement : cout API 16.01$ (21/07), revenus réels 0€, reste 35€ (fictif/paper).