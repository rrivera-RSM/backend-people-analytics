from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from ...base import Base


class SalaryOffer(Base):
    """ORM model for a proposed salary offer."""

    __tablename__ = "salary_offer"
    __table_args__ = (
        CheckConstraint(
            "new_salary > 0",
            name="ck_salary_offer_new_salary_positive",
        ),
        CheckConstraint(
            "new_bonus IS NULL OR new_bonus >= 0",
            name="ck_salary_offer_new_bonus_non_negative",
        ),
        CheckConstraint(
            "new_bonus IS NULL OR length(trim(month_payment_bonus)) > 0",
            name="ck_salary_offer_bonus_month_required",
        ),
        CheckConstraint(
            "bonus_next_fy IS NULL OR bonus_next_fy >= 0",
            name="ck_salary_offer_bonus_next_fy_non_negative",
        ),
        {"schema": "people"},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(nullable=False)
    new_salary: Mapped[float] = mapped_column(Float, nullable=False)
    new_bonus: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    month_payment_bonus: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )
    bonus_next_fy: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )
    new_category: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    observations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    aud_user_creation: Mapped[str] = mapped_column(String(150), nullable=False)
    aud_creation_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
