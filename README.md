# Streak

**API de suivi d'habitudes avec séries multi-échelles** (jour / semaine / mois / année) - pensée pour un usage quotidien réel.

*par Evan Guiheux*

## Stack

- **Back-end** : Python, FastAPI, SQLAlchemy 2, PostgreSQL
- **Front-end** : HTML, CSS, JavaScript (vanilla)

## Lancement

Prérequis : Docker, Python 3.13.

```bash
docker compose up -d
fastapi dev app/main.py
```

L'API tourne sur `http://127.0.0.1:8000`, la documentation interactive (Swagger) sur `/docs`.