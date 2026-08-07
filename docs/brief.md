# Brief Station — 2026-08-07 07:01 (Paris)

## 🔴 ALERTES
- 25_convergence_basis: KILL exécuté (2026-08-05) : R4 (05/08/2026) : PERDANT SIGNIFICATIF, t = -3,32 sur n = 542, esperance -0,2178, P&L -118,06 $. C'est le critere EXACT qui a servi a tuer le bot 24 le 29/07 (t = -3,21 sur n = 168) -- applique ici a un echantillon 3x plus grand et a un t plus net. Progression sans ambiguite : t = -1,11 a n=343 le 02/08, t = -3,32 a n=542 le 05/08. La derive s'accentue avec l'echantillon, ce qui est la signature d'un vrai perdant et non du bruit. Kill decide par le Commandant le 05/08 apres constat.
- 27d_rev_move_stop: esp20 -8.18 < borne -7.37 -> COUPER LE BOT
- 27f10_selecteur: KILL exécuté (2026-08-05) : R1 décrochage : esp20 -4.78 < borne -4.61 -> COUPER LE BOT

## 🟠 Avertissements
- 27e_arbitre: REGLE 15/07 : Delta<0 vs 27b a n>=30 -- KILL RECOMMANDE (prior negatif confirme)

## Statuts gate (GO-reel)
| Bot | Statut | n | esp | t | P&L $ | P&L/j | fwd |
|---|---|---|---|---|---|---|---|
| 24_funding_multivenues | ROUGE | 171 | -0.5092 | -3.3 | -87.07 | -1.961 | 44.4 j |
| 25_convergence_basis | ROUGE | 546 | -0.2221 | -3.4 | -121.24 | -10.363 | 11.7 j |
| 27a_rev_premium | ORANGE | 57 | -2.8466 | -1.31 | -162.26 | -3.663 | 44.3 j |
| 27b_rev_move | ORANGE | 70 | 1.2829 | 0.64 | 89.8 | 2.041 | 44.0 j |
| 27c_mom_move | ORANGE | 70 | -1.4229 | -0.71 | -99.6 | -2.264 | 44.0 j |
| 27d_rev_move_stop | ROUGE | 104 | -1.1818 | -0.87 | -122.91 | -3.209 | 38.3 j |
| 27e_arbitre | ROUGE | 30 | -1.0046 | -0.4 | -30.14 | -0.871 | 34.6 j |
| 27f10_selecteur | ROUGE | 175 | -0.0665 | -0.09 | -11.64 | -0.347 | 33.5 j |
| 27f_selecteur | ORANGE | 49 | -0.2543 | -0.1 | -12.46 | -0.372 | 33.5 j |
| 27g10_selecteur | ROUGE | 41 | 0.3552 | 0.17 | 14.56 | 0.565 | 25.8 j |
| 28_carry_hold | GRIS | 21 | -3.085 | -0.65 | -64.78 | -5.683 | 11.4 j |
| 29_carry_neutre | GRIS | 6 | -4.1776 | -0.54 | -25.07 | -2.199 | 11.4 j |
| rd_h2 | ORANGE | 133 | -0.0081 | -0.02 | -1.08 | -0.093 | 11.6 j |

**P&L paper cumule (hors temoin)** : -633.89 $

**BTC** 64227 $ — ret 1j -0.10% · 7j +2.18% · 30j +3.12%
**Moves 24h ≥ 20 %** : ACE +87.7%, CASHCAT -21.9%
**Calibration arbitre (J+7)** : {"tendance": {"n": 20, "taux_correct": 0.45, "brier_moyen": 0.27}}
**Autofinancement** : couts API 18.73 $ (releve 2026-07-26) · revenus reels 0 EUR / cible 35.0 EUR (reste 35.0 EUR)

_Genere automatiquement (PC eteint). Rien ici n'est un ordre : la gate decide,
le Commandant tranche. Zero argent reel._
