from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.src.database import Base

if TYPE_CHECKING:
    from server.src.models.sessao_analise import SessaoAnalise


SEVERIDADE_VALUES: tuple[str, ...] = ("informativo", "atencao", "critico")


class Recomendacao(Base):
    __tablename__ = "recomendacao"
    __table_args__ = (
        CheckConstraint(
            "severidade IN ('informativo','atencao','critico')",
            name="ck_recomendacao_severidade",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sessao_id: Mapped[int] = mapped_column(
        ForeignKey("sessao_analise.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    categoria: Mapped[str] = mapped_column(String(100), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    severidade: Mapped[str] = mapped_column(String(20), nullable=False)

    sessao: Mapped["SessaoAnalise"] = relationship(back_populates="recomendacoes")
