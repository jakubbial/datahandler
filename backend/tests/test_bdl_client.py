import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.bdl_client import BdlClient


@pytest.mark.parametrize(
    ("client_id", "expected"), [(" test-key ", "test-key"), ("", None)]
)
def test_bdl_client_id_header_comes_from_environment(monkeypatch, client_id, expected):
    monkeypatch.setenv("BDL_MONITORING", "0")
    monkeypatch.setenv("BDL_CLIENT_ID", client_id)

    with TestClient(app):
        headers = app.state.bdl_client._http.headers

        assert headers.get("X-ClientId") == expected


@pytest.mark.anyio
async def test_paginated_metadata_comes_from_first_page_and_get_all_stays_a_list():
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        page = int(request.url.params["page"])
        return httpx.Response(
            200,
            json={
                "totalRecords": 2,
                "variableId": 3643,
                "measureUnitId": 26 if page == 0 else 999,
                "aggregateId": 1,
                "lastUpdate": None if page == 0 else "later-page",
                "results": [{"id": page}],
            },
        )

    async with httpx.AsyncClient(
        base_url="https://bdl.test", transport=httpx.MockTransport(handler)
    ) as http:
        client = BdlClient(http)
        collection = await client.get_all_with_metadata("/data/by-variable/3643")
        assert collection.metadata == {
            "totalRecords": 2,
            "variableId": 3643,
            "measureUnitId": 26,
            "aggregateId": 1,
            "lastUpdate": None,
        }
        assert collection.results == [{"id": 0}, {"id": 1}]
        assert [r.url.params["page"] for r in requests] == ["0", "1"]
        assert await client.get_all("/subjects") == [{"id": 0}, {"id": 1}]
