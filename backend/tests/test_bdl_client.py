import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.parametrize(
    ("client_id", "expected"), [(" test-key ", "test-key"), ("", None)]
)
def test_bdl_client_id_header_comes_from_environment(monkeypatch, client_id, expected):
    monkeypatch.setenv("BDL_MONITORING", "0")
    monkeypatch.setenv("BDL_CLIENT_ID", client_id)

    with TestClient(app):
        headers = app.state.bdl_client._http.headers

        assert headers.get("X-ClientId") == expected
