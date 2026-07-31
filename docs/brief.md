# Brief Station — 2026-07-31 19:45 (Paris)

## 🔴 ALERTES
- 24_funding_multivenues: KILL exécuté (2026-07-29) : TRIPLE motif (29/07/2026) : (1) PERDANT SIGNIFICATIF, t = -3,21 sur n = 168 apres coupure comptable -- satisfait la regle R4 proposee (t <= -2 a n >= 100) ; (2) comptabilite FAUSSE, meme faute que le bot 28 : accrue += abs(taux_horaire) * notionnel * dt, funding en valeur absolue et AUCUN terme de prix ; (3) INEXECUTABLE : il mesure un carry Paradex et un spread HL<->Paradex alors que nous n'avons de compte que sur Hyperliquid. Ses appels ne recoivent meme pas de prix, le terme de prix est structurellement absent. Migrer sa comptabilite pour mesurer un trade impossible n'aurait aucun sens.

## 🟠 Avertissements
- 27e_arbitre: REGLE 15/07 : Delta<0 vs 27b a n>=30 -- KILL RECOMMANDE (prior negatif confirme)

## Statuts gate (GO-reel)
| Bot | Statut | n | esp | t | P&L $ | P&L/j | fwd |
|---|---|---|---|---|---|---|---|
| 24_funding_multivenues | ROUGE | 171 | -0.5092 | -3.3 | -87.07 | -2.291 | 38.0 j |
| 25_convergence_basis | ORANGE | 229 | -0.0252 | -0.23 | -5.77 | -1.11 | 5.2 j |
| 27a_rev_premium | ORANGE | 44 | -1.0937 | -0.47 | -48.12 | -1.27 | 37.9 j |
| 27b_rev_move | ORANGE | 64 | 2.7102 | 1.45 | 173.45 | 4.625 | 37.5 j |
| 27c_mom_move | ORANGE | 64 | -2.8502 | -1.52 | -182.41 | -4.864 | 37.5 j |
| 27d_rev_move_stop | ORANGE | 82 | 0.2176 | 0.14 | 17.84 | 0.559 | 31.9 j |
| 27e_arbitre | ROUGE | 30 | -1.0046 | -0.4 | -30.14 | -1.073 | 28.1 j |
| 27f10_selecteur | ORANGE | 156 | 0.5603 | 0.72 | 87.41 | 3.237 | 27.0 j |
| 27f_selecteur | ORANGE | 43 | -2.3574 | -1.06 | -101.37 | -3.754 | 27.0 j |
| 27g10_selecteur | ORANGE | 38 | 0.5005 | 0.22 | 19.02 | 0.985 | 19.3 j |
| 28_carry_hold | GRIS | 2 | 2.9024 | 0.33 | 5.8 | 1.185 | 4.9 j |
| rd_h2 | ORANGE | 66 | 0.539 | 1.11 | 35.57 | 6.841 | 5.2 j |

**P&L paper cumule (hors temoin)** : -115.79 $

**BTC** 63052 $ — ret 1j -2.63% · 7j -1.67% · 30j +5.07%
**Calibration arbitre (J+7)** : {"tendance": {"n": 20, "taux_correct": 0.45, "brier_moyen": 0.27}}
**Autofinancement** : couts API 18.73 $ (releve 2026-07-26) · revenus reels 0 EUR / cible 35.0 EUR (reste 35.0 EUR)

_Genere automatiquement (PC eteint). Rien ici n'est un ordre : la gate decide,
le Commandant tranche. Zero argent reel._
