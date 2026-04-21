"""Testes do cálculo de ângulo do joelho no contato inicial (US-008)."""

from __future__ import annotations

import math

from server.src.biomechanics.joelho import (
    KP_JOELHO_DIR,
    KP_JOELHO_ESQ,
    KP_QUADRIL_DIR,
    KP_QUADRIL_ESQ,
    calcular_angulo_joelho_contato_inicial,
)
from server.src.video_pipeline import (
    KEYPOINT_SCORE_THRESHOLD,
    NUM_KEYPOINTS,
    FrameKeypoints,
    Keypoint,
)

KP_TORNOZELO_ESQ = 15
KP_TORNOZELO_DIR = 16

SCORE = max(0.9, KEYPOINT_SCORE_THRESHOLD + 0.1)


def _frame(
    idx: int,
    *,
    quadril_esq: tuple[float, float] | None = None,
    joelho_esq: tuple[float, float] | None = None,
    tornozelo_esq: tuple[float, float] | None = None,
    quadril_dir: tuple[float, float] | None = None,
    joelho_dir: tuple[float, float] | None = None,
    tornozelo_dir: tuple[float, float] | None = None,
) -> FrameKeypoints:
    kps: list[Keypoint] = [None] * NUM_KEYPOINTS
    if quadril_esq is not None:
        kps[KP_QUADRIL_ESQ] = (quadril_esq[0], quadril_esq[1], SCORE)
    if joelho_esq is not None:
        kps[KP_JOELHO_ESQ] = (joelho_esq[0], joelho_esq[1], SCORE)
    if tornozelo_esq is not None:
        kps[KP_TORNOZELO_ESQ] = (tornozelo_esq[0], tornozelo_esq[1], SCORE)
    if quadril_dir is not None:
        kps[KP_QUADRIL_DIR] = (quadril_dir[0], quadril_dir[1], SCORE)
    if joelho_dir is not None:
        kps[KP_JOELHO_DIR] = (joelho_dir[0], joelho_dir[1], SCORE)
    if tornozelo_dir is not None:
        kps[KP_TORNOZELO_DIR] = (tornozelo_dir[0], tornozelo_dir[1], SCORE)
    return FrameKeypoints(frame_idx=idx, person_count=1, keypoints=kps)


def test_perna_estendida_retorna_180_graus() -> None:
    # Quadril (100,100) — joelho (100,300) — tornozelo (100,500): tudo colinear.
    # Vetores joelho→quadril = (0,-200) e joelho→tornozelo = (0,200) são
    # antiparalelos → arccos(-1) = 180°.
    # Pico de Y do tornozelo no frame 1 (500 > 450 vizinhos).
    frames = [
        _frame(
            0,
            quadril_esq=(100.0, 100.0),
            joelho_esq=(100.0, 300.0),
            tornozelo_esq=(100.0, 450.0),
        ),
        _frame(
            1,
            quadril_esq=(100.0, 100.0),
            joelho_esq=(100.0, 300.0),
            tornozelo_esq=(100.0, 500.0),
        ),
        _frame(
            2,
            quadril_esq=(100.0, 100.0),
            joelho_esq=(100.0, 300.0),
            tornozelo_esq=(100.0, 450.0),
        ),
    ]

    resultado = calcular_angulo_joelho_contato_inicial(frames)

    assert resultado.esquerdo is not None
    assert resultado.direito is None
    assert math.isclose(resultado.esquerdo.angulo_medio_graus, 180.0, abs_tol=1e-9)
    assert resultado.esquerdo.frames_contato == (1,)


def test_flexao_90_graus_conhecida() -> None:
    # Quadril (100,100), joelho (100,300), tornozelo (300,300):
    # joelho→quadril = (0,-200); joelho→tornozelo = (200,0) → perpendicular.
    # Pico de Y do tornozelo no frame 1 (300 > 250 vizinhos).
    frames = [
        _frame(
            0,
            quadril_esq=(100.0, 100.0),
            joelho_esq=(100.0, 300.0),
            tornozelo_esq=(300.0, 250.0),
        ),
        _frame(
            1,
            quadril_esq=(100.0, 100.0),
            joelho_esq=(100.0, 300.0),
            tornozelo_esq=(300.0, 300.0),
        ),
        _frame(
            2,
            quadril_esq=(100.0, 100.0),
            joelho_esq=(100.0, 300.0),
            tornozelo_esq=(300.0, 250.0),
        ),
    ]

    resultado = calcular_angulo_joelho_contato_inicial(frames)

    assert resultado.esquerdo is not None
    assert math.isclose(resultado.esquerdo.angulo_medio_graus, 90.0, abs_tol=1e-9)


def test_flexao_120_graus_conhecida() -> None:
    # Rotação de joelho→quadril = (0,-1) por 120° dá (sin 120°, -cos 120°)
    # = (0.866, 0.5). Multiplicado por 200 e somado ao joelho (100,300):
    # tornozelo ≈ (273.205, 400). O ângulo entre joelho→quadril e
    # joelho→tornozelo é, por construção, 120°.
    dx = 200.0 * math.sin(math.radians(120.0))
    dy = -200.0 * math.cos(math.radians(120.0))
    tornozelo_x = 100.0 + dx  # joelho.x + dx
    tornozelo_y = 300.0 + dy  # joelho.y + dy
    frames = [
        _frame(
            0,
            quadril_dir=(100.0, 100.0),
            joelho_dir=(100.0, 300.0),
            tornozelo_dir=(tornozelo_x, tornozelo_y - 1.0),
        ),
        _frame(
            1,
            quadril_dir=(100.0, 100.0),
            joelho_dir=(100.0, 300.0),
            tornozelo_dir=(tornozelo_x, tornozelo_y),
        ),
        _frame(
            2,
            quadril_dir=(100.0, 100.0),
            joelho_dir=(100.0, 300.0),
            tornozelo_dir=(tornozelo_x, tornozelo_y - 1.0),
        ),
    ]

    resultado = calcular_angulo_joelho_contato_inicial(frames)

    assert resultado.direito is not None
    assert math.isclose(
        resultado.direito.angulo_medio_graus, 120.0, rel_tol=1e-9, abs_tol=1e-9
    )


