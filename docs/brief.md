# Brief Station — 2026-08-05 07:30 (Paris)

## 🔴 ALERTES
- **BANC SUSPECT** : un temoin a |t| >= 2 — ne rien conclure.
- 25_convergence_basis: esp20 -1.05 < borne -0.90 -> COUPER LE BOT
- 27g10_selecteur: KILL exécuté (2026-08-02) : PAUSE TECHNIQUE, PAS UN VERDICT (02/08/2026). Ce bot est PUR LLM : ia_seule=True, il n'agit QUE sur les pieces ayant un avis IA frais (avis_piece_ia.py). Le credit API est epuise depuis le 02/08 -> plus aucun avis n'est produit. Le laisser tourner ne mesurerait rien : soit il ne trade pas du tout, soit il rejoue des avis perimes, ce qui polluerait son echantillon avec des donnees d'une autre nature (meme faute de fond que la coupure comptable du 26/07). Ses statistiques au moment de la pause : n=41, esp +0,3552, t=+0,17 -- indistinguable du hasard, aucune conclusion perdue. A RELANCER des le rechargement de l'API : 'relance 27g10_selecteur' sur Telegram, ou passer etat/api_credit.json a epuise=false puis retirer cette entree.

## 🟠 Avertissements
- 27e_arbitre: REGLE 15/07 : Delta<0 vs 27b a n>=30 -- KILL RECOMMANDE (prior negatif confirme)

## Statuts gate (GO-reel)
| Bot | Statut | n | esp | t | P&L $ | P&L/j | fwd |
|---|---|---|---|---|---|---|---|
| 24_funding_multivenues | ROUGE | 171 | -0.5092 | -3.3 | -87.07 | -2.049 | 42.5 j |
| 25_convergence_basis | ROUGE | 520 | -0.2145 | -3.17 | -111.52 | -11.497 | 9.7 j |
| 27a_rev_premium | ORANGE | 53 | -2.27 | -1.0 | -120.31 | -2.838 | 42.4 j |
| 27b_rev_move | ORANGE | 67 | 2.3064 | 1.2 | 154.53 | 3.679 | 42.0 j |
| 27c_mom_move | ORANGE | 67 | -2.4464 | -1.27 | -163.91 | -3.903 | 42.0 j |
| 27d_rev_move_stop | ORANGE | 92 | -0.3591 | -0.25 | -33.04 | -0.908 | 36.4 j |
| 27e_arbitre | ROUGE | 30 | -1.0046 | -0.4 | -30.14 | -0.925 | 32.6 j |
| 27f10_selecteur | ORANGE | 173 | 0.0558 | 0.07 | 9.66 | 0.307 | 31.5 j |
| 27f_selecteur | ORANGE | 46 | -1.6663 | -0.72 | -76.65 | -2.433 | 31.5 j |
| 27g10_selecteur | ROUGE | 41 | 0.3552 | 0.17 | 14.56 | 0.612 | 23.8 j |
| 28_carry_hold | GRIS | 11 | 0.6221 | 0.18 | 6.84 | 0.728 | 9.4 j |
| 29_carry_neutre | GRIS | 6 | -4.1776 | -0.54 | -25.07 | -2.667 | 9.4 j |
| rd_h2 | ORANGE | 119 | 0.2087 | 0.66 | 24.84 | 2.587 | 9.6 j |

**P&L paper cumule (hors temoin)** : -437.28 $

**BTC** 64388 $ — ret 1j +0.50% · 7j +0.67% · 30j +0.52%
**Moves 24h ≥ 20 %** : SKR +44.3%, CASHCAT +34.3%
**Calibration arbitre (J+7)** : {"tendance": {"n": 20, "taux_correct": 0.45, "brier_moyen": 0.27}}
**Autofinancement** : couts API 18.73 $ (releve 2026-07-26) · revenus reels 0 EUR / cible 35.0 EUR (reste 35.0 EUR)

_Genere automatiquement (PC eteint). Rien ici n'est un ordre : la gate decide,
le Commandant tranche. Zero argent reel._
