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
from typing import Sequence

from server.src.biomechanics.contact import (
    find_initial_contact_indices as _find_initial_contact_indices,
)
from server.src.biomechanics.geometry import angulo_interno
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
    return angulo_interno(a, b, c)


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
