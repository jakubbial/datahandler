from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request

from app.errors import BdlNotFoundError
from app.variables_service import Variable, VariableDetails, VariablesService

router = APIRouter()


def get_variables_service(request: Request) -> VariablesService:
    return request.app.state.variables_service


@router.get("/variables", response_model=list[Variable])
async def list_variables(
    service: Annotated[VariablesService, Depends(get_variables_service)],
    subject_id: Annotated[str, Query(pattern=r"^P[A-Za-z0-9]{1,15}$")],
):
    try:
        return await service.get_variables(subject_id)
    except BdlNotFoundError:
        raise HTTPException(status_code=404, detail="Subject not found")


@router.get("/variables/{variable_id}", response_model=VariableDetails)
async def get_variable(
    service: Annotated[VariablesService, Depends(get_variables_service)],
    variable_id: Annotated[int, Path(gt=0, le=2_147_483_647)],
):
    try:
        return await service.get_variable(variable_id)
    except BdlNotFoundError:
        raise HTTPException(status_code=404, detail="Variable not found")
