# Memoire Arbitre — MAJ 2026-07-24

## Verdicts dates
- 23_carry_funding : KILL exécuté 22/07. Résiduel esp20=0.56 (n=159) affiché 24/07 = stats glissantes post-kill, pas d'action nouvelle confirmée. Surveiller.
- 27e_arbitre : KILL exécuté 21/07. Résiduel pnl_j=-1.456 (n=30) 24/07, idem stats glissantes, clos sur activité.
- rd_h1 : ROUGE, KILL demandé 21/07 (esp20 -0.41<-0.32), NON EXECUTE au 24/07 (>72h), pnl_j=+2.578 encore positif -> ESCALADE RECIDIVE 3e jour consécutif. Anomalie systémique execution/gate à signaler.
- 27b/c miroirs : n=56/56, PnL +172.72/-180.56, somme -7.84. VERDICT DEFINITIF miroir confirmé (m1 clos, cohérent -6/-8 historique).
- 28_carry_hold : n=73(>60), t=3.42, E=4.0263, pnl_j=14.20. CREDIBLE, 5e confirmation consécutive (m2 clos sauf suivi).
- Témoin10 : n=902, t=-0.60 (gate sain=true). Stable, pas de rupture (<-1).
- 24_funding : ORANGE, t=-2.21 (n=146), biais négatif persistant, surveiller passage ROUGE.
- 25_conv : VERT, t=3.70 (n=919), référence banc solide, stable.
- 27a/f/g10 : n<30-35, ignorés (règle validée).

## Lecons
- t qui monte avec n croissant = crédible (25_conv, 28_carry confirmés répétitivement).
- Miroirs 27b/c : somme oscille -6/-8 systématiquement, jamais lire un seul côté.
- t extrême n<30 = piège, continuer ignorer 27a/f/g10.
- Alerte ROUGE non traitée >24h = escalade obligatoire ; rd_h1 en récidive 3j consécutifs = friction execution/gate majeure, à remonter fermement au Superviseur.
- KILL 'exécuté' peut laisser des stats glissantes résiduelles (23_carry, 27e) : ne pas confondre avec nouvelle activité, vérifier dernieres_actions.
- Calibration arbitre n=10, taux=0.7, brier=0.22 : n<20, prudence conf<=0.6 maintenue.

## A surveiller
- rd_h1 : vérifier si KILL enfin exécuté demain ; sinon signaler dysfonctionnement structurel du pipeline kill.
- 24_funding : t<-2 persistant, guetter passage ROUGE.
- 23_carry/27e : confirmer absence totale de nouvelle activité post-kill (pas dans dernieres_actions ce jour, bon signe).
- Biais décisions récentes : majorité MOM sur 15 dernières, sans preuve causale, à challenger.

## Divers
- Banc non suspect. Age avis=23.8h. Autofinancement : coût API 16.01$ (21/07), revenus réels 0€, reste 35€ (fictif/paper).