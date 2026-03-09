from datetime import datetime
from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.infrastructure.db.base import Base


class EmployeeHistory(Base):
    """
    Modelo ORM de Historial de Empleado.
    Representa el historial de un empleado en la base de datos.
    """

    __tablename__ = "employee_hst"
    __table_args__ = {"schema": "core"}
    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("core.employee.id"), index=True
    )

    start_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    end_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    society_id: Mapped[int | None] = mapped_column(
        ForeignKey("society.id"), nullable=True
    )
    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("department.id"), nullable=True
    )
    office_id: Mapped[int | None] = mapped_column(
        ForeignKey("office.id"), nullable=True
    )
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("param.id"), nullable=True
    )
