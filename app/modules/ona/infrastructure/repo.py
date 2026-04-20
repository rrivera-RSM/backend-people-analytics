from __future__ import annotations

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.core.employee import Employee
from app.infrastructure.db.models.people.ona_active import OnaActive
from app.infrastructure.db.models.people.ona_employee_node import (
    OnaEmployeeNode,
)


class OnaRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_ona_relations(self):
        stmt = (
            select(OnaEmployeeNode)
            .join(Employee, Employee.id == OnaEmployeeNode.from_employee_id)
            .order_by(
                OnaEmployeeNode.from_employee_id,
                OnaEmployeeNode.to_employee_id,
            )
        )
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def get_ona_relations_by_employee_id(self, employee_id: int):
        stmt = (
            select(OnaEmployeeNode)
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
        return res.scalars().all()

    async def get_ona_active_by_employee_id(self, employee_id: int):
        try:
            stmt = select(OnaActive).where(
                OnaActive.employee_id == employee_id
            )
            res = await self.db.execute(stmt)
            return res.scalar_one_or_none()
        except Exception:
            return None
