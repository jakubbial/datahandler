import logging

import httpx
import pytest

from app.bdl_client import BdlClient
from app.monitoring import (
    LOG_FILE_ENV_VAR,
    MONITORING_ENV_VAR,
    configure_monitoring,
    logger,
)
from app.subjects_service import SubjectsService


@pytest.fixture
def monitoring(monkeypatch, tmp_path):
    monkeypatch.setenv(MONITORING_ENV_VAR, "1")
    monkeypatch.setenv(LOG_FILE_ENV_VAR, str(tmp_path / "logs" / "bdl.log"))
    configure_monitoring()
    yield
    for handler in list(logger.handlers):
        handler.close()
    logger.handlers.clear()
    logger.setLevel(logging.NOTSET)
    logger.propagate = True


def _client(pages: int) -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params["page"])
        item = {
            "id": f"K{page}",
            "name": "x",
            "hasVariables": False,
            "parentId": None,
        }
        return httpx.Response(200, json={"totalRecords": pages, "results": [item]})

    return httpx.AsyncClient(
        base_url="https://bdl.test", transport=httpx.MockTransport(handler)
    )


@pytest.mark.anyio
async def test_logs_each_bdl_page_and_cache_outcomes(monitoring, caplog):
    caplog.set_level(logging.INFO, logger="datahandler.bdl")
    logger.propagate = True
    async with _client(pages=2) as http:
        service = SubjectsService(BdlClient(http))
        await service.get_subjects()
        await service.get_subjects()

    messages = [r.getMessage() for r in caplog.records]
    assert sum("bdl_request" in m and "status=200" in m for m in messages) == 2
    assert "'page': 1" in messages[2]
    assert any("cache=subjects outcome=miss" in m for m in messages)
    assert any("cache=subjects outcome=hit" in m for m in messages)


def test_writes_log_file(monitoring, tmp_path):
    logger.info("cache=test outcome=hit key=1")
    for handler in logger.handlers:
        handler.flush()

    content = (tmp_path / "logs" / "bdl.log").read_text(encoding="utf-8")
    assert "cache=test outcome=hit key=1" in content


def test_monitoring_can_be_disabled(monkeypatch):
    monkeypatch.setenv(MONITORING_ENV_VAR, "0")
    configure_monitoring()

    assert not logger.handlers
    assert not logger.isEnabledFor(logging.INFO)
