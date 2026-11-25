import asyncio
import time
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.bdl_client import BdlClient
from app.monitoring import log_cache

CACHE_TTL_SECONDS = 60 * 60
CACHE_MAX_ENTRIES = 500

CacheKey = tuple[int, tuple[int, ...], int | None, str | None, bool]


class DataValue(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    year: int
    value: float | None
    attribute_id: int = Field(alias="attributeId")


class UnitData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    unit_id: str = Field(alias="unitId")
    unit_name: str = Field(alias="unitName")
    values: list[DataValue]


class DataService:
    def __init__(
        self,
        client: BdlClient,
        ttl_seconds: float = CACHE_TTL_SECONDS,
        max_entries: int = CACHE_MAX_ENTRIES,
    ):
        self._client = client
        self._ttl = ttl_seconds
        self._max_entries = max_entries
        self._cache: dict[CacheKey, tuple[float, list[UnitData]]] = {}
        self._inflight: dict[CacheKey, asyncio.Task[list[UnitData]]] = {}

    async def get_data_by_variable(
        self,
        variable_id: int,
        years: list[int],
        unit_level: int | None = None,
        unit_parent_id: str | None = None,
        single_page: bool = False,
    ) -> list[UnitData]:
        unique_years = sorted(set(years))
        key: CacheKey = (
            variable_id,
            tuple(unique_years),
            unit_level,
            unit_parent_id,
            single_page,
        )

        cached = self._cache.get(key)
        if cached is not None and cached[0] > time.monotonic():
            log_cache("data", "hit", key)
            return cached[1]

        inflight = self._inflight.get(key)
        if inflight is not None:
            log_cache("data", "shared", key)
        else:
            log_cache("data", "expired" if cached is not None else "miss", key)
            inflight = asyncio.create_task(self._fetch(key, unique_years))
            self._inflight[key] = inflight
            inflight.add_done_callback(lambda task: self._finish(key, task))

        # Shielded so a cancelled caller does not abort the fetch shared by others.
        return await asyncio.shield(inflight)

    def _finish(self, key: CacheKey, task: asyncio.Task[list[UnitData]]) -> None:
        if self._inflight.get(key) is task:
            del self._inflight[key]
        if not task.cancelled():
            task.exception()  # Mark as retrieved when every caller was cancelled.

    async def _fetch(self, key: CacheKey, years: list[int]) -> list[UnitData]:
        variable_id, _, unit_level, unit_parent_id, single_page = key
        params: dict[str, Any] = {"year": years}
        if unit_level is not None:
            params["unit-level"] = unit_level
        if unit_parent_id:
            params["unit-parent-id"] = unit_parent_id

        raw_items = await self._client.get_all(
            f"/data/by-variable/{variable_id}", params, single_page=single_page
        )
        data = [self._simplify(item) for item in raw_items]

        if key not in self._cache and len(self._cache) >= self._max_entries:
            # Drop the oldest inserted entry (dicts keep insertion order).
            del self._cache[next(iter(self._cache))]
        self._cache[key] = (time.monotonic() + self._ttl, data)
        return data

    @staticmethod
    def _simplify(item: dict[str, Any]) -> UnitData:
        return UnitData.model_validate(
            {
                "unitId": item["id"],
                "unitName": item["name"].strip(),
                "values": [
                    {
                        "year": int(v["year"]),
                        "value": v.get("val"),
                        "attributeId": v["attrId"],
                    }
                    for v in item.get("values") or []
                ],
            }
        )
