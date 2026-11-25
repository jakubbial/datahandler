from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.units_service import Unit, UnitsService

router = APIRouter()


def get_units_service(request: Request) -> UnitsService:
    return request.app.state.units_service


@router.get("/units", response_model=list[Unit])
async def list_units(
    service: Annotated[UnitsService, Depends(get_units_service)],
    level: int,
    parent_id: Annotated[
        str | None, Query(min_length=12, max_length=12, pattern=r"^[0-9]+$")
    ] = None,
):
    if level not in (2, 5):
        raise HTTPException(status_code=422, detail="Unit level must be 2 or 5")
    if (level == 5) != (parent_id is not None):
        raise HTTPException(
            status_code=422, detail="A parent is required only for county units"
        )
    return await service.get_units(level, parent_id)
