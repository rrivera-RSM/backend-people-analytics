from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from settings import Settings

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
from app.modules.employee_insights.infrastructure.repo import (
    EmployeeInsightRepository,
)
from app.modules.employee_insights.application.services import (
    EmployeeInsightService,
)
from app.modules.evaluations.infrastructure.repo import (
    EvaluationScatterRepository,
)
from app.modules.evaluations.application.services import (
    EvaluationScatterService,
)
from app.modules.salary_offers.infrastructure.email_sender import (
    SalaryProposalEmailSender,
)
from app.modules.salary_offers.infrastructure.repo import SalaryOfferRepo
from app.modules.salary_offers.application.listeners import (
    SalaryOfferEventListener,
)
from app.modules.salary_offers.application.services import SalaryOfferService


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


def get_employee_insight_repository(
    db: AsyncSession = Depends(get_db),
) -> EmployeeInsightRepository:
    return EmployeeInsightRepository(db)


def get_employee_insight_service(
    repo: EmployeeInsightRepository = Depends(get_employee_insight_repository),
) -> EmployeeInsightService:
    return EmployeeInsightService(repo)


def get_evaluation_scatter_repo(
    db: AsyncSession = Depends(get_db),
) -> EvaluationScatterRepository:
    return EvaluationScatterRepository(db)


def get_evaluation_scatter_service(
    repo: EvaluationScatterRepository = Depends(get_evaluation_scatter_repo),
) -> EvaluationScatterService:
    return EvaluationScatterService(repo)


def get_salary_offer_repo(
    db: AsyncSession = Depends(get_db),
) -> SalaryOfferRepo:
    return SalaryOfferRepo(db)


@lru_cache
def get_salary_proposal_email_sender() -> SalaryProposalEmailSender:
    settings = Settings()
    return SalaryProposalEmailSender(
        tenant_id=settings.TENANT_ID,
        client_id=settings.APP_CLIENT_ID,
        client_secret=settings.APP_CLIENT_SECRET,
        sender_email=settings.GRAPH_MAIL_SENDER,
        recipients=settings.SALARY_PROPOSAL_NOTIFICATION_RECIPIENTS,
    )


def get_salary_offer_event_listener(
    repo: SalaryOfferRepo = Depends(get_salary_offer_repo),
    email_sender: SalaryProposalEmailSender = Depends(
        get_salary_proposal_email_sender
    ),
) -> SalaryOfferEventListener:
    return SalaryOfferEventListener(repo=repo, email_sender=email_sender)


def get_salary_offer_service(
    repo: SalaryOfferRepo = Depends(get_salary_offer_repo),
    event_listener: SalaryOfferEventListener = Depends(
        get_salary_offer_event_listener
    ),
) -> SalaryOfferService:
    return SalaryOfferService(repo=repo, event_listener=event_listener)
