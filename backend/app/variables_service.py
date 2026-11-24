import time
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.bdl_client import BdlClient

CACHE_TTL_SECONDS = 24 * 60 * 60
NAME_SEPARATOR = " - "


class Variable(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str
    n1: str | None = None
    n2: str | None = None
    n3: str | None = None
    n4: str | None = None
    n5: str | None = None
    level: int
    measure_unit_id: int = Field(alias="measureUnitId")
    measure_unit_name: str | None = Field(alias="measureUnitName")


class VariableDetails(Variable):
    subject_id: str | None = Field(alias="subjectId")
    description: str | None = None
    years: list[int]


class VariablesService:
    def __init__(self, client: BdlClient, ttl_seconds: float = CACHE_TTL_SECONDS):
        self._client = client
        self._ttl = ttl_seconds
        self._cache: dict[str, tuple[float, list[Variable]]] = {}
        self._details_cache: dict[int, tuple[float, VariableDetails]] = {}

    async def get_variables(self, subject_id: str) -> list[Variable]:
        cached = self._cache.get(subject_id)
        if cached is not None and cached[0] > time.monotonic():
            return cached[1]

        raw_items = await self._client.get_all(
            "/variables", {"subject-id": subject_id, "sort": "Id"}
        )
        variables = [self._simplify(item) for item in raw_items]
        self._cache[subject_id] = (time.monotonic() + self._ttl, variables)
        return variables

    async def get_variable(self, variable_id: int) -> VariableDetails:
        cached = self._details_cache.get(variable_id)
        if cached is not None and cached[0] > time.monotonic():
            return cached[1]

        item = await self._client.get_one(f"/variables/{variable_id}")
        details = self._simplify_details(item)
        self._details_cache[variable_id] = (time.monotonic() + self._ttl, details)
        return details

    @staticmethod
    def _base_fields(item: dict[str, Any]) -> dict[str, Any]:
        dimensions = [(item.get(f"n{i}") or "").strip() or None for i in range(1, 6)]
        return {
            "id": item["id"],
            "name": NAME_SEPARATOR.join(d for d in dimensions if d),
            "n1": dimensions[0],
            "n2": dimensions[1],
            "n3": dimensions[2],
            "n4": dimensions[3],
            "n5": dimensions[4],
            "level": item["level"],
            "measureUnitId": item["measureUnitId"],
            "measureUnitName": item.get("measureUnitName"),
        }

    @classmethod
    def _simplify(cls, item: dict[str, Any]) -> Variable:
        return Variable.model_validate(cls._base_fields(item))

    @classmethod
    def _simplify_details(cls, item: dict[str, Any]) -> VariableDetails:
        return VariableDetails.model_validate(
            {
                **cls._base_fields(item),
                "subjectId": item.get("subjectId"),
                "description": (item.get("description") or "").strip() or None,
                "years": sorted(item.get("years") or []),
            }
        )
