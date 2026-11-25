import time
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.bdl_client import BdlClient
from app.monitoring import log_cache

CACHE_TTL_SECONDS = 24 * 60 * 60


class Subject(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    parent_id: str | None = Field(alias="parentId")
    name: str
    has_variables: bool = Field(alias="hasVariables")
    levels: list[int]


class SubjectsService:
    def __init__(self, client: BdlClient, ttl_seconds: float = CACHE_TTL_SECONDS):
        self._client = client
        self._ttl = ttl_seconds
        self._cache: dict[str | None, tuple[float, list[Subject]]] = {}

    async def get_subjects(self, parent_id: str | None = None) -> list[Subject]:
        cached = self._cache.get(parent_id)
        if cached is not None and cached[0] > time.monotonic():
            log_cache("subjects", "hit", parent_id)
            return cached[1]
        log_cache("subjects", "expired" if cached is not None else "miss", parent_id)

        params: dict[str, Any] = {"sort": "Name"}
        if parent_id:
            params["parent-id"] = parent_id
        raw_items = await self._client.get_all("/subjects", params)

        subjects = [self._simplify(item) for item in raw_items]
        self._cache[parent_id] = (time.monotonic() + self._ttl, subjects)
        return subjects

    @staticmethod
    def _simplify(item: dict[str, Any]) -> Subject:
        return Subject.model_validate(
            {
                "id": item["id"],
                "parentId": item.get("parentId"),
                "name": item["name"].strip(),
                "hasVariables": item["hasVariables"],
                "levels": item.get("levels") or [],
            }
        )
