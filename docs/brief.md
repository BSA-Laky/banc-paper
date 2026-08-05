# Brief Station — 2026-08-05 23:00 (Paris)

## 🔴 ALERTES
- 25_convergence_basis: KILL exécuté (2026-08-05) : R4 (05/08/2026) : PERDANT SIGNIFICATIF, t = -3,32 sur n = 542, esperance -0,2178, P&L -118,06 $. C'est le critere EXACT qui a servi a tuer le bot 24 le 29/07 (t = -3,21 sur n = 168) -- applique ici a un echantillon 3x plus grand et a un t plus net. Progression sans ambiguite : t = -1,11 a n=343 le 02/08, t = -3,32 a n=542 le 05/08. La derive s'accentue avec l'echantillon, ce qui est la signature d'un vrai perdant et non du bruit. Kill decide par le Commandant le 05/08 apres constat.
- 27f10_selecteur: KILL exécuté (2026-08-05) : R1 décrochage : esp20 -4.78 < borne -4.61 -> COUPER LE BOT

## 🟠 Avertissements
- 27e_arbitre: REGLE 15/07 : Delta<0 vs 27b a n>=30 -- KILL RECOMMANDE (prior negatif confirme)

## Statuts gate (GO-reel)
| Bot | Statut | n | esp | t | P&L $ | P&L/j | fwd |
|---|---|---|---|---|---|---|---|
| 24_funding_multivenues | ROUGE | 171 | -0.5092 | -3.3 | -87.07 | -2.02 | 43.1 j |
| 25_convergence_basis | ROUGE | 546 | -0.2221 | -3.4 | -121.24 | -11.658 | 10.4 j |
| 27a_rev_premium | ORANGE | 53 | -2.27 | -1.0 | -120.31 | -2.798 | 43.0 j |
| 27b_rev_move | ORANGE | 68 | 1.754 | 0.89 | 119.27 | 2.8 | 42.6 j |
| 27c_mom_move | ORANGE | 68 | -1.894 | -0.96 | -128.79 | -3.023 | 42.6 j |
| 27d_rev_move_stop | ORANGE | 96 | -0.6255 | -0.45 | -60.05 | -1.623 | 37.0 j |
| 27e_arbitre | ROUGE | 30 | -1.0046 | -0.4 | -30.14 | -0.908 | 33.2 j |
| 27f10_selecteur | ROUGE | 175 | -0.0665 | -0.09 | -11.64 | -0.361 | 32.2 j |
| 27f_selecteur | ORANGE | 47 | -0.8845 | -0.37 | -41.57 | -1.291 | 32.2 j |
| 27g10_selecteur | ROUGE | 41 | 0.3552 | 0.17 | 14.56 | 0.597 | 24.4 j |
| 28_carry_hold | GRIS | 16 | -4.0572 | -0.65 | -64.92 | -6.492 | 10.0 j |
| 29_carry_neutre | GRIS | 6 | -4.1776 | -0.54 | -25.07 | -2.507 | 10.0 j |
| rd_h2 | ORANGE | 128 | 0.2053 | 0.69 | 26.28 | 2.552 | 10.3 j |

**P&L paper cumule (hors temoin)** : -530.69 $

**BTC** 64763 $ — ret 1j +1.08% · 7j +1.25% · 30j +1.11%
**Moves 24h ≥ 20 %** : CASHCAT +75.0%
**Calibration arbitre (J+7)** : {"tendance": {"n": 20, "taux_correct": 0.45, "brier_moyen": 0.27}}
**Autofinancement** : couts API 18.73 $ (releve 2026-07-26) · revenus reels 0 EUR / cible 35.0 EUR (reste 35.0 EUR)

_Genere automatiquement (PC eteint). Rien ici n'est un ordre : la gate decide,
le Commandant tranche. Zero argent reel._
