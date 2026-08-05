# Brief Station — 2026-08-05 11:01 (Paris)

## 🔴 ALERTES
- 27g10_selecteur: KILL exécuté (2026-08-02) : PAUSE TECHNIQUE, PAS UN VERDICT (02/08/2026). Ce bot est PUR LLM : ia_seule=True, il n'agit QUE sur les pieces ayant un avis IA frais (avis_piece_ia.py). Le credit API est epuise depuis le 02/08 -> plus aucun avis n'est produit. Le laisser tourner ne mesurerait rien : soit il ne trade pas du tout, soit il rejoue des avis perimes, ce qui polluerait son echantillon avec des donnees d'une autre nature (meme faute de fond que la coupure comptable du 26/07). Ses statistiques au moment de la pause : n=41, esp +0,3552, t=+0,17 -- indistinguable du hasard, aucune conclusion perdue. A RELANCER des le rechargement de l'API : 'relance 27g10_selecteur' sur Telegram, ou passer etat/api_credit.json a epuise=false puis retirer cette entree.

## 🟠 Avertissements
- 27e_arbitre: REGLE 15/07 : Delta<0 vs 27b a n>=30 -- KILL RECOMMANDE (prior negatif confirme)

## Statuts gate (GO-reel)
| Bot | Statut | n | esp | t | P&L $ | P&L/j | fwd |
|---|---|---|---|---|---|---|---|
| 24_funding_multivenues | ROUGE | 171 | -0.5092 | -3.3 | -87.07 | -2.044 | 42.6 j |
| 25_convergence_basis | ORANGE | 534 | -0.2228 | -3.35 | -118.97 | -12.017 | 9.9 j |
| 27a_rev_premium | ORANGE | 53 | -2.27 | -1.0 | -120.31 | -2.831 | 42.5 j |
| 27b_rev_move | ORANGE | 67 | 2.3064 | 1.2 | 154.53 | 3.671 | 42.1 j |
| 27c_mom_move | ORANGE | 67 | -2.4464 | -1.27 | -163.91 | -3.893 | 42.1 j |
| 27d_rev_move_stop | ORANGE | 93 | -0.4338 | -0.3 | -40.34 | -1.105 | 36.5 j |
| 27e_arbitre | ROUGE | 30 | -1.0046 | -0.4 | -30.14 | -0.922 | 32.7 j |
| 27f10_selecteur | ORANGE | 173 | 0.0558 | 0.07 | 9.66 | 0.305 | 31.7 j |
| 27f_selecteur | ORANGE | 46 | -1.6663 | -0.72 | -76.65 | -2.418 | 31.7 j |
| 27g10_selecteur | ROUGE | 41 | 0.3552 | 0.17 | 14.56 | 0.609 | 23.9 j |
| 28_carry_hold | GRIS | 14 | -5.4563 | -0.77 | -76.39 | -8.041 | 9.5 j |
| 29_carry_neutre | GRIS | 6 | -4.1776 | -0.54 | -25.07 | -2.639 | 9.5 j |
| rd_h2 | ORANGE | 122 | 0.2262 | 0.73 | 27.59 | 2.816 | 9.8 j |

**P&L paper cumule (hors temoin)** : -532.51 $

**BTC** 64108 $ — ret 1j +0.06% · 7j +0.23% · 30j +0.08%
**Moves 24h ≥ 20 %** : SKR +37.6%, CASHCAT +27.8%
**Calibration arbitre (J+7)** : {"tendance": {"n": 20, "taux_correct": 0.45, "brier_moyen": 0.27}}
**Autofinancement** : couts API 18.73 $ (releve 2026-07-26) · revenus reels 0 EUR / cible 35.0 EUR (reste 35.0 EUR)

_Genere automatiquement (PC eteint). Rien ici n'est un ordre : la gate decide,
le Commandant tranche. Zero argent reel._
