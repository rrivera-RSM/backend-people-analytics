from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from ...base import Base


class Department(Base):
    """
    Modelo ORM de Departamento.

    """

    __tablename__ = "department"
    __table_args__ = {"schema": "core"}

    # ---- Columns ----
    id: Mapped[int] = mapped_column(primary_key=True)
    society_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    description: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    aud_creation_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    aud_user_creation: Mapped[Optional[str]] = mapped_column(
        String(150), nullable=True
    )
