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


class RawFrame(BaseModel):
    """Frame individual na resposta de dados brutos (US-018).

    ``keypoints`` é uma lista de 17 entradas, cada uma ``null`` ou
    ``[x, y, score]``. As métricas per-frame podem ser ``null`` quando os
    keypoints requeridos estão ausentes.
    """

    frame_idx: int
    keypoints: list[list[float] | None]
    angulo_joelho_esq: float | None = None
    angulo_joelho_dir: float | None = None
    angulo_cotovelo_esq: float | None = None
    angulo_cotovelo_dir: float | None = None
    inclinacao_tronco: float | None = None
    y_com: float | None = None


class SimetriaResponse(BaseModel):
    tcs: float | None = None
    joelho: float | None = None
    oscilacao: float | None = None


class AnalysisRawResponse(BaseModel):
    fps: float | None = None
    frames: list[RawFrame] = []
    metricas_agregadas: list[MetricaResumida] = []
    simetria: SimetriaResponse = SimetriaResponse()
    erro: str | None = None
