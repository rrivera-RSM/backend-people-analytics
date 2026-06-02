from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from ...base import Base


class OnaInsights(Base):
    __tablename__ = "ona_insights"
    __table_args__ = {"schema": "people"}

    id: Mapped[int] = mapped_column(primary_key=True)

    employee_id: Mapped[int | None] = mapped_column(
        ForeignKey("core.employee.id", ondelete="CASCADE"),
        nullable=True,
    )

    ona_category: Mapped[str] = mapped_column(String(20), nullable=False)

    n_different_categories_in: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    n_same_category_in: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    n_upper_categories_in: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    n_lower_categories_in: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True
    )

    n_different_departments_in: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    n_same_dept_office_in: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    n_unique_same_dept_office_in_no_ci: Mapped[Optional[Decimal]] = (
        mapped_column(Numeric(10, 2), nullable=True)
    )
    n_same_dept_office_in_no_ci: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True
    )

    n_total_votes_in: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True
    )

    p80_n_different_categories_in: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    p80_n_same_dept_office_in_no_ci: Mapped[Optional[Decimal]] = (
        mapped_column(Numeric(10, 2), nullable=True)
    )
    p80_n_unique_same_dept_office_in_no_ci: Mapped[Optional[Decimal]] = (
        mapped_column(Numeric(10, 2), nullable=True)
    )
    p80_n_same_category_in: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    p80_n_different_departments_in: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True
    )

    n_personas: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    n_respuestas: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    tasa_respuestas: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True
    )
