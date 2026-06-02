from datetime import date as date_type
from datetime import datetime, timezone
from app.modules.employees.schemas import (
    EmployeeRowOut,
    EmployeeTimelineEvolutionOut,
    EmployeeTimelineEventOut,
)
from app.modules.employees.infrastructure.repo import EmployeeRepo
from app.auth import graph_get_user_photo_by_oid
from fastapi import HTTPException, Response


class EmployeeService:
    def __init__(self, read_repo: EmployeeRepo):
        self.read_repo = read_repo

    @staticmethod
    def _clean_timeline_payload(payload: dict) -> dict:
        return {key: value for key, value in payload.items() if value}

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

    async def employee_timeline_evolution(
        self, employee_id: int
    ) -> EmployeeTimelineEvolutionOut:
        def _to_utc(value: datetime | date_type) -> datetime:
            if isinstance(value, datetime):
                if value.tzinfo is None:
                    return value.replace(tzinfo=timezone.utc)
                return value.astimezone(timezone.utc)

            if isinstance(value, date_type):
                return datetime(
                    value.year,
                    value.month,
                    value.day,
                    tzinfo=timezone.utc,
                )

            raise ValueError(
                f"Unsupported date value type for timeline: {type(value)}"
            )

        employee = await self.read_repo.get_employee_by_id(employee_id)
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")

        history_rows = await self.read_repo.get_employee_history_timeline(
            employee_id=employee_id
        )
        salary_rows = await self.read_repo.get_employee_salary_timeline(
            employee_id=employee_id
        )
        evaluation_rows = await self.read_repo.get_employee_evaluation_timeline(
            employee_id=employee_id
        )

        events: list[EmployeeTimelineEventOut] = []

        for row in history_rows:
            events.append(
                EmployeeTimelineEventOut(
                    event_type="org_change",
                    event_at=_to_utc(row.start_at),
                    title="Cambio organizativo",
                    payload=self._clean_timeline_payload(
                        {
                            "start_at": row.start_at.isoformat(),
                            "end_at": (
                                row.end_at.isoformat() if row.end_at else None
                            ),
                            "society_id": row.society_id,
                            "society_name": row.society_name,
                            "department_id": row.department_id,
                            "department_name": row.department_name,
                            "office_id": row.office_id,
                            "office_name": row.office_name,
                            "category_id": row.category_id,
                            "category_name": row.category_name,
                        }
                    ),
                )
            )

        for row in salary_rows:
            events.append(
                EmployeeTimelineEventOut(
                    event_type="salary_change",
                    event_at=_to_utc(row.start_at),
                    title="Cambio retributivo",
                    payload=self._clean_timeline_payload(
                        {
                            "start_at": row.start_at.isoformat(),
                            "end_at": (
                                row.end_at.isoformat() if row.end_at else None
                            ),
                            "salary": float(row.salary),
                            "bonus": (
                                float(row.bonus)
                                if row.bonus is not None
                                else None
                            ),
                        }
                    ),
                )
            )

        for row in evaluation_rows:
            events.append(
                EmployeeTimelineEventOut(
                    event_type="evaluation",
                    event_at=_to_utc(row.evaluation_at),
                    title="Evaluación desempeño",
                    payload=self._clean_timeline_payload(
                        {
                            "evaluation_at": row.evaluation_at.isoformat(),
                            "final_score": float(row.final_score),
                            "bol_positive_impact": (
                                float(row.bol_positive_impact)
                                if row.bol_positive_impact is not None
                                else None
                            ),
                        }
                    ),
                )
            )

        events.sort(key=lambda item: item.event_at)

        return EmployeeTimelineEvolutionOut(
            employee_id=employee.id,
            employee_name=f"{employee.first_name} {employee.last_name}",
            joined_at=employee.joined_at,
            left_at=employee.left_at,
            total_events=len(events),
            events=events,
        )