def test_media_sobre_multiplos_ciclos() -> None:
    # Duas picos para o lado esquerdo: no frame 1 (ângulo = 180°) e frame 5
    # (ângulo = 90°). Média esperada = 135°.
    frames = [
        # Ciclo 1: tornozelo sobe para Y=500 (perna estendida) e desce.
        _frame(
            0,
            quadril_esq=(100.0, 100.0),
            joelho_esq=(100.0, 300.0),
            tornozelo_esq=(100.0, 400.0),
        ),
        _frame(
            1,
            quadril_esq=(100.0, 100.0),
            joelho_esq=(100.0, 300.0),
            tornozelo_esq=(100.0, 500.0),
        ),
        _frame(
            2,
            quadril_esq=(100.0, 100.0),
            joelho_esq=(100.0, 300.0),
            tornozelo_esq=(100.0, 350.0),
        ),
        _frame(
            3,
            quadril_esq=(100.0, 100.0),
            joelho_esq=(100.0, 300.0),
            tornozelo_esq=(200.0, 200.0),
        ),
        # Ciclo 2: tornozelo em (300,300) → flexão 90°; vizinhos em Y menor.
        _frame(
            4,
            quadril_esq=(100.0, 100.0),
            joelho_esq=(100.0, 300.0),
            tornozelo_esq=(300.0, 250.0),
        ),
        _frame(
            5,
            quadril_esq=(100.0, 100.0),
            joelho_esq=(100.0, 300.0),
            tornozelo_esq=(300.0, 300.0),
        ),
        _frame(
            6,
            quadril_esq=(100.0, 100.0),
            joelho_esq=(100.0, 300.0),
            tornozelo_esq=(300.0, 250.0),
        ),
    ]

    resultado = calcular_angulo_joelho_contato_inicial(frames)

    assert resultado.esquerdo is not None
    assert resultado.esquerdo.frames_contato == (1, 5)
    assert math.isclose(
        resultado.esquerdo.angulo_medio_graus, 135.0, rel_tol=1e-9, abs_tol=1e-9
    )


def test_frames_sem_keypoints_validos_sao_ignorados() -> None:
    # O pico de Y está no frame 1, mas o quadril está ausente lá → lado deve
    # ser None (o único candidato foi descartado por keypoints insuficientes).
    frames = [
        _frame(
            0,
            quadril_esq=(100.0, 100.0),
            joelho_esq=(100.0, 300.0),
            tornozelo_esq=(100.0, 400.0),
        ),
        _frame(
            1,
            quadril_esq=None,
            joelho_esq=(100.0, 300.0),
            tornozelo_esq=(100.0, 500.0),
        ),
        _frame(
            2,
            quadril_esq=(100.0, 100.0),
            joelho_esq=(100.0, 300.0),
            tornozelo_esq=(100.0, 400.0),
        ),
    ]

    resultado = calcular_angulo_joelho_contato_inicial(frames)

    assert resultado.esquerdo is None


def test_sem_ciclos_detectados_retorna_none() -> None:
    # Tornozelo nunca forma pico (Y monotonamente crescente).
    frames = [
        _frame(
            i,
            quadril_esq=(100.0, 100.0),
            joelho_esq=(100.0, 300.0),
            tornozelo_esq=(100.0, 400.0 + i * 10.0),
        )
        for i in range(5)
    ]

    resultado = calcular_angulo_joelho_contato_inicial(frames)

    assert resultado.esquerdo is None
    assert resultado.direito is None


def test_esq_e_dir_calculados_independentemente() -> None:
    # Frame 1: pico para ambos os lados. Lado esq estendido (180°), lado dir
    # em flexão de 90°.
    frames = [
        _frame(
            0,
            quadril_esq=(100.0, 100.0),
            joelho_esq=(100.0, 300.0),
            tornozelo_esq=(100.0, 400.0),
            quadril_dir=(200.0, 100.0),
            joelho_dir=(200.0, 300.0),
            tornozelo_dir=(400.0, 250.0),
        ),
        _frame(
            1,
            quadril_esq=(100.0, 100.0),
            joelho_esq=(100.0, 300.0),
            tornozelo_esq=(100.0, 500.0),
            quadril_dir=(200.0, 100.0),
            joelho_dir=(200.0, 300.0),
            tornozelo_dir=(400.0, 300.0),
        ),
        _frame(
            2,
            quadril_esq=(100.0, 100.0),
            joelho_esq=(100.0, 300.0),
            tornozelo_esq=(100.0, 400.0),
            quadril_dir=(200.0, 100.0),
            joelho_dir=(200.0, 300.0),
            tornozelo_dir=(400.0, 250.0),
        ),
    ]

    resultado = calcular_angulo_joelho_contato_inicial(frames)

    assert resultado.esquerdo is not None
    assert resultado.direito is not None
    assert math.isclose(resultado.esquerdo.angulo_medio_graus, 180.0, abs_tol=1e-9)
    assert math.isclose(resultado.direito.angulo_medio_graus, 90.0, abs_tol=1e-9)


def test_lista_vazia_retorna_ambos_none() -> None:
    resultado = calcular_angulo_joelho_contato_inicial([])
    assert resultado.esquerdo is None
    assert resultado.direito is None
