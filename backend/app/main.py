from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.routers.subjects import router as subjects_router
from app.subjects_service import SubjectsService
from app.routers.variables import router as variables_router
from app.variables_service import VariablesService
from app.data_service import DataService
from app.routers.data import router as data_router
from app.routers.units import router as units_router
from app.units_service import UnitsService
from app.dictionaries_service import DictionariesService
from app.routers.dictionaries import router as dictionaries_router

from app.bdl_client import BDL_BASE_URL, BDL_TIMEOUT_SECONDS, BdlClient, bdl_headers
from app.errors import BdlRateLimitError, BdlUpstreamError
from app.monitoring import configure_monitoring, logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_monitoring()
    headers = bdl_headers()
    logger.info("bdl_client_id configured=%s", "yes" if headers else "no")
    async with httpx.AsyncClient(
        base_url=BDL_BASE_URL, timeout=BDL_TIMEOUT_SECONDS, headers=headers
    ) as http:
        bdl_client = BdlClient(http)
        app.state.bdl_client = bdl_client
        app.state.subjects_service = SubjectsService(bdl_client)
        app.state.variables_service = VariablesService(bdl_client)
        app.state.dictionaries_service = DictionariesService(bdl_client)
        app.state.data_service = DataService(
            bdl_client, dictionaries=app.state.dictionaries_service
        )
        app.state.units_service = UnitsService(bdl_client)

        yield


app = FastAPI(title="DataHandler API", lifespan=lifespan)
app.include_router(subjects_router)
app.include_router(variables_router)
app.include_router(data_router)
app.include_router(units_router)
app.include_router(dictionaries_router)


@app.exception_handler(BdlRateLimitError)
async def bdl_rate_limit_handler(request: Request, exc: BdlRateLimitError):
    return JSONResponse(status_code=429, content={"detail": "BDL rate limit exceeded"})


@app.exception_handler(BdlUpstreamError)
async def bdl_upstream_handler(request: Request, exc: BdlUpstreamError):
    return JSONResponse(status_code=502, content={"detail": "BDL API is unavailable"})


@app.get("/health")
async def healthcheck():
    return {
        "status": "ok",
        "service": "backend",
    }


@app.get("/")
async def root():
    return {
        "message": "DataHandler backend is running",
        "docs": "/docs",
    }
