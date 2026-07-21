# Brief Station — 2026-07-21 17:45 (Paris)

## 🔴 ALERTES
- 25_convergence_basis: KILL exécuté (2026-07-20) : R2 échéance A/B : ne bat pas 23 à capital égal (delta 0.137 pt/j, t 1.96)
- 27e_arbitre: VERDICT PRÉ-ENREGISTRÉ -> KILL : R3 règle 15/07 : delta -3.88 $ < 0 vs 27b à n>=30
- 27e_arbitre: forward 18 j < 28 j
- 27e_arbitre: n 30 < n_go 50
- 27e_arbitre: t < 2
- rd_h1: esp20 -0.41 < borne -0.32 -> COUPER LE BOT

## 🟠 Avertissements
- 27e_arbitre: REGLE 15/07 : Delta<0 vs 27b a n>=30 -- KILL RECOMMANDE (prior negatif confirme)

## Changements de statut depuis hier
- 27b_rev_move : ROUGE → **ORANGE**
- 27e_arbitre : GRIS → **ROUGE**

## Statuts gate (GO-reel)
| Bot | Statut | n | esp | t | P&L $ | P&L/j | fwd |
|---|---|---|---|---|---|---|---|
| 23_carry_funding | ORANGE | 154 | 0.6715 | 1.21 | 103.42 | 3.693 | 28.0 j |
| 24_funding_multivenues | ORANGE | 136 | -0.3344 | -1.77 | -45.48 | -1.63 | 27.9 j |
| 25_convergence_basis | ROUGE | 829 | 0.4816 | 3.56 | 399.23 | 13.814 | 28.9 j |
| 27a_rev_premium | GRIS | 29 | 0.3826 | 0.13 | 11.1 | 0.399 | 27.8 j |
| 27b_rev_move | ORANGE | 49 | 2.8795 | 1.34 | 141.1 | 5.15 | 27.4 j |
| 27c_mom_move | ORANGE | 49 | -3.0195 | -1.4 | -147.96 | -5.4 | 27.4 j |
| 27d_rev_move_stop | ORANGE | 58 | -0.2459 | -0.13 | -14.26 | -0.654 | 21.8 j |
| 27e_arbitre | ROUGE | 30 | -1.0046 | -0.4 | -30.14 | -1.674 | 18.0 j |
| 27f10_selecteur | ORANGE | 112 | 0.9433 | 0.98 | 105.65 | 6.215 | 17.0 j |
| 27f_selecteur | GRIS | 28 | -2.9111 | -1.1 | -81.51 | -4.795 | 17.0 j |
| 27g10_selecteur | GRIS | 17 | 0.1524 | 0.03 | 2.59 | 0.282 | 9.2 j |
| 28_carry_hold | ORANGE | 62 | 4.2165 | 3.07 | 261.42 | 14.524 | 18.0 j |
| rd_h1 | ROUGE | 47 | 0.2249 | 1.27 | 10.57 | 7.046 | 1.5 j |

**P&L paper cumule (hors temoin)** : +715.73 $

**BTC** 66556 $ — ret 1j +2.04% · 7j +2.39% · 30j +5.19%
**Calibration arbitre (J+7)** : {"tendance": {"n": 10, "taux_correct": 0.7, "brier_moyen": 0.22}}
**Autofinancement** : couts API 16.01 $ (releve 2026-07-21) · revenus reels 0 EUR / cible 35.0 EUR (reste 35.0 EUR)

_Genere automatiquement (PC eteint). Rien ici n'est un ordre : la gate decide,
le Commandant tranche. Zero argent reel._
