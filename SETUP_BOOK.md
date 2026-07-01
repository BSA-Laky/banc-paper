# Book paper-forward : trend (#30) + prime de variance (#31)

Deux bots des edges VALIDES out-of-sample (backtest 30 ans) tournent en paper,
argent 100 % fictif, à côté du banc crypto. Rotation MENSUELLE (le 2 du mois).

## Fichiers (dossier cloud_github)
- `donnees_marche.py` — données marchés (Twelve Data, atteignable depuis le cloud)
- `bot_trend.py` — bot 30 (time-series momentum, 14 ETF) + témoin book aléatoire
- `bot_variance.py` — bot 31 (vente de vol à risque défini, VIX vs S&P réalisé)
- `run_book.py` — runner mensuel → journal `book_trades.csv` + `docs/book.html`
- `.github/workflows/book.yml` — cron mensuel (le 2, 14h UTC) + bouton manuel

## LA SEULE CHOSE À FAIRE (1 min, sans carte bleue)
Le runner GitHub ne peut pas lire Yahoo/Stooq (bloqués). Il faut une clé API gratuite :
1. Va sur https://twelvedata.com/pricing → plan **Free** → inscription (email seul, 0 carte).
   Copie ta clé API (Dashboard → API Key).
2. Sur le repo GitHub **BSA-Laky/banc-paper** : **Settings → Secrets and variables →
   Actions → New repository secret**. Nom exact : `TD_KEY`. Valeur : ta clé. **Add secret**.

C'est tout. Sans cette clé, le bot ne casse rien : il tourne "à vide" (aucune donnée,
aucun trade). Avec la clé, il rebalance chaque mois automatiquement, PC éteint.

## Dashboard
Une fois déployé + Pages actif : `https://bsa-laky.github.io/banc-paper/book.html`
(à mettre en favori sur le téléphone).

## Honnêteté (rappel)
- Le verdict forward est LENT par nature : ~1 point de mesure par mois. La preuve
  principale reste le backtest 30 ans OOS ; le forward vérifie les frictions live et
  la non-dégradation. Pas de raccourci — mais ça tourne pendant que le capital se constitue.
- VIX sur le tier gratuit Twelve Data : à confirmer. Si indisponible, le bot 31 reste
  dormant (le bot 30 trend tourne quand même) et je le rebranche sur une autre source.
- Rien en argent réel sans verdict forward confirmé battant le témoin (règle projet).
