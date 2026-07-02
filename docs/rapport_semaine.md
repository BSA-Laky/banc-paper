# Rapport du Superviseur — semaine du 2026-07-02

# Audit hebdo — 2026-07-02

## Etat du banc
- Banc sain : temoin aleatoire 10 OK (n=107, t=0.66). Aucune alerte, aucun ROUGE, banc_suspect=false.

## Verdicts en cours
- `25_convergence_basis` ORANGE : n=262, E=0.35, t=2.39. Seul candidat credible. Manque n_go 300 et forward 28j (10j actuels). Verdict banc : edge a CONFIRMER (profil asymetrique).
- `23_carry_funding` ORANGE : n=49, E=0.94, t=1.18. Esperance elevee mais non significative — suspecte de gonflement petit echantillon.
- `24_funding_multivenues` ORANGE : n=56, t=0.47. Rien de demontre.
- `27a-d` GRIS : n=4 a 17. Bruit pur (n<30). Les t=±2.5 sur n=17 sont des pieges, correctement ignores par l'Arbitre.

## Arbitre
- Calibration J+7 : null (aucun verdict score). Valeur non prouvee, non infirmee → consigne plafond 1.0 par defaut.
- Pannes : 0 consecutives. Notes de veille coherentes avec la gate (bonne discipline n<30).

## Cout / incidents
- RAS. Extreme DYDX -23.6% note, decision REV de l'Arbitre a scorer vers le 11/07.

## 3 points pour la semaine
1. Suivre `25_convergence` vers n=300 et forward 28j — seul chemin vers VERT.
2. Verifier au premier scoring J+7 si la calibration Arbitre existe enfin ; sinon investiguer le pipeline.
3. Surveiller E de `23_carry` quand n croit : si elle degonfle, le documenter.

_Consigne Arbitre : confiance_max 1.00 (Calibration J+7 null (n<20 verdicts scores) : plafond par defaut 1.0, a reevaluer au premier scoring.). Modele `claude-fable-5`._
