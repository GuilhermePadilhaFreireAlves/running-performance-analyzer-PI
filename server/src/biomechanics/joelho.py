"""Ângulo do joelho no contato inicial (US-008).

O contato inicial é identificado por ciclo como o frame em que o tornozelo
atinge a coordenada Y máxima (altitude mínima em coordenadas de imagem, onde
Y cresce para baixo). Nesse frame, calcula-se o ângulo interno do joelho via
arccos do produto escalar normalizado entre os vetores ``joelho→quadril`` e
``joelho→tornozelo``.

Convenção de ângulo (diferente da tela em `processing/src/mainGraph.py`):
  perna estendida ⇒ 180°; flexão cresce conforme o ângulo se afasta de 180°.
Esta convenção casa com o que o PRD pede para persistir em METRICA
(`angulo_joelho_esq` / `angulo_joelho_dir`, unidade `graus`).
"""

from __future__ import annotations

from dataclasses import dataclass
from math import acos, degrees, hypot
from typing import Sequence

from server.src.video_pipeline import FrameKeypoints

KP_QUADRIL_ESQ = 11
KP_QUADRIL_DIR = 12
KP_JOELHO_ESQ = 13
KP_JOELHO_DIR = 14
KP_TORNOZELO_ESQ = 15
KP_TORNOZELO_DIR = 16


@dataclass(frozen=True)
class AnguloJoelhoLado:
    """Ângulo médio do joelho no contato inicial em um lado do corpo."""

    angulo_medio_graus: float
    frames_contato: tuple[int, ...]


@dataclass(frozen=True)
class AnguloJoelhoContatoInicial:
    """Resultado agregado para os lados esquerdo e direito.

    Cada lado é `None` quando nenhum ciclo com keypoints válidos foi detectado
    (tornozelo não forma picos de Y, ou os três keypoints requeridos estão
    ausentes em todos os picos).
    """

    esquerdo: AnguloJoelhoLado | None
    direito: AnguloJoelhoLado | None


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
    # proteção contra erro numérico que empurra o cos levemente para fora de [-1,1]
    if cos_theta > 1.0:
        cos_theta = 1.0
    elif cos_theta < -1.0:
        cos_theta = -1.0
    return degrees(acos(cos_theta))


def _find_initial_contact_indices(
    frames: Sequence[FrameKeypoints], tornozelo_idx: int
) -> list[int]:
    """Índices (dentro de `frames`) onde o tornozelo atinge Y máximo local.

    Um frame `i` é pico quando o Y do tornozelo é estritamente maior que o Y
    do frame anterior e do frame seguinte, exigindo que o tornozelo esteja
    detectado nos três frames. Bordas (`i==0` e `i==n-1`) nunca são picos.
    """
    n = len(frames)
    peaks: list[int] = []
    for i in range(1, n - 1):
        cur = _ankle_y(frames[i], tornozelo_idx)
        prev_ = _ankle_y(frames[i - 1], tornozelo_idx)
        nxt = _ankle_y(frames[i + 1], tornozelo_idx)
        if cur is None or prev_ is None or nxt is None:
            continue
        if cur > prev_ and cur > nxt:
            peaks.append(i)
    return peaks


def _ankle_y(frame: FrameKeypoints, idx: int) -> float | None:
    if idx >= len(frame.keypoints):
        return None
    kp = frame.keypoints[idx]
    if kp is None:
        return None
    return kp[1]


def _calcular_lado(
    frames: Sequence[FrameKeypoints],
    quadril_idx: int,
    joelho_idx: int,
    tornozelo_idx: int,
) -> AnguloJoelhoLado | None:
    contatos = _find_initial_contact_indices(frames, tornozelo_idx)
    if not contatos:
        return None

    angulos: list[float] = []
    frames_usados: list[int] = []
    for i in contatos:
        kps = frames[i].keypoints
        if (
            quadril_idx >= len(kps)
            or joelho_idx >= len(kps)
            or tornozelo_idx >= len(kps)
        ):
            continue
        quadril = kps[quadril_idx]
        joelho = kps[joelho_idx]
        tornozelo = kps[tornozelo_idx]
        if quadril is None or joelho is None or tornozelo is None:
            continue
        angulo = _angulo_interno(
            (quadril[0], quadril[1]),
            (joelho[0], joelho[1]),
            (tornozelo[0], tornozelo[1]),
        )
        if angulo is None:
            continue
        angulos.append(angulo)
        frames_usados.append(frames[i].frame_idx)

    if not angulos:
        return None
    media = sum(angulos) / len(angulos)
    return AnguloJoelhoLado(
        angulo_medio_graus=media,
        frames_contato=tuple(frames_usados),
    )


def calcular_angulo_joelho_contato_inicial(
    frames: Sequence[FrameKeypoints],
) -> AnguloJoelhoContatoInicial:
    """Calcula o ângulo médio do joelho nos frames de contato inicial.

    Para cada lado:
      1. Detecta frames de contato inicial como picos locais em Y do tornozelo.
      2. Em cada pico, calcula o ângulo interno do joelho
         (`arccos` do produto escalar normalizado entre `joelho→quadril`
         e `joelho→tornozelo`).
      3. Média dos ângulos sobre todos os picos com keypoints válidos.

    Frames sem os três keypoints (quadril, joelho, tornozelo) do lado em
    questão são ignorados. Quando nenhum pico com dados válidos existe, o
    campo correspondente de `AnguloJoelhoContatoInicial` vem `None`.
    """
    esquerdo = _calcular_lado(
        frames, KP_QUADRIL_ESQ, KP_JOELHO_ESQ, KP_TORNOZELO_ESQ
    )
    direito = _calcular_lado(
        frames, KP_QUADRIL_DIR, KP_JOELHO_DIR, KP_TORNOZELO_DIR
    )
    return AnguloJoelhoContatoInicial(esquerdo=esquerdo, direito=direito)
