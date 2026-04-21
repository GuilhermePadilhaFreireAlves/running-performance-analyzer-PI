from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.orm import Session

from server.src.database import get_session
from server.src.models.usuario import Usuario
from server.src.security import decode_access_token

CREDENCIAIS_INVALIDAS_MSG = "Credenciais inválidas"
NAO_AUTENTICADO_MSG = "Não autenticado"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    session: Annotated[Session, Depends(get_session)],
) -> Usuario:
    if not token:
        raise _unauthorized(NAO_AUTENTICADO_MSG)

    try:
        payload = decode_access_token(token)
    except InvalidTokenError:
        raise _unauthorized(NAO_AUTENTICADO_MSG)

    sub = payload.get("sub")
    if sub is None:
        raise _unauthorized(NAO_AUTENTICADO_MSG)

    try:
        usuario_id = int(sub)
    except (TypeError, ValueError):
        raise _unauthorized(NAO_AUTENTICADO_MSG)

    usuario = session.scalar(select(Usuario).where(Usuario.id == usuario_id))
    if usuario is None:
        raise _unauthorized(NAO_AUTENTICADO_MSG)
    return usuario


CurrentUser = Annotated[Usuario, Depends(get_current_user)]
