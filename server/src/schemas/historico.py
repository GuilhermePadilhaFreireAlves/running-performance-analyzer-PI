from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class HistoricoItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    criado_em: datetime
    pace_min_km: float | None
    status: str
    nota_geral: float | None


class HistoricoResponse(BaseModel):
    items: list[HistoricoItem]
    total: int
    page: int
    limit: int
