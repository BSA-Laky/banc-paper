# Registre R&D — hypotheses & bots de Nova (Stratege)
_Nova code et met en service les bots paper en autonomie. Kill auto par la gate._

## h1 — Carry funding module par percentile roulant d'|funding|  `[actif]`
_Declencheur : 27f_selecteur (SIMULATION galop d'essai (Commandant) : bot repute juge perdant) — 2026-07-17_
- **Mecanisme** : Le funding perpetuel remunere le cote qui prend le risque du desequilibre OI. Quand |funding| est dans le haut de sa propre distribution roulante par coin, le taux tend a se maintenir quelques heures avant mean-reversion. On se positionne CONTRE le funding (short si funding>0) pour encaisser le flux, on ferme au retour vers la normale.
- **Entree** : Entrer contre le funding quand |funding| depasse le 80e percentile de sa distribution roulante propre au coin (fenetre glissante maintenue dans etat), et vol>0 pour liquidite. · **Sortie** : Sortir quand |funding| repasse sous sa mediane roulante, ou apres 12h de detention max.
- **Seuils** : Entree: p80 roulant |funding| par coin (min 40 obs). Sortie: p50 roulant. Hold max 12h. Size 100$. · **Frais** : 2*0.00035*100 = 0.07$/trade deduits du pnl funding accumule.
- **Kill** : Kill si t_stat<0 a n>=60, ou esp<-1$ a n>=40, ou MDD>80$. · **Prior** : Le carry funding a un mecanisme reel (28_carry_hold t 2.52) mais 23_carry stagne (t 1.08). Le percentile adaptatif par coin peut isoler les vrais extremes. Prior succes ~25%.
