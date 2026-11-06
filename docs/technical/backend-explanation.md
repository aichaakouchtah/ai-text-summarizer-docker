# Fonctionnement actuel du backend BART

Ce document décrit l'implémentation réellement présente dans `backend/app.py`. Le [`README.md`](../../README.md) reste la référence pour les commandes d'installation et d'exécution.

## Rôle du service

Le backend est une API Flask qui charge le modèle Hugging Face `facebook/bart-large-cnn`, valide les requêtes, génère un résumé abstractive et renvoie une réponse JSON. Dans Docker Compose, le frontend Gradio l'appelle avec le nom DNS interne `http://backend:5000`.

## Initialisation du modèle

La fonction `load_summarizer()` importe PyTorch et Transformers au moment du chargement, puis initialise `AutoTokenizer` et `BartForConditionalGeneration`. Transformers 5 ayant retiré le pipeline historique `summarization`, un adaptateur local appelle désormais `model.generate()` tout en conservant le même contrat pour l'API. Le Dockerfile installe la variante CPU officielle de PyTorch 2.15.0 ; le conteneur n'embarque donc aucune dépendance CUDA ou NVIDIA.

Le modèle est normalement chargé une seule fois au démarrage du processus. La variable `BART_SKIP_MODEL_LOAD=1` désactive ce chargement pour les tests automatisés, qui injectent un faux pipeline dans `create_app()` et ne téléchargent pas BART.

Les fichiers Hugging Face sont conservés dans le volume Docker nommé `model-cache`, monté dans `/app/cache`. Les variables `HF_HOME` et `TRANSFORMERS_CACHE` pointent vers ce répertoire afin que le cache survive aux reconstructions et aux recréations des conteneurs.

## API HTTP

### `GET /health`

Cette route vérifie la disponibilité réelle du pipeline :

- `200` avec `status: ok` lorsque le modèle est chargé ;
- `503` avec `status: unavailable` lorsque le modèle est absent.

Le healthcheck Docker interroge cette route. Le frontend ne démarre qu'après le passage du backend à l'état `healthy`.

### `POST /summarize`

Le corps doit être un objet JSON contenant :

```json
{
  "text": "A source text containing at least thirty words...",
  "max_length": 130,
  "min_length": 30
}
```

`max_length` et `min_length` sont facultatifs. Les valeurs par défaut sont respectivement 130 et 30. Ces paramètres correspondent à la longueur de génération manipulée par Transformers, exprimée en tokens, et non à un nombre garanti de mots.

Une réponse réussie contient le résumé ainsi que les nombres de mots du texte initial et du résultat :

```json
{
  "original_length": 120,
  "summary": "The generated summary...",
  "summary_length": 34
}
```

## Validations et sécurité applicative

Avant l'inférence, le backend contrôle notamment :

- le type JSON et la présence d'un texte non vide ;
- un minimum de 30 mots ;
- des longueurs entières comprises entre 10 et 500 ;
- `min_length <= max_length` ;
- une limite de 1 024 tokens BART, calculée sans troncature ;
- une taille maximale de requête de 1 MiB.

Les requêtes JSON mal formées, trop volumineuses ou invalides reçoivent un code HTTP explicite. Les exceptions internes sont journalisées côté serveur, mais la réponse client reste générique afin de ne pas exposer de détail sensible.

## Génération

Après validation, le pipeline est appelé avec `do_sample=False`. La génération est donc déterministe à paramètres identiques. Le résultat produit par Transformers est lu dans `result[0]["summary_text"]`, puis sérialisé par Flask.

Le modèle `facebook/bart-large-cnn` est principalement entraîné pour l'anglais. L'inférence CPU fonctionne sans GPU, mais elle demande plusieurs gigaoctets de mémoire et reste plus lente qu'une exécution accélérée.

## Versions verrouillées

- Python 3.11
- Flask 3.1.3
- Werkzeug 3.1.9
- Transformers 5.10.4
- PyTorch 2.15.0 CPU
- SentencePiece 0.2.2

Les versions faisant autorité sont celles de `backend/requirements.txt` et `backend/requirements-torch-cpu.txt`.

## Exécution dans Docker

Le conteneur exécute `python app.py`. Flask écoute sur `0.0.0.0:5000` à l'intérieur du conteneur, tandis que Compose publie le port uniquement sur `127.0.0.1:5000` de la machine hôte. Le processus s'exécute avec l'utilisateur non privilégié `appuser`.

La commande recommandée depuis la racine est :

```bash
docker compose up -d --build
```

Le serveur Flask intégré convient à cette démonstration locale. Pour une exposition publique en production, il faudrait ajouter une couche d'authentification, TLS et un serveur WSGI adapté ; ces éléments ne font pas partie du périmètre actuel.

## Tests

La suite `backend/tests` utilise le client de test Flask et un générateur simulé. Elle vérifie la disponibilité, une génération valide, les entrées courtes ou trop longues, les paramètres invalides, le JSON mal formé et la non-divulgation des exceptions internes.

Depuis la racine du projet :

```bash
python -m pip install -r backend/requirements-dev.txt
python -m pytest backend/tests
```

Ces tests sont hors ligne et ne valident pas la qualité linguistique du modèle. Le test fonctionnel réel doit être effectué sur les conteneurs avec le cache BART disponible.
