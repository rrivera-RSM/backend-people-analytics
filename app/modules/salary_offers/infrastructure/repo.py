from __future__ import annotations

from datetime import datetime, timezone
import uuid

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.core.employee import Employee
from app.infrastructure.db.models.people.app_manager import AppManager
from app.infrastructure.db.models.people.app_manager_employee import (
    AppManagerEmployee,
)
from app.infrastructure.db.models.people.salary_offer import SalaryOffer
from app.modules.salary_offers.application.events import AppManagerIdentity
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

    async def get_active_app_manager_by_audit_user(
        self,
        audit_user: str,
    ) -> AppManagerIdentity | None:
        normalized = audit_user.strip().lower()
        if not normalized:
            return None

        conditions = [func.lower(Employee.email) == normalized]
        parsed_oid = self._parse_uuid(normalized)
        if parsed_oid is not None:
            conditions.append(Employee.microsoft_id == str(parsed_oid))

        stmt = (
            select(
                Employee.id,
                Employee.first_name,
                Employee.last_name,
                Employee.email,
            )
            .join(AppManager, AppManager.id == Employee.id)
            .where(
                AppManager.bol_active == 1,
                or_(*conditions),
            )
            .limit(1)
        )
        row = (await self.session.execute(stmt)).mappings().first()
        if row is None:
            return None

        return AppManagerIdentity(
            employee_id=row["id"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            email=row["email"],
        )

    async def get_active_managee_ids(
        self,
        manager_employee_id: int,
    ) -> list[int]:
        stmt = select(AppManagerEmployee.employee_id).where(
            AppManagerEmployee.manager_id == manager_employee_id,
            AppManagerEmployee.bol_active == 1,
        )
        result = await self.session.scalars(stmt)
        return sorted(set(result.all()))

    async def get_salary_offer_employee_ids_for_year(
        self,
        *,
        employee_ids: list[int],
        year: int,
    ) -> set[int]:
        ids = sorted(set(employee_ids))
        if not ids:
            return set()

        start_at, end_at = self._year_bounds(year)
        stmt = (
            select(SalaryOffer.employee_id)
            .where(
                SalaryOffer.employee_id.in_(ids),
                SalaryOffer.aud_creation_at >= start_at,
                SalaryOffer.aud_creation_at < end_at,
            )
            .distinct()
        )
        result = await self.session.scalars(stmt)
        return set(result.all())

    async def get_salary_proposal_export_rows(
        self,
        *,
        manager_employee_id: int,
        year: int,
    ) -> list[dict[str, object]]:
        start_at, end_at = self._year_bounds(year)
        active_managees = select(AppManagerEmployee.employee_id).where(
            AppManagerEmployee.manager_id == manager_employee_id,
            AppManagerEmployee.bol_active == 1,
        )

        stmt = (
            select(
                SalaryOffer.id.label("salary_offer_id"),
                SalaryOffer.employee_id,
                Employee.first_name.label("employee_first_name"),
                Employee.last_name.label("employee_last_name"),
                SalaryOffer.new_salary,
                SalaryOffer.new_bonus,
                SalaryOffer.month_payment_bonus,
                SalaryOffer.bonus_next_fy,
                SalaryOffer.new_category,
                SalaryOffer.observations,
                SalaryOffer.aud_user_creation,
                SalaryOffer.aud_creation_at,
            )
            .join(Employee, Employee.id == SalaryOffer.employee_id)
            .where(
                SalaryOffer.employee_id.in_(active_managees),
                SalaryOffer.aud_creation_at >= start_at,
                SalaryOffer.aud_creation_at < end_at,
            )
            .order_by(
                Employee.last_name.asc(),
                Employee.first_name.asc(),
                SalaryOffer.aud_creation_at.asc(),
                SalaryOffer.id.asc(),
            )
        )
        rows = (await self.session.execute(stmt)).mappings().all()
        return [dict(row) for row in rows]

    @staticmethod
    def _year_bounds(year: int) -> tuple[datetime, datetime]:
        return (
            datetime(year, 1, 1, tzinfo=timezone.utc),
            datetime(year + 1, 1, 1, tzinfo=timezone.utc),
        )

    @staticmethod
    def _parse_uuid(value: str) -> uuid.UUID | None:
        try:
            return uuid.UUID(value)
        except (TypeError, ValueError):
            return None
