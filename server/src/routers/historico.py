from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from server.src.auth import CurrentUser
from server.src.database import get_session
from server.src.models.sessao_analise import SessaoAnalise
from server.src.schemas.historico import HistoricoItem, HistoricoResponse

LIMIT_MAXIMO = 50

router = APIRouter(prefix="/api", tags=["historico"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.get(
    "/historico-analise",
    response_model=HistoricoResponse,
    status_code=status.HTTP_200_OK,
)
def listar_historico(
    user: CurrentUser,
    session: SessionDep,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1)] = 10,
) -> HistoricoResponse:
    limit_efetivo = min(limit, LIMIT_MAXIMO)

    total = session.scalar(
        select(func.count(SessaoAnalise.id)).where(
            SessaoAnalise.usuario_id == user.id
        )
    )

    rows = (
        session.query(SessaoAnalise)
        .filter(SessaoAnalise.usuario_id == user.id)
        .order_by(SessaoAnalise.criado_em.desc())
        .offset((page - 1) * limit_efetivo)
        .limit(limit_efetivo)
        .all()
    )

    return HistoricoResponse(
        items=[HistoricoItem.model_validate(r) for r in rows],
        total=int(total or 0),
        page=page,
        limit=limit_efetivo,
    )
