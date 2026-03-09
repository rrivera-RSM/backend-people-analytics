from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.infrastructure.db.base import Base


class Param(Base):
    """
    Modelo ORM de Parámetro.
    Representa un parámetro en la base de datos.
    """
    __tablename__ = "param"
    __table_args__ = {"schema": "core"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    param_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    param_key: Mapped[str] = mapped_column(String(50), nullable=False)
    param_value: Mapped[str] = mapped_column(String(200), nullable=False)
    param_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
