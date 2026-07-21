# Brief Station — 2026-07-21 20:01 (Paris)

## 🔴 ALERTES
- 25_convergence_basis: KILL exécuté (2026-07-20) : R2 échéance A/B : ne bat pas 23 à capital égal (delta 0.137 pt/j, t 1.96)
- 27e_arbitre: KILL exécuté (2026-07-21) : R3 règle 15/07 : delta -3.88 $ < 0 vs 27b à n>=30
- 27e_arbitre: forward 18 j < 28 j
- 27e_arbitre: n 30 < n_go 50
- 27e_arbitre: t < 2
- rd_h1: esp20 -0.41 < borne -0.32 -> COUPER LE BOT

## 🟠 Avertissements
- 27e_arbitre: REGLE 15/07 : Delta<0 vs 27b a n>=30 -- KILL RECOMMANDE (prior negatif confirme)

## Statuts gate (GO-reel)
| Bot | Statut | n | esp | t | P&L $ | P&L/j | fwd |
|---|---|---|---|---|---|---|---|
| 23_carry_funding | ORANGE | 157 | 0.6282 | 1.16 | 98.63 | 3.51 | 28.1 j |
| 24_funding_multivenues | ORANGE | 141 | -0.369 | -2.02 | -52.02 | -1.858 | 28.0 j |
| 25_convergence_basis | ROUGE | 829 | 0.4816 | 3.56 | 399.23 | 13.814 | 28.9 j |
| 27a_rev_premium | GRIS | 29 | 0.3826 | 0.13 | 11.1 | 0.398 | 27.9 j |
| 27b_rev_move | ORANGE | 49 | 2.8795 | 1.34 | 141.1 | 5.131 | 27.5 j |
| 27c_mom_move | ORANGE | 49 | -3.0195 | -1.4 | -147.96 | -5.38 | 27.5 j |
| 27d_rev_move_stop | ORANGE | 58 | -0.2459 | -0.13 | -14.26 | -0.651 | 21.9 j |
| 27e_arbitre | ROUGE | 30 | -1.0046 | -0.4 | -30.14 | -1.665 | 18.1 j |
| 27f10_selecteur | ORANGE | 113 | 0.9097 | 0.95 | 102.79 | 6.011 | 17.1 j |
| 27f_selecteur | GRIS | 28 | -2.9111 | -1.1 | -81.51 | -4.767 | 17.1 j |
| 27g10_selecteur | GRIS | 18 | -0.0149 | -0.0 | -0.27 | -0.029 | 9.3 j |
| 28_carry_hold | ORANGE | 63 | 4.2221 | 3.12 | 265.99 | 14.696 | 18.1 j |
| rd_h1 | ROUGE | 47 | 0.2249 | 1.27 | 10.57 | 7.046 | 1.5 j |

**P&L paper cumule (hors temoin)** : +703.25 $

**BTC** 66159 $ — ret 1j +1.43% · 7j +1.78% · 30j +4.57%
**Moves 24h ≥ 20 %** : ACE -22.5%
**Calibration arbitre (J+7)** : {"tendance": {"n": 10, "taux_correct": 0.7, "brier_moyen": 0.22}}
**Autofinancement** : couts API 16.01 $ (releve 2026-07-21) · revenus reels 0 EUR / cible 35.0 EUR (reste 35.0 EUR)

_Genere automatiquement (PC eteint). Rien ici n'est un ordre : la gate decide,
le Commandant tranche. Zero argent reel._
