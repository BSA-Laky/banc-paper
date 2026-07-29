# Brief Station — 2026-07-29 15:01 (Paris)

## 🔴 ALERTES
- 24_funding_multivenues: KILL exécuté (2026-07-29) : TRIPLE motif (29/07/2026) : (1) PERDANT SIGNIFICATIF, t = -3,21 sur n = 168 apres coupure comptable -- satisfait la regle R4 proposee (t <= -2 a n >= 100) ; (2) comptabilite FAUSSE, meme faute que le bot 28 : accrue += abs(taux_horaire) * notionnel * dt, funding en valeur absolue et AUCUN terme de prix ; (3) INEXECUTABLE : il mesure un carry Paradex et un spread HL<->Paradex alors que nous n'avons de compte que sur Hyperliquid. Ses appels ne recoivent meme pas de prix, le terme de prix est structurellement absent. Migrer sa comptabilite pour mesurer un trade impossible n'aurait aucun sens.

## 🟠 Avertissements
- 27e_arbitre: REGLE 15/07 : Delta<0 vs 27b a n>=30 -- KILL RECOMMANDE (prior negatif confirme)

## Statuts gate (GO-reel)
| Bot | Statut | n | esp | t | P&L $ | P&L/j | fwd |
|---|---|---|---|---|---|---|---|
| 24_funding_multivenues | ROUGE | 171 | -0.5092 | -3.3 | -87.07 | -2.432 | 35.8 j |
| 25_convergence_basis | GRIS | 24 | 0.1202 | 0.39 | 2.89 | 0.962 | 3.0 j |
| 27a_rev_premium | ORANGE | 43 | -0.776 | -0.33 | -33.37 | -0.935 | 35.7 j |
| 27b_rev_move | ORANGE | 62 | 2.415 | 1.26 | 149.73 | 4.242 | 35.3 j |
| 27c_mom_move | ORANGE | 62 | -2.555 | -1.33 | -158.41 | -4.488 | 35.3 j |
| 27d_rev_move_stop | ORANGE | 79 | -0.0233 | -0.01 | -1.84 | -0.062 | 29.7 j |
| 27e_arbitre | ROUGE | 30 | -1.0046 | -0.4 | -30.14 | -1.164 | 25.9 j |
| 27f10_selecteur | ORANGE | 147 | 0.5237 | 0.64 | 76.98 | 3.104 | 24.8 j |
| 27f_selecteur | ORANGE | 41 | -3.051 | -1.35 | -125.09 | -5.044 | 24.8 j |
| 27g10_selecteur | ORANGE | 31 | 0.2671 | 0.1 | 8.28 | 0.484 | 17.1 j |
| 28_carry_hold | GRIS | 1 | 11.6387 | 0.0 | 11.64 | 4.311 | 2.7 j |
| rd_h2 | ORANGE | 35 | 0.3735 | 0.46 | 13.07 | 4.357 | 3.0 j |

**P&L paper cumule (hors temoin)** : -173.33 $

**BTC** 64235 $ — ret 1j +0.51% · 7j -2.80% · 30j +6.65%
**Calibration arbitre (J+7)** : {"tendance": {"n": 20, "taux_correct": 0.45, "brier_moyen": 0.27}}
**Autofinancement** : couts API 18.73 $ (releve 2026-07-26) · revenus reels 0 EUR / cible 35.0 EUR (reste 35.0 EUR)

_Genere automatiquement (PC eteint). Rien ici n'est un ordre : la gate decide,
le Commandant tranche. Zero argent reel._
