from __future__ import annotations

from datetime import datetime

from sqlalchemy import distinct, func, select, union
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.core.employee import Employee
from app.infrastructure.db.models.people.evaluation import Evaluation
from app.infrastructure.db.models.people.ona_active import OnaActive
from app.infrastructure.db.models.people.ona_employee_node import (
    OnaEmployeeNode,
)
from app.infrastructure.db.models.people.ona_insights import OnaInsights
from app.modules.employee_insights.schemas import EmployeeInsightContext


class EmployeeInsightRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_employee_by_id(self, employee_id: int) -> Employee | None:
        stmt = select(Employee).where(Employee.id == employee_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_latest_two_evaluations(
        self,
        employee_id: int,
        as_of: datetime,
    ) -> tuple[Evaluation | None, Evaluation | None]:
        stmt = (
            select(Evaluation)
            .where(Evaluation.employee_id == employee_id)
            .where(Evaluation.evaluation_at <= as_of)
            .order_by(Evaluation.evaluation_at.desc(), Evaluation.id.desc())
            .limit(2)
        )
        result = await self.session.execute(stmt)
        rows = list(result.scalars().all())

        current_evaluation = rows[0] if len(rows) >= 1 else None
        previous_evaluation = rows[1] if len(rows) >= 2 else None
        return current_evaluation, previous_evaluation

    async def get_ona_records(
        self,
        employee_id: int,
        as_of: datetime,
    ) -> list[OnaActive]:
        stmt = (
            select(OnaActive)
            .where(OnaActive.employee_id == employee_id)
            .where(OnaActive.aud_creation_at <= as_of)
            .order_by(OnaActive.aud_creation_at.desc(), OnaActive.id.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_ona_insight_records(
        self,
        employee_id: int,
    ) -> list[OnaInsights]:
        """
        Recupera los registros agregados de people.ona_insights del empleado.

        Asunción v1:
        - si existen múltiples filas por empleado (p. ej. distintas category),
          el service agregará por máximos.
        """
        stmt = (
            select(OnaInsights)
            .where(OnaInsights.employee_id == employee_id)
            .order_by(OnaInsights.id.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_ona_relation_counts(
        self,
        employee_id: int,
        as_of: datetime,
    ) -> tuple[int, int, int]:
        incoming_stmt = (
            select(func.count(distinct(OnaEmployeeNode.from_employee_id)))
            .where(OnaEmployeeNode.to_employee_id == employee_id)
            .where(OnaEmployeeNode.aud_creation_at <= as_of)
        )
        outgoing_stmt = (
            select(func.count(distinct(OnaEmployeeNode.to_employee_id)))
            .where(OnaEmployeeNode.from_employee_id == employee_id)
            .where(OnaEmployeeNode.aud_creation_at <= as_of)
        )

        incoming_result = await self.session.execute(incoming_stmt)
        outgoing_result = await self.session.execute(outgoing_stmt)

        incoming_unique_relations = int(incoming_result.scalar() or 0)
        outgoing_unique_relations = int(outgoing_result.scalar() or 0)

        peer_union = union(
            select(OnaEmployeeNode.to_employee_id.label("peer_id"))
            .where(OnaEmployeeNode.from_employee_id == employee_id)
            .where(OnaEmployeeNode.aud_creation_at <= as_of),
            select(OnaEmployeeNode.from_employee_id.label("peer_id"))
            .where(OnaEmployeeNode.to_employee_id == employee_id)
            .where(OnaEmployeeNode.aud_creation_at <= as_of),
        ).subquery()

        unique_stmt = select(func.count()).select_from(peer_union)
        unique_result = await self.session.execute(unique_stmt)
        unique_relations = int(unique_result.scalar() or 0)

        return (
            incoming_unique_relations,
            outgoing_unique_relations,
            unique_relations,
        )

    async def get_employee_insight_context(
        self,
        employee_id: int,
        as_of: datetime,
    ) -> EmployeeInsightContext | None:
        employee = await self.get_employee_by_id(employee_id)
        if employee is None:
            return None

        current_evaluation, previous_evaluation = (
            await self.get_latest_two_evaluations(
                employee_id=employee_id,
                as_of=as_of,
            )
        )

        ona_records = await self.get_ona_records(
            employee_id=employee_id,
            as_of=as_of,
        )

        ona_insight_records = await self.get_ona_insight_records(
            employee_id=employee_id,
        )

        (
            incoming_unique_relations,
            outgoing_unique_relations,
            unique_relations,
        ) = await self.get_ona_relation_counts(
            employee_id=employee_id,
            as_of=as_of,
        )

        return EmployeeInsightContext(
            employee=employee,
            current_evaluation=current_evaluation,
            previous_evaluation=previous_evaluation,
            ona_records=ona_records,
            ona_insight_records=ona_insight_records,
            incoming_unique_relations=incoming_unique_relations,
            outgoing_unique_relations=outgoing_unique_relations,
            unique_relations=unique_relations,
        )
