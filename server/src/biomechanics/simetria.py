"""Índice de simetria esq/dir (US-015).

Assimetria entre lados é um preditor de lesão em corrida (> 10% indica
desequilíbrio relevante, conforme a Seção 9 do PRD). O índice é calculado
como percentual da diferença absoluta sobre a média dos dois lados:

    IS = |valor_esq - valor_dir| / ((valor_esq + valor_dir) / 2) × 100

Aplicado a três grandezas onde o PRD exige simetria:

    * ``simetria_tcs``      — Tempo de Contato com o Solo (US-013, ms).
    * ``simetria_joelho``   — ângulo do joelho no contato inicial (US-008, °).
    * ``simetria_oscilacao``— oscilação vertical por ciclo (US-014, cm), com
                              os ciclos delimitados separadamente pelos contatos
                              do pé esquerdo e do direito.

Quando o valor de um dos lados está ausente o índice correspondente vem
``None`` — o helper de persistência do pipeline ignora o campo nesse caso
(critério "erro controlado: não persiste simetria" do PRD).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from server.src.video_pipeline import FrameKeypoints


@dataclass(frozen=True)
class SimetriaResultado:
    """Índices de simetria (%) para TCS, joelho e oscilação vertical.

    Cada campo é ``None`` quando o valor de um dos lados da métrica
    correspondente está ausente — nessa situação a simetria não pode ser
    calculada de forma consistente e não deve ser persistida.
    """

    simetria_tcs: float | None
    simetria_joelho: float | None
    simetria_oscilacao: float | None


def indice_simetria(
    valor_esq: float | None, valor_dir: float | None
) -> float | None:
    """Calcula o índice de simetria (%) entre dois valores esq/dir.

    Fórmula: ``IS = |valor_esq - valor_dir| / ((valor_esq + valor_dir) / 2) × 100``.

    Retorna ``None`` quando algum dos valores é ``None`` (lado ausente);
    lados com soma zero (ambos exatamente 0) são tratados como simetria
    perfeita ``0.0%`` para evitar divisão por zero — situação degenerada
    onde a fórmula do PRD é indefinida.
    """
    if valor_esq is None or valor_dir is None:
        return None
    soma = valor_esq + valor_dir
    if soma == 0:
        return 0.0
    return abs(valor_esq - valor_dir) / (soma / 2.0) * 100.0


def calcular_simetria(
    frames: Sequence[FrameKeypoints],
    fps: float,
    fator_escala: float | None,
) -> SimetriaResultado:
    """Calcula os três índices de simetria a partir dos keypoints suavizados.

    Orquestra os cálculos de US-008 (joelho), US-013 (TCS) e US-014
    (oscilação vertical por lado) e aplica ``indice_simetria`` a cada par
    esq/dir. Quando o cálculo base de um lado não produz valor (ciclo sem
    keypoints, nenhum contato detectado, FPS inválido, fator de escala
    ausente), o índice correspondente vem ``None``.

    ``fator_escala`` é opcional: quando ``None`` ou não-positivo, a
    simetria de oscilação é ``None`` (o PRD exige conversão a cm, que só é
    possível com o fator). ``fps <= 0`` descarta apenas a simetria de TCS
    — os demais índices não dependem de tempo real.
    """
    from server.src.biomechanics.joelho import (
        calcular_angulo_joelho_contato_inicial,
    )
    from server.src.biomechanics.oscilacao import (
        calcular_oscilacao_vertical_por_lado,
    )
    from server.src.biomechanics.tcs import calcular_tcs

    joelho = calcular_angulo_joelho_contato_inicial(frames)
    simetria_joelho = indice_simetria(
        joelho.esquerdo.angulo_medio_graus if joelho.esquerdo else None,
        joelho.direito.angulo_medio_graus if joelho.direito else None,
    )

    if fps > 0:
        tcs = calcular_tcs(frames, fps)
        simetria_tcs = indice_simetria(
            tcs.esquerdo.tcs_medio_ms if tcs.esquerdo else None,
            tcs.direito.tcs_medio_ms if tcs.direito else None,
        )
    else:
        simetria_tcs = None

    if fator_escala is not None and fator_escala > 0:
        oscilacao = calcular_oscilacao_vertical_por_lado(frames, fator_escala)
        simetria_oscilacao = indice_simetria(
            oscilacao.esquerdo.oscilacao_media_cm
            if oscilacao.esquerdo
            else None,
            oscilacao.direito.oscilacao_media_cm
            if oscilacao.direito
            else None,
        )
    else:
        simetria_oscilacao = None

    return SimetriaResultado(
        simetria_tcs=simetria_tcs,
        simetria_joelho=simetria_joelho,
        simetria_oscilacao=simetria_oscilacao,
    )
