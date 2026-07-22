# Brief Station — 2026-07-22 02:30 (Paris)

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
| 23_carry_funding | ORANGE | 158 | 0.6161 | 1.14 | 97.35 | 3.44 | 28.3 j |
| 24_funding_multivenues | ORANGE | 141 | -0.369 | -2.02 | -52.02 | -1.845 | 28.2 j |
| 25_convergence_basis | ROUGE | 829 | 0.4816 | 3.56 | 399.23 | 13.672 | 29.2 j |
| 27a_rev_premium | ORANGE | 30 | -0.2417 | -0.08 | -7.25 | -0.258 | 28.1 j |
| 27b_rev_move | ORANGE | 51 | 3.2165 | 1.54 | 164.04 | 5.901 | 27.8 j |
| 27c_mom_move | ORANGE | 51 | -3.3565 | -1.61 | -171.18 | -6.158 | 27.8 j |
| 27d_rev_move_stop | ORANGE | 61 | 0.152 | 0.08 | 9.27 | 0.42 | 22.1 j |
| 27e_arbitre | ROUGE | 30 | -1.0046 | -0.4 | -30.14 | -1.638 | 18.4 j |
| 27f10_selecteur | ORANGE | 118 | 0.7876 | 0.84 | 92.93 | 5.372 | 17.3 j |
| 27f_selecteur | ORANGE | 30 | -3.492 | -1.38 | -104.76 | -6.056 | 17.3 j |
| 27g10_selecteur | GRIS | 19 | -0.0422 | -0.01 | -0.8 | -0.083 | 9.6 j |
| 28_carry_hold | ORANGE | 63 | 4.2221 | 3.12 | 265.99 | 14.456 | 18.4 j |
| rd_h1 | ROUGE | 47 | 0.2249 | 1.27 | 10.57 | 5.871 | 1.8 j |

**P&L paper cumule (hors temoin)** : +673.23 $

**BTC** 66620 $ — ret 1j +0.14% · 7j +2.91% · 30j +4.07%
**Moves 24h ≥ 20 %** : HEMI -26.2%, ACE -20.9%
**Calibration arbitre (J+7)** : {"tendance": {"n": 10, "taux_correct": 0.7, "brier_moyen": 0.22}}
**Autofinancement** : couts API 16.01 $ (releve 2026-07-21) · revenus reels 0 EUR / cible 35.0 EUR (reste 35.0 EUR)

_Genere automatiquement (PC eteint). Rien ici n'est un ordre : la gate decide,
le Commandant tranche. Zero argent reel._
