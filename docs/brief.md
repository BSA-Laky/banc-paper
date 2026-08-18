# Brief Station — 2026-08-18 09:45 (Paris)

[station](station.html) · [dashboard crypto](index.html) · [réel](reel.html) · [exécution](execution.html) · [book](book.html) · [équipage](equipage.html)

## 🔴 ALERTES
- 27a_rev_premium: KILL exécuté (2026-08-15) : retrait 15/08 : signal independant mais rendement inexploitable au capital disponible
- 27b_rev_move: KILL exécuté (2026-08-15) : retrait 15/08 : n_go et forward atteints, t +0,52 — indiscernable du hasard
- 27c_mom_move: KILL exécuté (2026-08-15) : retrait 15/08 : miroir deterministe de 27b (somme -14 bp constants, 92/92) — zero information
- 27d_rev_move_stop: KILL exécuté (2026-08-15) : retrait 15/08 : n_go et forward atteints, t -0,86 ; le stop detruit 221 $ sur 146 trades
- 27f_selecteur: KILL exécuté (2026-08-15) : retrait 15/08 : question deja tranchee par le jumeau 27f10 (n=175, t -0,09)

## 🟠 Avertissements
- 27e_arbitre: REGLE 15/07 : Delta<0 vs 27b a n>=30 -- KILL RECOMMANDE (prior negatif confirme)

## Statuts gate (GO-reel) — banc actif
| Bot | Statut | n | esp | t | P&L $ | P&L/j | fwd |
|---|---|---|---|---|---|---|---|
| 29_carry_neutre | GRIS | 18 | 13.4441 | 1.27 | 241.99 | 10.755 | 22.5 j |
| 29b_carry_neutre_large | GRIS | 20 | 1.3233 | 0.78 | 26.47 | 2.101 | 12.6 j |
| 29c_carry_decale | ORANGE | 60 | -0.1279 | -0.95 | -7.68 | -0.614 | 12.5 j |
| rd_h2 | ORANGE | 133 | -0.0081 | -0.02 | -1.08 | -0.048 | 22.7 j |

### 🛑 Bots arretes / tues (11) — retires du banc, statistiques figees
| Bot | Statut | n | esp | t | P&L $ | P&L/j | fwd |
|---|---|---|---|---|---|---|---|
| 24_funding_multivenues | ROUGE | 171 | -0.5092 | -3.3 | -87.07 | -1.566 | 55.6 j |
| 25_convergence_basis | ROUGE | 546 | -0.2221 | -3.4 | -121.24 | -5.318 | 22.8 j |
| 27a_rev_premium | ROUGE | 85 | -1.6369 | -0.7 | -139.14 | -2.507 | 55.5 j |
| 27b_rev_move | ROUGE | 100 | 1.2581 | 0.76 | 125.81 | 2.283 | 55.1 j |
| 27c_mom_move | ROUGE | 100 | -1.3981 | -0.85 | -139.81 | -2.537 | 55.1 j |
| 27d_rev_move_stop | ROUGE | 163 | -0.6302 | -0.59 | -102.72 | -2.079 | 49.4 j |
| 27e_arbitre | ROUGE | 30 | -1.0046 | -0.4 | -30.14 | -0.66 | 45.7 j |
| 27f10_selecteur | ROUGE | 175 | -0.0665 | -0.09 | -11.64 | -0.261 | 44.6 j |
| 27f_selecteur | ROUGE | 71 | 0.1566 | 0.08 | 11.12 | 0.249 | 44.6 j |
| 27g10_selecteur | ROUGE | 41 | 0.3552 | 0.17 | 14.56 | 0.395 | 36.9 j |
| 28_carry_hold | ROUGE | 31 | -0.0412 | -0.01 | -1.28 | -0.057 | 22.5 j |

**P&L paper cumule (hors temoin, morts inclus)** : -221.85 $

**BTC** 64208 $ — ret 1j -0.44% · 7j +1.02% · 30j -0.79%
**Moves 24h ≥ 20 %** : ACE +27.2%
**Calibration arbitre (J+7)** : {"tendance": {"n": 20, "taux_correct": 0.45, "brier_moyen": 0.27}}
**Autofinancement** : couts API 18.73 $ (releve 2026-07-26) · revenus reels 0 EUR / cible 35.0 EUR (reste 35.0 EUR)

_Genere automatiquement (PC eteint). Rien ici n'est un ordre : la gate decide,
le Commandant tranche. Zero argent reel._
