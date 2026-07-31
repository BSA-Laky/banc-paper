# Brief Station — 2026-07-31 23:15 (Paris)

## 🔴 ALERTES
- 24_funding_multivenues: KILL exécuté (2026-07-29) : TRIPLE motif (29/07/2026) : (1) PERDANT SIGNIFICATIF, t = -3,21 sur n = 168 apres coupure comptable -- satisfait la regle R4 proposee (t <= -2 a n >= 100) ; (2) comptabilite FAUSSE, meme faute que le bot 28 : accrue += abs(taux_horaire) * notionnel * dt, funding en valeur absolue et AUCUN terme de prix ; (3) INEXECUTABLE : il mesure un carry Paradex et un spread HL<->Paradex alors que nous n'avons de compte que sur Hyperliquid. Ses appels ne recoivent meme pas de prix, le terme de prix est structurellement absent. Migrer sa comptabilite pour mesurer un trade impossible n'aurait aucun sens.

## 🟠 Avertissements
- 27e_arbitre: REGLE 15/07 : Delta<0 vs 27b a n>=30 -- KILL RECOMMANDE (prior negatif confirme)

## Statuts gate (GO-reel)
| Bot | Statut | n | esp | t | P&L $ | P&L/j | fwd |
|---|---|---|---|---|---|---|---|
| 24_funding_multivenues | ROUGE | 171 | -0.5092 | -3.3 | -87.07 | -2.285 | 38.1 j |
| 25_convergence_basis | ORANGE | 246 | -0.0311 | -0.3 | -7.65 | -1.416 | 5.4 j |
| 27a_rev_premium | ORANGE | 44 | -1.0937 | -0.47 | -48.12 | -1.266 | 38.0 j |
| 27b_rev_move | ORANGE | 65 | 2.7143 | 1.47 | 176.43 | 4.692 | 37.6 j |
| 27c_mom_move | ORANGE | 65 | -2.8543 | -1.55 | -185.53 | -4.934 | 37.6 j |
| 27d_rev_move_stop | ORANGE | 83 | 0.2508 | 0.16 | 20.82 | 0.651 | 32.0 j |
| 27e_arbitre | ROUGE | 30 | -1.0046 | -0.4 | -30.14 | -1.069 | 28.2 j |
| 27f10_selecteur | ORANGE | 157 | 0.5791 | 0.75 | 90.92 | 3.343 | 27.2 j |
| 27f_selecteur | ORANGE | 44 | -2.2362 | -1.03 | -98.39 | -3.617 | 27.2 j |
| 27g10_selecteur | ORANGE | 39 | 0.5777 | 0.26 | 22.53 | 1.155 | 19.5 j |
| 28_carry_hold | GRIS | 3 | 1.9611 | 0.38 | 5.88 | 1.177 | 5.0 j |
| rd_h2 | ORANGE | 66 | 0.539 | 1.11 | 35.57 | 6.712 | 5.3 j |

**P&L paper cumule (hors temoin)** : -104.75 $

**BTC** 62985 $ — ret 1j -2.73% · 7j -1.77% · 30j +4.96%
**Calibration arbitre (J+7)** : {"tendance": {"n": 20, "taux_correct": 0.45, "brier_moyen": 0.27}}
**Autofinancement** : couts API 18.73 $ (releve 2026-07-26) · revenus reels 0 EUR / cible 35.0 EUR (reste 35.0 EUR)

_Genere automatiquement (PC eteint). Rien ici n'est un ordre : la gate decide,
le Commandant tranche. Zero argent reel._
