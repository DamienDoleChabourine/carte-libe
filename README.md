# Libé sur le terrain — carte des articles abonnés en France

Carte automatique des articles **réservés aux abonnés** de *Libération*
localisés en **France (métropole + outre-mer)** sur une **fenêtre glissante
de deux mois**. Un article n'est retenu que si un lieu français figure dans
ses **tags**, son **titre** ou son **chapô**.

## Contenu

| Fichier | Rôle |
|---|---|
| `collect.py` | collecte RSS, filtres (date, géo, paywall), géocodage, écriture de `data/articles.json` |
| `gazetteer.py` | lieux reconnus (régions, départements, ~380 villes, DROM-COM) + liste des noms ambigus |
| `index.html` | la carte (Leaflet), lit `data/articles.json` |
| `.github/workflows/update.yml` | exécution automatique toutes les 2 h |
| `data/` | données générées (articles, caches géocodage et paywall) |

## Mise en route (~10 minutes)

1. **Créer un dépôt GitHub** (public pour bénéficier de GitHub Pages gratuit)
   et y pousser tout le contenu de ce dossier.
2. Dans `collect.py`, **remplacer l'e-mail** dans `USER_AGENT` par le vôtre
   (demandé par la politique d'usage de Nominatim, le géocodeur OpenStreetMap).
3. Onglet **Settings → Pages** : Source = *Deploy from a branch*,
   branche `main`, dossier `/ (root)`. La carte sera servie à
   `https://<votre-compte>.github.io/<repo>/`.
4. Onglet **Actions** : activer les workflows, puis lancer une première fois
   via *Collecte Libération → Run workflow*.
5. Vérifier le log du premier run (voir ci-dessous), puis laisser tourner.

En local : `pip install requests` puis `python collect.py --dry-run --debug`.

## À vérifier au premier lancement (important)

La **détection du paywall** repose sur des marqueurs standards
(`isAccessibleForFree: false` en JSON-LD, mentions `premium`/`paywall`
dans la page). Ces marqueurs n'ont pas pu être vérifiés sur liberation.fr
au moment de l'écriture du script. Au premier run :

- lancer `python collect.py --dry-run --debug` et regarder les lignes
  `paywall=True/False (marqueur: …)` ;
- ouvrir 2-3 articles à la main et vérifier que le statut est correct ;
- si tout ressort `False`, ouvrir le code source d'un article abonné et
  ajuster la liste `PREMIUM_PATTERNS` dans `collect.py`.

## Limites assumées

- **Démarrage progressif.** Les flux RSS n'exposent que les articles
  récents : la carte ne peut pas remonter deux mois en arrière au premier
  jour. Elle se remplit au fil des passages et atteint sa profondeur de
  deux mois environ deux mois après la mise en route. (Les flux de tags
  régionaux, peu volumineux, apportent tout de même un peu d'historique
  dès le premier run.)
- **Géolocalisation par gazetteer.** Un article situé dans une petite
  commune absente de `gazetteer.py`, sans tag géo ni mention du
  département, passera au travers. La liste s'enrichit en une ligne.
- **Noms ambigus.** « Tours », « Nord », « Somme », « Saint-Denis »… ne
  sont acceptés que via les tags pour éviter les faux positifs. Liste
  `RISKY_IN_TEXT` ajustable dans `gazetteer.py`.
- **Fenêtre glissante, pas purge au 1er du mois.** Chaque passage supprime
  ce qui a plus de 62 jours. Pour une purge calendaire stricte, remplacer
  le calcul de `cutoff` dans `collect.py`.

## Respect du site et des droits

Le projet ne stocke et n'affiche que **titre, chapô, date, lieu et lien**
vers liberation.fr — jamais le texte des articles. Les requêtes vers
liberation.fr sont espacées (0,7 s) et mises en cache ; le géocodage
Nominatim respecte la limite d'une requête par seconde avec cache
persistant. Usage personnel de veille : si le projet devait devenir
public à plus grande échelle, contacter Libération serait la chose
correcte à faire.
