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
and data is logged. Attributes and measures also log cache lookups. Monitoring is
enabled by default; set `BDL_MONITORING=0` to disable it.

Concurrent requests for the same variable data share one BDL fetch. Requests that
join an existing fetch are logged with `outcome=shared`.

Entries go to stderr and to `backend/logs/bdl-monitoring.log` (rotated at 5 MB, 3 backups,
ignored by git). Set `BDL_MONITORING_LOG_FILE` to change the path, or to an empty value to
disable the file.

## Territorial units

`GET /units?level=2` lists voivodeships. `GET /units?level=5&parent_id=...`
lists counties within a voivodeship. Results are cached for 24 hours. The
`unit_parent_id` parameter of `GET /data/by-variable/{variable_id}` limits
the upstream data request to descendants of that unit.
Set `single_page=true` to limit a data request to one BDL page. If more data is
available, the endpoint responds with HTTP 409 instead of returning partial data.

## BDL dictionaries and data metadata

- `GET /attributes` returns the complete attributes dictionary as
  `[{ id, name, symbol, description }]`.
- `GET /measures` returns the complete measures dictionary as
  `[{ id, name, description }]`.

These are separate endpoints so a consumer can fetch only the dictionary it needs.
Both follow all upstream pages and use a shared, in-memory 24-hour cache per backend
process. Concurrent cold reads of a dictionary fetch it only once. Failed fetches
are not cached.

**Breaking contract change:** `GET /data/by-variable/{variable_id}` now returns an
object instead of a bare `UnitData[]` array:

```json
{
  "measureUnit": { "id": 26, "name": "person" },
  "lastUpdate": null,
  "units": [
    {
      "unitId": "011200000000",
      "unitName": "Example region",
      "values": [
        {
          "year": 2023,
          "value": 12.5,
          "attributeId": 9,
          "attributeName": "value",
          "attributeDescription": "Preliminary estimate",
          "attributeSymbol": "s"
        }
      ]
    }
  ]
}
```

The names and descriptions above are illustrative English translations. Upstream
dictionary text is returned unchanged in the client's configured language
(currently Polish). Attribute names alone can be ambiguous (`"0"` or `"value"`),
so consumers should read the description and symbol as well. Blank symbols and
empty descriptions are valid and preserved.

The data service resolves both dictionaries in the backend using the same cache as
the dictionary endpoints: there are no per-value or per-measure-ID BDL requests,
and the frontend does not need additional dictionary requests. With the current
dictionary sizes, a cold cache costs one request per dictionary per 24 hours;
future larger dictionaries may require more pages. Data responses retain their
existing one-hour cache and concurrent-fetch sharing.

`measureUnit.id` and `lastUpdate` come from the first upstream data page, even when
`units` is empty. A missing or null `lastUpdate` becomes null; a missing/invalid
`measureUnitId` produces HTTP 502. An unknown attribute keeps its ID and raw value,
with null name, description and symbol. An unknown measure keeps its ID with a
null name. Both unknown-ID cases emit warnings rather than guessing meanings.
Dictionary failures propagate as upstream errors (HTTP 429 for rate limits,
HTTP 502 for unavailable/invalid dictionaries).

`BdlClient.get_all()` still returns only the combined results list for existing
services. `get_all_with_metadata()` returns the combined results and the first
page's non-results fields, with the same pagination and `single_page` checks.
Page-specific fields such as `links` in that metadata still describe the first
page, not the combined collection.

## Tests

```bash
poetry install --with dev
poetry run pytest
poetry run ruff check .
poetry run ruff format --check .
```

Python 3.12 is the supported development version.
