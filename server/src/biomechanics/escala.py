"""Fator de escala pixels→cm a partir da altura do usuário (US-007).

A altura do corredor em pixels é estimada como a distância euclidiana entre
o nariz (keypoint COCO 0) e o ponto médio dos tornozelos (keypoints 15/16).
Dividindo a altura real (em cm, cadastrada pelo usuário) por essa medida em
pixels, obtém-se o fator de conversão reutilizado por overstriding (US-012)
e oscilação vertical (US-014).

Sem detecção de fase de apoio (US-008 ainda não implementada), considera-se
"frame de apoio médio" qualquer frame em que os três keypoints requeridos
estão simultaneamente válidos. A média do fator sobre múltiplos frames
absorve ruído residual mesmo após a suavização do pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import hypot
from typing import Iterable

from server.src.video_pipeline import FrameKeypoints

KP_NARIZ = 0
KP_TORNOZELO_ESQ = 15
KP_TORNOZELO_DIR = 16

MSG_ALTURA_AUSENTE = (
    "Altura do usuário é obrigatória para calcular o fator de escala "
    "(pixels→cm). Preencha altura_cm no perfil."
)
MSG_SEM_FRAMES_VALIDOS = (
    "Não foi possível calcular o fator de escala — nenhum frame contém os "
    "keypoints necessários (nariz e ambos os tornozelos)."
)


@dataclass(frozen=True)
class FatorEscala:
    """Resultado do cálculo de fator de escala pixels→cm."""

    fator_escala: float
    altura_pixels_media: float
    frames_usados: int


def calcular_fator_escala(
    frames: Iterable[FrameKeypoints],
    altura_real_cm: float | None,
) -> FatorEscala:
    """Calcula o fator de escala (cm por pixel) médio sobre os frames válidos.

    Para cada frame:
      altura_em_pixels = ‖ nariz - ponto_medio(tornozelo_esq, tornozelo_dir) ‖
    Frames sem nariz ou sem ambos os tornozelos válidos são ignorados.

    Args:
        frames: série temporal de keypoints já filtrados/suavizados pelo
            pipeline.
        altura_real_cm: altura cadastrada do usuário em centímetros.

    Returns:
        FatorEscala com `fator_escala = altura_real_cm / altura_pixels_media`,
        a `altura_pixels_media` (média entre frames usados) e `frames_usados`.

    Raises:
        ValueError: se `altura_real_cm` for None ou ≤ 0; ou se nenhum frame
            permitir o cálculo da altura em pixels.
    """
    if altura_real_cm is None or altura_real_cm <= 0:
        raise ValueError(MSG_ALTURA_AUSENTE)

    alturas_pixels: list[float] = []
    for frame in frames:
        kps = frame.keypoints
        if (
            KP_NARIZ >= len(kps)
            or KP_TORNOZELO_ESQ >= len(kps)
            or KP_TORNOZELO_DIR >= len(kps)
        ):
            continue
        nariz = kps[KP_NARIZ]
        tornozelo_esq = kps[KP_TORNOZELO_ESQ]
        tornozelo_dir = kps[KP_TORNOZELO_DIR]
        if nariz is None or tornozelo_esq is None or tornozelo_dir is None:
            continue
        mid_x = (tornozelo_esq[0] + tornozelo_dir[0]) / 2.0
        mid_y = (tornozelo_esq[1] + tornozelo_dir[1]) / 2.0
        altura = hypot(nariz[0] - mid_x, nariz[1] - mid_y)
        if altura <= 0:
            continue
        alturas_pixels.append(altura)

    if not alturas_pixels:
        raise ValueError(MSG_SEM_FRAMES_VALIDOS)

    altura_media = sum(alturas_pixels) / len(alturas_pixels)
    fator = altura_real_cm / altura_media
    return FatorEscala(
        fator_escala=fator,
        altura_pixels_media=altura_media,
        frames_usados=len(alturas_pixels),
    )
