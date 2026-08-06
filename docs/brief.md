# Brief Station — 2026-08-06 14:45 (Paris)

## 🔴 ALERTES
- 25_convergence_basis: KILL exécuté (2026-08-05) : R4 (05/08/2026) : PERDANT SIGNIFICATIF, t = -3,32 sur n = 542, esperance -0,2178, P&L -118,06 $. C'est le critere EXACT qui a servi a tuer le bot 24 le 29/07 (t = -3,21 sur n = 168) -- applique ici a un echantillon 3x plus grand et a un t plus net. Progression sans ambiguite : t = -1,11 a n=343 le 02/08, t = -3,32 a n=542 le 05/08. La derive s'accentue avec l'echantillon, ce qui est la signature d'un vrai perdant et non du bruit. Kill decide par le Commandant le 05/08 apres constat.
- 27f10_selecteur: KILL exécuté (2026-08-05) : R1 décrochage : esp20 -4.78 < borne -4.61 -> COUPER LE BOT

## 🟠 Avertissements
- 27e_arbitre: REGLE 15/07 : Delta<0 vs 27b a n>=30 -- KILL RECOMMANDE (prior negatif confirme)

## Statuts gate (GO-reel)
| Bot | Statut | n | esp | t | P&L $ | P&L/j | fwd |
|---|---|---|---|---|---|---|---|
| 24_funding_multivenues | ROUGE | 171 | -0.5092 | -3.3 | -87.07 | -1.988 | 43.8 j |
| 25_convergence_basis | ROUGE | 546 | -0.2221 | -3.4 | -121.24 | -11.022 | 11.0 j |
| 27a_rev_premium | ORANGE | 56 | -2.8459 | -1.29 | -159.37 | -3.647 | 43.7 j |
| 27b_rev_move | ORANGE | 70 | 1.2829 | 0.64 | 89.8 | 2.074 | 43.3 j |
| 27c_mom_move | ORANGE | 70 | -1.4229 | -0.71 | -99.6 | -2.3 | 43.3 j |
| 27d_rev_move_stop | ORANGE | 100 | -0.8239 | -0.59 | -82.39 | -2.185 | 37.7 j |
| 27e_arbitre | ROUGE | 30 | -1.0046 | -0.4 | -30.14 | -0.889 | 33.9 j |
| 27f10_selecteur | ROUGE | 175 | -0.0665 | -0.09 | -11.64 | -0.355 | 32.8 j |
| 27f_selecteur | ORANGE | 49 | -0.2543 | -0.1 | -12.46 | -0.38 | 32.8 j |
| 27g10_selecteur | ROUGE | 41 | 0.3552 | 0.17 | 14.56 | 0.58 | 25.1 j |
| 28_carry_hold | GRIS | 18 | -3.345 | -0.61 | -60.21 | -5.627 | 10.7 j |
| 29_carry_neutre | GRIS | 6 | -4.1776 | -0.54 | -25.07 | -2.343 | 10.7 j |
| rd_h2 | ORANGE | 133 | -0.0081 | -0.02 | -1.08 | -0.099 | 10.9 j |

**P&L paper cumule (hors temoin)** : -585.91 $

**BTC** 64503 $ — ret 1j -0.19% · 7j -0.39% · 30j +1.81%
**Moves 24h ≥ 20 %** : CASHCAT +81.6%
**Calibration arbitre (J+7)** : {"tendance": {"n": 20, "taux_correct": 0.45, "brier_moyen": 0.27}}
**Autofinancement** : couts API 18.73 $ (releve 2026-07-26) · revenus reels 0 EUR / cible 35.0 EUR (reste 35.0 EUR)

_Genere automatiquement (PC eteint). Rien ici n'est un ordre : la gate decide,
le Commandant tranche. Zero argent reel._
