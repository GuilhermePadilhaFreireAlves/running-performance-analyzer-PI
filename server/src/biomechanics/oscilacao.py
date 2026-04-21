"""Oscilação vertical do centro de massa em cm (US-014).

A oscilação vertical do CoM é a excursão vertical do quadril entre o
contato inicial e o ápice da fase de voo, repetida a cada ciclo de
passada (stride). Um ciclo é delimitado por dois contatos iniciais
consecutivos do **pé direito** — mesma convenção usada por `cadencia.py`
(PRD Seção 6.3) para evitar ambiguidade entre "passo" e "passada".

Cálculo por ciclo:

    Y_CoM[frame] = (Y_quadril_esq[11] + Y_quadril_dir[12]) / 2
    ΔY_pixels    = max(Y_CoM) - min(Y_CoM)         (range fechado [i, j])
    oscilacao_cm = ΔY_pixels × fator_escala

A média final é calculada sobre todos os ciclos com pelo menos dois
frames de Y_CoM válidos. O ``fator_escala`` (cm/px) vem de
``biomechanics.escala.calcular_fator_escala`` (US-007) e é passado como
parâmetro puro — a camada biomecânica não lê ``usuario.altura_cm`` nem
toca o ORM.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from server.src.video_pipeline import FrameKeypoints

KP_QUADRIL_ESQ = 11
KP_QUADRIL_DIR = 12
KP_TORNOZELO_DIR = 16


@dataclass(frozen=True)
class OscilacaoVertical:
    """Oscilação vertical média do CoM em cm, com os ciclos processados."""

    oscilacao_media_cm: float
    ciclos_processados: tuple[int, ...]


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

    Mesma lógica usada em `biomechanics.joelho._find_initial_contact_indices`,
    `biomechanics.cadencia._find_initial_contact_indices` e
    `biomechanics.overstriding._find_initial_contact_indices`. Reaproveitada
    aqui para delimitar ciclos de passada via contatos consecutivos do pé
    direito.
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


def _y_com(frame: FrameKeypoints) -> float | None:
    kps = frame.keypoints
    if KP_QUADRIL_ESQ >= len(kps) or KP_QUADRIL_DIR >= len(kps):
        return None
    qe = kps[KP_QUADRIL_ESQ]
    qd = kps[KP_QUADRIL_DIR]
    if qe is None or qd is None:
        return None
    return (qe[1] + qd[1]) / 2.0


def calcular_oscilacao_vertical(
    frames: Sequence[FrameKeypoints], fator_escala: float
) -> OscilacaoVertical | None:
    """Calcula a oscilação vertical média do CoM em cm, por ciclo de passada.

    Para cada par de contatos iniciais consecutivos do pé direito ``(i, j)``:
      1. Coleta ``Y_CoM[frame]`` no intervalo fechado ``[i, j]`` (ignorando
         frames sem ambos os quadris válidos).
      2. ``ΔY_pixels = max(Y_CoM) - min(Y_CoM)``.
      3. Converte para cm via ``ΔY_pixels × fator_escala``.

    A média é calculada sobre os ciclos com pelo menos dois frames de
    ``Y_CoM`` válidos. Retorna ``None`` quando há menos de dois contatos
    detectados ou nenhum ciclo válido.
    """
    contatos = _find_initial_contact_indices(frames, KP_TORNOZELO_DIR)
    if len(contatos) < 2:
        return None

    oscilacoes_cm: list[float] = []
    ciclos_idx: list[int] = []
    for k in range(len(contatos) - 1):
        i_start = contatos[k]
        i_end = contatos[k + 1]
        ys: list[float] = []
        for j in range(i_start, i_end + 1):
            y = _y_com(frames[j])
            if y is not None:
                ys.append(y)
        if len(ys) < 2:
            continue
        delta_y = max(ys) - min(ys)
        oscilacoes_cm.append(delta_y * fator_escala)
        ciclos_idx.append(frames[i_start].frame_idx)

    if not oscilacoes_cm:
        return None
    media = sum(oscilacoes_cm) / len(oscilacoes_cm)
    return OscilacaoVertical(
        oscilacao_media_cm=media,
        ciclos_processados=tuple(ciclos_idx),
    )
