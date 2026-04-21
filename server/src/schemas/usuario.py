from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UsuarioCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    senha: str = Field(min_length=6, max_length=255)
    altura_cm: float = Field(gt=0, le=300)
    peso_kg: float | None = Field(default=None, gt=0, le=500)
    nivel_experiencia: str | None = Field(default=None, max_length=50)


class UsuarioPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    altura_cm: float
    peso_kg: float | None
    nivel_experiencia: str | None
    criado_em: datetime
