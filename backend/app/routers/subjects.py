from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.errors import BdlNotFoundError
from app.subjects_service import Subject, SubjectsService

router = APIRouter()


def get_subjects_service(request: Request) -> SubjectsService:
    return request.app.state.subjects_service


@router.get("/subjects", response_model=list[Subject])
async def list_subjects(
    service: Annotated[SubjectsService, Depends(get_subjects_service)],
    parent_id: Annotated[
        str | None, Query(max_length=16, pattern=r"^[A-Za-z0-9]+$")
    ] = None,
):
    try:
        return await service.get_subjects(parent_id)
    except BdlNotFoundError:
        raise HTTPException(status_code=404, detail="Subject not found")
