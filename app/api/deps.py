from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.employees.infrastructure.repo import EmployeeRepo
from app.modules.employees.application.services import EmployeeService
from app.infrastructure.db.session import get_db
from app.modules.ona.infrastructure.repo import OnaRepo
from app.modules.ona.application.services import OnaService


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
