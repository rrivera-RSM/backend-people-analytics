from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from ...base import Base


class OnaEmployeeNode(Base):
    """
    Modelo para representar las conexiones entre empleados en el análisis
    de redes organizacionales (ONA).
    """

    __tablename__ = "ona_employee_node"
    __table_args__ = {"schema": "people"}

    # ---- Columns ----
    id: Mapped[int] = mapped_column(primary_key=True)
    ona_question_id: Mapped[int] = mapped_column(nullable=False)
    from_employee_id: Mapped[int] = mapped_column(nullable=False)
    to_employee_id: Mapped[int] = mapped_column(nullable=False)
    aud_creation_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    aud_user_creation: Mapped[Optional[str]] = mapped_column(
        String(150), nullable=True
    )
