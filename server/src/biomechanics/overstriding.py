"""Overstriding horizontal do pé em relação ao CoM (US-012).

Para cada frame de contato inicial (pico local estrito de Y do tornozelo),
calcula-se:

    CoM_X = (quadril_esq_X[11] + quadril_dir_X[12]) / 2
    overstriding_px = tornozelo_X - CoM_X         (sinal preservado)
    overstriding_cm = overstriding_px × fator_escala

A média em cm é calculada sobre os ciclos por lado (esq/dir). O
`fator_escala` (cm/px) é o resultado de `biomechanics.escala.calcular_fator_escala`
(US-007) e entra como parâmetro — a camada biomecânica não lê
`usuario.altura_cm` nem toca o ORM.

Convenção de sinal: positivo ⇒ pé à frente do CoM (overstriding clássico,
associado a lesão); negativo ⇒ pé atrás do CoM. Válido para um vídeo lateral
com o corredor se deslocando no sentido +X. O sinal é propagado porque US-016
(tabela de thresholds) e US-018 (raw feed) precisam diferenciar superextensão
à frente vs. aterrissagem sob o quadril.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from server.src.video_pipeline import FrameKeypoints

KP_QUADRIL_ESQ = 11
KP_QUADRIL_DIR = 12
KP_TORNOZELO_ESQ = 15
KP_TORNOZELO_DIR = 16


@dataclass(frozen=True)
class OverstridingLado:
    """Overstriding médio em cm em um lado do corpo."""

    overstriding_medio_cm: float
    frames_contato: tuple[int, ...]


@dataclass(frozen=True)
class OverstridingResultado:
    """Resultado agregado para os lados esquerdo e direito.

    Cada lado é `None` quando nenhum ciclo com os três keypoints requeridos
    (tornozelo do lado + ambos os quadris) foi detectado no frame de
    contato inicial.
    """

    esquerdo: OverstridingLado | None
    direito: OverstridingLado | None


def _ankle_y(frame: FrameKeypoints, idx: int) -> float | None:
    if idx >= len(frame.keypoints):
        return None
    kp = frame.keypoints[idx]
    if kp is None:
        return None
    return kp[1]


def _find_initial_contact_indices(
    frames: Sequence[FrameKeypoints], tornozelo_idx: int
) -> list[int]:
    """Picos locais estritos de Y do tornozelo (ignora bordas).

    Mesma lógica usada em `biomechanics.joelho._find_initial_contact_indices`
    e `biomechanics.cadencia._find_initial_contact_indices`: um frame `i` é
    pico quando o Y do tornozelo é estritamente maior que o dos vizinhos
    imediatos, exigindo que o tornozelo esteja detectado nos três frames.
    Bordas (`i == 0` e `i == n - 1`) nunca são picos.
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


def _calcular_lado(
    frames: Sequence[FrameKeypoints],
    tornozelo_idx: int,
    fator_escala: float,
) -> OverstridingLado | None:
    contatos = _find_initial_contact_indices(frames, tornozelo_idx)
    if not contatos:
        return None

    overstridings_cm: list[float] = []
    frames_usados: list[int] = []
    for i in contatos:
        kps = frames[i].keypoints
        if (
            tornozelo_idx >= len(kps)
            or KP_QUADRIL_ESQ >= len(kps)
            or KP_QUADRIL_DIR >= len(kps)
        ):
            continue
        tornozelo = kps[tornozelo_idx]
        quadril_esq = kps[KP_QUADRIL_ESQ]
        quadril_dir = kps[KP_QUADRIL_DIR]
        if tornozelo is None or quadril_esq is None or quadril_dir is None:
            continue
        com_x = (quadril_esq[0] + quadril_dir[0]) / 2.0
        overstriding_px = tornozelo[0] - com_x
        overstridings_cm.append(overstriding_px * fator_escala)
        frames_usados.append(frames[i].frame_idx)

    if not overstridings_cm:
        return None
    media = sum(overstridings_cm) / len(overstridings_cm)
    return OverstridingLado(
        overstriding_medio_cm=media,
        frames_contato=tuple(frames_usados),
    )


def calcular_overstriding(
    frames: Sequence[FrameKeypoints], fator_escala: float
) -> OverstridingResultado:
    """Calcula overstriding (cm) esq/dir no contato inicial.

    Para cada lado:
      1. Detecta frames de contato inicial como picos locais em Y do tornozelo.
      2. No frame de contato: `CoM_X = mean(quadril_esq_X, quadril_dir_X)` e
         `overstriding_px = tornozelo_X - CoM_X` (sinal preservado).
      3. Converte para cm via `overstriding_px * fator_escala`.
      4. Média dos valores em cm sobre os picos com keypoints válidos.

    Frames sem os três keypoints requeridos (tornozelo do lado + ambos os
    quadris) são ignorados. Quando nenhum pico com dados válidos existe, o
    lado correspondente vem `None`.
    """
    esquerdo = _calcular_lado(frames, KP_TORNOZELO_ESQ, fator_escala)
    direito = _calcular_lado(frames, KP_TORNOZELO_DIR, fator_escala)
    return OverstridingResultado(esquerdo=esquerdo, direito=direito)
