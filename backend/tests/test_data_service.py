import asyncio

import httpx
import pytest
from fastapi.testclient import TestClient

from app.bdl_client import BdlClient
from app.data_service import DataService
from app.errors import BdlPageLimitError, BdlUpstreamError
from app.main import app
from app.routers.data import get_data_service


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


@pytest.mark.anyio
async def test_parent_filter_is_forwarded_and_cached_separately():
    service, requests = _service(_ok)

    await service.get_data_by_variable(1, [2020], 6, "011200000000")
    await service.get_data_by_variable(1, [2020], 6, "011200000000")
    await service.get_data_by_variable(1, [2020], 6, "012400000000")

    assert len(requests) == 4
    assert all(r.url.params["unit-level"] == "6" for r in requests)
    assert [r.url.params["unit-parent-id"] for r in requests] == [
        "011200000000",
        "011200000000",
        "012400000000",
        "012400000000",
    ]


@pytest.mark.anyio
@pytest.mark.parametrize("total", [100, 101])
async def test_single_page_limit_never_fetches_another_page(total):
    def handler(request: httpx.Request) -> httpx.Response:
        items = [{"id": str(i), "name": "x", "values": []} for i in range(100)]
        return httpx.Response(200, json={"totalRecords": total, "results": items})

    service, requests = _service(handler)
    if total == 100:
        assert len(await service.get_data_by_variable(1, [2020], 3, None, True)) == 100
        await service.get_data_by_variable(1, [2020], 3, None, True)
    else:
        with pytest.raises(BdlPageLimitError):
            await service.get_data_by_variable(1, [2020], 3, None, True)
    assert len(requests) == 1
    assert requests[0].url.params["page"] == "0"
    assert requests[0].url.params["page-size"] == "100"


@pytest.mark.anyio
async def test_single_page_requires_a_valid_total_and_does_not_share_unlimited_fetch():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"results": [{"id": "1", "name": "x", "values": []}]}
        )

    service, requests = _service(handler)
    assert len(await service.get_data_by_variable(1, [2020], 3)) == 1
    with pytest.raises(BdlUpstreamError):
        await service.get_data_by_variable(1, [2020], 3, None, True)
    assert len(requests) == 2


def test_data_route_reports_single_page_limit():
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "totalRecords": 101,
                "results": [{"id": "1", "name": "x", "values": []}],
            },
        )

    http = httpx.AsyncClient(
        base_url="https://bdl.test", transport=httpx.MockTransport(handler)
    )
    app.dependency_overrides[get_data_service] = lambda: DataService(BdlClient(http))
    try:
        with TestClient(app) as client:
            response = client.get(
                "/data/by-variable/1?year=2021&unit_level=3&single_page=true"
            )
        assert response.status_code == 409
        assert "Select a voivodeship" in response.json()["detail"]
        assert len(requests) == 1
    finally:
        app.dependency_overrides.pop(get_data_service)


def test_data_route_passes_territorial_filter():
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"totalRecords": 0, "results": []})

    http = httpx.AsyncClient(
        base_url="https://bdl.test", transport=httpx.MockTransport(handler)
    )
    app.dependency_overrides[get_data_service] = lambda: DataService(BdlClient(http))
    try:
        with TestClient(app) as client:
            response = client.get(
                "/data/by-variable/1",
                params={
                    "year": 2021,
                    "unit_level": 6,
                    "unit_parent_id": "011212001000",
                },
            )
        assert response.status_code == 200
        assert requests[0].url.params["unit-parent-id"] == "011212001000"
    finally:
        app.dependency_overrides.pop(get_data_service)
