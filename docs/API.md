# Documentation de l'API - Plateforme d'Analyse de Données Agentique

Ce document détaille les endpoints de l'API Backend (FastAPI).

## Authentification
Tous les endpoints (sauf `/health`, `/metrics`, `/auth/register` et `/auth/login`) nécessitent un token JWT valide dans le header `Authorization: Bearer <token>`.

### Inscription
- **URL** : `/api/v1/auth/register`
- **Méthode** : `POST`
- **Corps** : `{"email": "user@example.com", "password": "password"}`

### Connexion
- **URL** : `/api/v1/auth/login`
- **Méthode** : `POST`
- **Corps (Form Data)** : `username=user@example.com&password=password`
- **Réponse** : `{"access_token": "...", "token_type": "bearer"}`

## Sessions d'Analyse
### Liste des sessions
- **URL** : `/api/v1/sessions/`
- **Méthode** : `GET`

### Création d'une session
- **URL** : `/api/v1/sessions/`
- **Méthode** : `POST`
- **Corps** : `{"title": "Analyse Ventes", "dataset_id": 1}`

### Détail d'une session (Historique)
- **URL** : `/api/v1/sessions/{session_id}`
- **Méthode** : `GET`

## Datasets
### Upload de dataset
- **URL** : `/api/v1/sessions/upload`
- **Méthode** : `POST`
- **Corps (Multipart)** : `file=@dataset.csv`

### Liste des datasets
- **URL** : `/api/v1/sessions/datasets`
- **Méthode** : `GET`

## Agent d'Analyse
### Poser une question
- **URL** : `/api/v1/sessions/{session_id}/query`
- **Méthode** : `POST`
- **Corps** : `{"query": "Fais un histogramme de l'âge"}`
- **Réponse** : `{"synthesis": "...", "figures": [...]}`
