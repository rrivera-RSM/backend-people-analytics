from __future__ import annotations

from sqlalchemy import Integer, extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.core.employee import Employee
from app.infrastructure.db.models.people.evaluation import Evaluation
from app.infrastructure.db.models.people.ona_active import OnaActive
from app.modules.evaluations.schemas import (
    EvaluationScatterLatestCycleOut,
    EvaluationScatterPointOut,
)


class EvaluationScatterRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_latest_cycle_scatter(
        self,
    ) -> EvaluationScatterLatestCycleOut:
        latest_cycle_stmt = select(
            func.max(extract("year", Evaluation.evaluation_at)).label(
                "cycle_year"
            )
        )
        latest_cycle_result = await self.session.execute(latest_cycle_stmt)
        cycle_year = latest_cycle_result.scalar_one_or_none()

        if cycle_year is None:
            return EvaluationScatterLatestCycleOut(
                cycle_year=0,
                cycle_label="Sin ejercicio",
                total_points=0,
                points=[],
            )

        # --------------------------------------------------------------
        # 1) Última evaluación del último ejercicio por empleado
        # --------------------------------------------------------------
        ranked_evaluations_subq = (
            select(
                Evaluation.id.label("evaluation_id"),
                Evaluation.employee_id.label("employee_id"),
                Evaluation.evaluation_at.label("evaluation_at"),
                extract("year", Evaluation.evaluation_at)
                .cast(Integer)
                .label("evaluation_year"),
                Evaluation.final_score.label("final_score"),
                func.row_number()
                .over(
                    partition_by=Evaluation.employee_id,
                    order_by=(
                        Evaluation.evaluation_at.desc(),
                        Evaluation.id.desc(),
                    ),
                )
                .label("rn"),
            )
            .where(extract("year", Evaluation.evaluation_at) == cycle_year)
            .subquery()
        )

        # --------------------------------------------------------------
        # 2) Último OnaActive por empleado
        # --------------------------------------------------------------
        ranked_ona_active_subq = select(
            OnaActive.employee_id.label("employee_id"),
            OnaActive.overall_percentile.label("overall_percentile"),
            func.row_number()
            .over(
                partition_by=OnaActive.employee_id,
                order_by=(
                    OnaActive.aud_creation_at.desc(),
                    OnaActive.id.desc(),
                ),
            )
            .label("rn"),
        ).subquery()

        latest_ona_active_subq = (
            select(
                ranked_ona_active_subq.c.employee_id,
                ranked_ona_active_subq.c.overall_percentile,
            )
            .where(ranked_ona_active_subq.c.rn == 1)
            .subquery()
        )

        # --------------------------------------------------------------
        # 3) Join final
        # --------------------------------------------------------------
        stmt = (
            select(
                ranked_evaluations_subq.c.employee_id,
                Employee.society_id,
                Employee.department_id,
                Employee.category_id,
                ranked_evaluations_subq.c.evaluation_id,
                ranked_evaluations_subq.c.evaluation_at,
                ranked_evaluations_subq.c.evaluation_year,
                ranked_evaluations_subq.c.final_score,
                latest_ona_active_subq.c.overall_percentile,
            )
            .join(
                Employee, Employee.id == ranked_evaluations_subq.c.employee_id
            )
            .outerjoin(
                latest_ona_active_subq,
                latest_ona_active_subq.c.employee_id
                == ranked_evaluations_subq.c.employee_id,
            )
            .where(ranked_evaluations_subq.c.rn == 1)
            .where(
                (Employee.left_at.is_(None))
                | (Employee.left_at > ranked_evaluations_subq.c.evaluation_at)
            )
            .order_by(
                ranked_evaluations_subq.c.final_score.desc(),
                ranked_evaluations_subq.c.employee_id.asc(),
            )
        )

        result = await self.session.execute(stmt)
        rows = result.all()

        points = [
            EvaluationScatterPointOut(
                employee_id=row.employee_id,
                society_id=row.society_id,
                department_id=row.department_id,
                category_id=row.category_id,
                evaluation_id=row.evaluation_id,
                evaluation_at=row.evaluation_at,
                evaluation_year=row.evaluation_year,
                final_score=float(row.final_score),
                overall_percentile=(
                    float(row.overall_percentile)
                    if row.overall_percentile is not None
                    else None
                ),
            )
            for row in rows
        ]

        return EvaluationScatterLatestCycleOut(
            cycle_year=int(cycle_year),
            cycle_label=f"Ejercicio {int(cycle_year)}",
            total_points=len(points),
            points=points,
        )
