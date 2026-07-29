# Brief Station — 2026-07-29 22:30 (Paris)

## 🔴 ALERTES
- 24_funding_multivenues: KILL exécuté (2026-07-29) : TRIPLE motif (29/07/2026) : (1) PERDANT SIGNIFICATIF, t = -3,21 sur n = 168 apres coupure comptable -- satisfait la regle R4 proposee (t <= -2 a n >= 100) ; (2) comptabilite FAUSSE, meme faute que le bot 28 : accrue += abs(taux_horaire) * notionnel * dt, funding en valeur absolue et AUCUN terme de prix ; (3) INEXECUTABLE : il mesure un carry Paradex et un spread HL<->Paradex alors que nous n'avons de compte que sur Hyperliquid. Ses appels ne recoivent meme pas de prix, le terme de prix est structurellement absent. Migrer sa comptabilite pour mesurer un trade impossible n'aurait aucun sens.

## 🟠 Avertissements
- 27e_arbitre: REGLE 15/07 : Delta<0 vs 27b a n>=30 -- KILL RECOMMANDE (prior negatif confirme)

## Statuts gate (GO-reel)
| Bot | Statut | n | esp | t | P&L $ | P&L/j | fwd |
|---|---|---|---|---|---|---|---|
| 24_funding_multivenues | ROUGE | 171 | -0.5092 | -3.3 | -87.07 | -2.412 | 36.1 j |
| 25_convergence_basis | ORANGE | 61 | 0.2227 | 1.29 | 13.59 | 4.117 | 3.3 j |
| 27a_rev_premium | ORANGE | 43 | -0.776 | -0.33 | -33.37 | -0.927 | 36.0 j |
| 27b_rev_move | ORANGE | 62 | 2.415 | 1.26 | 149.73 | 4.206 | 35.6 j |
| 27c_mom_move | ORANGE | 62 | -2.555 | -1.33 | -158.41 | -4.45 | 35.6 j |
| 27d_rev_move_stop | ORANGE | 79 | -0.0233 | -0.01 | -1.84 | -0.061 | 30.0 j |
| 27e_arbitre | ROUGE | 30 | -1.0046 | -0.4 | -30.14 | -1.15 | 26.2 j |
| 27f10_selecteur | ORANGE | 147 | 0.5237 | 0.64 | 76.98 | 3.055 | 25.2 j |
| 27f_selecteur | ORANGE | 41 | -3.051 | -1.35 | -125.09 | -4.964 | 25.2 j |
| 27g10_selecteur | ORANGE | 31 | 0.2671 | 0.1 | 8.28 | 0.476 | 17.4 j |
| 28_carry_hold | GRIS | 1 | 11.6387 | 0.0 | 11.64 | 3.88 | 3.0 j |
| rd_h2 | ORANGE | 39 | 0.3183 | 0.43 | 12.41 | 3.761 | 3.3 j |

**P&L paper cumule (hors temoin)** : -163.29 $

**BTC** 63497 $ — ret 1j -0.64% · 7j -3.92% · 30j +5.43%
**Calibration arbitre (J+7)** : {"tendance": {"n": 20, "taux_correct": 0.45, "brier_moyen": 0.27}}
**Autofinancement** : couts API 18.73 $ (releve 2026-07-26) · revenus reels 0 EUR / cible 35.0 EUR (reste 35.0 EUR)

_Genere automatiquement (PC eteint). Rien ici n'est un ordre : la gate decide,
le Commandant tranche. Zero argent reel._
