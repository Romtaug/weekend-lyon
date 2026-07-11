# Weekend Lyon

Reçois chaque vendredi un mail avec un bouton **Ouvrir Claude**. Au clic, Claude cherche pour toi le meilleur du divertissement (concerts, ciné, sport, expos, restos, événements) autour du **5 rue de Condé, 69002 Lyon**, et te sort une sélection classée avec liens, trajets et coups de cœur.

Pas d'API Anthropic, pas de coût API : la recherche se fait dans ta session Claude, au clic. Le GitHub Action génère juste le lien daté et l'envoie par mail (SMTP).

Au clic, Claude te rend le résultat **en artefact** : une carte par sortie (coup de cœur, trajet, ambiance solo/couple/amis, bouton Itinéraire, lien résa), un mini programme idéal, et une rangée de **boutons cliquables** (Vendredi soir / Samedi / Dimanche / Gratuit) qui relancent une recherche ciblée.

## 1. Secrets à créer

Repo > **Settings > Secrets and variables > Actions > New repository secret**. **2 secrets requis** :

| Secret | Valeur |
|---|---|
| `SMTP_USER` | ton adresse Gmail (ex. `toi@gmail.com`) |
| `SMTP_PASS` | ton **mot de passe d'application Gmail** (16 caractères, voir ci-dessous) |

Le reste est déjà réglé dans le script : serveur `smtp.gmail.com`, port `587`, expéditeur et destinataire = ton adresse. Tu peux surcharger via les secrets `MAIL_TO`, `SMTP_PORT`, etc. si besoin, mais ce n'est pas nécessaire.

### Obtenir le mot de passe d'application Gmail

Depuis mai 2025, Gmail refuse le mot de passe classique pour le SMTP : il faut un mot de passe d'application.

1. Active la **validation en 2 étapes** sur ton compte Google (obligatoire, sinon l'option n'apparaît pas) : Compte Google > Sécurité > Validation en 2 étapes.
2. Va sur **https://myaccount.google.com/apppasswords** (lien direct ; Google a retiré l'entrée du menu).
3. Donne un nom (ex. `weekend-lyon`) et clique sur Créer.
4. Copie le code de **16 caractères**, **sans les espaces**.
5. Colle-le dans le secret GitHub `SMTP_PASS`.

C'est tout. Aucune clé API à gérer.

## 2. Paramètres du workflow (Actions > Weekend Lyon > Run workflow)

| Input | Rôle | Défaut |
|---|---|---|
| `period` | période couverte | `weekend` (ou texte libre : `ce soir`, `cette semaine`, `du 20 au 22 février`) |
| `mail_to` | destinataire(s) ponctuel(s), séparés par virgule | vide = ton adresse par défaut |
| `origin` | lieu / point de départ | vide = `5 rue de Condé, 69002 Lyon` |
| `dry_run` | `1` = génère le HTML sans envoyer | `0` |

Le cron du vendredi utilise toujours les valeurs par défaut (toi, Lyon, weekend). Les inputs ne servent que pour les lancements manuels.

## 3. Premier test

Actions > Weekend Lyon > Run workflow avec `dry_run = 1`. Récupère le fichier `weekend-lyon-html` dans les artifacts du run, ouvre-le, clique le bouton pour vérifier que Claude préremplit bien le prompt. Puis relance avec `dry_run = 0` pour recevoir un vrai mail. Ensuite le cron prend le relais.

## Bon à savoir

- **Heure d'envoi** : tous les vendredis à **17h heure de Paris, toute l'année** (été comme hiver). Le cron GitHub étant en UTC et ne gérant pas le changement d'heure, le job se déclenche à 15h et 16h UTC, et un garde-fou Python (`SEND_HOUR_PARIS=17`) ne laisse passer que l'occurrence à 17h Paris. Pour changer l'heure, modifie `SEND_HOUR_PARIS` et, si besoin, les deux lignes `cron`.
- **Expéditeur** : selon ton fournisseur SMTP, `MAIL_FROM` doit correspondre à un compte ou une adresse autorisée, sinon l'envoi est refusé.
- **Planning GitHub** : les workflows `schedule` ne tournent que depuis la branche par défaut, peuvent démarrer avec quelques minutes de retard, et sont mis en pause après ~60 jours sans activité sur le repo (un commit relance).

## Personnaliser plus loin

Tout est dans `weekend_lyon.py` (librairie standard uniquement) :
- `build_prompt()` : catégories, rayon, nombre de recos, ton, ambiance par reco.
- `render_html()` : style du mail et raccourcis par jour (Vendredi soir / Samedi / Dimanche).
