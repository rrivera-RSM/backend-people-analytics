from __future__ import annotations

from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.infrastructure.db.models.core.employee import Employee
from app.infrastructure.db.models.people.ona_active import OnaActive
from app.infrastructure.db.models.people.ona_employee_node import (
    OnaEmployeeNode,
)
from app.infrastructure.db.models.people.ona_insights import OnaInsights
from app.infrastructure.db.models.people.ona_participation_rate import (
    OnaParticipationRate,
)


class OnaRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_ona_relations(self, society_id: int | None = None):
        stmt = (
            select(
                OnaEmployeeNode.from_employee_id,
                OnaEmployeeNode.to_employee_id,
            )
            .join(Employee, Employee.id == OnaEmployeeNode.from_employee_id)
        )
        if society_id is not None:
            stmt = stmt.where(Employee.society_id == society_id)
        stmt = stmt.order_by(
            OnaEmployeeNode.from_employee_id,
            OnaEmployeeNode.to_employee_id,
        )
        edges_res = await self.db.execute(stmt)
        edge_rows = edges_res.all()

        edges = [
            {
                "from_id": row.from_employee_id,
                "to_id": row.to_employee_id,
            }
            for row in edge_rows
        ]

        employee_ids = {
            employee_id
            for row in edge_rows
            for employee_id in (row.from_employee_id, row.to_employee_id)
        }
        if not employee_ids:
            return {"nodes": [], "edges": []}

        latest_insights_subq = (
            select(
                OnaInsights.employee_id.label("employee_id"),
                func.max(OnaInsights.id).label("latest_id"),
            )
            .where(OnaInsights.employee_id.in_(employee_ids))
            .group_by(OnaInsights.employee_id)
            .subquery()
        )
        latest_active_subq = (
            select(
                OnaActive.employee_id.label("employee_id"),
                func.max(OnaActive.id).label("latest_id"),
            )
            .where(OnaActive.employee_id.in_(employee_ids))
            .group_by(OnaActive.employee_id)
            .subquery()
        )

        node_stmt = (
            select(
                Employee.id.label("employee_id"),
                OnaInsights.ona_category.label("ona_category"),
                OnaActive.graph_x_coordinate.label("graph_x_coordinate"),
                OnaActive.graph_y_coordinate.label("graph_y_coordinate"),
            )
            .join(
                latest_insights_subq,
                latest_insights_subq.c.employee_id == Employee.id,
                isouter=True,
            )
            .join(
                OnaInsights,
                OnaInsights.id == latest_insights_subq.c.latest_id,
                isouter=True,
            )
            .join(
                latest_active_subq,
                latest_active_subq.c.employee_id == Employee.id,
                isouter=True,
            )
            .join(
                OnaActive,
                OnaActive.id == latest_active_subq.c.latest_id,
                isouter=True,
            )
            .where(Employee.id.in_(employee_ids))
            .order_by(Employee.id)
        )

        nodes_res = await self.db.execute(node_stmt)
        nodes = [
            {
                "employee_id": row.employee_id,
                "ona_category": row.ona_category,
                "graph_x_coordinate": row.graph_x_coordinate,
                "graph_y_coordinate": row.graph_y_coordinate,
            }
            for row in nodes_res
        ]

        return {"nodes": nodes, "edges": edges}

    async def get_ona_relations_by_employee_id(self, employee_id: int):
        from_insight = aliased(OnaInsights)
        to_insight = aliased(OnaInsights)

        from_category_subq = (
            select(from_insight.ona_category)
            .where(from_insight.employee_id == OnaEmployeeNode.from_employee_id)
            .order_by(from_insight.id.desc())
            .limit(1)
            .scalar_subquery()
        )
        to_category_subq = (
            select(to_insight.ona_category)
            .where(to_insight.employee_id == OnaEmployeeNode.to_employee_id)
            .order_by(to_insight.id.desc())
            .limit(1)
            .scalar_subquery()
        )

        stmt = (
            select(
                OnaEmployeeNode.from_employee_id,
                OnaEmployeeNode.to_employee_id,
                OnaEmployeeNode.ona_question_id,
                from_category_subq.label("from_ona_category"),
                to_category_subq.label("to_ona_category"),
            )
            .where(
                or_(
                    OnaEmployeeNode.from_employee_id == employee_id,
                    OnaEmployeeNode.to_employee_id == employee_id,
                )
            )
            .order_by(
                OnaEmployeeNode.from_employee_id,
                OnaEmployeeNode.to_employee_id,
            )
        )
        res = await self.db.execute(stmt)
        return res.mappings().all()

    async def get_ona_active_by_employee_id(self, employee_id: int):
        try:
            stmt = select(OnaActive).where(
                OnaActive.employee_id == employee_id
            )
            res = await self.db.execute(stmt)
            return res.scalar_one_or_none()
        except Exception:
            return None

    async def get_participation_rate(
        self, society_id: int, office_id: int
    ):
        stmt = (
            select(
                OnaParticipationRate.id,
                OnaParticipationRate.society_id,
                OnaParticipationRate.office_id,
                OnaParticipationRate.employee_count,
                OnaParticipationRate.response_count,
                OnaParticipationRate.participation_rate,
            )
            .where(
                OnaParticipationRate.society_id == society_id,
                OnaParticipationRate.office_id == office_id,
            )
            .order_by(OnaParticipationRate.id.desc())
            .limit(1)
        )
        res = await self.db.execute(stmt)
        row = res.mappings().first()
        return dict(row) if row else None
