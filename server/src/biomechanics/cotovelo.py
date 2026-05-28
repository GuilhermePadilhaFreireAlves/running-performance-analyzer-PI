"""Ângulo médio do cotovelo (esq/dir) ao longo dos ciclos (US-009).

Para cada frame com os três keypoints requeridos (ombro, cotovelo, pulso) do
lado em questão, calcula-se o ângulo interno do cotovelo via arccos do
produto escalar normalizado entre os vetores ``cotovelo→ombro`` e
``cotovelo→pulso``. O resultado por lado é a média sobre todos os frames
válidos do vídeo — não há detecção de ciclo aqui, ao contrário do joelho.

Convenção de ângulo (igual à usada em `joelho.py`): braço totalmente
estendido ⇒ 180°; flexão máxima se aproxima de 0°. Isso difere da
convenção legada em `processing/src/mainGraph.py` (`180 - internal`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from server.src.biomechanics.geometry import angulo_interno
from server.src.video_pipeline import FrameKeypoints

KP_OMBRO_ESQ = 5
KP_OMBRO_DIR = 6
KP_COTOVELO_ESQ = 7
KP_COTOVELO_DIR = 8
KP_PULSO_ESQ = 9
KP_PULSO_DIR = 10


@dataclass(frozen=True)
class AnguloCotoveloLado:
    """Ângulo médio do cotovelo em um lado do corpo."""

    angulo_medio_graus: float
    frames_validos: int


@dataclass(frozen=True)
class AnguloCotoveloResultado:
    """Resultado agregado para os lados esquerdo e direito.

    Cada lado é `None` quando nenhum frame contém os três keypoints
    requeridos simultaneamente.
    """

    esquerdo: AnguloCotoveloLado | None
    direito: AnguloCotoveloLado | None


def _angulo_interno(
    a: tuple[float, float],
    b: tuple[float, float],
    c: tuple[float, float],
) -> float | None:
    """Ângulo em `b` entre os vetores `b→a` e `b→c` (em graus), via arccos."""
    return angulo_interno(a, b, c)


def _calcular_lado(
    frames: Sequence[FrameKeypoints],
    ombro_idx: int,
    cotovelo_idx: int,
    pulso_idx: int,
) -> AnguloCotoveloLado | None:
    angulos: list[float] = []
    for frame in frames:
        kps = frame.keypoints
        if (
            ombro_idx >= len(kps)
            or cotovelo_idx >= len(kps)
            or pulso_idx >= len(kps)
        ):
            continue
        ombro = kps[ombro_idx]
        cotovelo = kps[cotovelo_idx]
        pulso = kps[pulso_idx]
        if ombro is None or cotovelo is None or pulso is None:
            continue
        angulo = _angulo_interno(
            (ombro[0], ombro[1]),
            (cotovelo[0], cotovelo[1]),
            (pulso[0], pulso[1]),
        )
        if angulo is None:
            continue
        angulos.append(angulo)

    if not angulos:
        return None
    media = sum(angulos) / len(angulos)
    return AnguloCotoveloLado(
        angulo_medio_graus=media,
        frames_validos=len(angulos),
    )


def calcular_angulo_cotovelo(
    frames: Sequence[FrameKeypoints],
) -> AnguloCotoveloResultado:
    """Calcula o ângulo médio do cotovelo esq/dir sobre todos os frames válidos.

    Para cada lado:
      1. Para cada frame, calcula o ângulo interno do cotovelo
         (`arccos` do produto escalar normalizado entre `cotovelo→ombro`
         e `cotovelo→pulso`), desde que os três keypoints estejam presentes.
      2. Média sobre todos os frames válidos do vídeo.

    Quando nenhum frame contém os três keypoints do lado em questão, o campo
    correspondente de `AnguloCotoveloResultado` vem `None`.
    """
    esquerdo = _calcular_lado(
        frames, KP_OMBRO_ESQ, KP_COTOVELO_ESQ, KP_PULSO_ESQ
    )
    direito = _calcular_lado(
        frames, KP_OMBRO_DIR, KP_COTOVELO_DIR, KP_PULSO_DIR
    )
    return AnguloCotoveloResultado(esquerdo=esquerdo, direito=direito)
