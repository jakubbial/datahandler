import time
from typing import Any

import httpx

from app.errors import BdlRateLimitError, BdlUpstreamError, BdlNotFoundError
from app.monitoring import logger

BDL_BASE_URL = "https://bdl.stat.gov.pl/api/v1"
BDL_TIMEOUT_SECONDS = 10.0
PAGE_SIZE = 100

_BASE_PARAMS: dict[str, Any] = {
    "lang": "pl",
    "format": "json",
}


class BdlClient:
    def __init__(self, http: httpx.AsyncClient) -> None:
        self._http = http

    async def get_all(
        self, path: str, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Fetch every page of a paginated BDL resource and return all results."""
        results: list[dict[str, Any]] = []
        page = 0
        while True:
            data = await self._get_json(
                path, {**(params or {}), "page-size": PAGE_SIZE, "page": page}
            )
            items = data.get("results") or []
            results.extend(items)
            total = data.get("totalRecords")
            if not items or total is None or len(results) >= total:
                return results
            page += 1

    async def get_one(
        self, path: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Fetch a single (non-paginated) BDL resource."""
        return await self._get_json(path, params or {})

    async def _get_json(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        started = time.perf_counter()
        try:
            response = await self._http.get(path, params={**_BASE_PARAMS, **params})
        except httpx.HTTPError as exc:  # includes timeouts and network errors
            logger.info(
                "bdl_request path=%s params=%s status=error duration_ms=%.0f",
                path,
                params,
                (time.perf_counter() - started) * 1000,
            )
            raise BdlUpstreamError("BDL request failed") from exc
        logger.info(
            "bdl_request path=%s params=%s status=%s duration_ms=%.0f",
            path,
            params,
            response.status_code,
            (time.perf_counter() - started) * 1000,
        )

        if response.status_code == 404:
            raise BdlNotFoundError("BDL resource not found")
        if response.status_code == 429:
            raise BdlRateLimitError("BDL rate limit exceeded")
        if response.is_error:
            raise BdlUpstreamError(f"BDL returned HTTP {response.status_code}")

        try:
            data = response.json()
        except ValueError as exc:
            raise BdlUpstreamError("BDL returned invalid JSON") from exc
        if not isinstance(data, dict):
            raise BdlUpstreamError("BDL returned an unexpected response")
        return data
