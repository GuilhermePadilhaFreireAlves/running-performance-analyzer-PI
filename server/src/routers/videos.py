from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from server.src.auth import CurrentUser
from server.src.database import get_session
from server.src.models.sessao_analise import SessaoAnalise
from server.src.schemas.video import VideoStatusResponse, VideoUploadResponse
from server.src.video_pipeline import (
    FPS_MINIMO,
    MSG_FPS_INSUFICIENTE,
    MSG_PACE_INVALIDO,
    MSG_PERSPECTIVA_INVALIDA,
    VideoValidator,
    get_video_validator,
    is_pace_valido,
    run_pipeline,
)

STATUS_DESCRICAO: dict[str, str] = {
    "pendente": "Validando perspectiva",
    "validando_perspectiva": "Validando perspectiva",
    "detectando_pose": "Detectando pose com YOLOv8",
    "calculando_metricas": "Calculando métricas",
    "concluido": "Concluído",
    "erro_qualidade_keypoints": "Erro: qualidade de keypoints insuficiente",
    "erro_multiplas_pessoas": "Erro: múltiplas pessoas detectadas",
}

router = APIRouter(prefix="/api/videos", tags=["videos"])

SessionDep = Annotated[Session, Depends(get_session)]
ValidatorDep = Annotated[VideoValidator, Depends(get_video_validator)]

DEFAULT_UPLOAD_DIR = "./uploads"


def _upload_dir() -> Path:
    path = Path(os.environ.get("UPLOAD_DIR", DEFAULT_UPLOAD_DIR))
    path.mkdir(parents=True, exist_ok=True)
    return path


def _persist_upload(file: UploadFile) -> Path:
    suffix = Path(file.filename or "").suffix or ".mp4"
    dest = _upload_dir() / f"{uuid.uuid4().hex}{suffix}"
    with dest.open("wb") as fh:
        shutil.copyfileobj(file.file, fh)
    return dest


def _cleanup(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


@router.post(
    "/upload",
    response_model=VideoUploadResponse,
    status_code=status.HTTP_200_OK,
)
def upload_video(
    user: CurrentUser,
    session: SessionDep,
    validator: ValidatorDep,
    background_tasks: BackgroundTasks,
    pace_min_km: Annotated[float, Form()],
    file: Annotated[UploadFile, File()],
) -> VideoUploadResponse:
    if not is_pace_valido(pace_min_km):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=MSG_PACE_INVALIDO,
        )

    saved_path = _persist_upload(file)

    try:
        fps = validator.extract_fps(str(saved_path))
        if fps < FPS_MINIMO:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=MSG_FPS_INSUFICIENTE,
            )

        if not validator.is_lateral(str(saved_path)):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=MSG_PERSPECTIVA_INVALIDA,
            )
    except HTTPException:
        _cleanup(saved_path)
        raise

    sessao = SessaoAnalise(
        usuario_id=user.id,
        pace_min_km=pace_min_km,
        status="pendente",
    )
    session.add(sessao)
    session.commit()
    session.refresh(sessao)

    background_tasks.add_task(run_pipeline, sessao.id, str(saved_path))

    return VideoUploadResponse(video_id=sessao.id, status=sessao.status)


@router.get(
    "/{video_id}/status",
    response_model=VideoStatusResponse,
    status_code=status.HTTP_200_OK,
)
def get_video_status(
    video_id: int,
    user: CurrentUser,
    session: SessionDep,
) -> VideoStatusResponse:
    sessao = session.get(SessaoAnalise, video_id)
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

    descricao = STATUS_DESCRICAO.get(sessao.status, sessao.status)
    return VideoStatusResponse(
        video_id=sessao.id,
        status=sessao.status,
        status_descricao=descricao,
    )
