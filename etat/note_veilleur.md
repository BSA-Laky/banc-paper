_Note du Veilleur (Cadet Remy, claude-haiku-4-5-20251001) — 2026-08-01_

## Veille semaine 2026-08-01

### Execution testnet
Testnet : 336 ordres ouverts, 263 fermes, 47 rejets (taux fill 88 %). Deux causes dominent : 35 rejets par arrondi notionnel à 0 (seuil trop bas), 12 par absence de match immédiat. PnL cumulé : -1,59 USD sur 7j.

### Couts LLM
Budget avis du jour : 2 avis. Capital disponible : 0,0 USD. Aucune allocation en cours, zéro deficit. Tresorier à jour (2026-08-01T07:45:39 UTC).

### Anomalies & attention
**KILL 24_funding_multivenues (2026-07-29)** : bot ROUGE, triple violation (1) regle R4 : t=-3,21 sur n=168 apres coupure → satisfait seuil PERDANT ; (2) comptabilité FAUSSE : accrue += abs(taux) × notionnel × dt, funding en valeur absolue, terme prix ABSENT (meme faute que bot 28) ; (3) INEXECUTABLE : mesure carry+spread Paradex/HL alors que seul HL actif, appels sans prix reçus. **27e_arbitre ROUGE** : n=30, esp=-1,00, t=-0,4. Echecs arbitre : 0 consecutifs. Temoin sain (t=-1,5 sur n=1460). Neuf bots ORANGE (derives faibles, |t|<1,6). **Attention** : anomalie comptable structurelle identifiee ; impact budget négatif marginal.
