# Brief Station — 2026-07-30 16:45 (Paris)

## 🔴 ALERTES
- 24_funding_multivenues: KILL exécuté (2026-07-29) : TRIPLE motif (29/07/2026) : (1) PERDANT SIGNIFICATIF, t = -3,21 sur n = 168 apres coupure comptable -- satisfait la regle R4 proposee (t <= -2 a n >= 100) ; (2) comptabilite FAUSSE, meme faute que le bot 28 : accrue += abs(taux_horaire) * notionnel * dt, funding en valeur absolue et AUCUN terme de prix ; (3) INEXECUTABLE : il mesure un carry Paradex et un spread HL<->Paradex alors que nous n'avons de compte que sur Hyperliquid. Ses appels ne recoivent meme pas de prix, le terme de prix est structurellement absent. Migrer sa comptabilite pour mesurer un trade impossible n'aurait aucun sens.

## 🟠 Avertissements
- 27e_arbitre: REGLE 15/07 : Delta<0 vs 27b a n>=30 -- KILL RECOMMANDE (prior negatif confirme)

## Statuts gate (GO-reel)
| Bot | Statut | n | esp | t | P&L $ | P&L/j | fwd |
|---|---|---|---|---|---|---|---|
| 24_funding_multivenues | ROUGE | 171 | -0.5092 | -3.3 | -87.07 | -2.366 | 36.8 j |
| 25_convergence_basis | ORANGE | 130 | -0.0134 | -0.1 | -1.74 | -0.425 | 4.1 j |
| 27a_rev_premium | ORANGE | 44 | -1.0937 | -0.47 | -48.12 | -1.311 | 36.7 j |
| 27b_rev_move | ORANGE | 62 | 2.415 | 1.26 | 149.73 | 4.113 | 36.4 j |
| 27c_mom_move | ORANGE | 62 | -2.555 | -1.33 | -158.41 | -4.352 | 36.4 j |
| 27d_rev_move_stop | ORANGE | 80 | -0.1302 | -0.08 | -10.41 | -0.339 | 30.7 j |
| 27e_arbitre | ROUGE | 30 | -1.0046 | -0.4 | -30.14 | -1.116 | 27.0 j |
| 27f10_selecteur | ORANGE | 151 | 0.5864 | 0.73 | 88.55 | 3.419 | 25.9 j |
| 27f_selecteur | ORANGE | 41 | -3.051 | -1.35 | -125.09 | -4.83 | 25.9 j |
| 27g10_selecteur | ORANGE | 34 | 0.5447 | 0.21 | 18.52 | 1.018 | 18.2 j |
| 28_carry_hold | GRIS | 1 | 11.6387 | 0.0 | 11.64 | 3.063 | 3.8 j |
| rd_h2 | ORANGE | 49 | 0.3005 | 0.5 | 14.73 | 3.682 | 4.0 j |

**P&L paper cumule (hors temoin)** : -177.81 $

**BTC** 64726 $ — ret 1j +1.19% · 7j -0.53% · 30j +10.45%
**Moves 24h ≥ 20 %** : CASHCAT +20.6%
**Calibration arbitre (J+7)** : {"tendance": {"n": 20, "taux_correct": 0.45, "brier_moyen": 0.27}}
**Autofinancement** : couts API 18.73 $ (releve 2026-07-26) · revenus reels 0 EUR / cible 35.0 EUR (reste 35.0 EUR)

_Genere automatiquement (PC eteint). Rien ici n'est un ordre : la gate decide,
le Commandant tranche. Zero argent reel._
