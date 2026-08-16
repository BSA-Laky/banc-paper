# Brief Station — 2026-08-16 06:10 (Paris)

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
| 29_carry_neutre | GRIS | 12 | 20.1879 | 1.28 | 242.25 | 11.934 | 20.3 j |
| 29b_carry_neutre_large | GRIS | 20 | 1.3233 | 0.78 | 26.47 | 2.521 | 10.5 j |
| 29c_carry_decale | ORANGE | 40 | -0.1912 | -0.94 | -7.65 | -0.735 | 10.4 j |
| rd_h2 | ORANGE | 133 | -0.0081 | -0.02 | -1.08 | -0.052 | 20.6 j |

### 🛑 Bots arretes / tues (11) — retires du banc, statistiques figees
| Bot | Statut | n | esp | t | P&L $ | P&L/j | fwd |
|---|---|---|---|---|---|---|---|
| 24_funding_multivenues | ROUGE | 171 | -0.5092 | -3.3 | -87.07 | -1.63 | 53.4 j |
| 25_convergence_basis | ROUGE | 546 | -0.2221 | -3.4 | -121.24 | -5.857 | 20.7 j |
| 27a_rev_premium | ROUGE | 79 | -1.0971 | -0.46 | -86.67 | -1.626 | 53.3 j |
| 27b_rev_move | ROUGE | 94 | 1.179 | 0.68 | 110.83 | 2.095 | 52.9 j |
| 27c_mom_move | ROUGE | 94 | -1.319 | -0.76 | -123.99 | -2.344 | 52.9 j |
| 27d_rev_move_stop | ROUGE | 153 | -0.8766 | -0.78 | -134.12 | -2.835 | 47.3 j |
| 27e_arbitre | ROUGE | 30 | -1.0046 | -0.4 | -30.14 | -0.693 | 43.5 j |
| 27f10_selecteur | ROUGE | 175 | -0.0665 | -0.09 | -11.64 | -0.274 | 42.5 j |
| 27f_selecteur | ROUGE | 71 | 0.1566 | 0.08 | 11.12 | 0.262 | 42.5 j |
| 27g10_selecteur | ROUGE | 41 | 0.3552 | 0.17 | 14.56 | 0.42 | 34.7 j |
| 28_carry_hold | ROUGE | 31 | -0.0412 | -0.01 | -1.28 | -0.063 | 20.3 j |

**P&L paper cumule (hors temoin, morts inclus)** : -199.65 $

**BTC** 63107 $ — ret 1j +0.08% · 7j -2.71% · 30j -1.28%
**Moves 24h ≥ 20 %** : HEMI +60.9%, ACE -35.2%
**Calibration arbitre (J+7)** : {"tendance": {"n": 20, "taux_correct": 0.45, "brier_moyen": 0.27}}
**Autofinancement** : couts API 18.73 $ (releve 2026-07-26) · revenus reels 0 EUR / cible 35.0 EUR (reste 35.0 EUR)

_Genere automatiquement (PC eteint). Rien ici n'est un ordre : la gate decide,
le Commandant tranche. Zero argent reel._
