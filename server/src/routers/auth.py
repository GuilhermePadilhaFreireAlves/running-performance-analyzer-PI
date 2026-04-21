from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from server.src.auth import CREDENCIAIS_INVALIDAS_MSG
from server.src.database import get_session
from server.src.models.usuario import Usuario
from server.src.schemas.auth import LoginRequest, TokenResponse
from server.src.security import create_access_token, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
def login(payload: LoginRequest, session: SessionDep) -> TokenResponse:
    usuario = session.scalar(
        select(Usuario).where(Usuario.email == payload.email)
    )
    if usuario is None or not verify_password(payload.senha, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=CREDENCIAIS_INVALIDAS_MSG,
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(usuario.id)
    return TokenResponse(access_token=token)
