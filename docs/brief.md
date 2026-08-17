# Brief Station — 2026-08-17 19:01 (Paris)

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
| 29_carry_neutre | GRIS | 18 | 13.4441 | 1.27 | 241.99 | 11.05 | 21.9 j |
| 29b_carry_neutre_large | GRIS | 20 | 1.3233 | 0.78 | 26.47 | 2.206 | 12.0 j |
| 29c_carry_decale | ORANGE | 60 | -0.1279 | -0.95 | -7.68 | -0.645 | 11.9 j |
| rd_h2 | ORANGE | 133 | -0.0081 | -0.02 | -1.08 | -0.049 | 22.1 j |

### 🛑 Bots arretes / tues (11) — retires du banc, statistiques figees
| Bot | Statut | n | esp | t | P&L $ | P&L/j | fwd |
|---|---|---|---|---|---|---|---|
| 24_funding_multivenues | ROUGE | 171 | -0.5092 | -3.3 | -87.07 | -1.586 | 54.9 j |
| 25_convergence_basis | ROUGE | 546 | -0.2221 | -3.4 | -121.24 | -5.461 | 22.2 j |
| 27a_rev_premium | ROUGE | 84 | -1.7432 | -0.74 | -146.43 | -2.672 | 54.8 j |
| 27b_rev_move | ROUGE | 99 | 1.2191 | 0.73 | 120.69 | 2.214 | 54.5 j |
| 27c_mom_move | ROUGE | 99 | -1.3591 | -0.81 | -134.55 | -2.469 | 54.5 j |
| 27d_rev_move_stop | ROUGE | 162 | -0.683 | -0.63 | -110.65 | -2.267 | 48.8 j |
| 27e_arbitre | ROUGE | 30 | -1.0046 | -0.4 | -30.14 | -0.668 | 45.1 j |
| 27f10_selecteur | ROUGE | 175 | -0.0665 | -0.09 | -11.64 | -0.264 | 44.0 j |
| 27f_selecteur | ROUGE | 71 | 0.1566 | 0.08 | 11.12 | 0.253 | 44.0 j |
| 27g10_selecteur | ROUGE | 41 | 0.3552 | 0.17 | 14.56 | 0.401 | 36.3 j |
| 28_carry_hold | ROUGE | 31 | -0.0412 | -0.01 | -1.28 | -0.058 | 21.9 j |

**P&L paper cumule (hors temoin, morts inclus)** : -236.93 $

**BTC** 64080 $ — ret 1j +1.92% · 7j +0.20% · 30j -1.15%
**Moves 24h ≥ 20 %** : ACE +27.1%, HEMI +21.5%
**Calibration arbitre (J+7)** : {"tendance": {"n": 20, "taux_correct": 0.45, "brier_moyen": 0.27}}
**Autofinancement** : couts API 18.73 $ (releve 2026-07-26) · revenus reels 0 EUR / cible 35.0 EUR (reste 35.0 EUR)

_Genere automatiquement (PC eteint). Rien ici n'est un ordre : la gate decide,
le Commandant tranche. Zero argent reel._
