"""Testes do cálculo de inclinação do tronco em apoio médio (US-011)."""

from __future__ import annotations

import math

from server.src.biomechanics.tronco import (
    KP_JOELHO_DIR,
    KP_JOELHO_ESQ,
    KP_OMBRO_DIR,
    KP_OMBRO_ESQ,
    KP_QUADRIL_DIR,
    KP_QUADRIL_ESQ,
    KP_TORNOZELO_DIR,
    KP_TORNOZELO_ESQ,
    calcular_inclinacao_tronco,
)
from server.src.video_pipeline import (
    KEYPOINT_SCORE_THRESHOLD,
    NUM_KEYPOINTS,
    FrameKeypoints,
    Keypoint,
)

SCORE = max(0.9, KEYPOINT_SCORE_THRESHOLD + 0.1)

# Geometria de apoio médio (esquerdo): quadril (100,200), joelho (100,300),
# tornozelo (145,350). Por construção, ângulo interno do joelho ≈ 138°,
# logo flexão = 180-138 = 42°, dentro da janela [40°, 45°].
QUADRIL_ESQ_PADRAO = (100.0, 200.0)
JOELHO_ESQ_PADRAO = (100.0, 300.0)
TORNOZELO_ESQ_APOIO_MEDIO = (145.0, 350.0)
# Mesma geometria para o lado direito (espelhada conceitualmente).
QUADRIL_DIR_PADRAO = (100.0, 200.0)
JOELHO_DIR_PADRAO = (100.0, 300.0)
TORNOZELO_DIR_APOIO_MEDIO = (145.0, 350.0)


def _frame(
    idx: int,
    *,
    ombro_esq: tuple[float, float] | None = None,
    ombro_dir: tuple[float, float] | None = None,
    quadril_esq: tuple[float, float] | None = None,
    quadril_dir: tuple[float, float] | None = None,
    joelho_esq: tuple[float, float] | None = None,
    joelho_dir: tuple[float, float] | None = None,
    tornozelo_esq: tuple[float, float] | None = None,
    tornozelo_dir: tuple[float, float] | None = None,
) -> FrameKeypoints:
    kps: list[Keypoint] = [None] * NUM_KEYPOINTS
    if ombro_esq is not None:
        kps[KP_OMBRO_ESQ] = (ombro_esq[0], ombro_esq[1], SCORE)
    if ombro_dir is not None:
        kps[KP_OMBRO_DIR] = (ombro_dir[0], ombro_dir[1], SCORE)
    if quadril_esq is not None:
        kps[KP_QUADRIL_ESQ] = (quadril_esq[0], quadril_esq[1], SCORE)
    if quadril_dir is not None:
        kps[KP_QUADRIL_DIR] = (quadril_dir[0], quadril_dir[1], SCORE)
    if joelho_esq is not None:
        kps[KP_JOELHO_ESQ] = (joelho_esq[0], joelho_esq[1], SCORE)
    if joelho_dir is not None:
        kps[KP_JOELHO_DIR] = (joelho_dir[0], joelho_dir[1], SCORE)
    if tornozelo_esq is not None:
        kps[KP_TORNOZELO_ESQ] = (tornozelo_esq[0], tornozelo_esq[1], SCORE)
    if tornozelo_dir is not None:
        kps[KP_TORNOZELO_DIR] = (tornozelo_dir[0], tornozelo_dir[1], SCORE)
    return FrameKeypoints(frame_idx=idx, person_count=1, keypoints=kps)


def _frame_apoio_medio(
    idx: int,
    *,
    ombros_x: float,
    ombros_y: float = 100.0,
) -> FrameKeypoints:
    """Frame com knee em apoio médio (esq) e tronco em (ombros_x, ombros_y).

    Os quadris ficam fixos em (100, 200) — então a base do tronco é (100, 200)
    e o topo é (ombros_x, ombros_y). Inclinação resultante:
        arctan((ombros_x - 100) / -(ombros_y - 200))
        = arctan((ombros_x - 100) / (200 - ombros_y)).
    """
    return _frame(
        idx,
        ombro_esq=(ombros_x, ombros_y),
        ombro_dir=(ombros_x, ombros_y),
        quadril_esq=QUADRIL_ESQ_PADRAO,
        quadril_dir=QUADRIL_DIR_PADRAO,
        joelho_esq=JOELHO_ESQ_PADRAO,
        tornozelo_esq=TORNOZELO_ESQ_APOIO_MEDIO,
    )


def test_tronco_ereto_retorna_zero_graus() -> None:
    # Ombros e quadris alinhados verticalmente: ΔX = 0 ⇒ inclinação = 0°.
    frames = [_frame_apoio_medio(0, ombros_x=100.0)]

    resultado = calcular_inclinacao_tronco(frames)

    assert resultado is not None
    assert resultado.frames_validos == 1
    assert math.isclose(resultado.inclinacao_media_graus, 0.0, abs_tol=1e-9)


