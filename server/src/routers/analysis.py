from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from server.src.auth import CurrentUser
from server.src.database import get_session
from server.src.models.metrica import Metrica
from server.src.models.recomendacao import Recomendacao
from server.src.models.sessao_analise import SessaoAnalise
from server.src.routers.videos import STATUS_DESCRICAO
from server.src.schemas.analysis import (
    AnalysisSimpleResponse,
    MetricaResumida,
    RecomendacaoResponse,
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
