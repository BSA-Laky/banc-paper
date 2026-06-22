# Banc paper-trading dans le cloud — gratuit, sans carte bleue, sans PC allumé

Ce dossier fait tourner ton banc d'essai **tout seul, 24/7, gratuitement**, via
**GitHub Actions** (le robot exécute le code toutes les ~15 min) et affiche le
tableau de bord via **GitHub Pages** (une page web ouvrable depuis ton téléphone).

- 💸 **0 € et zéro carte bleue** — il faut juste un compte GitHub (email).
- 🔌 **Ton PC peut rester éteint** — c'est GitHub qui exécute.
- 🔒 **100 % fictif, lecture seule** — APIs publiques, aucune clé, aucun wallet, aucun ordre réel.

Ce qui tourne (tous tes bots actifs, un seul dashboard) : le **témoin aléatoire**,
le **bot 23** (carry funding seul = baseline), le **bot 24** (funding multi-venues
HL/Paradex/ADEN) et le **bot 25** (convergence du basis = l'hypothèse à prouver).
Le dashboard affiche l'**A/B décisif** : le bot 25 bat-il le bot 23 ?

> ℹ️ Le bot 24 lit 3 venues publiques (Hyperliquid, Paradex, ADEN). Si l'une est
> momentanément injoignable ou que son flux est « stale », le bot le détecte et
> passe son tour proprement — c'est attendu, pas une panne.

---

## Installation (≈ 10 min, tout dans le navigateur — aucun logiciel à installer)

### 1. Créer un compte GitHub (si tu n'en as pas)
→ https://github.com/signup — un email + un mot de passe. **Aucune carte bleue.**

### 2. Créer un dépôt (repo) public
- En haut à droite : **+** → **New repository**.
- *Repository name* : `banc-paper` (ou ce que tu veux).
- Coche **Public** (obligatoire pour Pages gratuit ; ce n'est que du code + des
  données fictives, rien de sensible).
- Clique **Create repository**.

### 3. Uploader les fichiers (glisser-déposer)
- Sur la page du repo : **Add file** → **Upload files**.
- Glisse **tout le contenu du dossier `cloud_github`** :
  `banc_essai_paper_trading.py`, `bots_cloud.py`, `bot_24_funding_multivenues.py`,
  `dashboard.py`, `run_once.py`, `README.md`, `.gitignore`, et le dossier `.github`.
  > ⚠️ Le dossier `.github` est indispensable (il contient le robot). S'il
  > n'apparaît pas au glisser-déposer, crée-le à la main : **Add file → Create new
  > file**, nom exact `.github/workflows/sampler.yml`, et colle le contenu fourni.
- **Commit changes**.

### 4. Activer le robot (Actions)
- Onglet **Actions** → si demandé, clique **I understand my workflows, enable them**.
- Tu verras le workflow **sampler**. Clique dessus → **Run workflow** pour lancer
  une première passe tout de suite (sinon il démarre au prochain quart d'heure).

### 5. Activer le tableau de bord (Pages)
- Onglet **Settings** → menu de gauche **Pages**.
- *Build and deployment* → *Source* : **Deploy from a branch**.
- *Branch* : **main** + dossier **/docs** → **Save**.
- Au bout d'1-2 min, l'URL de ton dashboard s'affiche en haut :
  `https://<ton-pseudo>.github.io/banc-paper/`
- **Mets cette URL en favori sur ton téléphone.** Elle se met à jour seule.

C'est fini. Le bot échantillonne ~toutes les 15 min, écrit les trades, met à jour
la page. Tu peux fermer ton PC.

---

## Bon à savoir (honnêteté)

- **Délais** : GitHub n'est pas à la seconde près — des retards de 10-30 min sur le
  cron sont normaux aux heures de pointe. Sans importance ici (funding horaire,
  basis à demi-vie ~7-8 h ; échantillonner au quart d'heure suffit largement).
- **Règle des 60 jours** : GitHub désactive un cron si le repo n'a eu aucune
  activité pendant 60 j. **Pas un souci** : le bot committe à chaque passe.
- **Le verdict** n'est pas le P&L : c'est l'**A/B**. On garde le bot 25 seulement
  s'il bat le bot 23 (carry simple) avec **t-stat ≥ 2 sur ≥ 2-4 semaines**. Sinon
  → **KILL**. Profil asymétrique attendu pour le 25 (peu de trades, gros gains) :
  lire l'espérance ET le nombre de trades, pas que le t-stat.
- **Régler les seuils** : dans `run_once.py` (bot 25) et les constructeurs, tu peux
  ajuster `premium_enter`, `max_hold_h`, `vol_min`, etc. Re-upload le fichier modifié.
- **Argent réel** : interdit tant que le verdict « edge positif » n'est pas confirmé.

---

## Le dashboard en local (optionnel)
Quand ton PC est allumé :
```
py run_once.py
```
puis ouvre `docs/index.html` dans ton navigateur.
