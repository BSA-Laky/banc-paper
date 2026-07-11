# Guide — portefeuille centralisé & wallet (architecture + mise en service)

## L'idée : un compte maître **par venue**, une gestion unifiée
- **Pas 1 wallet pour TOUS les bots** : crypto (perps) = **Hyperliquid** ; book actions/options = **courtier** (IBKR). Venues différentes → comptes différents.
- **« Universel » = 1 compte centralisé par venue + une couche de gestion commune** (`portefeuille.py`) : une seule vue, une seule compta, des plafonds.

## Côté Hyperliquid (tous les bots crypto)
- **1 compte MAÎTRE** = ton dépôt **et** ton retrait → la centralisation que tu veux, et ta main.
- **Plafonds logiciels par bot** (`portefeuille.config.json`) : chaque bot ne peut engager que X $. Simple, adapté à petit capital.
- **Piège évité** : un seul solde partagé = **marge commune** = un bot qui explose peut liquider les autres. Petit capital → risque borné. **Quand ça grossit → sous-comptes Hyperliquid** (marge isolée, les bots ne se touchent plus).
- **Exécution** : chaque bot passe par un **wallet AGENT** (trade-only, **pas de retrait**) via `execution_hl.py`.

## Prêt maintenant (paper, aucune clé)
- `portefeuille.py` — alloue le capital, plafonds durs, compta centralisée, route via `execution_hl`.
- `portefeuille.config.json` — capital total + allocation par bot (édite les chiffres).
- `python portefeuille.py` → l'état ; `python portefeuille.py dryrun` → simulation paper.

## Mise en service — **le jour où un bot est validé, pas avant**
> Règle d'or : **tu ne colles JAMAIS ta clé privée / seed dans le chat.** Tu la mets toi-même en variable/secret. Je te guide au clic près.
1. Créer un compte Hyperliquid + un **wallet agent** (trade-only, section API de l'app HL).
2. **Testnet d'abord** : faucet testnet, `HL_NET=testnet`, petit `HL_MAX_NOTIONAL`.
3. Régler `portefeuille.config.json` (capital = ce que tu déposes, ex. 30 $ ; allocation par bot).
4. Poser les variables (local ou secrets) : `HL_MODE`, `HL_LIVE_CONFIRM`, `HL_NET`, `HL_MAX_NOTIONAL`, `HL_API_KEY` (ta clé agent — toi seul).
5. `python execution_hl.py check`, puis **un** ordre testnet minuscule → vérifier le fill.
6. **Mainnet** seulement après : hypothèse validée en paper **+** testnet OK **+** ta décision. Capital petit.
7. **Retrait des gains** = depuis ton **wallet propriétaire**, quand tu veux. **Aucun bot ne peut retirer.**

## Brancher un bot (plus tard)
```python
from portefeuille import Portefeuille
pf = Portefeuille()                                   # paper par défaut
pf.ouvrir("27f_selecteur", "DYDX", is_buy=False, notional=8, prix_ref=mark)
print(pf.etat())                                      # compta centralisée par bot + total
```
En paper → simulé ; en live (double-confirmé) → ordre réel via le wallet agent. Le mois de validation finale = ces bots, capital réel centralisé, agents à la gestion — **après** verdict paper.
