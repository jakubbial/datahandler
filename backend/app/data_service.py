import time
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.bdl_client import BdlClient
from app.monitoring import log_cache

CACHE_TTL_SECONDS = 60 * 60
CACHE_MAX_ENTRIES = 500

CacheKey = tuple[int, tuple[int, ...], int | None, str | None]


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

    async def get_data_by_variable(
        self,
        variable_id: int,
        years: list[int],
        unit_level: int | None = None,
        unit_parent_id: str | None = None,
    ) -> list[UnitData]:
        unique_years = sorted(set(years))
        key: CacheKey = (variable_id, tuple(unique_years), unit_level, unit_parent_id)

        cached = self._cache.get(key)
        if cached is not None and cached[0] > time.monotonic():
            log_cache("data", "hit", key)
            return cached[1]
        log_cache("data", "expired" if cached is not None else "miss", key)

        params: dict[str, Any] = {"year": unique_years}
        if unit_level is not None:
            params["unit-level"] = unit_level
        if unit_parent_id:
            params["unit-parent-id"] = unit_parent_id

        raw_items = await self._client.get_all(
            f"/data/by-variable/{variable_id}", params
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
