from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, Float
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from ...base import Base


class EmployeeAttrition(Base):
    """
    Modelo ORM de Employee attrition.
    Representa un registro de ONA Activo en la base de datos.
    """

    __tablename__ = "employee_attrition"
    __table_args__ = {"schema": "people"}

    # ---- Columns ----
    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(nullable=False)
    attrition_rate: Mapped[float] = mapped_column(Float, nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    aud_creation_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    aud_user_creation: Mapped[Optional[str]] = mapped_column(
        String(150), nullable=True
    )
