from datetime import datetime
from pydantic import BaseModel


class EmployeeRowOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    dni: str
    email: str

    office_id: int | None = None
    office_name: str | None = None

    department_id: int | None = None
    department_name: str | None = None

    society_id: int | None = None
    society_name: str | None = None

    category_id: int | None = None
    category_name: str | None = None
    attrition_rate: float | None = None

    joined_at: datetime
    birth_date: datetime | None = None


class EmployeeTimelineEventOut(BaseModel):
    event_type: str
    event_at: datetime
    title: str
    payload: dict


class EmployeeTimelineEvolutionOut(BaseModel):
    employee_id: int
    employee_name: str
    joined_at: datetime | None = None
    left_at: datetime | None = None
    total_events: int
    events: list[EmployeeTimelineEventOut]
