from __future__ import annotations

from pydantic import BaseModel


class VideoUploadResponse(BaseModel):
    video_id: int
    status: str


class VideoStatusResponse(BaseModel):
    video_id: int
    status: str
    status_descricao: str
