# Brief Station — 2026-07-22 06:30 (Paris)

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
| 23_carry_funding | ORANGE | 158 | 0.6161 | 1.14 | 97.35 | 3.416 | 28.5 j |
| 24_funding_multivenues | ORANGE | 141 | -0.369 | -2.02 | -52.02 | -1.832 | 28.4 j |
| 25_convergence_basis | ROUGE | 829 | 0.4816 | 3.56 | 399.23 | 13.579 | 29.4 j |
| 27a_rev_premium | ORANGE | 30 | -0.2417 | -0.08 | -7.25 | -0.256 | 28.3 j |
| 27b_rev_move | ORANGE | 51 | 3.2165 | 1.54 | 164.04 | 5.88 | 27.9 j |
| 27c_mom_move | ORANGE | 51 | -3.3565 | -1.61 | -171.18 | -6.135 | 27.9 j |
| 27d_rev_move_stop | ORANGE | 62 | 0.0409 | 0.02 | 2.54 | 0.114 | 22.3 j |
| 27e_arbitre | ROUGE | 30 | -1.0046 | -0.4 | -30.14 | -1.629 | 18.5 j |
| 27f10_selecteur | ORANGE | 119 | 0.7688 | 0.83 | 91.49 | 5.228 | 17.5 j |
| 27f_selecteur | ORANGE | 30 | -3.492 | -1.38 | -104.76 | -5.986 | 17.5 j |
| 27g10_selecteur | GRIS | 20 | 0.9398 | 0.24 | 18.8 | 1.918 | 9.8 j |
| 28_carry_hold | ORANGE | 63 | 4.2221 | 3.12 | 265.99 | 14.378 | 18.5 j |
| rd_h1 | ROUGE | 47 | 0.2249 | 1.27 | 10.57 | 5.284 | 2.0 j |

**P&L paper cumule (hors temoin)** : +684.66 $

**BTC** 66323 $ — ret 1j -0.31% · 7j +2.45% · 30j +3.61%
**Moves 24h ≥ 20 %** : CASHCAT -23.2%
**Calibration arbitre (J+7)** : {"tendance": {"n": 10, "taux_correct": 0.7, "brier_moyen": 0.22}}
**Autofinancement** : couts API 16.01 $ (releve 2026-07-21) · revenus reels 0 EUR / cible 35.0 EUR (reste 35.0 EUR)

_Genere automatiquement (PC eteint). Rien ici n'est un ordre : la gate decide,
le Commandant tranche. Zero argent reel._
