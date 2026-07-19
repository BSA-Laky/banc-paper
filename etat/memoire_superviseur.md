# Meta-memoire Superviseur — maj 2026-07-19 (semaine 3)

## Tendances de fond
- BTC 61839→64654 sur 3 semaines ; ret1/7/30 faibles (19/07 : -0.3%/+1.4%/+1.8%). Regime neutre persistant.
- Banc fiable en continu : banc_suspect=false depuis le debut. Temoin 10 sain MAIS t=-0.65 (n=395) hors plage historique [0.37;0.84] observee jusqu'a n~310 — premiere rupture, a confirmer avant conclusion.

## Verdicts dates
- **25_conv** : t 2.39(02/07)→2.41(12/07)→2.62(15/07)→2.91(18/07)→3.33(19/07), n 262→681, E~0.51 stable. CREDIBLE, reference du banc. fwd 26.6j → 28j vers 21/07 = seul chemin VERT visible.
- **28_carry_hold** : t 1.81(12/07)→2.65(19/07), n 36→52. E=4.22 = 3.4x mu_ref, ecart AUDITE 15/07 (funding reel HL, 5/5 coherents, queue droite top3=63% du P&L). Prometteur, n court.
- **23_carry** : t 1.08(12/07)→1.79(19/07), n 138. Remonte mais stagne sous 2 depuis 3 releves.
- **27b/c** : miroirs CONFIRMES 3 semaines de suite (somme -5.74→-6.16 a n=44). Verdict quasi definitif au passage n=50.
- **24** nul (t=-1.04, n=115). 27a/e/f/g10 : n<30 bruit. 27f10 : t 0.55→0.24 (n=97), nul.
- 27f_selecteur juge perdant (galop d'essai Commandant) → fiche R&D h1 emise 17/07, en attente approve.

## Qualite de l'Arbitre dans le temps
- Calibration J+7 : null semaines 1-2, puis n=8 taux=0.625 brier=0.235 fige depuis ~11j. n<20 → non probante, plafond 1.0. Escalade calibration DIFFEREE : pipeline produit des scores (plus null), il accumule lentement. Reevaluer si n<20 encore au ~26/07.
- Qualitatif : rigoureux, auto-plafonne sa conf 0.5-0.58, respecte n<30, a detecte la rupture du temoin. 2 pannes le 17/07 (avis perime 50h), resolues, 0 depuis.
- m1 (issues DYDX/FARTCOIN) : donnees jamais fournies dans le flux — lacune source, mission abandonnee, notee comme trou de donnees.

## Echeances
- ~21/07 : 25_conv fwd 28j → dossier VERT si t>=2 tient (decision humaine).
- 27b/c n=50 ; 28_carry n=60 ; calibration n=20.

## Regles
- Seule la calibration J+7 (n>=20) bouge le plafond.
- Jamais lire un seul cote d'une paire miroir.
- Juger t en tendance multi-semaines, pas au jour.