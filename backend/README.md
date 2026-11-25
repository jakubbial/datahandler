# Backend

FastAPI application managed with Poetry.

## Run with Compose

```bash
docker compose up backend --build
```

The API is exposed on port `8100`; its health endpoint is `/health` and Swagger UI is at `/docs`.

## BDL monitoring

Every request to the BDL API (`path`, `params` including `page`, `status`, `duration_ms`)
and every cache lookup (`hit`, `miss`, `expired`) for subjects, variables, variable details
and data is logged. Monitoring is enabled by default; set `BDL_MONITORING=0` to disable it.

Entries go to stderr and to `backend/logs/bdl-monitoring.log` (rotated at 5 MB, 3 backups,
ignored by git). Set `BDL_MONITORING_LOG_FILE` to change the path, or to an empty value to
disable the file.

## Tests

```bash
poetry install --with dev
poetry run pytest
```

Python 3.12 is the supported development version.
