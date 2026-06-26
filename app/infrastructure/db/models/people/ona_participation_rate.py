from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Numeric
from sqlalchemy.orm import Mapped, mapped_column

from ...base import Base


class OnaParticipationRate(Base):
    __tablename__ = "ona_participation_rate"
    __table_args__ = {"schema": "people"}

    id: Mapped[int] = mapped_column(primary_key=True)
    society_id: Mapped[int] = mapped_column(Numeric, nullable=False)
    office_id: Mapped[int] = mapped_column(Numeric, nullable=False)
    employee_count: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    response_count: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    participation_rate: Mapped[Decimal] = mapped_column(
        Numeric, nullable=False
    )
