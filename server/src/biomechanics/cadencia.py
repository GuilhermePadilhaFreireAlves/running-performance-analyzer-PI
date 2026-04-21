"""Cálculo de cadência (spm) — US-010.

A cadência (passos por minuto) é estimada a partir dos contatos iniciais
detectados no pé direito: picos locais estritos de Y do tornozelo direito
(KP 16) na série temporal. Conforme a Seção 6.3 do PRD, conta-se apenas um
pé e multiplica-se por 2 para obter o total de passos (um passo = um pé
tocando o solo).

Fórmulas:
    duracao_segundos = len(frames) / fps
    cadencia_spm = (n_contatos_pe_direito × 2 / duracao_segundos) × 60

A métrica é persistida em METRICA com `apenas_informativa=True` porque
varia diretamente com o pace e, conforme o PRD, não deve penalizar a nota
geral — apenas informar o corredor.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from server.src.video_pipeline import FrameKeypoints

KP_TORNOZELO_DIR = 16

MSG_FPS_INVALIDO = (
    "FPS inválido — é necessário FPS positivo para calcular a cadência."
)


@dataclass(frozen=True)
class Cadencia:
    """Resultado do cálculo de cadência (spm)."""

    cadencia_spm: float
    contatos_pe_direito: int
    duracao_segundos: float


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

    Mesma lógica usada em `biomechanics.joelho._find_initial_contact_indices`:
    frame `i` é pico quando o Y do tornozelo é estritamente maior que o dos
    vizinhos imediatos, exigindo que o tornozelo esteja detectado nos três
    frames. Bordas (`i==0` e `i==n-1`) nunca são picos.
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


def calcular_cadencia(
    frames: Sequence[FrameKeypoints], fps: float
) -> Cadencia | None:
    """Calcula a cadência (spm) a partir de contatos do pé direito.

    Etapas:
      1. Detecta contatos iniciais do pé direito como picos locais estritos
         de Y do tornozelo direito (keypoint 16).
      2. Duração do vídeo: `len(frames) / fps`.
      3. `cadencia_spm = (n_contatos × 2 / duracao) × 60`, conforme
         Seção 6.3 do PRD (contagem de um pé × 2 = total de passos).

    Retorna `None` quando a lista de frames está vazia ou quando nenhum
    contato é detectado (não há ciclos suficientes para estimar cadência).
    Levanta `ValueError(MSG_FPS_INVALIDO)` quando `fps` é não-positivo.
    """
    if fps <= 0:
        raise ValueError(MSG_FPS_INVALIDO)
    if len(frames) == 0:
        return None
    contatos = _find_initial_contact_indices(frames, KP_TORNOZELO_DIR)
    if not contatos:
        return None
    duracao = len(frames) / fps
    if duracao <= 0:
        return None
    cadencia = (len(contatos) * 2.0 / duracao) * 60.0
    return Cadencia(
        cadencia_spm=cadencia,
        contatos_pe_direito=len(contatos),
        duracao_segundos=duracao,
    )
