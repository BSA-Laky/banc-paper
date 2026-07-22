# Brief Station — 2026-07-22 19:45 (Paris)

## 🔴 ALERTES
- 23_carry_funding: KILL exécuté (2026-07-22) : R1 décrochage : esp20 -2.60 < borne -2.48 -> COUPER LE BOT
- 23_carry_funding: esp20 -2.60 < borne -2.48 -> COUPER LE BOT
- 25_convergence_basis: KILL exécuté (2026-07-20) : R2 échéance A/B : ne bat pas 23 à capital égal (delta 0.137 pt/j, t 1.96)
- 27e_arbitre: KILL exécuté (2026-07-21) : R3 règle 15/07 : delta -3.88 $ < 0 vs 27b à n>=30
- 27e_arbitre: forward 19 j < 28 j
- 27e_arbitre: n 30 < n_go 50
- 27e_arbitre: t < 2
- rd_h1: esp20 -0.41 < borne -0.32 -> COUPER LE BOT

## 🟠 Avertissements
- 27e_arbitre: REGLE 15/07 : Delta<0 vs 27b a n>=30 -- KILL RECOMMANDE (prior negatif confirme)

## Statuts gate (GO-reel)
| Bot | Statut | n | esp | t | P&L $ | P&L/j | fwd |
|---|---|---|---|---|---|---|---|
| 23_carry_funding | ROUGE | 159 | 0.5601 | 1.04 | 89.05 | 3.071 | 29.0 j |
| 24_funding_multivenues | ORANGE | 141 | -0.369 | -2.02 | -52.02 | -1.794 | 29.0 j |
| 25_convergence_basis | ROUGE | 829 | 0.4816 | 3.56 | 399.23 | 13.352 | 29.9 j |
| 27a_rev_premium | ORANGE | 33 | -0.5878 | -0.21 | -19.4 | -0.671 | 28.9 j |
| 27b_rev_move | ORANGE | 52 | 3.6829 | 1.75 | 191.51 | 6.72 | 28.5 j |
| 27c_mom_move | ORANGE | 52 | -3.8229 | -1.82 | -198.79 | -6.975 | 28.5 j |
| 27d_rev_move_stop | ORANGE | 64 | 0.3388 | 0.18 | 21.68 | 0.947 | 22.9 j |
| 27e_arbitre | ROUGE | 30 | -1.0046 | -0.4 | -30.14 | -1.578 | 19.1 j |
| 27f10_selecteur | ORANGE | 123 | 0.7143 | 0.79 | 87.85 | 4.881 | 18.0 j |
| 27f_selecteur | ORANGE | 31 | -2.6516 | -1.03 | -82.2 | -4.567 | 18.0 j |
| 27g10_selecteur | GRIS | 22 | 1.0811 | 0.3 | 23.78 | 2.309 | 10.3 j |
| 28_carry_hold | ORANGE | 67 | 4.1765 | 3.27 | 279.82 | 14.65 | 19.1 j |
| rd_h1 | ROUGE | 47 | 0.2249 | 1.27 | 10.57 | 4.227 | 2.5 j |

**P&L paper cumule (hors temoin)** : +720.94 $

**BTC** 66131 $ — ret 1j -0.60% · 7j +2.15% · 30j +3.31%
**Calibration arbitre (J+7)** : {"tendance": {"n": 10, "taux_correct": 0.7, "brier_moyen": 0.22}}
**Autofinancement** : couts API 16.01 $ (releve 2026-07-21) · revenus reels 0 EUR / cible 35.0 EUR (reste 35.0 EUR)

_Genere automatiquement (PC eteint). Rien ici n'est un ordre : la gate decide,
le Commandant tranche. Zero argent reel._
