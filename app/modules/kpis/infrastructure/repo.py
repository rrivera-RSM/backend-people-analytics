from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.infrastructure.db.models.core.category import Category
from app.infrastructure.db.models.core.department import Department
from app.infrastructure.db.models.core.office import Office
from app.infrastructure.db.models.core.society import Society
from app.infrastructure.db.models.people.kpis import BonusAvg, SalaryIncreaseAvg


MV_DATA_START_DATE = date(2025, 9, 1)


class KpisRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _matches_truth_table(
        dimension_id: ColumnElement[int | None],
        selected_id: int | None,
    ) -> ColumnElement[bool]:
        if selected_id is None:
            return dimension_id.is_(None)

        return or_(dimension_id == selected_id, dimension_id.is_(None))

    async def list_kpis(
        self,
        as_of: datetime | None = None,
        society_id: int | None = None,
        department_id: int | None = None,
        office_id: int | None = None,
        category_id: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ):
        # These materialized views are snapshot aggregates and are not
        # versioned by validity ranges. If the caller asks for a date
        # before the source window, there is no matching data.
        if as_of and as_of.date() < MV_DATA_START_DATE:
            return []

        salary_increase_avgs = (
            select(
                SalaryIncreaseAvg.society_id.label("society_id"),
                SalaryIncreaseAvg.department_id.label("department_id"),
                SalaryIncreaseAvg.office_id.label("office_id"),
                SalaryIncreaseAvg.category_id.label("category_id"),
                SalaryIncreaseAvg.g_society.label("g_society"),
                SalaryIncreaseAvg.g_department.label("g_department"),
                SalaryIncreaseAvg.g_office.label("g_office"),
                SalaryIncreaseAvg.g_category.label("g_category"),
                SalaryIncreaseAvg.avg_increase_amount.label(
                    "salary_increase_avg"
                ),
                SalaryIncreaseAvg.avg_increase_percentage.label(
                    "salary_increase_percentage_avg"
                ),
            )
            .cte("salary_increase_avgs")
        )

        bonus_avgs = (
            select(
                BonusAvg.society_id.label("society_id"),
                BonusAvg.department_id.label("department_id"),
                BonusAvg.office_id.label("office_id"),
                BonusAvg.category_id.label("category_id"),
                BonusAvg.g_society.label("g_society"),
                BonusAvg.g_department.label("g_department"),
                BonusAvg.g_office.label("g_office"),
                BonusAvg.g_category.label("g_category"),
                BonusAvg.avg_bonus.label("bonus_avg"),
            )
            .cte("bonus_avgs")
        )

        join_condition = and_(
            salary_increase_avgs.c.society_id.is_not_distinct_from(
                bonus_avgs.c.society_id
            ),
            salary_increase_avgs.c.department_id.is_not_distinct_from(
                bonus_avgs.c.department_id
            ),
            salary_increase_avgs.c.office_id.is_not_distinct_from(
                bonus_avgs.c.office_id
            ),
            salary_increase_avgs.c.category_id.is_not_distinct_from(
                bonus_avgs.c.category_id
            ),
            salary_increase_avgs.c.g_society == bonus_avgs.c.g_society,
            salary_increase_avgs.c.g_department == bonus_avgs.c.g_department,
            salary_increase_avgs.c.g_office == bonus_avgs.c.g_office,
            salary_increase_avgs.c.g_category == bonus_avgs.c.g_category,
        )

        current_kpis = (
            select(
                func.coalesce(
                    salary_increase_avgs.c.society_id,
                    bonus_avgs.c.society_id,
                ).label("society_id"),
                func.coalesce(
                    salary_increase_avgs.c.department_id,
                    bonus_avgs.c.department_id,
                ).label("department_id"),
                func.coalesce(
                    salary_increase_avgs.c.office_id,
                    bonus_avgs.c.office_id,
                ).label("office_id"),
                func.coalesce(
                    salary_increase_avgs.c.category_id,
                    bonus_avgs.c.category_id,
                ).label("category_id"),
                func.coalesce(
                    salary_increase_avgs.c.g_society,
                    bonus_avgs.c.g_society,
                ).label("g_society"),
                func.coalesce(
                    salary_increase_avgs.c.g_department,
                    bonus_avgs.c.g_department,
                ).label("g_department"),
                func.coalesce(
                    salary_increase_avgs.c.g_office,
                    bonus_avgs.c.g_office,
                ).label("g_office"),
                func.coalesce(
                    salary_increase_avgs.c.g_category,
                    bonus_avgs.c.g_category,
                ).label("g_category"),
                salary_increase_avgs.c.salary_increase_avg,
                bonus_avgs.c.bonus_avg,
                func.coalesce(salary_increase_avgs.c.salary_increase_percentage_avg).label(
                    "salary_increase_percentage_avg"
                ),
            )
            .select_from(
                salary_increase_avgs.join(
                    bonus_avgs,
                    join_condition,
                    full=True,
                )
            )
            .cte("current_kpis")
        )

        stmt = (
            select(
                current_kpis.c.society_id,
                Society.name.label("society_name"),
                current_kpis.c.department_id,
                Department.name.label("department_name"),
                current_kpis.c.office_id,
                Office.name.label("office_name"),
                current_kpis.c.category_id,
                Category.name.label("category_name"),
                current_kpis.c.salary_increase_avg,
                current_kpis.c.salary_increase_percentage_avg,
                current_kpis.c.bonus_avg,
            )
            .select_from(current_kpis)
            .outerjoin(Society, Society.id == current_kpis.c.society_id)
            .outerjoin(
                Department, Department.id == current_kpis.c.department_id
            )
            .outerjoin(Office, Office.id == current_kpis.c.office_id)
            .outerjoin(Category, Category.id == current_kpis.c.category_id)
            .where(
                and_(
                    self._matches_truth_table(
                        current_kpis.c.society_id, society_id
                    ),
                    self._matches_truth_table(
                        current_kpis.c.department_id, department_id
                    ),
                    self._matches_truth_table(
                        current_kpis.c.office_id, office_id
                    ),
                    self._matches_truth_table(
                        current_kpis.c.category_id, category_id
                    ),
                )
            )
        )

        stmt = (
            stmt.order_by(
                case((current_kpis.c.society_id.is_(None), 0), else_=1),
                case((current_kpis.c.department_id.is_(None), 0), else_=1),
                case((current_kpis.c.office_id.is_(None), 0), else_=1),
                case((current_kpis.c.category_id.is_(None), 0), else_=1),
            )
            .limit(limit)
            .offset(offset)
        )

        res = await self.db.execute(stmt)
        return res.mappings().all()
