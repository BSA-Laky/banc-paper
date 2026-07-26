# Registre R&D — hypotheses & bots de Nova (Stratege)
_Nova code et met en service les bots paper en autonomie. Kill auto par la gate._

## h2 — Convergence basis intraday : mark vs proxy funding-implied  `[actif]`
_Declencheur : 23_carry_funding (ROUGE/decrochage) — 2026-07-26_
- **Mecanisme** : Le mark spot/perp d'un coin devie d'un niveau d'equilibre implicite quand le funding horaire est fortement signe : un funding tres positif signale des longs surpayes qui tendent a corriger a la baisse (et inverse). On parie sur le retour du prix vers sa moyenne courte quand funding ET ret24h pointent dans le meme sens extreme (surextension). Seuil d'extension = percentile roulant maintenu dans etat, pas fixe.
- **Entree** : Entree SHORT si funding > P80 roulant de funding_positif ET ret24h>0 (longs surpayes + prix deja monte). Entree LONG si funding < P20 roulant ET ret24h<0. Un seul coin par passe (le plus extreme). · **Sortie** : Sortie quand ret24h revient sous la mediane roulante (retour vers moyenne) OU apres 8h (32 passes) time-stop.
- **Seuils** : P20/P80 percentiles roulants sur fenetre glissante de |funding| et funding signe (min 40 obs). Time-stop 8h. Mise 100$. · **Frais** : 2*0.00035*100=0.07$ par trade round-trip, integres au pnl.
- **Kill** : kill si esp_glissante_20 < borne_decrochage, ou t_stat<0.5 a n>=80, ou MDD>40$. · **Prior** : Faible : le carry funding est deja mort (23 ROUGE) et 24 multivenues negatif. La reversion sur surextension funding est plausible mais souvent arbitree ; ~20% de survie.

## h1 — Carry funding module par percentile roulant d'|funding|  `[kill (ROUGE/decrochage a la gate)]`
_Declencheur : 27f_selecteur (SIMULATION galop d'essai (Commandant) : bot repute juge perdant) — 2026-07-17_
- **Mecanisme** : Le funding perpetuel remunere le cote qui prend le risque du desequilibre OI. Quand |funding| est dans le haut de sa propre distribution roulante par coin, le taux tend a se maintenir quelques heures avant mean-reversion. On se positionne CONTRE le funding (short si funding>0) pour encaisser le flux, on ferme au retour vers la normale.
- **Entree** : Entrer contre le funding quand |funding| depasse le 80e percentile de sa distribution roulante propre au coin (fenetre glissante maintenue dans etat), et vol>0 pour liquidite. · **Sortie** : Sortir quand |funding| repasse sous sa mediane roulante, ou apres 12h de detention max.
- **Seuils** : Entree: p80 roulant |funding| par coin (min 40 obs). Sortie: p50 roulant. Hold max 12h. Size 100$. · **Frais** : 2*0.00035*100 = 0.07$/trade deduits du pnl funding accumule.
- **Kill** : Kill si t_stat<0 a n>=60, ou esp<-1$ a n>=40, ou MDD>80$. · **Prior** : Le carry funding a un mecanisme reel (28_carry_hold t 2.52) mais 23_carry stagne (t 1.08). Le percentile adaptatif par coin peut isoler les vrais extremes. Prior succes ~25%.
