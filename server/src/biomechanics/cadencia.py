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

from server.src.biomechanics.contact import (
    find_initial_contact_indices as _find_initial_contact_indices,
)
from server.src.video_pipeline import FrameKeypoints

KP_TORNOZELO_DIR = 16

MSG_FPS_INVALIDO_CADENCIA = (
    "FPS inválido — é necessário FPS positivo para calcular a cadência."
)
MSG_FPS_INVALIDO = MSG_FPS_INVALIDO_CADENCIA


@dataclass(frozen=True)
class CadenciaEvento:
    """Cadência instantânea (spm) derivada do intervalo entre duas passadas consecutivas."""

    frame_idx: int
    cadencia_spm: float


@dataclass(frozen=True)
class Cadencia:
    """Resultado do cálculo de cadência (spm)."""

    cadencia_spm: float
    contatos_pe_direito: int
    duracao_segundos: float
    eventos: tuple[CadenciaEvento, ...]


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
    Levanta `ValueError(MSG_FPS_INVALIDO_CADENCIA)` quando `fps` é não-positivo.
    """
    if fps <= 0:
        raise ValueError(MSG_FPS_INVALIDO_CADENCIA)
    if len(frames) == 0:
        return None
    contatos = _find_initial_contact_indices(frames, KP_TORNOZELO_DIR)
    if not contatos:
        return None
    duracao = len(frames) / fps
    if duracao <= 0:
        return None
    cadencia = (len(contatos) * 2.0 / duracao) * 60.0
    eventos: list[CadenciaEvento] = []
    for i in range(len(contatos) - 1):
        delta = contatos[i + 1] - contatos[i]
        if delta > 0:
            spm = (2.0 * fps / delta) * 60.0
            eventos.append(CadenciaEvento(
                frame_idx=frames[contatos[i]].frame_idx,
                cadencia_spm=spm,
            ))
    return Cadencia(
        cadencia_spm=cadencia,
        contatos_pe_direito=len(contatos),
        duracao_segundos=duracao,
        eventos=tuple(eventos),
    )
