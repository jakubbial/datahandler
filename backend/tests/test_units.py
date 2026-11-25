from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi.testclient import TestClient

from app.bdl_client import BdlClient
from app.main import app
from app.routers.units import get_units_service
from app.units_service import Unit, UnitsService


@pytest.mark.anyio
async def test_units_are_filtered_upstream_and_cached_per_parent():
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={"totalRecords": 1, "results": [{"id": "1", "name": " Unit "}]},
        )

    async with httpx.AsyncClient(
        base_url="https://bdl.test", transport=httpx.MockTransport(handler)
    ) as http:
        service = UnitsService(BdlClient(http))
        units = await service.get_units(2, None)
        await service.get_units(2, None)
        await service.get_units(5, "011200000000")
        await service.get_units(5, "012400000000")

    assert units[0].name == "Unit"
    assert len(requests) == 3
    assert requests[0].url.params["level"] == "2"
    assert "parent-id" not in requests[0].url.params
    assert requests[1].url.params["parent-id"] == "011200000000"
    assert requests[1].url.params["level"] == "5"
    assert requests[2].url.params["parent-id"] == "012400000000"


@pytest.mark.parametrize(
    ("query", "level", "parent_id"),
    [
        ("level=2", 2, None),
        ("level=5&parent_id=011200000000", 5, "011200000000"),
    ],
)
def test_units_route_accepts_valid_filters(query, level, parent_id):
    service = AsyncMock(spec=UnitsService)
    service.get_units.return_value = [Unit(id="011200000000", name="Example")]
    app.dependency_overrides[get_units_service] = lambda: service
    try:
        with TestClient(app) as client:
            response = client.get(f"/units?{query}")
        assert response.status_code == 200
        assert response.json() == [{"id": "011200000000", "name": "Example"}]
        service.get_units.assert_awaited_once_with(level, parent_id)
    finally:
        app.dependency_overrides.pop(get_units_service)


def test_units_route_rejects_unbounded_county_requests():
    app.dependency_overrides[get_units_service] = lambda: None
    try:
        with TestClient(app) as client:
            assert client.get("/units?level=5").status_code == 422
            assert client.get("/units?level=3").status_code == 422
            assert client.get("/units?level=6").status_code == 422
            assert (
                client.get("/units?level=2&parent_id=011200000000").status_code == 422
            )
            assert client.get("/units?level=5&parent_id=bad").status_code == 422
    finally:
        app.dependency_overrides.pop(get_units_service)
