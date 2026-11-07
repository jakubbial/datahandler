# Backend

FastAPI (Python) application.

## Run locally

```bash
docker compose up backend --build
```

The app is exposed on port `8000` and the main health check is available at:

- http://localhost:8000/health
- http://localhost:8000/docs

## Stack

- Python 3.12
- FastAPI
- Poetry
