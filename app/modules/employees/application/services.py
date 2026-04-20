from datetime import datetime
from app.modules.employees.schemas import EmployeeRowOut
from app.modules.employees.infrastructure.repo import EmployeeRepo
from app.auth import graph_get_user_photo_by_oid
from fastapi import HTTPException, Response


class EmployeeService:
    def __init__(self, read_repo: EmployeeRepo):
        self.read_repo = read_repo

    async def list_rows(
        self,
        as_of: datetime | None = None,
        office: str | None = None,
        department: str | None = None,
        society: str | None = None,
        category: str | None = None,
        q: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[EmployeeRowOut]:
        rows = await self.read_repo.list_employee_rows(
            as_of=as_of,
            office=office,
            department=department,
            society=society,
            category=category,
            q=q,
            limit=limit,
            offset=offset,
        )
        return [EmployeeRowOut(**row) for row in rows]

    async def list_rows_by_manager(
        self,
        current_user,
        as_of: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[EmployeeRowOut]:

        azure_oid = getattr(current_user, "oid", None)

        manager_employee_id = await self.read_repo.get_employee_id_by_oid(
            azure_oid=azure_oid
        )
        rows = await self.read_repo.list_employee_rows_by_manager(
            manager_employee_id=manager_employee_id,
            as_of=as_of,
            limit=limit,
            offset=offset,
        )
        return [EmployeeRowOut(**row) for row in rows]

    async def employee_photo(
        self, employee_id: int, authorization: str
    ) -> dict:
        # 1) DB: obtener azure_oid
        oid = await self.read_repo.get_employee_oid(employee_id=employee_id)
        if not oid:
            raise HTTPException(status_code=404, detail="No OID for employee")

        # 2) Graph: /users/{oid}/photo/$value
        photo = await graph_get_user_photo_by_oid(
            oid=oid, size="48x48", authorization=authorization
        )

        if not photo:
            raise HTTPException(
                status_code=404, detail="No photo for employee"
            )

        return Response(
            content=photo["photo"]["bytes"],
            media_type=photo["photo"]["contentType"],
            headers={
                "Cache-Control": "private, max-age=3600",
            },
        )

    async def employee_evaluations(self, employee_id: int) -> list[dict]:
        evaluations = await self.read_repo.get_employee_scores(
            employee_id=employee_id
        )
        return evaluations

    async def employee_monetary_info(
        self, employee_id: int, as_of: datetime | None = None
    ) -> dict:
        monetary_info = await self.read_repo.get_employee_salary(
            employee_id=employee_id, as_of=as_of
        )
        return monetary_info

    async def employee_attrition_rate(
        self, employee_id: int, as_of: datetime | None = None
    ) -> dict:
        attrition_info = await self.read_repo.get_employee_attrition_rate(
            employee_id=employee_id, as_of=as_of
        )
        attrition_rate = (
            attrition_info.attrition_rate if attrition_info else None
        )
        attrition_response = {
            "employee_id": employee_id,
            "attrition_rate": attrition_rate,
        }
        return attrition_response
