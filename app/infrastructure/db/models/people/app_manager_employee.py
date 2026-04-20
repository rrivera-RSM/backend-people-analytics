from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, DateTime, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from ...base import Base


class AppManagerEmployee(Base):
    """
    Modelo ORM de Employee.
    Representa a un empleado en la base de datos.
    """

    __tablename__ = "app_manager_employee"
    __table_args__ = {"schema": "people"}

    # ---- Columns ----
    id: Mapped[int] = mapped_column(primary_key=True)
    manager_id: Mapped[int] = mapped_column(
        ForeignKey("core.employee.id"), index=True
    )
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("core.employee.id"), index=True
    )
    bol_active: Mapped[int] = mapped_column(Integer, default=0)

    aud_creation_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    aud_user_creation: Mapped[Optional[str]] = mapped_column(
        String(150), nullable=True
    )
