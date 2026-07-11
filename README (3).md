# Weekend Lyon

Reçois chaque vendredi un mail avec un bouton **Ouvrir Claude**. Au clic, Claude cherche pour toi le meilleur du divertissement (concerts, ciné, sport, expos, restos, événements) autour du **5 rue de Condé, 69002 Lyon**, et te sort une sélection classée avec liens, trajets et coups de cœur.

Pas d'API Anthropic, pas de coût API : la recherche se fait dans ta session Claude, au clic. Le GitHub Action génère juste le lien daté et l'envoie par mail (Brevo SMTP).

Au clic, Claude te rend le résultat **en artefact** : une carte par sortie (coup de cœur, trajet, ambiance solo/couple/amis, bouton Itinéraire, lien résa), un mini programme idéal, et une rangée de **boutons cliquables** (Vendredi soir / Samedi / Dimanche / Gratuit) qui relancent une recherche ciblée.

## 1. Secrets à créer

Repo > **Settings > Secrets and variables > Actions > New repository secret** :

| Secret | Valeur |
|---|---|
| `SMTP_USER` | ton login SMTP Brevo (SMTP & API > SMTP) |
| `SMTP_PASS` | ta clé SMTP Brevo |
| `MAIL_FROM` | adresse expéditeur **vérifiée** sur Brevo |
| `MAIL_TO` | destinataire(s) par défaut = toi. Plusieurs adresses possibles, séparées par des virgules. Optionnel : si absent, on utilise `MAIL_FROM` |

C'est tout. Aucune clé API à gérer.

## 2. Paramètres du workflow (Actions > Weekend Lyon > Run workflow)

| Input | Rôle | Défaut |
|---|---|---|
| `period` | période couverte | `weekend` (ou texte libre : `ce soir`, `cette semaine`, `du 20 au 22 février`) |
| `mail_to` | destinataire(s) ponctuel(s), séparés par virgule | vide = ton adresse par défaut |
| `origin` | lieu / point de départ | vide = `5 rue de Condé, 69002 Lyon` |
| `attachments` | fichier(s) à joindre, chemins séparés par virgule (les fichiers doivent être dans le repo) | vide = aucune pièce jointe |
| `dry_run` | `1` = génère le HTML sans envoyer | `0` |

Le cron du vendredi utilise toujours les valeurs par défaut (toi, Lyon, weekend). Les inputs ne servent que pour les lancements manuels.

## 3. Premier test

Actions > Weekend Lyon > Run workflow avec `dry_run = 1`. Récupère le fichier `weekend-lyon-html` dans les artifacts du run, ouvre-le, clique le bouton pour vérifier que Claude préremplit bien le prompt. Puis relance avec `dry_run = 0` pour recevoir un vrai mail. Ensuite le cron prend le relais.

## Bon à savoir

- **Heure d'envoi** : tous les vendredis à **17h heure de Paris, toute l'année** (été comme hiver). Le cron GitHub étant en UTC et ne gérant pas le changement d'heure, le job se déclenche à 15h et 16h UTC, et un garde-fou Python (`SEND_HOUR_PARIS=17`) ne laisse passer que l'occurrence à 17h Paris. Pour changer l'heure, modifie `SEND_HOUR_PARIS` et, si besoin, les deux lignes `cron`.
- **Brevo** : `MAIL_FROM` doit être un expéditeur validé, sinon l'envoi est refusé.
- **Planning GitHub** : les workflows `schedule` ne tournent que depuis la branche par défaut, peuvent démarrer avec quelques minutes de retard, et sont mis en pause après ~60 jours sans activité sur le repo (un commit relance).

## Personnaliser plus loin

Tout est dans `weekend_lyon.py` (librairie standard uniquement) :
- `build_prompt()` : catégories, rayon, nombre de recos, ton, ambiance par reco.
- `render_html()` : style du mail et raccourcis par jour (Vendredi soir / Samedi / Dimanche).
