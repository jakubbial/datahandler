import time
from typing import Any

from pydantic import BaseModel

from app.bdl_client import BdlClient


class Unit(BaseModel):
    id: str
    name: str


class UnitsService:
    def __init__(self, client: BdlClient, ttl_seconds: float = 24 * 60 * 60):
        self._client = client
        self._ttl = ttl_seconds
        self._cache: dict[tuple[int, str | None], tuple[float, list[Unit]]] = {}

    async def get_units(self, level: int, parent_id: str | None) -> list[Unit]:
        key = (level, parent_id)
        cached = self._cache.get(key)
        if cached is not None and cached[0] > time.monotonic():
            return cached[1]

        params: dict[str, Any] = {"level": level, "sort": "Name"}
        if parent_id is not None:
            params["parent-id"] = parent_id
        items = await self._client.get_all("/units", params)
        units = [Unit(id=item["id"], name=item["name"].strip()) for item in items]
        self._cache[key] = (time.monotonic() + self._ttl, units)
        return units
