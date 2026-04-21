from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

logger = logging.getLogger(__name__)

FPS_MINIMO = 60.0
PACE_MIN = 3.0
PACE_MAX = 12.0
RAZAO_LATERAL_MAXIMA = 0.30
PERSPECTIVA_FRAMES_AMOSTRA = 5

MSG_FPS_INSUFICIENTE = (
    "FPS do vídeo insuficiente — grave com pelo menos 60 FPS para garantir "
    "precisão na análise"
)
MSG_PERSPECTIVA_INVALIDA = (
    "Perspectiva inválida — grave o vídeo de lado (perfil), perpendicular à "
    "direção da corrida"
)
MSG_PACE_INVALIDO = (
    "Pace fora do intervalo permitido — informe um valor entre 3:00 e 12:00 min/km"
)


class VideoValidator(Protocol):
    def extract_fps(self, video_path: str) -> float: ...
    def is_lateral(self, video_path: str) -> bool: ...


@dataclass
class DefaultVideoValidator:
    """Production validator using OpenCV (FPS) and YOLOv8-pose (perspective).

    The YOLO model is loaded lazily so that environments without model weights
    (e.g. unit tests that override this dependency) do not pay the import cost.
    """

    model_path: str | None = None

    def extract_fps(self, video_path: str) -> float:
        import cv2

        cap = cv2.VideoCapture(video_path)
        try:
            if not cap.isOpened():
                return 0.0
            fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
        finally:
            cap.release()
        return fps

    def is_lateral(self, video_path: str) -> bool:
        import cv2

        cap = cv2.VideoCapture(video_path)
        try:
            if not cap.isOpened():
                return False
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            if total_frames <= 0:
                return False
            sample_indices = _sample_indices(total_frames, PERSPECTIVA_FRAMES_AMOSTRA)
            frames = []
            for idx in sample_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ok, frame = cap.read()
                if ok and frame is not None:
                    frames.append(frame)
        finally:
            cap.release()

        if not frames:
            return False

        model = self._load_model()
        if model is None:
            return False

        ratios: list[float] = []
        for frame in frames:
            ratio = _shoulder_hip_ratio(model, frame)
            if ratio is not None:
                ratios.append(ratio)

        if not ratios:
            return False
        ratios.sort()
        median = ratios[len(ratios) // 2]
        return median < RAZAO_LATERAL_MAXIMA

    def _load_model(self) -> object | None:
        path = self.model_path or os.environ.get("YOLO_POSE_MODEL", "yolo26x-pose.pt")
        if not Path(path).exists():
            logger.warning("Modelo YOLO não encontrado em %s", path)
            return None
        try:
            from ultralytics import YOLO
        except ImportError:
            logger.warning("Ultralytics não instalado")
            return None
        return YOLO(path)


def _sample_indices(total: int, n: int) -> list[int]:
    if total <= n:
        return list(range(total))
    step = total / (n + 1)
    return [int(step * (i + 1)) for i in range(n)]


def _shoulder_hip_ratio(model: object, frame: object) -> float | None:
    """Return max(shoulder_width, hip_width) / torso_height for the pose in frame.

    Returns None when keypoints required for the computation are missing.
    Lower ratio ⇒ closer to a true lateral (profile) shot.
    """
    predict = getattr(model, "predict", None)
    if predict is None:
        return None
    results = predict(source=frame, verbose=False)
    if not results:
        return None
    kpts_obj = getattr(results[0], "keypoints", None)
    if kpts_obj is None:
        return None
    xy = getattr(kpts_obj, "xy", None)
    if xy is None or len(xy) == 0:
        return None
    pontos = xy[0]
    try:
        ls = pontos[5]
        rs = pontos[6]
        lh = pontos[11]
        rh = pontos[12]
    except (IndexError, KeyError):
        return None

    if min(float(ls[0]), float(rs[0]), float(lh[0]), float(rh[0])) <= 0:
        return None

    shoulder_width = abs(float(rs[0]) - float(ls[0]))
    hip_width = abs(float(rh[0]) - float(lh[0]))
    shoulder_mid_y = (float(ls[1]) + float(rs[1])) / 2
    hip_mid_y = (float(lh[1]) + float(rh[1])) / 2
    torso_height = abs(hip_mid_y - shoulder_mid_y)
    if torso_height <= 0:
        return None
    return max(shoulder_width, hip_width) / torso_height


_default_validator = DefaultVideoValidator()


def get_video_validator() -> VideoValidator:
    return _default_validator


def is_pace_valido(pace_min_km: float) -> bool:
    return PACE_MIN <= pace_min_km <= PACE_MAX


def run_pipeline(sessao_id: int, video_path: str) -> None:
    """Background task entrypoint for the biomechanics pipeline.

    Implemented in US-006; the upload endpoint schedules this task immediately
    after validation so the HTTP response is not blocked by YOLO inference.
    """
    logger.info(
        "Pipeline agendado (stub) para sessao_id=%s em %s", sessao_id, video_path
    )
