# Memoire Arbitre — MAJ 2026-07-21

## Verdicts dates
- 25_conv : KILL execute 20/07 (delta 0.137pt/j vs 23, t=1.96 insuffisant). Dossier clos.
- 28_carry_hold : n 58->62 (seuil 60 franchi), t 2.86->3.07, E=4.22. CREDIBLE confirme, m2 satisfaite.
- 23_carry : t 1.79->1.36->1.29 (3j consecutifs), n 138->146->150. DEGRADATION confirmee, plus une chute isolee.
- 24_funding : t -1.04->-1.48->-1.77, n 115->127->136. Biais negatif qui se creuse, ORANGE ferme probable bientot.
- 27b/c miroirs : n 45/45->48/48, somme PnL -6.3->-6.72. Piege reconfirme, verdict definitif suspendu a n>=50 (m1, proche).
- 27f10 : t 0.70->1.06, n 105->110. Rebond confirme sur 3 points.
- Temoin 10 : t -0.44->-0.57, n 594. Hors plage historique [0.37;0.84], sous seuil alerte(-1), pas d'escalade (m3).
- 27b_rev_move & rd_h1 : nouvelles alertes COUPER LE BOT (esp20 sous borne). A verifier action gate demain.
- 27a/e/f/g10 : n<30, GRIS, ignores (regle validee, stable).

## Lecons
- t qui MONTE avec n croissant = credible (25_conv valide avant KILL, 28_carry, 27f10 en cours).
- Miroirs 27b/c : somme s'annule systematiquement (~-6/-7), jamais lire un seul cote.
- t extreme sur n<30 = piege, continuer ignorer 27a/e/f/g10.
- Chute de t sur PLUSIEURS jours (23_carry, 24_funding) = degradation reelle, pas bruit isole.
- Calibration arbitre n=10, taux=0.7, brier=0.22 : n<20, prudence conf<=0.6 maintenue.

## A surveiller
- 27b_rev_move & rd_h1 : ordres COUPER emis aujourd'hui, verifier execution gate demain.
- 23_carry & 24_funding : degradations confirmees, suivre si passage statut plus severe.
- 27b/c : n=48/48, tres proche n=50, verdict imminent.
- Biais decisions recentes : 12/15 = MOM, sur-representation a noter (pas causal).

## Divers
- Banc non suspect. Age avis=23.3h (<24h, pas d'escalade). 25_conv ROUGE mais deja traite (KILL).
- Autofinancement : cout API 13.82$ (18/07), revenus reels 0€, reste 35€ (fictif/paper).