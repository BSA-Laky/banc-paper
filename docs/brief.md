# Brief Station — 2026-07-23 08:15 (Paris)

## 🔴 ALERTES
- 23_carry_funding: KILL exécuté (2026-07-22) : R1 décrochage : esp20 -2.60 < borne -2.48 -> COUPER LE BOT
- 23_carry_funding: esp20 -2.60 < borne -2.48 -> COUPER LE BOT
- 25_convergence_basis: KILL exécuté (2026-07-20) : R2 échéance A/B : ne bat pas 23 à capital égal (delta 0.137 pt/j, t 1.96)
- 27e_arbitre: KILL exécuté (2026-07-21) : R3 règle 15/07 : delta -3.88 $ < 0 vs 27b à n>=30
- 27e_arbitre: forward 20 j < 28 j
- 27e_arbitre: n 30 < n_go 50
- 27e_arbitre: t < 2
- rd_h1: esp20 -0.41 < borne -0.32 -> COUPER LE BOT

## 🟠 Avertissements
- 27e_arbitre: REGLE 15/07 : Delta<0 vs 27b a n>=30 -- KILL RECOMMANDE (prior negatif confirme)

## Statuts gate (GO-reel)
| Bot | Statut | n | esp | t | P&L $ | P&L/j | fwd |
|---|---|---|---|---|---|---|---|
| 23_carry_funding | ROUGE | 159 | 0.5601 | 1.04 | 89.05 | 3.009 | 29.6 j |
| 24_funding_multivenues | ORANGE | 145 | -0.3868 | -2.18 | -56.08 | -1.901 | 29.5 j |
| 25_convergence_basis | ROUGE | 829 | 0.4816 | 3.56 | 399.23 | 13.089 | 30.5 j |
| 27a_rev_premium | ORANGE | 34 | 0.0885 | 0.03 | 3.01 | 0.102 | 29.4 j |
| 27b_rev_move | ORANGE | 55 | 2.8701 | 1.39 | 157.86 | 5.443 | 29.0 j |
| 27c_mom_move | ORANGE | 55 | -3.0101 | -1.46 | -165.56 | -5.709 | 29.0 j |
| 27d_rev_move_stop | ORANGE | 67 | 0.0463 | 0.03 | 3.1 | 0.133 | 23.4 j |
| 27e_arbitre | ROUGE | 30 | -1.0046 | -0.4 | -30.14 | -1.538 | 19.6 j |
| 27f10_selecteur | ORANGE | 127 | 0.8642 | 0.98 | 109.75 | 5.901 | 18.6 j |
| 27f_selecteur | ORANGE | 33 | -2.7169 | -1.12 | -89.66 | -4.82 | 18.6 j |
| 27g10_selecteur | GRIS | 25 | 0.4577 | 0.14 | 11.44 | 1.06 | 10.8 j |
| 28_carry_hold | ORANGE | 70 | 4.0604 | 3.31 | 284.23 | 14.501 | 19.6 j |
| rd_h1 | ROUGE | 47 | 0.2249 | 1.27 | 10.57 | 3.409 | 3.1 j |

**P&L paper cumule (hors temoin)** : +726.80 $

**BTC** 65643 $ — ret 1j -0.67% · 7j +2.86% · 30j +4.68%
**Moves 24h ≥ 20 %** : CASHCAT -31.1%
**Calibration arbitre (J+7)** : {"tendance": {"n": 10, "taux_correct": 0.7, "brier_moyen": 0.22}}
**Autofinancement** : couts API 16.01 $ (releve 2026-07-21) · revenus reels 0 EUR / cible 35.0 EUR (reste 35.0 EUR)

_Genere automatiquement (PC eteint). Rien ici n'est un ordre : la gate decide,
le Commandant tranche. Zero argent reel._
