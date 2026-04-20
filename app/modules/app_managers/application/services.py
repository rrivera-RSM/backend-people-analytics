from __future__ import annotations
from fastapi import HTTPException

from app.modules.app_managers.infrastructure.repo import (
    AppManagerPermissionRepo,
)
from app.modules.app_managers.schemas import (
    AddManageesOut,
    RevokeManageesOut,
)


class AppManagerPermissionService:
    """
    Service de aplicación para:
    - añadir managees a un app manager
    - revocar managees a un app manager
    """

    def __init__(self, repo: AppManagerPermissionRepo) -> None:
        self.repo = repo

    async def add_managees(
        self,
        manager_employee_id: int,
        current_user: str | None,
        managee_ids: list[int],
    ) -> AddManageesOut:
        audit_user = getattr(current_user, "email", None) or "unknown"
        requested = self._normalize_ids(managee_ids)

        await self._ensure_manager_is_valid(manager_employee_id)

        existing_employee_ids = await self.repo.get_existing_employee_ids(
            [manager_employee_id, *requested]
        )

        # self-management bloqueado
        self_management_blocked = (
            [manager_employee_id] if manager_employee_id in requested else []
        )

        valid_requested = [
            employee_id
            for employee_id in requested
            if employee_id != manager_employee_id
        ]

        invalid_employee_ids = sorted(
            set(valid_requested)
            - (existing_employee_ids - {manager_employee_id})
        )

        current_active = await self.repo.get_active_managee_ids(
            manager_employee_id=manager_employee_id,
            managee_ids=valid_requested,
        )

        to_add = sorted(
            set(valid_requested)
            - set(invalid_employee_ids)
            - set(current_active)
        )
        already_active = sorted(current_active)

        try:
            if to_add:
                await self.repo.add_managee_relations(
                    manager_employee_id=manager_employee_id,
                    managee_ids=to_add,
                    audit_user=audit_user,
                )
                await self.repo.commit()
        except Exception:
            await self.repo.rollback()
            raise

        active_after = sorted(
            await self.repo.get_active_managee_ids(manager_employee_id)
        )

        return AddManageesOut(
            manager_employee_id=manager_employee_id,
            requested=requested,
            added=to_add,
            already_active=already_active,
            invalid_employee_ids=invalid_employee_ids,
            self_management_blocked=self_management_blocked,
            active_managees_after_operation=active_after,
        )

    async def revoke_managees(
        self,
        manager_employee_id: int,
        managee_ids: list[int],
    ) -> RevokeManageesOut:
        requested = self._normalize_ids(managee_ids)

        await self._ensure_manager_is_valid(manager_employee_id)

        existing_employee_ids = await self.repo.get_existing_employee_ids(
            [manager_employee_id, *requested]
        )

        # self-management bloqueado
        self_management_blocked = (
            [manager_employee_id] if manager_employee_id in requested else []
        )

        valid_requested = [
            employee_id
            for employee_id in requested
            if employee_id != manager_employee_id
        ]

        invalid_employee_ids = sorted(
            set(valid_requested)
            - (existing_employee_ids - {manager_employee_id})
        )

        active_requested = await self.repo.get_active_managee_ids(
            manager_employee_id=manager_employee_id,
            managee_ids=valid_requested,
        )

        revoked = sorted(active_requested)
        already_inactive = sorted(
            set(valid_requested) - set(invalid_employee_ids) - set(revoked)
        )

        try:
            if revoked:
                await self.repo.revoke_managee_relations(
                    manager_employee_id=manager_employee_id,
                    managee_ids=revoked,
                )
                await self.repo.commit()
        except Exception:
            await self.repo.rollback()
            raise

        active_after = sorted(
            await self.repo.get_active_managee_ids(manager_employee_id)
        )

        return RevokeManageesOut(
            manager_employee_id=manager_employee_id,
            requested=requested,
            revoked=revoked,
            already_inactive=already_inactive,
            invalid_employee_ids=invalid_employee_ids,
            self_management_blocked=self_management_blocked,
            active_managees_after_operation=active_after,
        )

    async def _ensure_manager_is_valid(self, manager_employee_id: int) -> None:
        exists = await self.repo.employee_exists(manager_employee_id)
        if not exists:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Manager employee_id {manager_employee_id} "
                    "does not exist."
                ),
            )

        is_app_manager = await self.repo.is_active_app_manager(
            manager_employee_id
        )
        if not is_app_manager:
            raise HTTPException(
                status_code=403,
                detail=(
                    f"Employee_id {manager_employee_id} "
                    "is not an active app manager."
                ),
            )

    @staticmethod
    def _normalize_ids(employee_ids: list[int]) -> list[int]:
        """
        Elimina duplicados preservando orden de entrada.
        """
        seen: set[int] = set()
        normalized: list[int] = []

        for employee_id in employee_ids:
            if employee_id not in seen:
                seen.add(employee_id)
                normalized.append(employee_id)

        return normalized
