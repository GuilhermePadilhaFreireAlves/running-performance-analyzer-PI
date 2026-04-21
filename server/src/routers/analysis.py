from __future__ import annotations

import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from server.src.auth import CurrentUser
from server.src.database import get_session
from server.src.models.metrica import Metrica
from server.src.models.recomendacao import Recomendacao
from server.src.models.sessao_analise import SessaoAnalise
from server.src.routers.videos import STATUS_DESCRICAO
from server.src.schemas.analysis import (
    AnalysisRawResponse,
    AnalysisSimpleResponse,
    MetricaResumida,
    RawFrame,
    RecomendacaoResponse,
    SimetriaResponse,
)

SIMETRIA_TIPOS: frozenset[str] = frozenset(
    {"simetria_tcs", "simetria_joelho", "simetria_oscilacao"}
)

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

SessionDep = Annotated[Session, Depends(get_session)]

STATUS_ERRO: frozenset[str] = frozenset(
    {"erro_qualidade_keypoints", "erro_multiplas_pessoas"}
)


@router.get(
    "/{analysis_id}/simple",
    response_model=AnalysisSimpleResponse,
    status_code=status.HTTP_200_OK,
)
def get_simple_analysis(
    analysis_id: int,
    user: CurrentUser,
    session: SessionDep,
) -> AnalysisSimpleResponse:
    sessao = session.get(SessaoAnalise, analysis_id)
    if sessao is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sessão de análise não encontrada",
        )
    if sessao.usuario_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado a esta sessão de análise",
        )

    if sessao.status in STATUS_ERRO:
        return AnalysisSimpleResponse(
            erro=STATUS_DESCRICAO.get(sessao.status, sessao.status),
        )

    metricas = (
        session.query(Metrica).filter(Metrica.sessao_id == analysis_id).all()
    )
    recomendacoes = (
        session.query(Recomendacao)
        .filter(Recomendacao.sessao_id == analysis_id)
        .all()
    )

    return AnalysisSimpleResponse(
        nota_geral=sessao.nota_geral,
        feedback_ia=sessao.feedback_ia,
        recomendacoes=[RecomendacaoResponse.model_validate(r) for r in recomendacoes],
        metricas_resumidas=[MetricaResumida.model_validate(m) for m in metricas],
    )


@router.get(
    "/{analysis_id}/raw",
    response_model=AnalysisRawResponse,
    status_code=status.HTTP_200_OK,
)
def get_raw_analysis(
    analysis_id: int,
    user: CurrentUser,
    session: SessionDep,
) -> AnalysisRawResponse:
    sessao = session.get(SessaoAnalise, analysis_id)
    if sessao is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sessão de análise não encontrada",
        )
    if sessao.usuario_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado a esta sessão de análise",
        )

    if sessao.status in STATUS_ERRO:
        return AnalysisRawResponse(
            fps=sessao.fps,
            erro=STATUS_DESCRICAO.get(sessao.status, sessao.status),
        )

    metricas = (
        session.query(Metrica).filter(Metrica.sessao_id == analysis_id).all()
    )

    simetria = SimetriaResponse()
    metricas_agregadas: list[MetricaResumida] = []
    for m in metricas:
        if m.tipo == "simetria_tcs":
            simetria.tcs = m.valor
        elif m.tipo == "simetria_joelho":
            simetria.joelho = m.valor
        elif m.tipo == "simetria_oscilacao":
            simetria.oscilacao = m.valor
        else:
            metricas_agregadas.append(MetricaResumida.model_validate(m))

    frames = _parse_frames(sessao.dados_brutos_json)

    return AnalysisRawResponse(
        fps=sessao.fps,
        frames=frames,
        metricas_agregadas=metricas_agregadas,
        simetria=simetria,
    )


def _parse_frames(raw_json: str | None) -> list[RawFrame]:
    if not raw_json:
        return []
    try:
        payload: Any = json.loads(raw_json)
    except ValueError:
        return []
    if not isinstance(payload, list):
        return []
    return [RawFrame.model_validate(item) for item in payload]
