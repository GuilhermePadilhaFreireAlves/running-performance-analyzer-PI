from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, false
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.src.database import Base

if TYPE_CHECKING:
    from server.src.models.sessao_analise import SessaoAnalise


class Metrica(Base):
    __tablename__ = "metrica"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sessao_id: Mapped[int] = mapped_column(
        ForeignKey("sessao_analise.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tipo: Mapped[str] = mapped_column(String(100), nullable=False)
    valor: Mapped[float | None] = mapped_column(Float, nullable=True)
    unidade: Mapped[str | None] = mapped_column(String(50), nullable=True)
    apenas_informativa: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )

    sessao: Mapped["SessaoAnalise"] = relationship(back_populates="metricas")
