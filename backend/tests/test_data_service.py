import asyncio

import httpx
import pytest

from app.bdl_client import BdlClient
from app.data_service import DataService
from app.errors import BdlUpstreamError


def _service(handler) -> tuple[DataService, list[httpx.Request]]:
    requests: list[httpx.Request] = []

    async def record(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        await asyncio.sleep(0.01)
        return handler(request)

    http = httpx.AsyncClient(
        base_url="https://bdl.test", transport=httpx.MockTransport(record)
    )
    return DataService(BdlClient(http)), requests


def _ok(request: httpx.Request) -> httpx.Response:
    page = int(request.url.params["page"])
    item = {"id": f"U{page}", "name": "x", "values": []}
    return httpx.Response(200, json={"totalRecords": 2, "results": [item]})


@pytest.mark.anyio
async def test_concurrent_identical_requests_share_one_fetch():
    service, requests = _service(_ok)

    results = await asyncio.gather(
        *(service.get_data_by_variable(1, [2020], 5) for _ in range(3))
    )

    assert len(requests) == 2  # two pages, fetched once
    assert all(len(r) == 2 for r in results)
    await service.get_data_by_variable(1, [2020], 5)
    assert len(requests) == 2  # served from cache


@pytest.mark.anyio
async def test_failed_fetch_is_not_cached_and_is_retried():
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(500)
        return _ok(request)

    service, _ = _service(handler)

    with pytest.raises(BdlUpstreamError):
        await service.get_data_by_variable(1, [2020])
    assert len(await service.get_data_by_variable(1, [2020])) == 2


@pytest.mark.anyio
async def test_cancelled_caller_does_not_abort_shared_fetch():
    service, requests = _service(_ok)

    first = asyncio.create_task(service.get_data_by_variable(1, [2020]))
    await asyncio.sleep(0)
    second = asyncio.create_task(service.get_data_by_variable(1, [2020]))
    await asyncio.sleep(0)
    first.cancel()

    assert len(await second) == 2
    assert len(requests) == 2
