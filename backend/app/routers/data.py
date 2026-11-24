from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from pydantic import Field

from app.data_service import DataService, UnitData
from app.errors import BdlNotFoundError

router = APIRouter()

MAX_YEARS = 30


def get_data_service(request: Request) -> DataService:
    return request.app.state.data_service


@router.get("/data/by-variable/{variable_id}", response_model=list[UnitData])
async def get_data_by_variable(
    service: Annotated[DataService, Depends(get_data_service)],
    variable_id: Annotated[int, Path(gt=0, le=2_147_483_647)],
    year: Annotated[
        list[Annotated[int, Field(gt=0, le=9999)]],
        Query(min_length=1, max_length=MAX_YEARS),
    ],
    unit_level: Annotated[int | None, Query(ge=0, le=7)] = None,
    unit_parent_id: Annotated[
        str | None, Query(max_length=20, pattern=r"^[A-Za-z0-9]+$")
    ] = None,
):
    try:
        return await service.get_data_by_variable(
            variable_id, year, unit_level, unit_parent_id
        )
    except BdlNotFoundError:
        raise HTTPException(status_code=404, detail="Variable not found")
