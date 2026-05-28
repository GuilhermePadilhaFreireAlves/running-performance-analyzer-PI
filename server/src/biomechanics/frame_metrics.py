"""Per-frame biomechanics metrics for the raw data endpoint (US-018)."""

from __future__ import annotations

from math import atan, degrees

from server.src.biomechanics.cotovelo import (
    KP_COTOVELO_DIR,
    KP_COTOVELO_ESQ,
    KP_OMBRO_DIR,
    KP_OMBRO_ESQ,
    KP_PULSO_DIR,
    KP_PULSO_ESQ,
)
from server.src.biomechanics.geometry import angulo_interno
from server.src.biomechanics.joelho import (
    KP_JOELHO_DIR,
    KP_JOELHO_ESQ,
    KP_QUADRIL_DIR,
    KP_QUADRIL_ESQ,
    KP_TORNOZELO_DIR,
    KP_TORNOZELO_ESQ,
)
from server.src.video_pipeline import FrameKeypoints

_JOELHO_INDICES = {
    "esq": (KP_QUADRIL_ESQ, KP_JOELHO_ESQ, KP_TORNOZELO_ESQ),
    "dir": (KP_QUADRIL_DIR, KP_JOELHO_DIR, KP_TORNOZELO_DIR),
}

_COTOVELO_INDICES = {
    "esq": (KP_OMBRO_ESQ, KP_COTOVELO_ESQ, KP_PULSO_ESQ),
    "dir": (KP_OMBRO_DIR, KP_COTOVELO_DIR, KP_PULSO_DIR),
}


def _coord(frame: FrameKeypoints, idx: int) -> tuple[float, float] | None:
    if idx >= len(frame.keypoints):
        return None
    kp = frame.keypoints[idx]
    if kp is None:
        return None
    return (kp[0], kp[1])


def _angulo_interno(
    a: tuple[float, float],
    b: tuple[float, float],
    c: tuple[float, float],
) -> float | None:
    return angulo_interno(a, b, c)


def _indices_por_lado(
    indices_por_lado: dict[str, tuple[int, int, int]],
    lado: str,
) -> tuple[int, int, int]:
    try:
        return indices_por_lado[lado]
    except KeyError:
        raise ValueError(f"lado inválido: {lado!r}")


def _angulo_tres_pontos_frame(
    frame: FrameKeypoints,
    indices: tuple[int, int, int],
) -> float | None:
    primeiro_idx, vertice_idx, terceiro_idx = indices
    primeiro = _coord(frame, primeiro_idx)
    vertice = _coord(frame, vertice_idx)
    terceiro = _coord(frame, terceiro_idx)
    if primeiro is None or vertice is None or terceiro is None:
        return None
    return _angulo_interno(primeiro, vertice, terceiro)


def angulo_joelho_frame(frame: FrameKeypoints, lado: str) -> float | None:
    """Internal knee angle in a single frame. Returns None if keypoints are missing."""
    indices = _indices_por_lado(_JOELHO_INDICES, lado)
    return _angulo_tres_pontos_frame(frame, indices)


def angulo_cotovelo_frame(frame: FrameKeypoints, lado: str) -> float | None:
    """Internal elbow angle in a single frame. Returns None if keypoints are missing."""
    indices = _indices_por_lado(_COTOVELO_INDICES, lado)
    return _angulo_tres_pontos_frame(frame, indices)


def inclinacao_tronco_frame(frame: FrameKeypoints) -> float | None:
    """Anterior trunk inclination in degrees for a single frame."""
    ombro_esq = _coord(frame, KP_OMBRO_ESQ)
    ombro_dir = _coord(frame, KP_OMBRO_DIR)
    quadril_esq = _coord(frame, KP_QUADRIL_ESQ)
    quadril_dir = _coord(frame, KP_QUADRIL_DIR)
    if (
        ombro_esq is None
        or ombro_dir is None
        or quadril_esq is None
        or quadril_dir is None
    ):
        return None

    topo = (
        (ombro_esq[0] + ombro_dir[0]) / 2.0,
        (ombro_esq[1] + ombro_dir[1]) / 2.0,
    )
    base = (
        (quadril_esq[0] + quadril_dir[0]) / 2.0,
        (quadril_esq[1] + quadril_dir[1]) / 2.0,
    )
    dx = topo[0] - base[0]
    vertical_para_cima = -(topo[1] - base[1])
    if vertical_para_cima <= 0:
        return None
    return degrees(atan(dx / vertical_para_cima))


def y_com_frame(frame: FrameKeypoints) -> float | None:
    """Y coordinate of the center of mass proxy in a single frame."""
    quadril_esq = _coord(frame, KP_QUADRIL_ESQ)
    quadril_dir = _coord(frame, KP_QUADRIL_DIR)
    if quadril_esq is None or quadril_dir is None:
        return None
    return (quadril_esq[1] + quadril_dir[1]) / 2.0
