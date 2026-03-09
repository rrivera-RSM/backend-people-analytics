from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from ...base import Base


class Employee(Base):
    """
    Modelo ORM de Employee.
    Representa a un empleado en la base de datos.
    """

    __tablename__ = "employee"
    __table_args__ = {"schema": "core"}

    # ---- Columns ----
    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=True
    )
    gender_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    dni: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    birth_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    joined_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    left_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    postal_code: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )
    bol_organic_onboard: Mapped[bool] = mapped_column(Boolean, default=False)
    aud_creation_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    aud_user_creation: Mapped[Optional[str]] = mapped_column(
        String(150), nullable=True
    )
    microsoft_id: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, nullable=True
    )
