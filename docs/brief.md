# Brief Station — 2026-08-07 12:01 (Paris)

## 🔴 ALERTES
- 25_convergence_basis: KILL exécuté (2026-08-05) : R4 (05/08/2026) : PERDANT SIGNIFICATIF, t = -3,32 sur n = 542, esperance -0,2178, P&L -118,06 $. C'est le critere EXACT qui a servi a tuer le bot 24 le 29/07 (t = -3,21 sur n = 168) -- applique ici a un echantillon 3x plus grand et a un t plus net. Progression sans ambiguite : t = -1,11 a n=343 le 02/08, t = -3,32 a n=542 le 05/08. La derive s'accentue avec l'echantillon, ce qui est la signature d'un vrai perdant et non du bruit. Kill decide par le Commandant le 05/08 apres constat.
- 27f10_selecteur: KILL exécuté (2026-08-05) : R1 décrochage : esp20 -4.78 < borne -4.61 -> COUPER LE BOT

## 🟠 Avertissements
- 27e_arbitre: REGLE 15/07 : Delta<0 vs 27b a n>=30 -- KILL RECOMMANDE (prior negatif confirme)

## Statuts gate (GO-reel)
| Bot | Statut | n | esp | t | P&L $ | P&L/j | fwd |
|---|---|---|---|---|---|---|---|
| 24_funding_multivenues | ROUGE | 171 | -0.5092 | -3.3 | -87.07 | -1.952 | 44.6 j |
| 25_convergence_basis | ROUGE | 546 | -0.2221 | -3.4 | -121.24 | -10.189 | 11.9 j |
| 27a_rev_premium | ORANGE | 58 | -2.485 | -1.15 | -144.13 | -3.239 | 44.5 j |
| 27b_rev_move | ORANGE | 71 | 1.2269 | 0.62 | 87.11 | 1.971 | 44.2 j |
| 27c_mom_move | ORANGE | 71 | -1.3669 | -0.69 | -97.05 | -2.196 | 44.2 j |
| 27d_rev_move_stop | ORANGE | 106 | -1.2607 | -0.95 | -133.63 | -3.471 | 38.5 j |
| 27e_arbitre | ROUGE | 30 | -1.0046 | -0.4 | -30.14 | -0.866 | 34.8 j |
| 27f10_selecteur | ROUGE | 175 | -0.0665 | -0.09 | -11.64 | -0.345 | 33.7 j |
| 27f_selecteur | ORANGE | 50 | -0.3032 | -0.13 | -15.16 | -0.45 | 33.7 j |
| 27g10_selecteur | ROUGE | 41 | 0.3552 | 0.17 | 14.56 | 0.56 | 26.0 j |
| 28_carry_hold | GRIS | 23 | 0.4962 | 0.08 | 11.41 | 0.984 | 11.6 j |
| 29_carry_neutre | GRIS | 6 | -4.1776 | -0.54 | -25.07 | -2.161 | 11.6 j |
| rd_h2 | ORANGE | 133 | -0.0081 | -0.02 | -1.08 | -0.092 | 11.8 j |

**P&L paper cumule (hors temoin)** : -553.13 $

**BTC** 64793 $ — ret 1j +0.78% · 7j +3.08% · 30j +4.03%
**Moves 24h ≥ 20 %** : ACE +81.8%, CASHCAT -22.2%
**Calibration arbitre (J+7)** : {"tendance": {"n": 20, "taux_correct": 0.45, "brier_moyen": 0.27}}
**Autofinancement** : couts API 18.73 $ (releve 2026-07-26) · revenus reels 0 EUR / cible 35.0 EUR (reste 35.0 EUR)

_Genere automatiquement (PC eteint). Rien ici n'est un ordre : la gate decide,
le Commandant tranche. Zero argent reel._
