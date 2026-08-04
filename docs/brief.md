# Brief Station — 2026-08-04 19:14 (Paris)

## 🔴 ALERTES
- **BANC SUSPECT** : un temoin a |t| >= 2 — ne rien conclure.
- 27g10_selecteur: KILL exécuté (2026-08-02) : PAUSE TECHNIQUE, PAS UN VERDICT (02/08/2026). Ce bot est PUR LLM : ia_seule=True, il n'agit QUE sur les pieces ayant un avis IA frais (avis_piece_ia.py). Le credit API est epuise depuis le 02/08 -> plus aucun avis n'est produit. Le laisser tourner ne mesurerait rien : soit il ne trade pas du tout, soit il rejoue des avis perimes, ce qui polluerait son echantillon avec des donnees d'une autre nature (meme faute de fond que la coupure comptable du 26/07). Ses statistiques au moment de la pause : n=41, esp +0,3552, t=+0,17 -- indistinguable du hasard, aucune conclusion perdue. A RELANCER des le rechargement de l'API : 'relance 27g10_selecteur' sur Telegram, ou passer etat/api_credit.json a epuise=false puis retirer cette entree.

## 🟠 Avertissements
- 27e_arbitre: REGLE 15/07 : Delta<0 vs 27b a n>=30 -- KILL RECOMMANDE (prior negatif confirme)

## Statuts gate (GO-reel)
| Bot | Statut | n | esp | t | P&L $ | P&L/j | fwd |
|---|---|---|---|---|---|---|---|
| 24_funding_multivenues | ROUGE | 171 | -0.5092 | -3.3 | -87.07 | -2.078 | 41.9 j |
| 25_convergence_basis | ORANGE | 475 | -0.1736 | -2.4 | -82.47 | -8.965 | 9.2 j |
| 27a_rev_premium | ORANGE | 53 | -2.27 | -1.0 | -120.31 | -2.878 | 41.8 j |
| 27b_rev_move | ORANGE | 67 | 2.3064 | 1.2 | 154.53 | 3.724 | 41.5 j |
| 27c_mom_move | ORANGE | 67 | -2.4464 | -1.27 | -163.91 | -3.95 | 41.5 j |
| 27d_rev_move_stop | ORANGE | 88 | -0.051 | -0.03 | -4.49 | -0.125 | 35.8 j |
| 27e_arbitre | ROUGE | 30 | -1.0046 | -0.4 | -30.14 | -0.939 | 32.1 j |
| 27f10_selecteur | ORANGE | 170 | 0.0386 | 0.05 | 6.56 | 0.212 | 31.0 j |
| 27f_selecteur | ORANGE | 46 | -1.6663 | -0.72 | -76.65 | -2.473 | 31.0 j |
| 27g10_selecteur | ROUGE | 41 | 0.3552 | 0.17 | 14.56 | 0.625 | 23.3 j |
| 28_carry_hold | GRIS | 11 | 0.6221 | 0.18 | 6.84 | 0.769 | 8.9 j |
| 29_carry_neutre | GRIS | 6 | -4.1776 | -0.54 | -25.07 | -2.816 | 8.9 j |
| rd_h2 | ORANGE | 113 | 0.2487 | 0.75 | 28.1 | 3.088 | 9.1 j |

**P&L paper cumule (hors temoin)** : -379.52 $

**BTC** 64036 $ — ret 1j +0.86% · 7j +0.20% · 30j +0.63%
**Moves 24h ≥ 20 %** : CASHCAT +36.5%
**Calibration arbitre (J+7)** : {"tendance": {"n": 20, "taux_correct": 0.45, "brier_moyen": 0.27}}
**Autofinancement** : couts API 18.73 $ (releve 2026-07-26) · revenus reels 0 EUR / cible 35.0 EUR (reste 35.0 EUR)

_Genere automatiquement (PC eteint). Rien ici n'est un ordre : la gate decide,
le Commandant tranche. Zero argent reel._
