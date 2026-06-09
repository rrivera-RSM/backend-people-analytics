from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from ...base import Base


class SalaryIncreaseAvg(Base):
    __tablename__ = "mv_salary_increase_avgs"
    __table_args__ = {"schema": "people"}

    society_id: Mapped[Optional[int]] = mapped_column(
        primary_key=True, nullable=True
    )
    office_id: Mapped[Optional[int]] = mapped_column(
        primary_key=True, nullable=True
    )
    category_id: Mapped[Optional[int]] = mapped_column(
        primary_key=True, nullable=True
    )
    department_id: Mapped[Optional[int]] = mapped_column(
        primary_key=True, nullable=True
    )
    avg_increase_amount: Mapped[float] = mapped_column(nullable=False)
    avg_increase_percentage: Mapped[float] = mapped_column(nullable=False)
    increases_count: Mapped[int] = mapped_column(nullable=False)
    g_society: Mapped[int] = mapped_column(primary_key=True, nullable=False)
    g_office: Mapped[int] = mapped_column(primary_key=True, nullable=False)
    g_category: Mapped[int] = mapped_column(primary_key=True, nullable=False)
    g_department: Mapped[int] = mapped_column(primary_key=True, nullable=False)


class BonusAvg(Base):
    __tablename__ = "mv_bonus_avgs"
    __table_args__ = {"schema": "people"}

    society_id: Mapped[Optional[int]] = mapped_column(
        primary_key=True, nullable=True
    )
    office_id: Mapped[Optional[int]] = mapped_column(
        primary_key=True, nullable=True
    )
    category_id: Mapped[Optional[int]] = mapped_column(
        primary_key=True, nullable=True
    )
    department_id: Mapped[Optional[int]] = mapped_column(
        primary_key=True, nullable=True
    )
    avg_bonus: Mapped[float] = mapped_column(nullable=False)
    records_count: Mapped[int] = mapped_column(nullable=False)
    g_society: Mapped[int] = mapped_column(primary_key=True, nullable=False)
    g_office: Mapped[int] = mapped_column(primary_key=True, nullable=False)
    g_category: Mapped[int] = mapped_column(primary_key=True, nullable=False)
    g_department: Mapped[int] = mapped_column(primary_key=True, nullable=False)
