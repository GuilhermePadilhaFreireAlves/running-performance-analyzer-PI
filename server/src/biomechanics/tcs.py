"""Tempo de Contato com o Solo — TCS em ms (US-013).

Para cada pé (esq/dir), o ciclo de contato é delimitado pelo tornozelo:

    Contato inicial: frame em que Y do tornozelo atinge o máximo local
        (a série Y cresce estritamente até o frame `i`, e o próximo frame
        tem Y ≤ Y[i]; plateau é aceito).
    Saída do pé:     primeiro frame `j > i` em que Y decresce estritamente
        (``Y[j] < Y[j-1]``), indicando o início da elevação contínua.

    frames_de_contato = j - i
    tcs_ms            = (frames_de_contato / fps) × 1000

O valor final por lado é a média dos `tcs_ms` sobre os ciclos válidos.
A métrica é persistida em METRICA com ``apenas_informativa=True`` porque,
conforme o PRD, o TCS absoluto não deve penalizar a nota geral — apenas a
simetria esq/dir (US-015) pode penalizar.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from server.src.video_pipeline import FrameKeypoints

KP_TORNOZELO_ESQ = 15
KP_TORNOZELO_DIR = 16

MSG_FPS_INVALIDO = (
    "FPS inválido — é necessário FPS positivo para calcular o TCS."
)


@dataclass(frozen=True)
class TcsLado:
    """TCS médio (ms) para um lado do corpo, sobre ciclos válidos."""

    tcs_medio_ms: float
    frames_contato: tuple[int, ...]


@dataclass(frozen=True)
class TcsResultado:
    """Resultado agregado para os lados esquerdo e direito.

    Cada lado é `None` quando nenhum ciclo de contato com Y do tornozelo
    válido foi detectado na série.
    """

    esquerdo: TcsLado | None
    direito: TcsLado | None


def _ankle_y(frame: FrameKeypoints, idx: int) -> float | None:
    if idx >= len(frame.keypoints):
        return None
    kp = frame.keypoints[idx]
    if kp is None:
        return None
    return kp[1]


def _detectar_ciclos_contato(
    y_series: list[float | None],
) -> list[tuple[int, int]]:
    """Identifica ciclos de contato na série Y do tornozelo.

    Retorna lista de ``(inicio_idx, frames_de_contato)``:
      * ``inicio_idx`` — índice (dentro da série) do frame em que o tornozelo
        atinge Y máximo local (plateau aceito): ``Y[i-1] < Y[i]`` e
        ``Y[i+1] ≤ Y[i]``. Bordas (``i == 0`` ou ``i == n-1``) nunca são
        início de contato.
      * ``frames_de_contato`` — número de frames de ``inicio_idx`` até a
        primeira queda estrita (``Y[j] < Y[j-1]``, com ``j > inicio_idx``).

    Ciclos cujo fim não é observado (série terminou ou foi interrompida por
    ``None`` antes de uma queda) são descartados silenciosamente.
    """
    cycles: list[tuple[int, int]] = []
    n = len(y_series)
    i = 1
    while i < n - 1:
        prev_y = y_series[i - 1]
        cur_y = y_series[i]
        next_y = y_series[i + 1]
        if prev_y is None or cur_y is None or next_y is None:
            i += 1
            continue
        if cur_y > prev_y and next_y <= cur_y:
            fim_idx: int | None = None
            j = i + 1
            while j < n:
                y_j = y_series[j]
                y_prev_j = y_series[j - 1]
                if y_j is None or y_prev_j is None:
                    break
                if y_j < y_prev_j:
                    fim_idx = j
                    break
                j += 1
            if fim_idx is not None:
                cycles.append((i, fim_idx - i))
                i = fim_idx
                continue
            # série terminou ou foi interrompida sem detectar queda estrita;
            # pula o ponto de interrupção e continua procurando ciclos.
            i = j + 1
            continue
        i += 1
    return cycles


def _calcular_lado(
    frames: Sequence[FrameKeypoints], tornozelo_idx: int, fps: float
) -> TcsLado | None:
    ys: list[float | None] = [_ankle_y(f, tornozelo_idx) for f in frames]
    ciclos = _detectar_ciclos_contato(ys)
    if not ciclos:
        return None
    tcs_values_ms: list[float] = []
    frames_usados: list[int] = []
    for inicio_idx, n_contato in ciclos:
        tcs_values_ms.append((n_contato / fps) * 1000.0)
        frames_usados.append(frames[inicio_idx].frame_idx)
    media = sum(tcs_values_ms) / len(tcs_values_ms)
    return TcsLado(
        tcs_medio_ms=media,
        frames_contato=tuple(frames_usados),
    )


def calcular_tcs(
    frames: Sequence[FrameKeypoints], fps: float
) -> TcsResultado:
    """Calcula o TCS (ms) esq/dir a partir da série de keypoints suavizada.

    Para cada lado:
      1. Monta a série Y do tornozelo (``None`` para frames sem keypoint).
      2. Detecta ciclos de contato: início em ``Y`` máximo local (plateau
         aceito) e fim na primeira queda estrita (``Y[j] < Y[j-1]``).
      3. ``tcs_ms = (frames_de_contato / fps) × 1000`` por ciclo.
      4. Média sobre ciclos válidos.

    Levanta ``ValueError(MSG_FPS_INVALIDO)`` quando ``fps <= 0``. Quando
    nenhum ciclo é detectado em um lado, o campo correspondente vem
    ``None``.
    """
    if fps <= 0:
        raise ValueError(MSG_FPS_INVALIDO)
    esquerdo = _calcular_lado(frames, KP_TORNOZELO_ESQ, fps)
    direito = _calcular_lado(frames, KP_TORNOZELO_DIR, fps)
    return TcsResultado(esquerdo=esquerdo, direito=direito)
