# Backend

FastAPI application managed with Poetry.

## Run with Compose

```bash
docker compose up backend --build
```

The API is exposed on port `8100`; its health endpoint is `/health` and Swagger UI is at `/docs`.

## BDL API key

The backend sends the `BDL_CLIENT_ID` environment variable as the `X-ClientId` header,
which raises the BDL rate limits (register at <https://api.stat.gov.pl/Home/BdlApi>).
Without it, requests are anonymous. The key must never be committed.

- **Local dev container:** copy `.env.example` in the repository root to `.env`
  (git-ignored) and set `BDL_CLIENT_ID`. Docker Compose reads it automatically.
- **Codespaces:** add a Codespaces secret named `BDL_CLIENT_ID` with access to this
  repository (GitHub Settings → Codespaces → Secrets).

Rebuild or restart the containers after changing the key. On startup the monitoring log
shows `bdl_client_id configured=yes` or `configured=no`; the key itself is never logged.

## BDL monitoring

Every request to the BDL API (`path`, `params` including `page`, `status`, `duration_ms`)
and every cache lookup (`hit`, `miss`, `expired`) for subjects, variables, variable details
and data is logged. Monitoring is enabled by default; set `BDL_MONITORING=0` to disable it.

Concurrent requests for the same variable data share one BDL fetch. Requests that
join an existing fetch are logged with `outcome=shared`.

Entries go to stderr and to `backend/logs/bdl-monitoring.log` (rotated at 5 MB, 3 backups,
ignored by git). Set `BDL_MONITORING_LOG_FILE` to change the path, or to an empty value to
disable the file.

## Tests

```bash
poetry install --with dev
poetry run pytest
```

Python 3.12 is the supported development version.
