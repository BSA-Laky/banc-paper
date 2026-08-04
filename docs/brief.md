# Brief Station — 2026-08-04 08:01 (Paris)

## 🔴 ALERTES
- **BANC SUSPECT** : un temoin a |t| >= 2 — ne rien conclure.
- 27g10_selecteur: KILL exécuté (2026-08-02) : PAUSE TECHNIQUE, PAS UN VERDICT (02/08/2026). Ce bot est PUR LLM : ia_seule=True, il n'agit QUE sur les pieces ayant un avis IA frais (avis_piece_ia.py). Le credit API est epuise depuis le 02/08 -> plus aucun avis n'est produit. Le laisser tourner ne mesurerait rien : soit il ne trade pas du tout, soit il rejoue des avis perimes, ce qui polluerait son echantillon avec des donnees d'une autre nature (meme faute de fond que la coupure comptable du 26/07). Ses statistiques au moment de la pause : n=41, esp +0,3552, t=+0,17 -- indistinguable du hasard, aucune conclusion perdue. A RELANCER des le rechargement de l'API : 'relance 27g10_selecteur' sur Telegram, ou passer etat/api_credit.json a epuise=false puis retirer cette entree.

## 🟠 Avertissements
- 27e_arbitre: REGLE 15/07 : Delta<0 vs 27b a n>=30 -- KILL RECOMMANDE (prior negatif confirme)

## Statuts gate (GO-reel)
| Bot | Statut | n | esp | t | P&L $ | P&L/j | fwd |
|---|---|---|---|---|---|---|---|
| 24_funding_multivenues | ROUGE | 171 | -0.5092 | -3.3 | -87.07 | -2.098 | 41.5 j |
| 25_convergence_basis | ORANGE | 440 | -0.1558 | -2.03 | -68.54 | -7.878 | 8.7 j |
| 27a_rev_premium | ORANGE | 51 | -1.2224 | -0.59 | -62.34 | -1.506 | 41.4 j |
| 27b_rev_move | ORANGE | 66 | 2.975 | 1.62 | 196.35 | 4.789 | 41.0 j |
| 27c_mom_move | ORANGE | 66 | -3.115 | -1.7 | -205.59 | -5.014 | 41.0 j |
| 27d_rev_move_stop | ORANGE | 87 | 0.0348 | 0.02 | 3.03 | 0.086 | 35.4 j |
| 27e_arbitre | ROUGE | 30 | -1.0046 | -0.4 | -30.14 | -0.954 | 31.6 j |
| 27f10_selecteur | ORANGE | 169 | 0.0566 | 0.07 | 9.56 | 0.312 | 30.6 j |
| 27f_selecteur | ORANGE | 45 | -2.6322 | -1.22 | -118.45 | -3.871 | 30.6 j |
| 27g10_selecteur | ROUGE | 41 | 0.3552 | 0.17 | 14.56 | 0.639 | 22.8 j |
| 28_carry_hold | GRIS | 8 | -1.1732 | -0.5 | -9.39 | -1.117 | 8.4 j |
| 29_carry_neutre | GRIS | 6 | -4.1776 | -0.54 | -25.07 | -2.984 | 8.4 j |
| rd_h2 | ORANGE | 109 | 0.2749 | 0.82 | 29.97 | 3.444 | 8.7 j |

**P&L paper cumule (hors temoin)** : -353.12 $

**BTC** 63746 $ — ret 1j +0.40% · 7j -0.25% · 30j +0.17%
**Moves 24h ≥ 20 %** : CASHCAT +63.4%
**Calibration arbitre (J+7)** : {"tendance": {"n": 20, "taux_correct": 0.45, "brier_moyen": 0.27}}
**Autofinancement** : couts API 18.73 $ (releve 2026-07-26) · revenus reels 0 EUR / cible 35.0 EUR (reste 35.0 EUR)

_Genere automatiquement (PC eteint). Rien ici n'est un ordre : la gate decide,
le Commandant tranche. Zero argent reel._
