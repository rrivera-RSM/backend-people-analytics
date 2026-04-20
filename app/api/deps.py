from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.employees.infrastructure.repo import EmployeeRepo
from app.modules.employees.application.services import EmployeeService
from app.infrastructure.db.session import get_db
from app.modules.ona.infrastructure.repo import OnaRepo
from app.modules.ona.application.services import OnaService
from app.modules.kpis.infrastructure.repo import KpisRepo
from app.modules.kpis.application.services import KpisService
from app.modules.app_managers.infrastructure.repo import (
    AppManagerPermissionRepo,
)
from app.modules.app_managers.application.services import (
    AppManagerPermissionService,
)


def get_employee_repo(
    db: AsyncSession = Depends(get_db),
) -> EmployeeRepo:
    return EmployeeRepo(db)


def get_employee_service(
    repo: EmployeeRepo = Depends(get_employee_repo),
) -> EmployeeService:
    return EmployeeService(repo)


def get_ona_repo(
    db: AsyncSession = Depends(get_db),
) -> OnaRepo:
    return OnaRepo(db)


def get_ona_service(
    repo: OnaRepo = Depends(get_ona_repo),
) -> OnaService:
    return OnaService(repo)


def get_kpis_repo(
    db: AsyncSession = Depends(get_db),
) -> KpisRepo:
    return KpisRepo(db)


def get_kpis_service(
    repo: KpisRepo = Depends(get_kpis_repo),
) -> KpisService:
    return KpisService(repo)


def get_app_manager_permission_repo(
    db: AsyncSession = Depends(get_db),
) -> AppManagerPermissionRepo:
    return AppManagerPermissionRepo(db)


def get_app_manager_permission_service(
    repo: AppManagerPermissionRepo = Depends(get_app_manager_permission_repo),
) -> AppManagerPermissionService:
    return AppManagerPermissionService(repo)
