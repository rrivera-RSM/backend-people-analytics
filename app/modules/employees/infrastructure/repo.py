from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import and_, func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.core.employee import Employee
from app.infrastructure.db.models.core.employee_history import EmployeeHistory
from app.infrastructure.db.models.core.param import Param
from app.infrastructure.db.models.core.office import Office
from app.infrastructure.db.models.core.department import Department
from app.infrastructure.db.models.core.society import Society

from app.infrastructure.db.models.people.evaluation import Evaluation
from app.infrastructure.db.models.people.positive_impact import PositiveImpact
from app.infrastructure.db.models.people.salary import Salary


class EmployeeRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_employee_rows(
        self,
        as_of: datetime | None = None,
        office: str | None = None,
        department: str | None = None,
        society: str | None = None,
        category: str | None = None,
        q: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ):
        as_of = as_of or datetime.now(timezone.utc)

        rn = (
            func.row_number()
            .over(
                partition_by=EmployeeHistory.employee_id,
                order_by=EmployeeHistory.start_at.desc(),
            )
            .label("rn")
        )

        current_hist = (
            select(
                EmployeeHistory.employee_id,
                EmployeeHistory.start_at,
                EmployeeHistory.end_at,
                EmployeeHistory.society_id,
                EmployeeHistory.department_id,
                EmployeeHistory.office_id,
                EmployeeHistory.category_id,
                rn,
            )
            .where(
                EmployeeHistory.end_at.is_(None)
                | (EmployeeHistory.end_at > as_of)
            )
            .cte("current_hist")
        )

        stmt = (
            select(
                Employee.id,
                Employee.first_name,
                Employee.last_name,
                Employee.dni,
                Employee.email,
                Param.param_value.label("category_name"),
                Office.id.label("office_id"),
                Office.name.label("office_name"),
                Department.id.label("department_id"),
                Department.name.label("department_name"),
                Society.id.label("society_id"),
                Society.name.label("society_name"),
                current_hist.c.start_at,
            )
            .join(
                current_hist,
                and_(
                    current_hist.c.employee_id == Employee.id,
                    current_hist.c.rn == 1,
                ),
            )
            .outerjoin(Office, Office.id == current_hist.c.office_id)
            .outerjoin(
                Department, Department.id == current_hist.c.department_id
            )
            .outerjoin(Society, Society.id == current_hist.c.society_id)
            .outerjoin(
                Param,
                and_(
                    Param.param_key == current_hist.c.category_id,
                    Param.param_type == "category",
                ),
            )
        )

        # ---- Filtros por tablas "lookup" (name) ----
        if office:
            # match parcial e insensible a mayúsculas/minúsculas
            stmt = stmt.where(Office.name.ilike(f"%{office}%"))

        if department:
            stmt = stmt.where(Department.name.ilike(f"%{department}%"))

        if society:
            stmt = stmt.where(Society.name.ilike(f"%{society}%"))

        if category:
            # como category viene de Param.param_value
            stmt = stmt.where(
                Param.param_type == "category",
                Param.param_value.ilike(f"%{category}%"),
            )

        # ---- Búsqueda libre (nombre, apellido, dni, email, etc.) ----
        if q:
            stmt = stmt.where(
                or_(
                    Employee.first_name.ilike(f"%{q}%"),
                    Employee.last_name.ilike(f"%{q}%"),
                    Employee.dni.ilike(f"%{q}%"),
                    Employee.email.ilike(f"%{q}%"),
                )
            )

        # ---- Paginación ----
        stmt = stmt.limit(limit).offset(offset)

        res = await self.db.execute(stmt)
        return res.mappings().all()

    async def get_employee_oid(self, employee_id: int) -> str | None:
        stmt = select(Employee.microsoft_id).where(Employee.id == employee_id)
        res = await self.db.execute(stmt)
        row = res.first()
        return row[0] if row else None

    async def get_employee_scores(self, employee_id: int):
        stmt = (
            select(
                Evaluation.evaluation_at,
                Evaluation.final_score,
                PositiveImpact.evaluation_at.label("impact_evaluation_at"),
                PositiveImpact.bol_positive_impact.label(
                    "bol_positive_impact"
                ),
            )
            .outerjoin(
                PositiveImpact,
                and_(
                    PositiveImpact.employee_id == Evaluation.employee_id,
                    func.date_trunc("year", PositiveImpact.evaluation_at)
                    == func.date_trunc("year", Evaluation.evaluation_at),
                ),
            )
            .where(Evaluation.employee_id == employee_id)
            .order_by(Evaluation.evaluation_at.desc())
        )

        res = await self.db.execute(stmt)
        return res.mappings().all()

    async def get_employee_salary(
        self, employee_id: int, as_of: datetime | None = None
    ):
        as_of = as_of or datetime.now(timezone.utc)

        stmt = (
            select(Salary)
            .where(
                Salary.employee_id == employee_id,
                Salary.start_at <= as_of,
                or_(Salary.end_at.is_(None), Salary.end_at > as_of),
            )
            .order_by(Salary.start_at.asc())
        )
        res = await self.db.execute(stmt)
        return res.scalars().first()
