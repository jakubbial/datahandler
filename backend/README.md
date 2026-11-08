# Backend

FastAPI application managed with Poetry.

## Run with Compose

```bash
docker compose up backend --build
```

The API is exposed on port `8000`; its health endpoint is `/health` and Swagger UI is at `/docs`.

## Tests

```bash
poetry install --with dev
poetry run pytest
```

Python 3.12 is the supported development version.
