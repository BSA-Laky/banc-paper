# Guide — couche d'exécution Hyperliquid (`execution_hl.py`)

**But** : rendre les bots *capables* d'un vrai wallet, sans jamais franchir seul la barrière humaine.
Par défaut tout est **simulé (paper)**. Le réel demande **plusieurs interrupteurs, tous posés par toi**.

## Modèle de sécurité (ce qui protège l'argent réel)
- **Paper par défaut** : sans variables d'environnement, chaque ordre est simulé (aucun réseau).
- **Double verrou pour le live** : `HL_MODE=live` **ET** `HL_LIVE_CONFIRM=OUI_ARGENT_REEL`.
- **Testnet d'abord** : `HL_NET=testnet` (défaut) = argent de test. `HL_NET=mainnet` = argent réel (explicite).
- **Plafond de taille** : `HL_MAX_NOTIONAL` (défaut 25 $) → tout ordre plus gros est refusé.
- **Wallet AGENT (API), pas ton wallet principal** : il peut **trader mais pas retirer**. La clé reste chez toi, jamais dans le repo ni le chat.
- **Aucune fonction de retrait/transfert** dans le module, par conception.

## Prérequis (une fois)
1. Compte Hyperliquid + un peu de fonds **testnet** (faucet sur l'app testnet HL).
2. Générer un **wallet agent / API** (section API de l'app HL) → il donne une **clé privée d'agent** (trade-only, pas de retrait). Voir docs HL « API wallets / agents ».
3. Dépendances (hors « stdlib only » du banc, donc environnement séparé) :
   ```
   pip install hyperliquid-python-sdk eth-account
   ```

## Étape 1 — vérifier la config (sans rien risquer)
```
python execution_hl.py check      # doit afficher mode PAPER, argent_reel=false
python execution_hl.py dryrun     # simule 2 ordres, écrit etat/execution_paper.csv
```

## Étape 2 — TESTNET (argent de test, jamais réel)
```
export HL_MODE=live
export HL_LIVE_CONFIRM=OUI_ARGENT_REEL
export HL_NET=testnet
export HL_MAX_NOTIONAL=15
export HL_API_KEY=<clé privée de ton wallet agent testnet>
python execution_hl.py check      # doit montrer LIVE / reseau testnet / argent_reel=false
```
Puis, depuis un petit script à toi, passe **un** ordre minuscule et vérifie le fill sur l'app testnet.
Le module appelle `exchange.market_open` / `exchange.order` du SDK officiel.

## Étape 3 — MAINNET (argent réel) — **uniquement après** :
- une hypothèse **validée en paper** (n≥50, t≥2, bat le témoin **et** « toujours-réversion »),
- le **testnet** OK,
- **ta** décision explicite (gate humaine `GO_REEL.md`), capital ≥ plancher.

Alors seulement : `HL_NET=mainnet`, capital petit, `HL_MAX_NOTIONAL` prudent. **C'est ta main, pas la mienne** : je ne lance jamais le live, je ne touche jamais la clé.

## Brancher un bot dessus (plus tard)
Un bot appelle toujours les mêmes méthodes ; on ne change que l'exécuteur :
```python
from execution_hl import ExecutionHL
ex = ExecutionHL()                       # paper par défaut
ex.market_open("DYDX", is_buy=False, notional_usd=10, prix_ref=mark)
```
En paper → simulé ; en live (double-confirmé) → ordre réel HL. Le mois de validation finale = ce bot, en live mainnet, capital réel, agents à la gestion — **après** verdict paper.
