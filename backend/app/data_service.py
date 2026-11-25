import asyncio
import time
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.bdl_client import BdlClient
from app.dictionaries_service import Attribute, DictionariesService
from app.errors import BdlUpstreamError
from app.monitoring import log_cache, logger

CACHE_TTL_SECONDS = 60 * 60
CACHE_MAX_ENTRIES = 500

CacheKey = tuple[int, tuple[int, ...], int | None, str | None, bool]


class DataValue(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    year: int
    value: float | None
    attribute_id: int = Field(alias="attributeId")
    attribute_name: str | None = Field(alias="attributeName")
    attribute_description: str | None = Field(alias="attributeDescription")
    attribute_symbol: str | None = Field(alias="attributeSymbol")


class UnitData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    unit_id: str = Field(alias="unitId")
    unit_name: str = Field(alias="unitName")
    values: list[DataValue]


class MeasureUnit(BaseModel):
    id: int
    name: str | None


class VariableData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    measure_unit: MeasureUnit = Field(alias="measureUnit")
    last_update: str | None = Field(alias="lastUpdate")
    units: list[UnitData]


class _DataMetadata(BaseModel):
    measure_unit_id: int = Field(alias="measureUnitId")
    last_update: str | None = Field(default=None, alias="lastUpdate")


class DataService:
    def __init__(
        self,
        client: BdlClient,
        ttl_seconds: float = CACHE_TTL_SECONDS,
        max_entries: int = CACHE_MAX_ENTRIES,
        *,
        dictionaries: DictionariesService | None = None,
    ):
        self._client = client
        self._dictionaries = dictionaries or DictionariesService(client)
        self._ttl = ttl_seconds
        self._max_entries = max_entries
        self._cache: dict[CacheKey, tuple[float, VariableData]] = {}
        self._inflight: dict[CacheKey, asyncio.Task[VariableData]] = {}

    async def get_data_by_variable(
        self,
        variable_id: int,
        years: list[int],
        unit_level: int | None = None,
        unit_parent_id: str | None = None,
        single_page: bool = False,
    ) -> VariableData:
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

    def _finish(self, key: CacheKey, task: asyncio.Task[VariableData]) -> None:
        if self._inflight.get(key) is task:
            del self._inflight[key]
        if not task.cancelled():
            task.exception()  # Mark as retrieved when every caller was cancelled.

    async def _fetch(self, key: CacheKey, years: list[int]) -> VariableData:
        variable_id, _, unit_level, unit_parent_id, single_page = key
        params: dict[str, Any] = {"year": years}
        if unit_level is not None:
            params["unit-level"] = unit_level
        if unit_parent_id:
            params["unit-parent-id"] = unit_parent_id

        collection = await self._client.get_all_with_metadata(
            f"/data/by-variable/{variable_id}", params, single_page=single_page
        )
        try:
            metadata = _DataMetadata.model_validate(collection.metadata)
        except ValidationError as exc:
            raise BdlUpstreamError("BDL returned invalid data metadata") from exc

        attribute_items, measures = await asyncio.gather(
            self._dictionaries.get_attributes(), self._dictionaries.get_measures()
        )
        attributes = {attribute.id: attribute for attribute in attribute_items}
        measure = next(
            (item for item in measures if item.id == metadata.measure_unit_id), None
        )
        if measure is None:
            logger.warning("bdl_unknown_measure id=%s", metadata.measure_unit_id)
        units = [self._simplify(item, attributes) for item in collection.results]
        unknown_attributes = {
            value.attribute_id
            for unit in units
            for value in unit.values
            if value.attribute_id not in attributes
        }
        for attribute_id in sorted(unknown_attributes):
            logger.warning("bdl_unknown_attribute id=%s", attribute_id)
        data = VariableData(
            measure_unit=MeasureUnit(
                id=metadata.measure_unit_id,
                name=measure.name if measure is not None else None,
            ),
            last_update=metadata.last_update,
            units=units,
        )

        if key not in self._cache and len(self._cache) >= self._max_entries:
            # Drop the oldest inserted entry (dicts keep insertion order).
            del self._cache[next(iter(self._cache))]
        self._cache[key] = (time.monotonic() + self._ttl, data)
        return data

    @staticmethod
    def _simplify(item: dict[str, Any], attributes: dict[int, Attribute]) -> UnitData:
        values = []
        for value in item.get("values") or []:
            attribute = attributes.get(value["attrId"])
            values.append(
                DataValue(
                    year=int(value["year"]),
                    value=value.get("val"),
                    attribute_id=value["attrId"],
                    attribute_name=attribute.name if attribute is not None else None,
                    attribute_description=(
                        attribute.description if attribute is not None else None
                    ),
                    attribute_symbol=attribute.symbol
                    if attribute is not None
                    else None,
                )
            )
        return UnitData.model_validate(
            {
                "unitId": item["id"],
                "unitName": item["name"].strip(),
                "values": values,
            }
        )
