from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class RecomendacaoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    categoria: str
    descricao: str
    severidade: str


class MetricaResumida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tipo: str
    valor: float | None
    unidade: str | None


class AnalysisSimpleResponse(BaseModel):
    nota_geral: float | None = None
    feedback_ia: str | None = None
    recomendacoes: list[RecomendacaoResponse] = []
    metricas_resumidas: list[MetricaResumida] = []
    erro: str | None = None
