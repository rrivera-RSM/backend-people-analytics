from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.core.employee import Employee
from app.infrastructure.db.models.people.salary_offer import SalaryOffer
from app.modules.salary_offers.schemas import SalaryOfferCreateIn


class SalaryOfferRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()

    async def employee_exists(self, employee_id: int) -> bool:
        stmt = select(Employee.id).where(Employee.id == employee_id).limit(1)
        result = await self.session.scalar(stmt)
        return result is not None

    async def create_salary_offer(
        self,
        payload: SalaryOfferCreateIn,
        audit_user: str,
    ) -> SalaryOffer:
        salary_offer = SalaryOffer(
            **payload.model_dump(),
            aud_user_creation=audit_user,
        )

        self.session.add(salary_offer)
        await self.session.flush()
        await self.session.refresh(salary_offer)
        return salary_offer

    async def get_latest_salary_offer(
        self,
        employee_id: int,
    ) -> SalaryOffer | None:
        stmt = (
            select(SalaryOffer)
            .where(SalaryOffer.employee_id == employee_id)
            .order_by(
                SalaryOffer.aud_creation_at.desc(),
                SalaryOffer.id.desc(),
            )
            .limit(1)
        )
        result = await self.session.scalars(stmt)
        return result.first()
