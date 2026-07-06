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
from app.modules.salary_offers.infrastructure.repo import SalaryOfferRepo
from app.modules.salary_offers.application.services import SalaryOfferService
from app.modules.assistant.application.ports import AIProviderPort
from app.modules.assistant.application.services import AssistantService
from app.modules.assistant.application.tool_registry import (
    AssistantToolRegistry,
)
from app.modules.assistant.infrastructure.ai.factory import build_ai_provider
from app.modules.assistant.infrastructure.repo import AssistantShapRepository
from settings import Settings


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
    repo: EmployeeInsightRepository = Depends(
        get_employee_insight_repository
    ),
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


def get_salary_offer_service(
    repo: SalaryOfferRepo = Depends(get_salary_offer_repo),
) -> SalaryOfferService:
    return SalaryOfferService(repo)


def get_ai_provider() -> AIProviderPort:
    return build_ai_provider(Settings())


def get_assistant_shap_repository(
    db: AsyncSession = Depends(get_db),
) -> AssistantShapRepository:
    return AssistantShapRepository(db)


def get_assistant_tool_registry(
    shap_repository: AssistantShapRepository = Depends(
        get_assistant_shap_repository
    ),
) -> AssistantToolRegistry:
    return AssistantToolRegistry(shap_repository=shap_repository)


def get_assistant_service(
    ai_provider: AIProviderPort = Depends(get_ai_provider),
    tool_registry: AssistantToolRegistry = Depends(
        get_assistant_tool_registry
    ),
) -> AssistantService:
    return AssistantService(
        ai_provider=ai_provider, tool_registry=tool_registry
    )
