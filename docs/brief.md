# Brief Station — 2026-08-08 07:01 (Paris)

## 🔴 ALERTES
- 25_convergence_basis: KILL exécuté (2026-08-05) : R4 (05/08/2026) : PERDANT SIGNIFICATIF, t = -3,32 sur n = 542, esperance -0,2178, P&L -118,06 $. C'est le critere EXACT qui a servi a tuer le bot 24 le 29/07 (t = -3,21 sur n = 168) -- applique ici a un echantillon 3x plus grand et a un t plus net. Progression sans ambiguite : t = -1,11 a n=343 le 02/08, t = -3,32 a n=542 le 05/08. La derive s'accentue avec l'echantillon, ce qui est la signature d'un vrai perdant et non du bruit. Kill decide par le Commandant le 05/08 apres constat.
- 27f10_selecteur: KILL exécuté (2026-08-05) : R1 décrochage : esp20 -4.78 < borne -4.61 -> COUPER LE BOT

## 🟠 Avertissements
- 27e_arbitre: REGLE 15/07 : Delta<0 vs 27b a n>=30 -- KILL RECOMMANDE (prior negatif confirme)

## Statuts gate (GO-reel)
| Bot | Statut | n | esp | t | P&L $ | P&L/j | fwd |
|---|---|---|---|---|---|---|---|
| 24_funding_multivenues | ROUGE | 171 | -0.5092 | -3.3 | -87.07 | -1.918 | 45.4 j |
| 25_convergence_basis | ROUGE | 546 | -0.2221 | -3.4 | -121.24 | -9.547 | 12.7 j |
| 27a_rev_premium | ORANGE | 59 | -1.8125 | -0.81 | -106.94 | -2.361 | 45.3 j |
| 27b_rev_move | ORANGE | 73 | 0.9494 | 0.47 | 69.31 | 1.54 | 45.0 j |
| 27c_mom_move | ORANGE | 73 | -1.0894 | -0.54 | -79.53 | -1.767 | 45.0 j |
| 27d_rev_move_stop | ORANGE | 109 | -1.0415 | -0.78 | -113.52 | -2.889 | 39.3 j |
| 27e_arbitre | ROUGE | 30 | -1.0046 | -0.4 | -30.14 | -0.847 | 35.6 j |
| 27f10_selecteur | ROUGE | 175 | -0.0665 | -0.09 | -11.64 | -0.337 | 34.5 j |
| 27f_selecteur | ORANGE | 52 | 0.0454 | 0.02 | 2.36 | 0.068 | 34.5 j |
| 27g10_selecteur | ROUGE | 41 | 0.3552 | 0.17 | 14.56 | 0.543 | 26.8 j |
| 28_carry_hold | GRIS | 23 | 0.4962 | 0.08 | 11.41 | 0.92 | 12.4 j |
| 29_carry_neutre | GRIS | 6 | -4.1776 | -0.54 | -25.07 | -2.021 | 12.4 j |
| rd_h2 | ORANGE | 133 | -0.0081 | -0.02 | -1.08 | -0.086 | 12.6 j |

**P&L paper cumule (hors temoin)** : -478.59 $

**BTC** 64974 $ — ret 1j +0.14% · 7j +3.48% · 30j +2.77%
**Calibration arbitre (J+7)** : {"tendance": {"n": 20, "taux_correct": 0.45, "brier_moyen": 0.27}}
**Autofinancement** : couts API 18.73 $ (releve 2026-07-26) · revenus reels 0 EUR / cible 35.0 EUR (reste 35.0 EUR)

_Genere automatiquement (PC eteint). Rien ici n'est un ordre : la gate decide,
le Commandant tranche. Zero argent reel._
