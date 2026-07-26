# Bibliothèque — règles PROUVÉES (maj 2026-07-26)

## Statistique / lecture du banc
- [02-26/07] t qui MONTE avec n croissant = crédibilité réelle. Preuve : 25_conv t 2.39→3.72 sur n 262→1068, E stable ~0.45 ; 28_carry t 2.86→3.70 sur n 58→82.
- [02-19/07] t extrême sur n<30 = piège systématique (27a-d : t ±2.5 à n=4-20, tous retombés ou miroirs).
- [12-22/07] E élevée + t<2 stagnant avec n croissant = E gonflée par outliers → finit en kill. Preuve : 23_carry E~1.0, t plafonné 1.0-1.8 sur n 98-159, décrochage R1 le 22/07.
- [15/07] E >> mu_ref exige AUDIT vs données réelles avant crédit. Preuve : 28_carry E=4.2 vs ref 1.26, vérifié funding HL (5/5 cohérents, top3=63% du P&L).
- [21-26/07] Dégradation monotone de t sur 4+ relevés = structurelle, pas du bruit. Preuve : 24_funding t -1.48→-2.97 (n 127→162).

## Pièges vérifiés
- [09-26/07] Miroirs 27b/27c : somme PnL -6/-8 systématique à chaque n (36→58) pour ±190 de brut. DÉFINITIF : jamais lire un seul côté.
- [21/07] Méta-bot ne bat pas son sous-jacent : 27e delta -3.88 vs 27b à n>=30 → kill R3. Prior négatif confirmé.
- [22-26/07] KILL exécuté laisse des stats ROUGES résiduelles (23, 27e) : vérifier absence dans dernieres_actions avant re-signalement.
- [12/07] MDD 217 sous statut ORANGE : le statut n'exonère pas un perdant significatif.

## Contrôles
- [02-26/07] Témoin10 : t=-0.81 (n=1104), sain ; hors plage [0.37;0.84] depuis 19/07 sans rupture → plage historique trop étroite, seuil d'alerte t<-1 pertinent.
- [26/07] Calibration Arbitre n=13 : toujours n<20, aucune règle prouvable sur sa valeur prédictive.
- [18-25/07] Testnet : rejets 'no match' = friction structurelle stable (77.6% des rejets ; fill 89%), pas une panne.