def test_tronco_inclinado_10_graus_para_frente() -> None:
    # Topo deslocado tan(10°)*100 ≈ 17.633 px em +X em relação à base; o
    # vetor base→topo forma 10° com a vertical.
    deslocamento = 100.0 * math.tan(math.radians(10.0))
    frames = [_frame_apoio_medio(0, ombros_x=100.0 + deslocamento)]

    resultado = calcular_inclinacao_tronco(frames)

    assert resultado is not None
    assert resultado.frames_validos == 1
    assert math.isclose(
        resultado.inclinacao_media_graus, 10.0, rel_tol=1e-9, abs_tol=1e-9
    )


def test_media_sobre_multiplos_frames_em_apoio_medio() -> None:
    # Dois frames em apoio médio: 0° e 10°. Média esperada = 5°.
    desloc_10 = 100.0 * math.tan(math.radians(10.0))
    frames = [
        _frame_apoio_medio(0, ombros_x=100.0),
        _frame_apoio_medio(1, ombros_x=100.0 + desloc_10),
    ]

    resultado = calcular_inclinacao_tronco(frames)

    assert resultado is not None
    assert resultado.frames_validos == 2
    assert math.isclose(
        resultado.inclinacao_media_graus, 5.0, rel_tol=1e-9, abs_tol=1e-9
    )


def test_frames_fora_do_apoio_medio_sao_ignorados() -> None:
    # Joelho com flexão fora de [40°, 45°] (perna estendida ⇒ flexão 0°)
    # não deve contar para a média, mesmo com tronco bem definido.
    desloc_10 = 100.0 * math.tan(math.radians(10.0))
    frames = [
        # Frame 0: joelho estendido (perna colinear) ⇒ flexão 0° ⇒ não-apoio.
        _frame(
            0,
            ombro_esq=(100.0 + desloc_10, 100.0),
            ombro_dir=(100.0 + desloc_10, 100.0),
            quadril_esq=QUADRIL_ESQ_PADRAO,
            quadril_dir=QUADRIL_DIR_PADRAO,
            joelho_esq=JOELHO_ESQ_PADRAO,
            tornozelo_esq=(100.0, 400.0),
        ),
        # Frame 1: apoio médio com tronco a 0°.
        _frame_apoio_medio(1, ombros_x=100.0),
    ]

    resultado = calcular_inclinacao_tronco(frames)

    assert resultado is not None
    assert resultado.frames_validos == 1
    assert math.isclose(resultado.inclinacao_media_graus, 0.0, abs_tol=1e-9)


def test_frame_sem_ombros_ou_quadris_eh_descartado() -> None:
    # Apoio médio confirmado pelo joelho esq, mas falta um dos ombros
    # ⇒ frame inteiro descartado (sem topo definido).
    frames = [
        _frame(
            0,
            ombro_esq=(100.0, 100.0),
            # ombro_dir ausente
            quadril_esq=QUADRIL_ESQ_PADRAO,
            quadril_dir=QUADRIL_DIR_PADRAO,
            joelho_esq=JOELHO_ESQ_PADRAO,
            tornozelo_esq=TORNOZELO_ESQ_APOIO_MEDIO,
        ),
    ]

    resultado = calcular_inclinacao_tronco(frames)

    assert resultado is None


def test_apoio_medio_pode_vir_de_qualquer_lado() -> None:
    # Apenas o joelho direito está em apoio médio; o esquerdo não tem
    # keypoints. Mesmo assim o frame é considerado apoio médio.
    frames = [
        _frame(
            0,
            ombro_esq=(100.0, 100.0),
            ombro_dir=(100.0, 100.0),
            quadril_esq=QUADRIL_ESQ_PADRAO,
            quadril_dir=QUADRIL_DIR_PADRAO,
            joelho_dir=JOELHO_DIR_PADRAO,
            tornozelo_dir=TORNOZELO_DIR_APOIO_MEDIO,
        ),
    ]

    resultado = calcular_inclinacao_tronco(frames)

    assert resultado is not None
    assert resultado.frames_validos == 1
    assert math.isclose(resultado.inclinacao_media_graus, 0.0, abs_tol=1e-9)


def test_lista_vazia_retorna_none() -> None:
    assert calcular_inclinacao_tronco([]) is None


def test_inclinacao_para_tras_tem_sinal_negativo() -> None:
    # Topo deslocado em -X em relação à base ⇒ inclinação negativa
    # (tronco para trás), magnitude 10°.
    desloc = 100.0 * math.tan(math.radians(10.0))
    frames = [_frame_apoio_medio(0, ombros_x=100.0 - desloc)]

    resultado = calcular_inclinacao_tronco(frames)

    assert resultado is not None
    assert math.isclose(
        resultado.inclinacao_media_graus, -10.0, rel_tol=1e-9, abs_tol=1e-9
    )
