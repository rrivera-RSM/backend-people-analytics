from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from ...base import Base


class Kpis(Base):
    """
    Modelo ORM de Kpis.
    Representa un registro de evaluación en la base de datos.
    """

    __tablename__ = "salary_avg"
    __table_args__ = {"schema": "people"}

    # ---- Columns ----
    id: Mapped[int] = mapped_column(primary_key=True)
    start_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    end_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    society_id: Mapped[int] = mapped_column(nullable=False)
    department_id: Mapped[int] = mapped_column(nullable=False)
    office_id: Mapped[int] = mapped_column(nullable=False)
    category_id: Mapped[int] = mapped_column(nullable=False)
    salary_avg: Mapped[float] = mapped_column(nullable=False)
    bonus_avg: Mapped[float] = mapped_column(nullable=False)

    aud_creation_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    aud_user_creation: Mapped[Optional[str]] = mapped_column(
        String(150), nullable=True
    )
