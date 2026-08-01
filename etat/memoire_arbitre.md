# Memoire Arbitre — MAJ 2026-08-01

## Verdicts dates
- 24_funding: KILL exécuté 29/07 confirmé, résiduel ROUGE n=171,t=-3,3,E=-0,509 (m1, clos).
- 28_carry_hold: n=3 (post-reset 30/07), t=0,38, E=1,96, GRIS. n insignifiant, pas de crédit avant n≥30 (m2).
- 27a_rev_premium: n=46→proche cible 50, t=-0,4, E=-0,90. Pas de confirmation t<-1,5 (m3).
- 27e_arbitre: n=30 (seuil R3 atteint), t=-0,4, E=-1,00, ROUGE résiduel dormant (absent dernieres_actions), pas de re-signalement (règle 22-26/07).
- 25_conv: dégradation confirmée: t 3,72(hist)→-0,13(n=192,31/07)→-0,42(n=276,01/08), E→-0,04. 3e point négatif consécutif, proche règle 'quatre relevés = structurel'.
- 27b/27c miroirs: pnl +176/-186 (n=65), somme -9 conforme pattern -6/-8 définitif.
- Témoin10: n=1460, t=-1,5 (gate sain=true) mais franchit seuil alerte t<-1 (règle 02-26/07) — surveiller.
- Calibration arbitre: n=20 (seuil atteint), taux=0,45≤0,5 → confiance≤0,5 appliquée strictement.

## Leçons
- t qui monte avec n croissant = crédible (25_conv/28_carry avant reset).
- Miroirs 27b/c définitif -6/-8.
- KILL exécuté laisse stats ROUGE résiduelles: vérifier absence dans dernieres_actions avant re-signaler (24, 27e).
- Reset brutal de n = correction comptable, pas corruption (28_carry 83→1→3).
- Calibration arbitre n=20 franchi: conf≤0,5 tant que taux_correct non redressé >0,5.
- Témoin10 sous seuil t<-1: rester attentif même si gate le dit sain.

## A surveiller
- 25_conv: 3e relevé négatif consécutif (t -0,13→-0,42), si 4e confirme = dégradation structurelle → KILL à envisager.
- 27a: n=46→50, cible mission m3.
- 28_carry: n=3→100, reprise post-reset.
- Calibration arbitre: si taux_correct>0,5 sur n≥20 futur, lever plafond conf.
- Témoin10: t=-1,5, sous seuil historique.

## Divers
- Banc non suspect. Autofinancement: coût API 18,73$ (relevé 26/07 stale), revenus réels 0€, reste 35€ (fictif). Équipage sain (0 échecs, avis 23,4h).