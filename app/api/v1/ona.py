from fastapi import APIRouter, Depends, Security

from app.modules.ona.schemas import OnaRelationsOut, OnaActiveOut
from app.modules.ona.application.services import OnaService
from app.api.deps import get_ona_service
from app.auth import azure_scheme


ona_router = APIRouter(
    prefix="/ona",
    tags=["ona"],
    dependencies=[Security(azure_scheme, scopes=["user_impersonation"])],
)


@ona_router.get(
    "/relations",
    response_model=list[OnaRelationsOut],
    response_model_exclude_none=True,
    dependencies=[Depends(azure_scheme)],
)
async def list_ona_relations(
    service: OnaService = Depends(get_ona_service),
):
    return await service.get_all_ona_relations()


@ona_router.get(
    "/{employee_id}/relations",
    response_model=list[OnaRelationsOut],
    response_model_exclude_none=True,
    dependencies=[Depends(azure_scheme)],
)
async def list_ona_relations_by_employee_id(
    employee_id: int,
    service: OnaService = Depends(get_ona_service),
):
    return await service.get_ona_relations_by_employee_id(
        employee_id=employee_id
    )


@ona_router.get(
    "/{employee_id}/active",
    response_model=OnaActiveOut | None,
    dependencies=[Depends(azure_scheme)],
)
async def get_ona_active_by_employee_id(
    employee_id: int,
    service: OnaService = Depends(get_ona_service),
):
    return await service.get_ona_active_by_employee_id(employee_id=employee_id)
