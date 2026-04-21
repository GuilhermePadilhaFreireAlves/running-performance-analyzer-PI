from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from server.src.database import get_session
from server.src.models.usuario import Usuario
from server.src.schemas.usuario import UsuarioCreate, UsuarioPublic
from server.src.security import hash_password

router = APIRouter(prefix="/api/users", tags=["users"])

SessionDep = Annotated[Session, Depends(get_session)]

EMAIL_DUPLICADO_MSG = "E-mail já cadastrado"


@router.post(
    "/register",
    response_model=UsuarioPublic,
    status_code=status.HTTP_200_OK,
)
def register_user(payload: UsuarioCreate, session: SessionDep) -> UsuarioPublic:
    existing = session.scalar(
        select(Usuario).where(Usuario.email == payload.email)
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=EMAIL_DUPLICADO_MSG,
        )

    usuario = Usuario(
        name=payload.name,
        email=payload.email,
        senha_hash=hash_password(payload.senha),
        altura_cm=payload.altura_cm,
        peso_kg=payload.peso_kg,
        nivel_experiencia=payload.nivel_experiencia,
    )
    session.add(usuario)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=EMAIL_DUPLICADO_MSG,
        )
    session.refresh(usuario)
    return UsuarioPublic.model_validate(usuario)
