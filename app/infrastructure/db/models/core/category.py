from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from ...base import Base


class Category(Base):
    """
    Modelo ORM de Sociedad.

    """

    __tablename__ = "category"
    __table_args__ = {"schema": "core"}

    # ---- Columns ----
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
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
