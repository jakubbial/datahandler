from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.dictionaries_service import Attribute, DictionariesService, Measure

router = APIRouter()


def get_dictionaries_service(request: Request) -> DictionariesService:
    return request.app.state.dictionaries_service


@router.get("/attributes", response_model=list[Attribute])
async def list_attributes(
    service: Annotated[DictionariesService, Depends(get_dictionaries_service)],
):
    return await service.get_attributes()


@router.get("/measures", response_model=list[Measure])
async def list_measures(
    service: Annotated[DictionariesService, Depends(get_dictionaries_service)],
):
    return await service.get_measures()
