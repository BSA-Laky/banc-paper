# Brief Station — 2026-07-31 03:15 (Paris)

## 🔴 ALERTES
- 24_funding_multivenues: KILL exécuté (2026-07-29) : TRIPLE motif (29/07/2026) : (1) PERDANT SIGNIFICATIF, t = -3,21 sur n = 168 apres coupure comptable -- satisfait la regle R4 proposee (t <= -2 a n >= 100) ; (2) comptabilite FAUSSE, meme faute que le bot 28 : accrue += abs(taux_horaire) * notionnel * dt, funding en valeur absolue et AUCUN terme de prix ; (3) INEXECUTABLE : il mesure un carry Paradex et un spread HL<->Paradex alors que nous n'avons de compte que sur Hyperliquid. Ses appels ne recoivent meme pas de prix, le terme de prix est structurellement absent. Migrer sa comptabilite pour mesurer un trade impossible n'aurait aucun sens.

## 🟠 Avertissements
- 27e_arbitre: REGLE 15/07 : Delta<0 vs 27b a n>=30 -- KILL RECOMMANDE (prior negatif confirme)

## Statuts gate (GO-reel)
| Bot | Statut | n | esp | t | P&L $ | P&L/j | fwd |
|---|---|---|---|---|---|---|---|
| 24_funding_multivenues | ROUGE | 171 | -0.5092 | -3.3 | -87.07 | -2.334 | 37.3 j |
| 25_convergence_basis | ORANGE | 172 | -0.0616 | -0.48 | -10.59 | -2.353 | 4.5 j |
| 27a_rev_premium | ORANGE | 44 | -1.0937 | -0.47 | -48.12 | -1.294 | 37.2 j |
| 27b_rev_move | ORANGE | 64 | 2.7102 | 1.45 | 173.45 | 4.713 | 36.8 j |
| 27c_mom_move | ORANGE | 64 | -2.8502 | -1.52 | -182.41 | -4.957 | 36.8 j |
| 27d_rev_move_stop | ORANGE | 81 | 0.0877 | 0.06 | 7.1 | 0.228 | 31.2 j |
| 27e_arbitre | ROUGE | 30 | -1.0046 | -0.4 | -30.14 | -1.1 | 27.4 j |
| 27f10_selecteur | ORANGE | 153 | 0.5558 | 0.7 | 85.04 | 3.221 | 26.4 j |
| 27f_selecteur | ORANGE | 43 | -2.3574 | -1.06 | -101.37 | -3.84 | 26.4 j |
| 27g10_selecteur | ORANGE | 35 | 0.4755 | 0.19 | 16.64 | 0.895 | 18.6 j |
| 28_carry_hold | GRIS | 1 | 11.6387 | 0.0 | 11.64 | 2.771 | 4.2 j |
| rd_h2 | ORANGE | 56 | 0.3165 | 0.6 | 17.72 | 3.939 | 4.5 j |

**P&L paper cumule (hors temoin)** : -148.11 $

**BTC** 65132 $ — ret 1j +0.58% · 7j +1.57% · 30j +8.54%
**Calibration arbitre (J+7)** : {"tendance": {"n": 20, "taux_correct": 0.45, "brier_moyen": 0.27}}
**Autofinancement** : couts API 18.73 $ (releve 2026-07-26) · revenus reels 0 EUR / cible 35.0 EUR (reste 35.0 EUR)

_Genere automatiquement (PC eteint). Rien ici n'est un ordre : la gate decide,
le Commandant tranche. Zero argent reel._
