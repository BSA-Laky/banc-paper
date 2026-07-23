# Brief Station — 2026-07-23 02:01 (Paris)

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
| 23_carry_funding | ROUGE | 159 | 0.5601 | 1.04 | 89.05 | 3.039 | 29.3 j |
| 24_funding_multivenues | ORANGE | 145 | -0.3868 | -2.18 | -56.08 | -1.921 | 29.2 j |
| 25_convergence_basis | ROUGE | 829 | 0.4816 | 3.56 | 399.23 | 13.219 | 30.2 j |
| 27a_rev_premium | ORANGE | 33 | -0.5878 | -0.21 | -19.4 | -0.667 | 29.1 j |
| 27b_rev_move | ORANGE | 53 | 3.4971 | 1.69 | 185.35 | 6.436 | 28.8 j |
| 27c_mom_move | ORANGE | 53 | -3.6371 | -1.76 | -192.77 | -6.693 | 28.8 j |
| 27d_rev_move_stop | ORANGE | 66 | 0.2114 | 0.12 | 13.95 | 0.604 | 23.1 j |
| 27e_arbitre | ROUGE | 30 | -1.0046 | -0.4 | -30.14 | -1.554 | 19.4 j |
| 27f10_selecteur | ORANGE | 126 | 0.8232 | 0.92 | 103.72 | 5.668 | 18.3 j |
| 27f_selecteur | ORANGE | 32 | -2.7615 | -1.1 | -88.37 | -4.829 | 18.3 j |
| 27g10_selecteur | GRIS | 22 | 1.0811 | 0.3 | 23.78 | 2.244 | 10.6 j |
| 28_carry_hold | ORANGE | 70 | 4.0604 | 3.31 | 284.23 | 14.651 | 19.4 j |
| rd_h1 | ROUGE | 47 | 0.2249 | 1.27 | 10.57 | 3.774 | 2.8 j |

**P&L paper cumule (hors temoin)** : +723.12 $

**BTC** 66078 $ — ret 1j -0.01% · 7j +3.55% · 30j +5.38%
**Moves 24h ≥ 20 %** : CASHCAT -23.0%
**Calibration arbitre (J+7)** : {"tendance": {"n": 10, "taux_correct": 0.7, "brier_moyen": 0.22}}
**Autofinancement** : couts API 16.01 $ (releve 2026-07-21) · revenus reels 0 EUR / cible 35.0 EUR (reste 35.0 EUR)

_Genere automatiquement (PC eteint). Rien ici n'est un ordre : la gate decide,
le Commandant tranche. Zero argent reel._
