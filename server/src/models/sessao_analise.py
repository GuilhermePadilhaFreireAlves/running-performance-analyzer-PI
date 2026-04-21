from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.src.database import Base

if TYPE_CHECKING:
    from server.src.models.metrica import Metrica
    from server.src.models.recomendacao import Recomendacao
    from server.src.models.usuario import Usuario


SESSAO_STATUS_VALUES: tuple[str, ...] = (
    "pendente",
    "validando_perspectiva",
    "detectando_pose",
    "calculando_metricas",
    "concluido",
    "erro_qualidade_keypoints",
    "erro_multiplas_pessoas",
)


class SessaoAnalise(Base):
    __tablename__ = "sessao_analise"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pendente','validando_perspectiva','detectando_pose',"
            "'calculando_metricas','concluido','erro_qualidade_keypoints',"
            "'erro_multiplas_pessoas')",
            name="ck_sessao_analise_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False, index=True
    )
    pace_min_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    fps: Mapped[float | None] = mapped_column(Float, nullable=True)
    nota_geral: Mapped[float | None] = mapped_column(Float, nullable=True)
    feedback_ia: Mapped[str | None] = mapped_column(Text, nullable=True)
    dados_brutos_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="pendente"
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    usuario: Mapped["Usuario"] = relationship(back_populates="sessoes")
    metricas: Mapped[list["Metrica"]] = relationship(
        back_populates="sessao", cascade="all, delete-orphan"
    )
    recomendacoes: Mapped[list["Recomendacao"]] = relationship(
        back_populates="sessao", cascade="all, delete-orphan"
    )
