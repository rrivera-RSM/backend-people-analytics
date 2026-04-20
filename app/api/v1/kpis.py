from fastapi import APIRouter, Depends, Security
from app.modules.kpis.application.services import KpisService
from app.api.deps import get_kpis_service
from app.auth import azure_scheme
from datetime import datetime
from app.common.enums import (
    SocietyType,
    DepartmentType,
    OfficeName,
    CategoryType,
)


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
    society: SocietyType | None = None,
    department: DepartmentType | None = None,
    office: OfficeName | None = None,
    category: CategoryType | None = None,    
    limit: int = 100,
    offset: int = 0,
    service: KpisService = Depends(get_kpis_service),
):
    return await service.list_kpis(
        as_of=as_of,
        society=society.value if society else None,
        department=department.value if department else None,
        office=office.value if office else None,
        category=category.value if category else None,
        limit=limit,
        offset=offset,
    )
