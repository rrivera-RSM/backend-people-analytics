from datetime import datetime
from fastapi import APIRouter, Depends, Query, Request, Security, Response

from app.modules.employees.schemas import EmployeeRowOut
from app.modules.employees.application.services import EmployeeService
from app.api.deps import get_employee_service
from app.auth import azure_scheme

from app.common.enums import (
    SocietyType,
    DepartmentType,
    OfficeName,
    CategoryType,
)

employee_router = APIRouter(
    prefix="/employees",
    tags=["employees"],
    dependencies=[Security(azure_scheme, scopes=["user_impersonation"])],
)


@employee_router.get(
    "/rows",
    response_model=list[EmployeeRowOut],
    response_model_exclude_none=True,
    dependencies=[Depends(azure_scheme)],
)
async def list_employee_rows(
    as_of: datetime | None = Query(default=None),
    office: OfficeName | None = Query(
        default=None,
        description="Nombre de oficina (parcial, case-insensitive)",
    ),
    department: DepartmentType | None = Query(default=None),
    society: SocietyType | None = Query(default=None),
    category: CategoryType | None = Query(
        default=None, description="Ej: Junior/Senior (Param.param_value)"
    ),
    q: str | None = Query(
        default=None, description="Búsqueda libre: nombre, dni, email..."
    ),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    service: EmployeeService = Depends(get_employee_service),
):
    return await service.list_rows(
        as_of=as_of,
        office=office.value if office else None,
        department=department.value if department else None,
        society=society.value if society else None,
        category=category.value if category else None,
        q=q,
        limit=limit,
        offset=offset,
    )


@employee_router.get(
    "/{employee_id}/photo",
    dependencies=[Depends(azure_scheme)],
    response_class=Response,
)
async def get_employee_photo(
    employee_id: int,
    request: Request,
    service: EmployeeService = Depends(get_employee_service),
):
    authorization: str = request.headers.get("Authorization", "")
    return await service.employee_photo(
        employee_id=employee_id, authorization=authorization
    )


@employee_router.get(
    "/{employee_id}/evaluations",
    dependencies=[Depends(azure_scheme)],
)
async def get_employee_evaluations(
    employee_id: int,
    service: EmployeeService = Depends(get_employee_service),
):
    return await service.employee_evaluations(employee_id=employee_id)


@employee_router.get(
    "/{employee_id}/monetary-info",
    dependencies=[Depends(azure_scheme)],
)
async def get_employee_monetary_info(
    employee_id: int,
    as_of: datetime | None = Query(default=None),
    service: EmployeeService = Depends(get_employee_service),
):
    return await service.employee_monetary_info(
        employee_id=employee_id, as_of=as_of
    )
