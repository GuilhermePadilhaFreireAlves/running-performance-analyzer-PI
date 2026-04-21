from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.src.database import Base

if TYPE_CHECKING:
    from server.src.models.sessao_analise import SessaoAnalise


class Usuario(Base):
    __tablename__ = "usuario"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    altura_cm: Mapped[float] = mapped_column(Float, nullable=False)
    peso_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    nivel_experiencia: Mapped[str | None] = mapped_column(String(50), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    sessoes: Mapped[list["SessaoAnalise"]] = relationship(
        back_populates="usuario", cascade="all, delete-orphan"
    )
