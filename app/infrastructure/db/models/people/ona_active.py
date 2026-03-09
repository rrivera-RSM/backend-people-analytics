from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from ...base import Base


class OnaActive(Base):
    """
    Modelo ORM de ONA Activo.
    Representa un registro de ONA Activo en la base de datos.
    """

    __tablename__ = "ona_active"
    __table_args__ = {"schema": "people"}

    # ---- Columns ----
    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(nullable=False)
    ona_category_id: Mapped[int] = mapped_column(nullable=False)
    ona_influence_id: Mapped[int] = mapped_column(nullable=False)
    percentile_1: Mapped[float] = mapped_column(nullable=False)
    percentile_2: Mapped[float] = mapped_column(nullable=False)
    percentile_3: Mapped[float] = mapped_column(nullable=False)
    percentile_4: Mapped[float] = mapped_column(nullable=False)
    degree_centrality: Mapped[float] = mapped_column(Float, nullable=False)
    closeness_centrality: Mapped[float] = mapped_column(Float, nullable=True)
    betweenness_centrality: Mapped[float] = mapped_column(Float, nullable=True)
    eigenvector_centrality: Mapped[float] = mapped_column(Float, nullable=True)
    aud_creation_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    aud_user_creation: Mapped[Optional[str]] = mapped_column(
        String(150), nullable=True
    )
