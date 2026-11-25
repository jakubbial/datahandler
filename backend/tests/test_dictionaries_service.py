import asyncio
from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient

from app.bdl_client import BdlClient
from app.dictionaries_service import DictionariesService
from app.errors import BdlUpstreamError
from app.main import app
from app.routers.dictionaries import get_dictionaries_service


@pytest.mark.anyio
async def test_dictionary_pages_are_cached_and_concurrent_reads_share_fetch(
    monkeypatch,
):
    now = 100.0
    monkeypatch.setattr(
        "app.dictionaries_service.time", SimpleNamespace(monotonic=lambda: now)
    )
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        await asyncio.sleep(0)
        page = int(request.url.params["page"])
        item = {"id": page, "name": "value", "description": ""}
        if request.url.path == "/attributes":
            item["symbol"] = " "
        return httpx.Response(200, json={"totalRecords": 2, "results": [item]})

    async with httpx.AsyncClient(
        base_url="https://bdl.test", transport=httpx.MockTransport(handler)
    ) as http:
        service = DictionariesService(BdlClient(http), ttl_seconds=10)
        results = await asyncio.gather(*(service.get_attributes() for _ in range(3)))
        assert all([a.id for a in result] == [0, 1] for result in results)
        assert len(requests) == 2
        assert results[0][0].symbol == " "

        await service.get_measures()
        await service.get_attributes()
        await service.get_measures()
        assert len(requests) == 4
        now = 110
        await service.get_attributes()
        await service.get_measures()
        assert len(requests) == 8
        assert [r.url.path for r in requests].count("/attributes") == 4
        assert [r.url.path for r in requests].count("/measures") == 4


@pytest.mark.anyio
@pytest.mark.parametrize("failure", [500, 404, "invalid"])
async def test_failed_dictionary_fetch_is_not_cached(failure):
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return (
                httpx.Response(200, json={"results": [{"id": 1}]})
                if failure == "invalid"
                else httpx.Response(failure)
            )
        return httpx.Response(200, json={"totalRecords": 0, "results": []})

    async with httpx.AsyncClient(
        base_url="https://bdl.test", transport=httpx.MockTransport(handler)
    ) as http:
        service = DictionariesService(BdlClient(http))
        with pytest.raises(BdlUpstreamError):
            await service.get_attributes()
        assert await service.get_attributes() == []
        assert calls == 2


def test_dictionary_endpoints_return_complete_fields():
    def handler(request: httpx.Request) -> httpx.Response:
        item = {"id": 1, "name": "value", "description": "Explanation"}
        if request.url.path == "/attributes":
            item["symbol"] = "s"
        return httpx.Response(200, json={"totalRecords": 1, "results": [item]})

    http = httpx.AsyncClient(
        base_url="https://bdl.test", transport=httpx.MockTransport(handler)
    )
    service = DictionariesService(BdlClient(http))
    app.dependency_overrides[get_dictionaries_service] = lambda: service
    try:
        with TestClient(app) as client:
            assert client.get("/attributes").json() == [
                {"id": 1, "name": "value", "description": "Explanation", "symbol": "s"}
            ]
            assert client.get("/measures").json() == [
                {"id": 1, "name": "value", "description": "Explanation"}
            ]
    finally:
        app.dependency_overrides.pop(get_dictionaries_service)
