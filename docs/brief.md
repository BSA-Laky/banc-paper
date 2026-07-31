# Brief Station — 2026-07-31 06:30 (Paris)

## 🔴 ALERTES
- 24_funding_multivenues: KILL exécuté (2026-07-29) : TRIPLE motif (29/07/2026) : (1) PERDANT SIGNIFICATIF, t = -3,21 sur n = 168 apres coupure comptable -- satisfait la regle R4 proposee (t <= -2 a n >= 100) ; (2) comptabilite FAUSSE, meme faute que le bot 28 : accrue += abs(taux_horaire) * notionnel * dt, funding en valeur absolue et AUCUN terme de prix ; (3) INEXECUTABLE : il mesure un carry Paradex et un spread HL<->Paradex alors que nous n'avons de compte que sur Hyperliquid. Ses appels ne recoivent meme pas de prix, le terme de prix est structurellement absent. Migrer sa comptabilite pour mesurer un trade impossible n'aurait aucun sens.

## 🟠 Avertissements
- 27e_arbitre: REGLE 15/07 : Delta<0 vs 27b a n>=30 -- KILL RECOMMANDE (prior negatif confirme)

## Statuts gate (GO-reel)
| Bot | Statut | n | esp | t | P&L $ | P&L/j | fwd |
|---|---|---|---|---|---|---|---|
| 24_funding_multivenues | ROUGE | 171 | -0.5092 | -3.3 | -87.07 | -2.328 | 37.4 j |
| 25_convergence_basis | ORANGE | 179 | -0.0331 | -0.26 | -5.92 | -1.259 | 4.7 j |
| 27a_rev_premium | ORANGE | 44 | -1.0937 | -0.47 | -48.12 | -1.29 | 37.3 j |
| 27b_rev_move | ORANGE | 64 | 2.7102 | 1.45 | 173.45 | 4.701 | 36.9 j |
| 27c_mom_move | ORANGE | 64 | -2.8502 | -1.52 | -182.41 | -4.943 | 36.9 j |
| 27d_rev_move_stop | ORANGE | 82 | 0.2176 | 0.14 | 17.84 | 0.57 | 31.3 j |
| 27e_arbitre | ROUGE | 30 | -1.0046 | -0.4 | -30.14 | -1.096 | 27.5 j |
| 27f10_selecteur | ORANGE | 153 | 0.5558 | 0.7 | 85.04 | 3.209 | 26.5 j |
| 27f_selecteur | ORANGE | 43 | -2.3574 | -1.06 | -101.37 | -3.825 | 26.5 j |
| 27g10_selecteur | ORANGE | 35 | 0.4755 | 0.19 | 16.64 | 0.885 | 18.8 j |
| 28_carry_hold | GRIS | 1 | 11.6387 | 0.0 | 11.64 | 2.707 | 4.3 j |
| rd_h2 | ORANGE | 56 | 0.3165 | 0.6 | 17.72 | 3.853 | 4.6 j |

**P&L paper cumule (hors temoin)** : -132.70 $

**BTC** 64325 $ — ret 1j -0.66% · 7j +0.32% · 30j +7.19%
**Calibration arbitre (J+7)** : {"tendance": {"n": 20, "taux_correct": 0.45, "brier_moyen": 0.27}}
**Autofinancement** : couts API 18.73 $ (releve 2026-07-26) · revenus reels 0 EUR / cible 35.0 EUR (reste 35.0 EUR)

_Genere automatiquement (PC eteint). Rien ici n'est un ordre : la gate decide,
le Commandant tranche. Zero argent reel._
