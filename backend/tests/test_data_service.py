import asyncio

import httpx
import pytest
from fastapi.testclient import TestClient

from app.bdl_client import BdlClient
from app.data_service import DataService
from app.dictionaries_service import DictionariesService
from app.errors import BdlPageLimitError, BdlUpstreamError
from app.main import app
from app.routers.data import get_data_service


def _dictionary_response(request: httpx.Request) -> httpx.Response | None:
    if request.url.path == "/attributes":
        return httpx.Response(
            200,
            json={
                "totalRecords": 2,
                "results": [
                    {"id": 0, "name": "0", "symbol": " ", "description": ""},
                    {
                        "id": 9,
                        "name": "value",
                        "symbol": "s",
                        "description": "Preliminary estimate",
                    },
                ],
            },
        )
    if request.url.path == "/measures":
        return httpx.Response(
            200,
            json={
                "totalRecords": 1,
                "results": [{"id": 26, "name": "person", "description": "person"}],
            },
        )
    return None


def _service(handler) -> tuple[DataService, list[httpx.Request]]:
    requests: list[httpx.Request] = []

    async def record(request: httpx.Request) -> httpx.Response:
        dictionary = _dictionary_response(request)
        if dictionary is not None:
            return dictionary
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
    return httpx.Response(
        200, json={"totalRecords": 2, "measureUnitId": 26, "results": [item]}
    )


@pytest.mark.anyio
async def test_concurrent_identical_requests_share_one_fetch():
    service, requests = _service(_ok)

    results = await asyncio.gather(
        *(service.get_data_by_variable(1, [2020], 5) for _ in range(3))
    )

    assert len(requests) == 2  # two pages, fetched once
    assert all(len(r.units) == 2 for r in results)
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
    assert len((await service.get_data_by_variable(1, [2020])).units) == 2


@pytest.mark.anyio
async def test_cancelled_caller_does_not_abort_shared_fetch():
    service, requests = _service(_ok)

    first = asyncio.create_task(service.get_data_by_variable(1, [2020]))
    await asyncio.sleep(0)
    second = asyncio.create_task(service.get_data_by_variable(1, [2020]))
    await asyncio.sleep(0)
    first.cancel()

    assert len((await second).units) == 2
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
        return httpx.Response(
            200, json={"totalRecords": total, "measureUnitId": 26, "results": items}
        )

    service, requests = _service(handler)
    if total == 100:
        data = await service.get_data_by_variable(1, [2020], 3, None, True)
        assert len(data.units) == 100
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
            200,
            json={
                "measureUnitId": 26,
                "results": [{"id": "1", "name": "x", "values": []}],
            },
        )

    service, requests = _service(handler)
    assert len((await service.get_data_by_variable(1, [2020], 3)).units) == 1
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
        dictionary = _dictionary_response(request)
        if dictionary is not None:
            return dictionary
        requests.append(request)
        return httpx.Response(
            200, json={"totalRecords": 0, "measureUnitId": 26, "results": []}
        )

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
        assert response.json() == {
            "measureUnit": {"id": 26, "name": "person"},
            "lastUpdate": None,
            "units": [],
        }
        assert requests[0].url.params["unit-parent-id"] == "011212001000"
    finally:
        app.dependency_overrides.pop(get_data_service)


@pytest.mark.anyio
@pytest.mark.parametrize("last_update", [None, "2026-05-08T13:36:47.723"])
async def test_data_metadata_and_attribute_mapping(last_update, caplog):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "totalRecords": 1,
                "measureUnitId": 26,
                "lastUpdate": last_update,
                "results": [
                    {
                        "id": "011200000000",
                        "name": " Region ",
                        "values": [
                            {"year": "2021", "val": 0, "attrId": 0},
                            {"year": "2022", "val": 12.5, "attrId": 9},
                            {"year": "2023", "val": None, "attrId": 999},
                        ],
                    }
                ],
            },
        )

    service, _ = _service(handler)
    data = (await service.get_data_by_variable(1, [2021, 2022, 2023])).model_dump(
        by_alias=True
    )

    assert data == {
        "measureUnit": {"id": 26, "name": "person"},
        "lastUpdate": last_update,
        "units": [
            {
                "unitId": "011200000000",
                "unitName": "Region",
                "values": [
                    {
                        "year": 2021,
                        "value": 0.0,
                        "attributeId": 0,
                        "attributeName": "0",
                        "attributeDescription": "",
                        "attributeSymbol": " ",
                    },
                    {
                        "year": 2022,
                        "value": 12.5,
                        "attributeId": 9,
                        "attributeName": "value",
                        "attributeDescription": "Preliminary estimate",
                        "attributeSymbol": "s",
                    },
                    {
                        "year": 2023,
                        "value": None,
                        "attributeId": 999,
                        "attributeName": None,
                        "attributeDescription": None,
                        "attributeSymbol": None,
                    },
                ],
            }
        ],
    }
    assert "bdl_unknown_attribute id=999" in caplog.text


@pytest.mark.anyio
async def test_unknown_measure_preserves_id_and_logs_warning(caplog):
    service, _ = _service(
        lambda request: httpx.Response(
            200, json={"measureUnitId": 999, "totalRecords": 0, "results": []}
        )
    )

    data = await service.get_data_by_variable(1, [2021])

    assert data.measure_unit.id == 999
    assert data.measure_unit.name is None
    assert "bdl_unknown_measure id=999" in caplog.text


@pytest.mark.anyio
async def test_missing_measure_metadata_is_an_upstream_error():
    service, _ = _service(
        lambda request: httpx.Response(200, json={"totalRecords": 0, "results": []})
    )

    with pytest.raises(BdlUpstreamError, match="invalid data metadata"):
        await service.get_data_by_variable(1, [2021])


@pytest.mark.anyio
async def test_data_and_dictionary_reads_reuse_the_same_cache():
    paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        dictionary = _dictionary_response(request)
        if dictionary is not None:
            return dictionary
        return httpx.Response(
            200, json={"measureUnitId": 26, "totalRecords": 0, "results": []}
        )

    async with httpx.AsyncClient(
        base_url="https://bdl.test", transport=httpx.MockTransport(handler)
    ) as http:
        client = BdlClient(http)
        dictionaries = DictionariesService(client)
        service = DataService(client, dictionaries=dictionaries)
        await dictionaries.get_attributes()
        await service.get_data_by_variable(1, [2021])
        await service.get_data_by_variable(2, [2022])
        await dictionaries.get_measures()

    assert paths.count("/attributes") == 1
    assert paths.count("/measures") == 1
    assert paths.count("/data/by-variable/1") == 1
    assert paths.count("/data/by-variable/2") == 1
