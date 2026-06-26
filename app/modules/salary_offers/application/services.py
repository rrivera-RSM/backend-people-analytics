from __future__ import annotations

from fastapi import HTTPException

from app.modules.salary_offers.infrastructure.repo import SalaryOfferRepo
from app.modules.salary_offers.schemas import (
    SalaryOfferCreateIn,
    SalaryOfferOut,
)


class SalaryOfferService:
    def __init__(self, repo: SalaryOfferRepo) -> None:
        self.repo = repo

    async def create_salary_offer(
        self,
        payload: SalaryOfferCreateIn,
        current_user: object,
    ) -> SalaryOfferOut:
        exists = await self.repo.employee_exists(payload.employee_id)
        if not exists:
            raise HTTPException(status_code=404, detail="Employee not found")

        audit_user = self._get_audit_user(current_user)

        try:
            salary_offer = await self.repo.create_salary_offer(
                payload=payload,
                audit_user=audit_user,
            )
            await self.repo.commit()
        except Exception:
            await self.repo.rollback()
            raise

        return SalaryOfferOut.model_validate(salary_offer)

    async def get_latest_salary_offer(
        self,
        employee_id: int,
    ) -> SalaryOfferOut:
        exists = await self.repo.employee_exists(employee_id)
        if not exists:
            raise HTTPException(status_code=404, detail="Employee not found")

        salary_offer = await self.repo.get_latest_salary_offer(employee_id)
        if not salary_offer:
            raise HTTPException(
                status_code=404,
                detail="Salary offer not found",
            )

        return SalaryOfferOut.model_validate(salary_offer)

    @staticmethod
    def _get_audit_user(current_user: object) -> str:
        for attribute in ("preferred_username", "email", "upn", "name", "oid"):
            value = getattr(current_user, attribute, None)
            if isinstance(value, str) and value.strip():
                return value.strip()[:150]

        if isinstance(current_user, dict):
            for key in ("preferred_username", "email", "upn", "name", "oid"):
                value = current_user.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()[:150]

        return "unknown"
