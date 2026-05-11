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
