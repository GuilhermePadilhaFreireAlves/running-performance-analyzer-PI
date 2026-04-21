"""Métricas per-frame para o endpoint de dados biomecânicos brutos (US-018).

Este módulo expõe funções que operam em **um único** ``FrameKeypoints`` e
retornam o valor da métrica naquele frame (ou ``None`` quando os keypoints
requeridos estão ausentes). Diferem das funções agregadas em
``biomechanics.joelho``/``cotovelo``/``tronco``/``oscilacao`` (que produzem
média/ciclos sobre a série inteira) porque o endpoint ``/raw`` expõe a série
temporal frame a frame, sem filtragem por fase de apoio ou detecção de
ciclo.

Convenção de ângulo (alinhada aos demais módulos biomecânicos do backend):
articulação estendida ⇒ 180°; flexão máxima ⇒ próximo de 0°.
"""

from __future__ import annotations

from math import acos, atan, degrees, hypot

from server.src.biomechanics.cotovelo import (
    KP_COTOVELO_DIR,
    KP_COTOVELO_ESQ,
    KP_OMBRO_DIR,
    KP_OMBRO_ESQ,
    KP_PULSO_DIR,
    KP_PULSO_ESQ,
)
from server.src.biomechanics.joelho import (
    KP_JOELHO_DIR,
    KP_JOELHO_ESQ,
    KP_QUADRIL_DIR,
    KP_QUADRIL_ESQ,
    KP_TORNOZELO_DIR,
    KP_TORNOZELO_ESQ,
)
from server.src.video_pipeline import FrameKeypoints


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
    v1x, v1y = a[0] - b[0], a[1] - b[1]
    v2x, v2y = c[0] - b[0], c[1] - b[1]
    mag1 = hypot(v1x, v1y)
    mag2 = hypot(v2x, v2y)
    if mag1 == 0 or mag2 == 0:
        return None
    cos_theta = (v1x * v2x + v1y * v2y) / (mag1 * mag2)
    if cos_theta > 1.0:
        cos_theta = 1.0
    elif cos_theta < -1.0:
        cos_theta = -1.0
    return degrees(acos(cos_theta))


def angulo_joelho_frame(frame: FrameKeypoints, lado: str) -> float | None:
    """Ângulo interno do joelho no frame (esq/dir). None se keypoint ausente."""
    if lado == "esq":
        quadril_idx, joelho_idx, tornozelo_idx = (
            KP_QUADRIL_ESQ,
            KP_JOELHO_ESQ,
            KP_TORNOZELO_ESQ,
        )
    elif lado == "dir":
        quadril_idx, joelho_idx, tornozelo_idx = (
            KP_QUADRIL_DIR,
            KP_JOELHO_DIR,
            KP_TORNOZELO_DIR,
        )
    else:
        raise ValueError(f"lado inválido: {lado!r}")
    quadril = _coord(frame, quadril_idx)
    joelho = _coord(frame, joelho_idx)
    tornozelo = _coord(frame, tornozelo_idx)
    if quadril is None or joelho is None or tornozelo is None:
        return None
    return _angulo_interno(quadril, joelho, tornozelo)


def angulo_cotovelo_frame(frame: FrameKeypoints, lado: str) -> float | None:
    """Ângulo interno do cotovelo no frame (esq/dir). None se keypoint ausente."""
    if lado == "esq":
        ombro_idx, cotovelo_idx, pulso_idx = (
            KP_OMBRO_ESQ,
            KP_COTOVELO_ESQ,
            KP_PULSO_ESQ,
        )
    elif lado == "dir":
        ombro_idx, cotovelo_idx, pulso_idx = (
            KP_OMBRO_DIR,
            KP_COTOVELO_DIR,
            KP_PULSO_DIR,
        )
    else:
        raise ValueError(f"lado inválido: {lado!r}")
    ombro = _coord(frame, ombro_idx)
    cotovelo = _coord(frame, cotovelo_idx)
    pulso = _coord(frame, pulso_idx)
    if ombro is None or cotovelo is None or pulso is None:
        return None
    return _angulo_interno(ombro, cotovelo, pulso)


def inclinacao_tronco_frame(frame: FrameKeypoints) -> float | None:
    """Inclinação anterior do tronco no frame em graus.

    Sem filtro de apoio médio — o endpoint ``/raw`` devolve a série
    temporal completa frame a frame. Retorna ``None`` quando algum dos
    quatro keypoints requeridos (ombros e quadris) está ausente ou quando
    o tronco está horizontal/invertido (``-ΔY ≤ 0``).
    """
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
    topo = ((ombro_esq[0] + ombro_dir[0]) / 2.0, (ombro_esq[1] + ombro_dir[1]) / 2.0)
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
    """Y do centro de massa (média dos quadris) no frame. None se ausente."""
    quadril_esq = _coord(frame, KP_QUADRIL_ESQ)
    quadril_dir = _coord(frame, KP_QUADRIL_DIR)
    if quadril_esq is None or quadril_dir is None:
        return None
    return (quadril_esq[1] + quadril_dir[1]) / 2.0
