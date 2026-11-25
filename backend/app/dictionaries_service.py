import asyncio
import time

from pydantic import BaseModel, ValidationError

from app.bdl_client import BdlClient
from app.errors import BdlNotFoundError, BdlUpstreamError
from app.monitoring import log_cache

CACHE_TTL_SECONDS = 24 * 60 * 60


class Measure(BaseModel):
    id: int
    name: str
    description: str


class Attribute(BaseModel):
    id: int
    name: str
    symbol: str
    description: str


class DictionariesService:
    def __init__(self, client: BdlClient, ttl_seconds: float = CACHE_TTL_SECONDS):
        self._client = client
        self._ttl = ttl_seconds
        self._attributes: dict[str, tuple[float, list[Attribute]]] = {}
        self._measures: dict[str, tuple[float, list[Measure]]] = {}
        self._locks = {"/attributes": asyncio.Lock(), "/measures": asyncio.Lock()}

    async def get_attributes(self) -> list[Attribute]:
        return await self._get("/attributes", Attribute, self._attributes)

    async def get_measures(self) -> list[Measure]:
        return await self._get("/measures", Measure, self._measures)

    async def _get[T: BaseModel](
        self,
        path: str,
        model: type[T],
        cache: dict[str, tuple[float, list[T]]],
    ) -> list[T]:
        # Recheck the cache under the lock so concurrent cold reads fetch only once.
        async with self._locks[path]:
            cached = cache.get(path)
            if cached is not None and cached[0] > time.monotonic():
                log_cache(path.removeprefix("/"), "hit", None)
                return cached[1]
            log_cache(
                path.removeprefix("/"),
                "expired" if cached is not None else "miss",
                None,
            )
            try:
                items = await self._client.get_all(path)
            except BdlNotFoundError as exc:
                raise BdlUpstreamError("BDL dictionary not found") from exc
            try:
                entries = [model.model_validate(item) for item in items]
            except ValidationError as exc:
                raise BdlUpstreamError("BDL returned an invalid dictionary") from exc
            cache[path] = (time.monotonic() + self._ttl, entries)
            return entries
