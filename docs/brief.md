# Brief Station — 2026-08-08 13:30 (Paris)

## 🔴 ALERTES
- 25_convergence_basis: KILL exécuté (2026-08-05) : R4 (05/08/2026) : PERDANT SIGNIFICATIF, t = -3,32 sur n = 542, esperance -0,2178, P&L -118,06 $. C'est le critere EXACT qui a servi a tuer le bot 24 le 29/07 (t = -3,21 sur n = 168) -- applique ici a un echantillon 3x plus grand et a un t plus net. Progression sans ambiguite : t = -1,11 a n=343 le 02/08, t = -3,32 a n=542 le 05/08. La derive s'accentue avec l'echantillon, ce qui est la signature d'un vrai perdant et non du bruit. Kill decide par le Commandant le 05/08 apres constat.
- 27f10_selecteur: KILL exécuté (2026-08-05) : R1 décrochage : esp20 -4.78 < borne -4.61 -> COUPER LE BOT

## 🟠 Avertissements
- 27e_arbitre: REGLE 15/07 : Delta<0 vs 27b a n>=30 -- KILL RECOMMANDE (prior negatif confirme)
- 28_carry_hold: esp20 0.07 sous la borne 0.66 mais > 0 -- surveiller

## Statuts gate (GO-reel)
| Bot | Statut | n | esp | t | P&L $ | P&L/j | fwd |
|---|---|---|---|---|---|---|---|
| 24_funding_multivenues | ROUGE | 171 | -0.5092 | -3.3 | -87.07 | -1.905 | 45.7 j |
| 25_convergence_basis | ROUGE | 546 | -0.2221 | -3.4 | -121.24 | -9.327 | 13.0 j |
| 27a_rev_premium | ORANGE | 61 | -1.9255 | -0.89 | -117.45 | -2.576 | 45.6 j |
| 27b_rev_move | ORANGE | 75 | 1.0234 | 0.52 | 76.75 | 1.698 | 45.2 j |
| 27c_mom_move | ORANGE | 75 | -1.1634 | -0.59 | -87.25 | -1.93 | 45.2 j |
| 27d_rev_move_stop | ORANGE | 112 | -0.7577 | -0.57 | -84.86 | -2.143 | 39.6 j |
| 27e_arbitre | ROUGE | 30 | -1.0046 | -0.4 | -30.14 | -0.842 | 35.8 j |
| 27f10_selecteur | ROUGE | 175 | -0.0665 | -0.09 | -11.64 | -0.334 | 34.8 j |
| 27f_selecteur | ORANGE | 54 | -0.3449 | -0.15 | -18.62 | -0.535 | 34.8 j |
| 27g10_selecteur | ROUGE | 41 | 0.3552 | 0.17 | 14.56 | 0.537 | 27.1 j |
| 28_carry_hold | GRIS | 25 | 0.2479 | 0.05 | 6.2 | 0.492 | 12.6 j |
| 29_carry_neutre | GRIS | 6 | -4.1776 | -0.54 | -25.07 | -1.989 | 12.6 j |
| rd_h2 | ORANGE | 133 | -0.0081 | -0.02 | -1.08 | -0.084 | 12.9 j |

**P&L paper cumule (hors temoin)** : -486.91 $

**BTC** 64941 $ — ret 1j +0.09% · 7j +3.43% · 30j +2.71%
**Moves 24h ≥ 20 %** : ACE -21.0%
**Calibration arbitre (J+7)** : {"tendance": {"n": 20, "taux_correct": 0.45, "brier_moyen": 0.27}}
**Autofinancement** : couts API 18.73 $ (releve 2026-07-26) · revenus reels 0 EUR / cible 35.0 EUR (reste 35.0 EUR)

_Genere automatiquement (PC eteint). Rien ici n'est un ordre : la gate decide,
le Commandant tranche. Zero argent reel._
