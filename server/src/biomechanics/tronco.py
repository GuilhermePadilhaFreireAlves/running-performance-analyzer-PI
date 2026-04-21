"""Inclinação anterior do tronco em fase de apoio médio (US-011).

Cada frame válido contribui com um valor de inclinação calculado entre o
ponto médio dos ombros (KP 5/6) e o ponto médio dos quadris (KP 11/12):

    ponto_topo = média(ombro_esq, ombro_dir)
    ponto_base = média(quadril_esq, quadril_dir)
    ΔX = topo.x - base.x
    ΔY_imagem = topo.y - base.y          (Y cresce para baixo na imagem)
    inclinação = arctan(ΔX / -ΔY_imagem) em graus

A negação de ``ΔY_imagem`` reorienta o eixo vertical para que a fórmula
``arctan(ΔX/ΔY)`` do PRD produza valor positivo ao inclinar para frente
(direção +X). Frames com o tronco horizontal ou invertido (``-ΔY ≤ 0``)
são descartados.

Apenas frames em **fase de apoio médio** entram na média — definidos como
frames em que pelo menos um joelho apresenta flexão entre 40° e 45°.
"Flexão" segue a convenção do PRD (`180 - ângulo_interno`), enquanto a
biomecânica nova mantém o ângulo interno (perna estendida = 180°), então
internamente comparamos ``180 - ângulo_interno ∈ [40, 45]``.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import acos, atan, degrees, hypot
from typing import Sequence

from server.src.video_pipeline import FrameKeypoints

KP_OMBRO_ESQ = 5
KP_OMBRO_DIR = 6
KP_QUADRIL_ESQ = 11
KP_QUADRIL_DIR = 12
KP_JOELHO_ESQ = 13
KP_JOELHO_DIR = 14
KP_TORNOZELO_ESQ = 15
KP_TORNOZELO_DIR = 16

FLEXAO_APOIO_MEDIO_MIN_GRAUS = 40.0
FLEXAO_APOIO_MEDIO_MAX_GRAUS = 45.0


@dataclass(frozen=True)
class InclinacaoTronco:
    """Inclinação média do tronco (em graus) sobre frames de apoio médio.

    Sinal positivo ⇒ tronco inclinado para frente (sentido +X da imagem);
    sinal negativo ⇒ inclinado para trás. ``frames_validos`` é a contagem
    de frames de apoio médio com keypoints suficientes para o cálculo.
    """

    inclinacao_media_graus: float
    frames_validos: int


def _coord(frame: FrameKeypoints, idx: int) -> tuple[float, float] | None:
    if idx >= len(frame.keypoints):
        return None
    kp = frame.keypoints[idx]
    if kp is None:
        return None
    return (kp[0], kp[1])


def _media(
    a: tuple[float, float], b: tuple[float, float]
) -> tuple[float, float]:
    return ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)


def _angulo_interno(
    a: tuple[float, float],
    b: tuple[float, float],
    c: tuple[float, float],
) -> float | None:
    """Ângulo em `b` entre os vetores `b→a` e `b→c` (em graus), via arccos."""
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


def _flexao_joelho(
    frame: FrameKeypoints,
    quadril_idx: int,
    joelho_idx: int,
    tornozelo_idx: int,
) -> float | None:
    quadril = _coord(frame, quadril_idx)
    joelho = _coord(frame, joelho_idx)
    tornozelo = _coord(frame, tornozelo_idx)
    if quadril is None or joelho is None or tornozelo is None:
        return None
    interno = _angulo_interno(quadril, joelho, tornozelo)
    if interno is None:
        return None
    return 180.0 - interno


def _eh_apoio_medio(frame: FrameKeypoints) -> bool:
    """Frame é apoio médio se algum joelho tem flexão em [40°, 45°]."""
    for quadril_idx, joelho_idx, tornozelo_idx in (
        (KP_QUADRIL_ESQ, KP_JOELHO_ESQ, KP_TORNOZELO_ESQ),
        (KP_QUADRIL_DIR, KP_JOELHO_DIR, KP_TORNOZELO_DIR),
    ):
        flexao = _flexao_joelho(frame, quadril_idx, joelho_idx, tornozelo_idx)
        if flexao is None:
            continue
        if FLEXAO_APOIO_MEDIO_MIN_GRAUS <= flexao <= FLEXAO_APOIO_MEDIO_MAX_GRAUS:
            return True
    return False


def _topo_base(
    frame: FrameKeypoints,
) -> tuple[tuple[float, float], tuple[float, float]] | None:
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
    return _media(ombro_esq, ombro_dir), _media(quadril_esq, quadril_dir)


def _inclinacao_graus(
    topo: tuple[float, float], base: tuple[float, float]
) -> float | None:
    """Inclinação anterior em graus a partir do vetor base→topo.

    Em coordenadas de imagem (Y crescente para baixo), o tronco ereto tem
    ``topo.y < base.y``, ou seja, ``ΔY < 0``. Aplicamos a fórmula do PRD
    com o eixo vertical orientado para cima (``-ΔY``) para que inclinar
    para frente (``ΔX > 0``) renda valor positivo. Retorna `None` quando
    o tronco está horizontal ou invertido (``-ΔY ≤ 0``).
    """
    dx = topo[0] - base[0]
    dy = topo[1] - base[1]
    vertical_para_cima = -dy
    if vertical_para_cima <= 0:
        return None
    return degrees(atan(dx / vertical_para_cima))


def calcular_inclinacao_tronco(
    frames: Sequence[FrameKeypoints],
) -> InclinacaoTronco | None:
    """Calcula a inclinação média do tronco sobre frames em apoio médio.

    Etapas:
      1. Filtra frames em fase de apoio médio (algum joelho com flexão em
         [40°, 45°] — convenção PRD: flexão = ``180 - ângulo_interno``).
      2. Em cada frame, calcula ``topo`` (média dos ombros) e ``base``
         (média dos quadris); descarta o frame se algum desses keypoints
         estiver ausente.
      3. Inclinação = ``arctan(ΔX / -ΔY_imagem)`` do vetor base→topo, em
         graus; positivo ⇒ inclinação anterior (para frente).
      4. Retorna a média sobre os frames válidos. ``None`` quando nenhum
         frame qualifica.
    """
    valores: list[float] = []
    for frame in frames:
        if not _eh_apoio_medio(frame):
            continue
        pontos = _topo_base(frame)
        if pontos is None:
            continue
        topo, base = pontos
        inc = _inclinacao_graus(topo, base)
        if inc is None:
            continue
        valores.append(inc)

    if not valores:
        return None
    media = sum(valores) / len(valores)
    return InclinacaoTronco(
        inclinacao_media_graus=media,
        frames_validos=len(valores),
    )
