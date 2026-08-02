# Brief Station — 2026-08-02 14:15 (Paris)

## 🔴 ALERTES
- 27g10_selecteur: KILL exécuté (2026-08-02) : PAUSE TECHNIQUE, PAS UN VERDICT (02/08/2026). Ce bot est PUR LLM : ia_seule=True, il n'agit QUE sur les pieces ayant un avis IA frais (avis_piece_ia.py). Le credit API est epuise depuis le 02/08 -> plus aucun avis n'est produit. Le laisser tourner ne mesurerait rien : soit il ne trade pas du tout, soit il rejoue des avis perimes, ce qui polluerait son echantillon avec des donnees d'une autre nature (meme faute de fond que la coupure comptable du 26/07). Ses statistiques au moment de la pause : n=41, esp +0,3552, t=+0,17 -- indistinguable du hasard, aucune conclusion perdue. A RELANCER des le rechargement de l'API : 'relance 27g10_selecteur' sur Telegram, ou passer etat/api_credit.json a epuise=false puis retirer cette entree.

## 🟠 Avertissements
- 27e_arbitre: REGLE 15/07 : Delta<0 vs 27b a n>=30 -- KILL RECOMMANDE (prior negatif confirme)

## Statuts gate (GO-reel)
| Bot | Statut | n | esp | t | P&L $ | P&L/j | fwd |
|---|---|---|---|---|---|---|---|
| 24_funding_multivenues | ROUGE | 171 | -0.5092 | -3.3 | -87.07 | -2.193 | 39.7 j |
| 25_convergence_basis | ORANGE | 347 | -0.1152 | -1.35 | -39.97 | -5.71 | 7.0 j |
| 27a_rev_premium | ORANGE | 47 | -0.8563 | -0.39 | -40.24 | -1.016 | 39.6 j |
| 27b_rev_move | ORANGE | 65 | 2.7143 | 1.47 | 176.43 | 4.489 | 39.3 j |
| 27c_mom_move | ORANGE | 65 | -2.8543 | -1.55 | -185.53 | -4.721 | 39.3 j |
| 27d_rev_move_stop | ORANGE | 83 | 0.2508 | 0.16 | 20.82 | 0.62 | 33.6 j |
| 27e_arbitre | ROUGE | 30 | -1.0046 | -0.4 | -30.14 | -1.008 | 29.9 j |
| 27f10_selecteur | ORANGE | 162 | 0.5151 | 0.68 | 83.45 | 2.898 | 28.8 j |
| 27f_selecteur | ORANGE | 44 | -2.2362 | -1.03 | -98.39 | -3.416 | 28.8 j |
| 27g10_selecteur | ROUGE | 41 | 0.3552 | 0.17 | 14.56 | 0.69 | 21.1 j |
| 28_carry_hold | GRIS | 6 | -0.4577 | -0.16 | -2.75 | -0.41 | 6.7 j |
| rd_h2 | ORANGE | 90 | 0.4387 | 1.2 | 39.48 | 5.722 | 6.9 j |

**P&L paper cumule (hors temoin)** : -149.35 $

**BTC** 63133 $ — ret 1j +0.55% · 7j -3.42% · 30j +0.89%
**Calibration arbitre (J+7)** : {"tendance": {"n": 20, "taux_correct": 0.45, "brier_moyen": 0.27}}
**Autofinancement** : couts API 18.73 $ (releve 2026-07-26) · revenus reels 0 EUR / cible 35.0 EUR (reste 35.0 EUR)

_Genere automatiquement (PC eteint). Rien ici n'est un ordre : la gate decide,
le Commandant tranche. Zero argent reel._
