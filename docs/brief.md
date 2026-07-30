# Brief Station — 2026-07-30 11:15 (Paris)

## 🔴 ALERTES
- 24_funding_multivenues: KILL exécuté (2026-07-29) : TRIPLE motif (29/07/2026) : (1) PERDANT SIGNIFICATIF, t = -3,21 sur n = 168 apres coupure comptable -- satisfait la regle R4 proposee (t <= -2 a n >= 100) ; (2) comptabilite FAUSSE, meme faute que le bot 28 : accrue += abs(taux_horaire) * notionnel * dt, funding en valeur absolue et AUCUN terme de prix ; (3) INEXECUTABLE : il mesure un carry Paradex et un spread HL<->Paradex alors que nous n'avons de compte que sur Hyperliquid. Ses appels ne recoivent meme pas de prix, le terme de prix est structurellement absent. Migrer sa comptabilite pour mesurer un trade impossible n'aurait aucun sens.

## 🟠 Avertissements
- 27e_arbitre: REGLE 15/07 : Delta<0 vs 27b a n>=30 -- KILL RECOMMANDE (prior negatif confirme)

## Statuts gate (GO-reel)
| Bot | Statut | n | esp | t | P&L $ | P&L/j | fwd |
|---|---|---|---|---|---|---|---|
| 24_funding_multivenues | ROUGE | 171 | -0.5092 | -3.3 | -87.07 | -2.379 | 36.6 j |
| 25_convergence_basis | ORANGE | 111 | 0.0346 | 0.25 | 3.84 | 0.986 | 3.9 j |
| 27a_rev_premium | ORANGE | 43 | -0.776 | -0.33 | -33.37 | -0.914 | 36.5 j |
| 27b_rev_move | ORANGE | 62 | 2.415 | 1.26 | 149.73 | 4.148 | 36.1 j |
| 27c_mom_move | ORANGE | 62 | -2.555 | -1.33 | -158.41 | -4.388 | 36.1 j |
| 27d_rev_move_stop | ORANGE | 80 | -0.1302 | -0.08 | -10.41 | -0.341 | 30.5 j |
| 27e_arbitre | ROUGE | 30 | -1.0046 | -0.4 | -30.14 | -1.129 | 26.7 j |
| 27f10_selecteur | ORANGE | 149 | 0.523 | 0.64 | 77.92 | 3.032 | 25.7 j |
| 27f_selecteur | ORANGE | 41 | -3.051 | -1.35 | -125.09 | -4.867 | 25.7 j |
| 27g10_selecteur | ORANGE | 32 | 0.2468 | 0.09 | 7.9 | 0.439 | 18.0 j |
| 28_carry_hold | GRIS | 1 | 11.6387 | 0.0 | 11.64 | 3.325 | 3.5 j |
| rd_h2 | ORANGE | 48 | 0.2654 | 0.43 | 12.74 | 3.353 | 3.8 j |

**P&L paper cumule (hors temoin)** : -180.72 $

**BTC** 64362 $ — ret 1j +0.63% · 7j -1.09% · 30j +9.83%
**Moves 24h ≥ 20 %** : CASHCAT +21.1%
**Calibration arbitre (J+7)** : {"tendance": {"n": 20, "taux_correct": 0.45, "brier_moyen": 0.27}}
**Autofinancement** : couts API 18.73 $ (releve 2026-07-26) · revenus reels 0 EUR / cible 35.0 EUR (reste 35.0 EUR)

_Genere automatiquement (PC eteint). Rien ici n'est un ordre : la gate decide,
le Commandant tranche. Zero argent reel._
