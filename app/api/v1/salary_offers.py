from __future__ import annotations

from fastapi import APIRouter, Depends, Security, status

from app.api.deps import get_salary_offer_service
from app.auth import azure_scheme
from app.modules.salary_offers.application.services import SalaryOfferService
from app.modules.salary_offers.schemas import (
    SalaryOfferCreateIn,
    SalaryOfferOut,
)


salary_offers_router = APIRouter(
    prefix="/salary-offers",
    tags=["salary-offers"],
    dependencies=[Security(azure_scheme, scopes=["user_impersonation"])],
)


@salary_offers_router.post(
    "",
    response_model=SalaryOfferOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_salary_offer(
    payload: SalaryOfferCreateIn,
    current_user=Depends(azure_scheme),
    service: SalaryOfferService = Depends(get_salary_offer_service),
) -> SalaryOfferOut:
    return await service.create_salary_offer(
        payload=payload,
        current_user=current_user,
    )


@salary_offers_router.get(
    "/employees/{employee_id}/latest",
    response_model=SalaryOfferOut,
)
async def get_latest_salary_offer(
    employee_id: int,
    service: SalaryOfferService = Depends(get_salary_offer_service),
) -> SalaryOfferOut:
    return await service.get_latest_salary_offer(employee_id=employee_id)
