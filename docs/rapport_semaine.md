# Rapport du Superviseur — semaine du 2026-07-26

# Audit hebdo — 2026-07-26

**Salles.** VERT : 25_conv (n=1068, t=3.72, E=0.42) — référence du banc. Fort mais ORANGE : 28_carry (n=82, t=3.70, E=4.03, audité 15/07, seul bot 'reel'). ROUGE résiduels post-KILL : 23_carry (kill 22/07, R1) et 27e (kill 21/07, R3) — inactifs, dossiers clos. Dégradation : 24_funding t=-2.97 (n=162), perdant significatif, bascule ROUGE probable. 27b/c miroirs : verdict DÉFINITIF (n=58/58, somme -8.12). 27a/27f/27g10 : bruit (n<50). rd_h1 : disparu, résolution confirmée J+1.

**Arbitre.** Calibration J+7 : n=13, taux 0.538, Brier 0.252 → n<20, non prouvable. 0 panne cette semaine, missions traitées chaque jour, escalade rd_h1 correcte (résolue). Consigne : plafond levé à 1.0 (calibration inconnue), le seuil 0.6 de la gate reste le vrai garde-fou.

**Coûts.** API 16.01 $ (relevé 21/07), revenus réels 0 €. Testnet : fill 89 %, friction 'no match' stable (Veilleur).

**3 points semaine.**
1. 24_funding : acter la bascule ROUGE, préparer kill si R1/R2 déclenche.
2. 28_carry : viser n=100 et forward 28 j sans dégradation (t<2.3 = signal).
3. Calibration Arbitre : atteindre n=20 pour premier verdict sur sa valeur.

_Consigne Arbitre : confiance_max 1.00 (Calibration J+7 n=13 <20 : valeur inconnue, plafond levé. Réévaluer au barème dès n>=20.). Modele `claude-fable-5`._
