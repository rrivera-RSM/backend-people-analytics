from fastapi import APIRouter, Depends, Security
from app.modules.kpis.application.services import KpisService
from app.api.deps import get_kpis_service
from app.auth import azure_scheme
from datetime import datetime


kpis_router = APIRouter(
    prefix="/kpis",
    tags=["kpis"],
    dependencies=[Security(azure_scheme, scopes=["user_impersonation"])],
)


@kpis_router.get(
    "/",
    response_model=list[dict],
    response_model_exclude_none=True,
    dependencies=[Depends(azure_scheme)],
)
async def list_kpis(
    as_of: datetime | None = None,
    society_id: int | None = None,
    department_id: int | None = None,
    office_id: int | None = None,
    category_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
    service: KpisService = Depends(get_kpis_service),
):
    return await service.list_kpis(
        as_of=as_of,
        society_id=society_id,
        department_id=department_id,
        office_id=office_id,
        category_id=category_id,
        limit=limit,
        offset=offset,
    )
