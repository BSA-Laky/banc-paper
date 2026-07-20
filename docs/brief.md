# Brief Station — 2026-07-20 20:45 (Paris)

## 🔴 ALERTES
- 25_convergence_basis: KILL exécuté (2026-07-20) : R2 échéance A/B : ne bat pas 23 à capital égal (delta 0.137 pt/j, t 1.96)
- 25_convergence_basis: ne bat pas 23_carry_funding a capital egal (delta rendement/j 0.137 pt, t 1.96)
- rd_h1: esp20 -0.41 < borne -0.32 -> COUPER LE BOT

## Statuts gate (GO-reel)
| Bot | Statut | n | esp | t | P&L $ | P&L/j | fwd |
|---|---|---|---|---|---|---|---|
| 23_carry_funding | ORANGE | 149 | 0.7316 | 1.31 | 109.01 | 4.022 | 27.1 j |
| 24_funding_multivenues | ORANGE | 136 | -0.3344 | -1.77 | -45.48 | -1.685 | 27.0 j |
| 25_convergence_basis | ROUGE | 829 | 0.4816 | 3.56 | 399.23 | 14.258 | 28.0 j |
| 27a_rev_premium | GRIS | 27 | 0.451 | 0.15 | 12.18 | 0.453 | 26.9 j |
| 27b_rev_move | ORANGE | 45 | 3.2132 | 1.41 | 144.6 | 5.456 | 26.5 j |
| 27c_mom_move | ORANGE | 45 | -3.3532 | -1.47 | -150.9 | -5.694 | 26.5 j |
| 27d_rev_move_stop | ORANGE | 54 | -0.4122 | -0.21 | -22.26 | -1.065 | 20.9 j |
| 27e_arbitre | GRIS | 26 | -1.2954 | -0.47 | -33.68 | -1.97 | 17.1 j |
| 27f10_selecteur | ORANGE | 106 | 0.7251 | 0.73 | 76.86 | 4.774 | 16.1 j |
| 27f_selecteur | GRIS | 24 | -3.7769 | -1.31 | -90.65 | -5.63 | 16.1 j |
| 27g10_selecteur | GRIS | 15 | -0.4505 | -0.09 | -6.76 | -0.805 | 8.4 j |
| 28_carry_hold | ORANGE | 62 | 4.2165 | 3.07 | 261.42 | 15.288 | 17.1 j |
| rd_h1 | ROUGE | 47 | 0.2249 | 1.27 | 10.57 | 17.614 | 0.6 j |

**P&L paper cumule (hors temoin)** : +664.14 $

**BTC** 65225 $ — ret 1j +0.78% · 7j +4.64% · 30j +1.48%
**Moves 24h ≥ 20 %** : ACE +77.9%, HEMI +26.6%
**Calibration arbitre (J+7)** : {"tendance": {"n": 10, "taux_correct": 0.7, "brier_moyen": 0.22}}
**Autofinancement** : couts API 13.82 $ (releve 2026-07-18) · revenus reels 0 EUR / cible 35.0 EUR (reste 35.0 EUR)

_Genere automatiquement (PC eteint). Rien ici n'est un ordre : la gate decide,
le Commandant tranche. Zero argent reel._
