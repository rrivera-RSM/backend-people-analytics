from __future__ import annotations
from fastapi import APIRouter, Security, Depends
from app.auth import azure_scheme

from app.modules.app_managers.application.services import (
    AppManagerPermissionService,
)
from app.modules.app_managers.schemas import (
    AddManageesOut,
    RevokeManageesOut,
    ManageeBatchIn,
)
from app.api.deps import get_app_manager_permission_service


app_managers_router = APIRouter(
    prefix="/app-managers",
    tags=["app-managers"],
    dependencies=[Security(azure_scheme, scopes=["user_impersonation"])],
)


@app_managers_router.post(
    "/app-managers/{manager_employee_id}/managees",
    response_model=AddManageesOut,
)
async def add_managees(
    manager_employee_id: int,
    payload: ManageeBatchIn,
    service: AppManagerPermissionService = Depends(
        get_app_manager_permission_service
    ),
) -> AddManageesOut:
    return await service.add_managees(
        current_user=Depends(azure_scheme),
        manager_employee_id=manager_employee_id,
        managee_ids=payload.managees,
    )


@app_managers_router.post(
    "/app-managers/{manager_employee_id}/managees/revoke",
    response_model=RevokeManageesOut,
)
async def revoke_managees(
    manager_employee_id: int,
    payload: ManageeBatchIn,
    service: AppManagerPermissionService = Depends(
        get_app_manager_permission_service
    ),
) -> RevokeManageesOut:
    return await service.revoke_managees(
        manager_employee_id=manager_employee_id,
        managee_ids=payload.managees,
    )
