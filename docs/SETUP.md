# Guide d'Installation - Plateforme d'Analyse de Données Moderne

Ce guide vous aide à déployer la plateforme localement ou via Docker.

## Prérequis
- Docker et Docker Compose
- Python 3.12 (pour le développement local)
- Clé API OpenAI

## Déploiement Rapide (Docker)
1. Copier le fichier d'environnement :
   ```bash
   cp .env.example .env
   ```
2. Éditer le fichier `.env` pour ajouter votre `OPENAI_API_KEY`.
3. Lancer la stack complète :
   ```bash
   docker-compose up -d --build
   ```
4. Accéder à l'application :
   - Frontend Streamlit : `http://localhost:8501`
   - Backend API : `http://localhost:8000`
   - Documentation API Swagger : `http://localhost:8000/docs`

## Développement Local
1. Créer un environnement virtuel :
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Lancer le Postgres (ou configurer une base locale) :
   ```bash
   docker-compose up -d postgres redis
   ```
3. Exécuter les migrations :
   ```bash
   cd backend
   alembic upgrade head
   ```
4. Lancer le backend :
   ```bash
   uvicorn backend.api.main:app --reload
   ```
5. Lancer le frontend (dans un autre terminal) :
   ```bash
   streamlit run frontend/app.py
   ```

## Tests
Exécuter la suite de tests avec couverture :
```bash
export PYTHONPATH=$PYTHONPATH:.
pytest backend/tests/ -v --cov=backend
```
