# Brief Station — 2026-08-05 19:15 (Paris)

## 🔴 ALERTES
- **BANC SUSPECT** : un temoin a |t| >= 2 — ne rien conclure.
- 25_convergence_basis: KILL exécuté (2026-08-05) : R4 (05/08/2026) : PERDANT SIGNIFICATIF, t = -3,32 sur n = 542, esperance -0,2178, P&L -118,06 $. C'est le critere EXACT qui a servi a tuer le bot 24 le 29/07 (t = -3,21 sur n = 168) -- applique ici a un echantillon 3x plus grand et a un t plus net. Progression sans ambiguite : t = -1,11 a n=343 le 02/08, t = -3,32 a n=542 le 05/08. La derive s'accentue avec l'echantillon, ce qui est la signature d'un vrai perdant et non du bruit. Kill decide par le Commandant le 05/08 apres constat.
- 27f10_selecteur: VERDICT PRÉ-ENREGISTRÉ -> KILL : R1 décrochage : esp20 -4.78 < borne -4.61 -> COUPER LE BOT
- 27f10_selecteur: esp20 -4.78 < borne -4.61 -> COUPER LE BOT

## 🟠 Avertissements
- 27e_arbitre: REGLE 15/07 : Delta<0 vs 27b a n>=30 -- KILL RECOMMANDE (prior negatif confirme)

## Changements de statut depuis hier
- 27f10_selecteur : ORANGE → **ROUGE**

## Statuts gate (GO-reel)
| Bot | Statut | n | esp | t | P&L $ | P&L/j | fwd |
|---|---|---|---|---|---|---|---|
| 24_funding_multivenues | ROUGE | 171 | -0.5092 | -3.3 | -87.07 | -2.03 | 42.9 j |
| 25_convergence_basis | ROUGE | 546 | -0.2221 | -3.4 | -121.24 | -11.887 | 10.2 j |
| 27a_rev_premium | ORANGE | 53 | -2.27 | -1.0 | -120.31 | -2.811 | 42.8 j |
| 27b_rev_move | ORANGE | 68 | 1.754 | 0.89 | 119.27 | 2.806 | 42.5 j |
| 27c_mom_move | ORANGE | 68 | -1.894 | -0.96 | -128.79 | -3.03 | 42.5 j |
| 27d_rev_move_stop | ORANGE | 94 | -0.5055 | -0.35 | -47.51 | -1.291 | 36.8 j |
| 27e_arbitre | ROUGE | 30 | -1.0046 | -0.4 | -30.14 | -0.911 | 33.1 j |
| 27f10_selecteur | ROUGE | 175 | -0.0665 | -0.09 | -11.64 | -0.364 | 32.0 j |
| 27f_selecteur | ORANGE | 47 | -0.8845 | -0.37 | -41.57 | -1.299 | 32.0 j |
| 27g10_selecteur | ROUGE | 41 | 0.3552 | 0.17 | 14.56 | 0.599 | 24.3 j |
| 28_carry_hold | GRIS | 16 | -4.0572 | -0.65 | -64.92 | -6.557 | 9.9 j |
| 29_carry_neutre | GRIS | 6 | -4.1776 | -0.54 | -25.07 | -2.532 | 9.9 j |
| rd_h2 | ORANGE | 126 | 0.2148 | 0.71 | 27.06 | 2.679 | 10.1 j |

**P&L paper cumule (hors temoin)** : -517.37 $

**BTC** 64549 $ — ret 1j +0.75% · 7j +0.92% · 30j +0.77%
**Moves 24h ≥ 20 %** : CASHCAT +34.2%
**Calibration arbitre (J+7)** : {"tendance": {"n": 20, "taux_correct": 0.45, "brier_moyen": 0.27}}
**Autofinancement** : couts API 18.73 $ (releve 2026-07-26) · revenus reels 0 EUR / cible 35.0 EUR (reste 35.0 EUR)

_Genere automatiquement (PC eteint). Rien ici n'est un ordre : la gate decide,
le Commandant tranche. Zero argent reel._
