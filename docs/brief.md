# Brief Station — 2026-07-21 01:30 (Paris)

## 🔴 ALERTES
- 25_convergence_basis: KILL exécuté (2026-07-20) : R2 échéance A/B : ne bat pas 23 à capital égal (delta 0.137 pt/j, t 1.96)
- 25_convergence_basis: ne bat pas 23_carry_funding a capital egal (delta rendement/j 0.138 pt, t 1.97)
- rd_h1: esp20 -0.41 < borne -0.32 -> COUPER LE BOT

## Statuts gate (GO-reel)
| Bot | Statut | n | esp | t | P&L $ | P&L/j | fwd |
|---|---|---|---|---|---|---|---|
| 23_carry_funding | ORANGE | 150 | 0.7179 | 1.29 | 107.69 | 3.945 | 27.3 j |
| 24_funding_multivenues | ORANGE | 136 | -0.3344 | -1.77 | -45.48 | -1.672 | 27.2 j |
| 25_convergence_basis | ROUGE | 829 | 0.4816 | 3.56 | 399.23 | 14.157 | 28.2 j |
| 27a_rev_premium | GRIS | 28 | 1.1797 | 0.39 | 33.03 | 1.219 | 27.1 j |
| 27b_rev_move | ORANGE | 47 | 2.697 | 1.21 | 126.76 | 4.747 | 26.7 j |
| 27c_mom_move | ORANGE | 47 | -2.837 | -1.27 | -133.34 | -4.994 | 26.7 j |
| 27d_rev_move_stop | ORANGE | 56 | -0.827 | -0.42 | -46.31 | -2.195 | 21.1 j |
| 27e_arbitre | GRIS | 28 | -0.5605 | -0.21 | -15.69 | -0.907 | 17.3 j |
| 27f10_selecteur | ORANGE | 109 | 1.0449 | 1.06 | 113.9 | 6.988 | 16.3 j |
| 27f_selecteur | GRIS | 26 | -2.5795 | -0.91 | -67.07 | -4.114 | 16.3 j |
| 27g10_selecteur | GRIS | 16 | 0.1743 | 0.04 | 2.79 | 0.324 | 8.6 j |
| 28_carry_hold | ORANGE | 62 | 4.2165 | 3.07 | 261.42 | 15.111 | 17.3 j |
| rd_h1 | ROUGE | 47 | 0.2249 | 1.27 | 10.57 | 13.21 | 0.8 j |

**P&L paper cumule (hors temoin)** : +747.50 $

**BTC** 65212 $ — ret 1j +0.76% · 7j +4.62% · 30j +1.46%
**Moves 24h ≥ 20 %** : HEMI +56.2%, MET +21.1%, ACE +20.9%
**Calibration arbitre (J+7)** : {"tendance": {"n": 10, "taux_correct": 0.7, "brier_moyen": 0.22}}
**Autofinancement** : couts API 13.82 $ (releve 2026-07-18) · revenus reels 0 EUR / cible 35.0 EUR (reste 35.0 EUR)

_Genere automatiquement (PC eteint). Rien ici n'est un ordre : la gate decide,
le Commandant tranche. Zero argent reel._
