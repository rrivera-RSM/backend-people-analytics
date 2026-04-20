from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.people.kpis import Kpis
from app.infrastructure.db.models.core.category import Category
from app.infrastructure.db.models.core.office import Office
from app.infrastructure.db.models.core.department import Department
from app.infrastructure.db.models.core.society import Society


class KpisRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_kpis(
        self,
        as_of: datetime | None = None,
        society: str | None = None,
        department: str | None = None,
        office: str | None = None,
        category: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ):
        as_of = as_of or datetime.now(timezone.utc)

        rn = (
            func.row_number()
            .over(
                partition_by=(
                    Kpis.society_id,
                    Kpis.department_id,
                    Kpis.office_id,
                    Kpis.category_id,
                ),
                order_by=Kpis.start_at.desc(),
            )
            .label("rn")
        )

        current_kpis = (
            select(
                Kpis.id,
                Kpis.start_at,
                Kpis.end_at,
                Kpis.society_id,
                Kpis.department_id,
                Kpis.office_id,
                Kpis.category_id,
                Kpis.salary_avg,
                Kpis.bonus_avg,
                rn,
            )
            .where(
                and_(
                    Kpis.start_at <= as_of,
                    Kpis.end_at > as_of,
                )
            )
            .cte("current_kpis")
        )

        stmt = (
            select(
                current_kpis.c.id,
                current_kpis.c.start_at,
                current_kpis.c.end_at,
                current_kpis.c.society_id,
                Society.name.label("society_name"),
                current_kpis.c.department_id,
                Department.name.label("department_name"),
                current_kpis.c.office_id,
                Office.name.label("office_name"),
                current_kpis.c.category_id,
                Category.name.label("category_name"),
                current_kpis.c.salary_avg,
                current_kpis.c.bonus_avg,
            )
            .select_from(current_kpis)
            .outerjoin(Society, Society.id == current_kpis.c.society_id)
            .outerjoin(
                Department, Department.id == current_kpis.c.department_id
            )
            .outerjoin(Office, Office.id == current_kpis.c.office_id)
            .outerjoin(Category, Category.id == current_kpis.c.category_id)
            .where(current_kpis.c.rn == 1)
        )

        # ---- Filtros por nombre (lookup tables) ----
        if society:
            stmt = stmt.where(Society.name.ilike(f"%{society}%"))

        if department:
            stmt = stmt.where(Department.name.ilike(f"%{department}%"))

        if office:
            stmt = stmt.where(Office.name.ilike(f"%{office}%"))

        if category:
            stmt = stmt.where(Category.name.ilike(f"%{category}%"))

        # ---- Paginación ----
        stmt = stmt.limit(limit).offset(offset)

        res = await self.db.execute(stmt)
        return res.mappings().all()
