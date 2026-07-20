# Brief Station — 2026-07-20 23:45 (Paris)

## 🔴 ALERTES
- 25_convergence_basis: KILL exécuté (2026-07-20) : R2 échéance A/B : ne bat pas 23 à capital égal (delta 0.137 pt/j, t 1.96)
- 25_convergence_basis: ne bat pas 23_carry_funding a capital egal (delta rendement/j 0.138 pt, t 1.97)
- rd_h1: esp20 -0.41 < borne -0.32 -> COUPER LE BOT

## Statuts gate (GO-reel)
| Bot | Statut | n | esp | t | P&L $ | P&L/j | fwd |
|---|---|---|---|---|---|---|---|
| 23_carry_funding | ORANGE | 150 | 0.7179 | 1.29 | 107.69 | 3.959 | 27.2 j |
| 24_funding_multivenues | ORANGE | 136 | -0.3344 | -1.77 | -45.48 | -1.678 | 27.1 j |
| 25_convergence_basis | ROUGE | 829 | 0.4816 | 3.56 | 399.23 | 14.207 | 28.1 j |
| 27a_rev_premium | GRIS | 27 | 0.451 | 0.15 | 12.18 | 0.451 | 27.0 j |
| 27b_rev_move | ORANGE | 45 | 3.2132 | 1.41 | 144.6 | 5.416 | 26.7 j |
| 27c_mom_move | ORANGE | 45 | -3.3532 | -1.47 | -150.9 | -5.652 | 26.7 j |
| 27d_rev_move_stop | ORANGE | 56 | -0.827 | -0.42 | -46.31 | -2.205 | 21.0 j |
| 27e_arbitre | GRIS | 26 | -1.2954 | -0.47 | -33.68 | -1.947 | 17.3 j |
| 27f10_selecteur | ORANGE | 108 | 0.8615 | 0.88 | 93.04 | 5.743 | 16.2 j |
| 27f_selecteur | GRIS | 24 | -3.7769 | -1.31 | -90.65 | -5.595 | 16.2 j |
| 27g10_selecteur | GRIS | 16 | 0.1743 | 0.04 | 2.79 | 0.328 | 8.5 j |
| 28_carry_hold | ORANGE | 62 | 4.2165 | 3.07 | 261.42 | 15.111 | 17.3 j |
| rd_h1 | ROUGE | 47 | 0.2249 | 1.27 | 10.57 | 15.098 | 0.7 j |

**P&L paper cumule (hors temoin)** : +664.50 $

**BTC** 65336 $ — ret 1j +0.95% · 7j +4.82% · 30j +1.65%
**Moves 24h ≥ 20 %** : HEMI +64.7%, ACE +49.9%, MET +21.4%
**Calibration arbitre (J+7)** : {"tendance": {"n": 10, "taux_correct": 0.7, "brier_moyen": 0.22}}
**Autofinancement** : couts API 13.82 $ (releve 2026-07-18) · revenus reels 0 EUR / cible 35.0 EUR (reste 35.0 EUR)

_Genere automatiquement (PC eteint). Rien ici n'est un ordre : la gate decide,
le Commandant tranche. Zero argent reel._
