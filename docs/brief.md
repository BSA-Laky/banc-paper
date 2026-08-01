# Brief Station — 2026-08-01 08:45 (Paris)

## 🔴 ALERTES
- 24_funding_multivenues: KILL exécuté (2026-07-29) : TRIPLE motif (29/07/2026) : (1) PERDANT SIGNIFICATIF, t = -3,21 sur n = 168 apres coupure comptable -- satisfait la regle R4 proposee (t <= -2 a n >= 100) ; (2) comptabilite FAUSSE, meme faute que le bot 28 : accrue += abs(taux_horaire) * notionnel * dt, funding en valeur absolue et AUCUN terme de prix ; (3) INEXECUTABLE : il mesure un carry Paradex et un spread HL<->Paradex alors que nous n'avons de compte que sur Hyperliquid. Ses appels ne recoivent meme pas de prix, le terme de prix est structurellement absent. Migrer sa comptabilite pour mesurer un trade impossible n'aurait aucun sens.

## 🟠 Avertissements
- 27e_arbitre: REGLE 15/07 : Delta<0 vs 27b a n>=30 -- KILL RECOMMANDE (prior negatif confirme)

## Statuts gate (GO-reel)
| Bot | Statut | n | esp | t | P&L $ | P&L/j | fwd |
|---|---|---|---|---|---|---|---|
| 24_funding_multivenues | ROUGE | 171 | -0.5092 | -3.3 | -87.07 | -2.261 | 38.5 j |
| 25_convergence_basis | ORANGE | 272 | -0.037 | -0.38 | -10.07 | -1.736 | 5.8 j |
| 27a_rev_premium | ORANGE | 46 | -0.9001 | -0.4 | -41.41 | -1.078 | 38.4 j |
| 27b_rev_move | ORANGE | 65 | 2.7143 | 1.47 | 176.43 | 4.643 | 38.0 j |
| 27c_mom_move | ORANGE | 65 | -2.8543 | -1.55 | -185.53 | -4.882 | 38.0 j |
| 27d_rev_move_stop | ORANGE | 83 | 0.2508 | 0.16 | 20.82 | 0.643 | 32.4 j |
| 27e_arbitre | ROUGE | 30 | -1.0046 | -0.4 | -30.14 | -1.054 | 28.6 j |
| 27f10_selecteur | ORANGE | 159 | 0.534 | 0.69 | 84.9 | 3.076 | 27.6 j |
| 27f_selecteur | ORANGE | 44 | -2.2362 | -1.03 | -98.39 | -3.565 | 27.6 j |
| 27g10_selecteur | ORANGE | 39 | 0.5777 | 0.26 | 22.53 | 1.132 | 19.9 j |
| 28_carry_hold | GRIS | 3 | 1.9611 | 0.38 | 5.88 | 1.09 | 5.4 j |
| rd_h2 | ORANGE | 70 | 0.5579 | 1.22 | 39.05 | 6.851 | 5.7 j |

**P&L paper cumule (hors temoin)** : -103.00 $

**BTC** 63034 $ — ret 1j +0.28% · 7j -2.06% · 30j +2.35%
**Calibration arbitre (J+7)** : {"tendance": {"n": 20, "taux_correct": 0.45, "brier_moyen": 0.27}}
**Autofinancement** : couts API 18.73 $ (releve 2026-07-26) · revenus reels 0 EUR / cible 35.0 EUR (reste 35.0 EUR)

_Genere automatiquement (PC eteint). Rien ici n'est un ordre : la gate decide,
le Commandant tranche. Zero argent reel._
