# Brief Station — 2026-07-21 00:45 (Paris)

## 🔴 ALERTES
- 25_convergence_basis: KILL exécuté (2026-07-20) : R2 échéance A/B : ne bat pas 23 à capital égal (delta 0.137 pt/j, t 1.96)
- 25_convergence_basis: ne bat pas 23_carry_funding a capital egal (delta rendement/j 0.138 pt, t 1.97)
- rd_h1: esp20 -0.41 < borne -0.32 -> COUPER LE BOT

## Statuts gate (GO-reel)
| Bot | Statut | n | esp | t | P&L $ | P&L/j | fwd |
|---|---|---|---|---|---|---|---|
| 23_carry_funding | ORANGE | 150 | 0.7179 | 1.29 | 107.69 | 3.945 | 27.3 j |
| 24_funding_multivenues | ORANGE | 136 | -0.3344 | -1.77 | -45.48 | -1.672 | 27.2 j |
| 25_convergence_basis | ROUGE | 829 | 0.4816 | 3.56 | 399.23 | 14.207 | 28.1 j |
| 27a_rev_premium | GRIS | 27 | 0.451 | 0.15 | 12.18 | 0.449 | 27.1 j |
| 27b_rev_move | ORANGE | 46 | 3.212 | 1.44 | 147.75 | 5.534 | 26.7 j |
| 27c_mom_move | ORANGE | 46 | -3.352 | -1.51 | -154.19 | -5.775 | 26.7 j |
| 27d_rev_move_stop | ORANGE | 56 | -0.827 | -0.42 | -46.31 | -2.195 | 21.1 j |
| 27e_arbitre | GRIS | 27 | -1.3536 | -0.51 | -36.55 | -2.113 | 17.3 j |
| 27f10_selecteur | ORANGE | 108 | 0.8615 | 0.88 | 93.04 | 5.708 | 16.3 j |
| 27f_selecteur | GRIS | 25 | -3.5168 | -1.26 | -87.92 | -5.394 | 16.3 j |
| 27g10_selecteur | GRIS | 16 | 0.1743 | 0.04 | 2.79 | 0.328 | 8.5 j |
| 28_carry_hold | ORANGE | 62 | 4.2165 | 3.07 | 261.42 | 15.111 | 17.3 j |
| rd_h1 | ROUGE | 47 | 0.2249 | 1.27 | 10.57 | 15.098 | 0.7 j |

**P&L paper cumule (hors temoin)** : +664.22 $

**BTC** 65109 $ — ret 1j +0.60% · 7j +4.46% · 30j +1.30%
**Moves 24h ≥ 20 %** : HEMI +55.1%, ACE +28.6%, MET +21.3%
**Calibration arbitre (J+7)** : {"tendance": {"n": 10, "taux_correct": 0.7, "brier_moyen": 0.22}}
**Autofinancement** : couts API 13.82 $ (releve 2026-07-18) · revenus reels 0 EUR / cible 35.0 EUR (reste 35.0 EUR)

_Genere automatiquement (PC eteint). Rien ici n'est un ordre : la gate decide,
le Commandant tranche. Zero argent reel._
