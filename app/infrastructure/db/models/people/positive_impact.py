from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from ...base import Base


class PositiveImpact(Base):
    """
    Modelo ORM de Impacto Positivo.
    Representa un registro de impacto positivo en la base de datos.
    """

    __tablename__ = "positive_impact"
    __table_args__ = {"schema": "people"}

    # ---- Columns ----
    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(nullable=False)
    evaluation_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    bol_positive_impact: Mapped[float] = mapped_column(nullable=False)
    aud_creation_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    aud_user_creation: Mapped[Optional[str]] = mapped_column(
        String(150), nullable=True
    )
