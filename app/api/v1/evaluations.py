from __future__ import annotations

from fastapi import APIRouter, Depends

from app.modules.evaluations.application.services import (
    EvaluationScatterService,
)
from app.modules.evaluations.schemas import (
    EvaluationScatterLatestCycleOut,
)
from app.api.deps import get_evaluation_scatter_service

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@router.get(
    "/scatter/latest-cycle",
    response_model=EvaluationScatterLatestCycleOut,
)
async def get_latest_cycle_scatter(
    service: EvaluationScatterService = Depends(
        get_evaluation_scatter_service
    ),
) -> EvaluationScatterLatestCycleOut:
    return await service.get_latest_cycle_scatter()
