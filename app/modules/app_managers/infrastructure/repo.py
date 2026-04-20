from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

# Ajusta estos imports a tu estructura real
from app.infrastructure.db.models.people.app_manager import AppManager
from app.infrastructure.db.models.people.app_manager_employee import (
    AppManagerEmployee,
)
from app.infrastructure.db.models.core.employee import Employee


class AppManagerPermissionRepo:
    """
    Repo encargado de gestionar las relaciones activas manager -> managee
    sobre people.app_manager_employee.
    """

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

    async def is_active_app_manager(self, manager_employee_id: int) -> bool:
        """
        Valida que el employee exista como AppManager activo.

        Asunción:
        - AppManager.microsoft_id guarda el OID de Entra/Azure AD
        - Employee.azure_oid contiene ese mismo OID
        """
        stmt = (
            select(AppManager.id)
            .join(Employee, Employee.id == AppManager.id)
            .where(
                Employee.id == manager_employee_id,
                AppManager.bol_active == 1,  # noqa: E712
            )
            .limit(1)
        )
        result = await self.session.scalar(stmt)
        return result is not None

    async def get_existing_employee_ids(
        self,
        employee_ids: Iterable[int],
    ) -> set[int]:
        ids = sorted(set(employee_ids))
        if not ids:
            return set()

        stmt = select(Employee.id).where(Employee.id.in_(ids))
        result = await self.session.scalars(stmt)
        return set(result.all())

    async def get_active_managee_ids(
        self,
        manager_employee_id: int,
        managee_ids: Iterable[int] | None = None,
    ) -> set[int]:
        stmt = select(AppManagerEmployee.employee_id).where(
            AppManagerEmployee.manager_id == manager_employee_id,
            AppManagerEmployee.bol_active == 1,
        )

        if managee_ids is not None:
            ids = sorted(set(managee_ids))
            if not ids:
                return set()
            stmt = stmt.where(AppManagerEmployee.employee_id.in_(ids))

        result = await self.session.scalars(stmt)
        return set(result.all())

    async def add_managee_relations(
        self,
        manager_employee_id: int,
        managee_ids: Iterable[int],
        audit_user: str | None,
    ) -> None:
        """
        Inserta nuevas relaciones activas.
        No reabre históricos: crea una nueva fila de vigencia.
        """
        ids = sorted(set(managee_ids))
        if not ids:
            return

        rows = [
            AppManagerEmployee(
                manager_id=manager_employee_id,
                employee_id=managee_id,
                bol_active=1,
                aud_user_creation=audit_user,
            )
            for managee_id in ids
        ]

        self.session.add_all(rows)
        await self.session.flush()

    async def revoke_managee_relations(
        self,
        manager_employee_id: int,
        managee_ids: Iterable[int],
    ) -> None:
        """
        Cierra vigencia de relaciones activas. No borra físicamente.
        """
        ids = sorted(set(managee_ids))
        if not ids:
            return
        stmt = (
            update(AppManagerEmployee)
            .where(
                AppManagerEmployee.manager_id == manager_employee_id,
                AppManagerEmployee.employee_id.in_(ids),
                AppManagerEmployee.bol_active == 1,  # noqa: E712
            )
            .values(
                bol_active=0,
            )
            .execution_options(synchronize_session=False)
        )

        await self.session.execute(stmt)
        await self.session.flush()
