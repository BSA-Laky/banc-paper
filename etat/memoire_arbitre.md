# Memoire Arbitre — MAJ 2026-07-31

## Verdicts dates
- 24_funding: KILL execute 29/07 (n=168->171, t=-3,21->-3,3, E=-0,504->-0,509). Residuel ROUGE confirme, clos (m1).
- 28_carry_hold: reset n=83->1 (30/07), t=0,0, E=11,64, statut GRIS. Correction comptable probable (meme faute funding abs que 24). NE PAS crediter, resuivre n->100 (m2).
- 27a_rev_premium: n=41->44, t=-0,27->-0,47, E=-0,649->-1,094 — stable, suivi n->50 (m3).
- 25_conv: ORANGE n=192, t=-0,13, E=-0,015 — decrochage vs historique VERT n=1098 (t etait 3,72), a surveiller.
- 27b/27c miroirs: pattern -6/-8 DEFINITIF, ne plus requestionner.
- 27e_arbitre: ROUGE residuel (n=30, t=-0,4), avertissement recycle depuis 15/07, absent des dernieres actions -> pas d'escalade repetee.
- Temoin10: n=1359, t=-1,31, sain, hors plage historique sans rupture.
- Calibration arbitre: n=20 (SEUIL ATTEINT), taux_correct=0,45 <=0,5 -> regle stricte: confiance <=0,5 appliquee.

## Lecons
- t qui monte avec n croissant = credible (historique pre-reset 25_conv/28_carry).
- Miroirs 27b/c definitif -6/-8.
- KILL 'execute' laisse stats residuelles: verifier absence dans dernieres_actions avant re-signalement.
- Reset brutal de n (28_carry 83->1) = correction comptable probable, pas corruption — verifier avant de crediter E elevee sur petit n.
- Calibration arbitre franchit n=20 avec taux=0,45: conf<=0,5 systematique tant que non redresse.
- NOUVEAU 31/07: 25_conv t chute a -0,13 (etait 3,72 historique) — surveiller si degradation monotone se confirme (regle 21-26/07).

## A surveiller
- 28_carry: progression n=1->100 post-reset, verifier coherence comptable
- 27a: n=44->50
- 25_conv: t=-0,13 sur n=192, verifier si degradation structurelle ou bruit
- Calibration arbitre: suivre taux_correct, si redresse >0,5 lever plafond conf

## Divers
- Banc non suspect. Autofinancement: cout API 18,73$ (26/07), revenus reels 0€, reste 35€ (fictif).