# Dashboard Météo & Qualité de l'Air

Projet Python de 3e année. C'est un dashboard Streamlit qui récupère la météo et la qualité de l'air pour 5 villes (Paris, Lyon, Marseille, Londres, Madrid) avec l'API Open-Meteo. Les réponses sont gardées en cache dans une base SQLite, et le dashboard affiche une alerte quand les seuils de pollution (OMS) ou de chaleur sont dépassés.

## Lancer le projet

Il faut Python 3.10 ou plus (on a testé avec Python 3.13).

Installer les dépendances :

```
python -m pip install -r requirements.txt
```

Lancer le dashboard :

```
python -m streamlit run app.py
```

Le navigateur s'ouvre normalement tout seul sur http://localhost:8501.

On passe par `python -m streamlit` plutôt que `streamlit` tout court parce que sur Windows la commande `streamlit` n'est souvent pas dans le PATH après l'installation, et ça donne l'erreur "le terme streamlit n'est pas reconnu".

Pas besoin de clé API : Open-Meteo est gratuit et sans clé, donc il n'y a pas de fichier `.env`. Il est quand même dans le `.gitignore` au cas où on change d'API plus tard.

Pour lancer les tests :

```
python -m pytest
```

## Organisation du code

```
dashboard_meteo/
    app.py                  point d'entrée, lance le dashboard
    data/                   cache SQLite (créé tout seul au premier lancement)
    src/
        api_client.py       appels API, cache SQLite de 30 min, données simulées
        data_processing.py  mise en forme avec pandas, score de confort, stats et tendances
        alerts.py           seuils et détection des alertes
        dashboard.py        l'interface Streamlit
    tests/
        test_api.py         tests du cache et du mode déconnecté
        test_processing.py  tests des calculs et des alertes
    requirements.txt
    pytest.ini
```

L'idée c'est de séparer la récupération des données (`api_client`), les calculs (`data_processing` et `alerts`) et l'affichage (`dashboard`), comme demandé dans le cahier des charges.

## Ce que j'ai modifié / ajouté par rapport au code de départ

À la base on avait un seul fichier (`dashboard_meteo_qualite_air_boilerplate.py`) qui contenait tout. J'ai repris ce code-là, je ne l'ai pas refait de zéro.

### Les bugs corrigés

- Le dashboard plantait dès qu'on choisissait une ville, avec l'erreur `cannot convert float NaN to integer`. En fait l'API renvoie aussi les prévisions des jours suivants, et le code prenait la dernière ligne du tableau en pensant que c'était l'heure actuelle. Sauf que c'était une heure dans 5 jours, où la qualité de l'air n'est pas encore connue (valeurs vides). Maintenant je garde seulement les heures déjà passées (`keep_past_hours`) pour les indicateurs et les alertes.
- L'onglet carte plantait aussi : `px.scatter_mapbox` n'existe plus dans les versions récentes de Plotly, je l'ai remplacé par `px.scatter_map`.
- Les graphiques disaient "7 derniers jours" et "24 dernières heures" mais il n'y avait que du futur dedans. J'ai ajouté `past_days=7` dans les appels API pour avoir l'historique, et `timezone=auto` pour avoir l'heure locale de la ville (sinon tout est en heure GMT).
- J'ai enlevé `use_container_width=True` sur les graphiques, c'est obsolète dans Streamlit (et de toute façon c'est maintenant le comportement par défaut).

### Ce qui manquait par rapport au cahier des charges

- Données météo : j'ai ajouté la température ressentie, les précipitations, la couverture nuageuse et la direction du vent. La pression était déjà récupérée mais pas affichée, elle l'est maintenant. Le min/max du jour est calculé à partir des données heure par heure.
- Score de confort : il utilise maintenant la température ressentie au lieu de la température normale, vu que c'est ce que demande le cahier des charges.
- Statistiques : nouvel onglet avec la moyenne et la médiane sur 24h et sur 7 jours, plus la tendance (valeur actuelle moins la valeur d'il y a 24h ou 7 jours).
- Alertes : il manquait l'alerte canicule (le seuil de 38 °C existait mais n'était jamais utilisé), la vigilance NO2 et les alertes PM10.
- Panneau de sélection : en plus de la ville, on peut choisir la période affichée et les métriques à afficher.
- Carte : elle affiche les 5 villes avec une couleur selon l'indice AQI (vert = bon, jusqu'à bordeaux = dangereux). Du coup les données des 5 villes sont récupérées au lancement. Le premier chargement prend quelques secondes, après c'est le cache qui prend le relais.
- Structure : le code est découpé en modules comme dans l'arborescence recommandée, avec un `requirements.txt` et un `.gitignore`.
- Tests : passés en pytest dans `tests/`. Il y en a 10 maintenant au lieu de 2 (cache, expiration du cache, coupure réseau, données simulées, score, alertes, stats, catégories AQI).

## Comment ça marche en gros

Le cache : chaque réponse de l'API est enregistrée dans SQLite avec l'heure. Si on redemande la même ville dans les 30 minutes, on relit le cache au lieu de rappeler l'API.

Le mode déconnecté : la case dans la barre latérale génère de fausses données. Et si l'API ne répond pas (pas de réseau, erreur HTTP, JSON cassé), le code bascule tout seul sur ces données simulées au lieu de planter.

Le score de confort (de 0 à 100, plus c'est haut mieux c'est) : on part de 100 et on enlève des points selon l'écart avec 21 °C ressentis, l'écart avec 50 % d'humidité, et le taux de PM2.5.

Les alertes : on regarde la dernière heure mesurée et on la compare à ces seuils :

| Mesure | Vigilance | Alerte |
|---|---|---|
| PM2.5 | 15 µg/m³ | 25 µg/m³ |
| PM10 | 45 µg/m³ | 50 µg/m³ |
| NO2 | 25 µg/m³ | 50 µg/m³ |
| Température | 33 °C | 38 °C (canicule) |

Les seuils de vigilance pour la pollution sont les valeurs guides de l'OMS sur 24h. Les seuils d'alerte viennent du code de départ, ce ne sont pas des valeurs officielles.

## Limites

- On compare une valeur horaire à des valeurs guides de l'OMS qui sont prévues pour une moyenne sur 24h, c'est une simplification.
- "Maintenant" est calculé avec l'heure du PC. Pour Londres il peut donc y avoir une heure de décalage, vu qu'il n'y a pas le même fuseau horaire qu'en France.
- En mode déconnecté les données sont aléatoires et changent à chaque clic, c'est juste pour tester l'affichage.
