from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from ...base import Base


class OnaInsights(Base):
    """
    Modelo ORM de OnaInsights.

    Representa un registro agregado de insights ONA de un empleado,
    calculado a partir de métricas de red organizativa y clasificaciones
    derivadas.

    La columna `ona_category` debe contener uno de estos valores:
    - 'hipo'
    - 'central'
    - 'peripheral'
    - 'intermediary'
    """

    __tablename__ = "ona_insights"
    __table_args__ = {"schema": "people"}

    # ---- Columns ----
    id: Mapped[int] = mapped_column(primary_key=True)

    employee_id: Mapped[int | None] = mapped_column(
        ForeignKey("core.employee.id", ondelete="CASCADE"),
        nullable=True,
    )

    ona_category: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    n_different_categories_in: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )
    n_same_category_in: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )
    n_upper_categories_in: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )
    n_different_departments_in: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )
    n_same_dept_office_in: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )
    n_total_votes_in: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )
    percentile_80_votes_dpt_office: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )
    category_from_senior: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )
    category_from_manager: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )
    category_from_junior: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )
    category_from_structure: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )
    category_from_director: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )
