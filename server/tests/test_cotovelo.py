"""Testes do cálculo de ângulo médio do cotovelo (US-009)."""

from __future__ import annotations

import math

from server.src.biomechanics.cotovelo import (
    KP_COTOVELO_DIR,
    KP_COTOVELO_ESQ,
    KP_OMBRO_DIR,
    KP_OMBRO_ESQ,
    KP_PULSO_DIR,
    KP_PULSO_ESQ,
    calcular_angulo_cotovelo,
)
from server.src.video_pipeline import (
    KEYPOINT_SCORE_THRESHOLD,
    NUM_KEYPOINTS,
    FrameKeypoints,
    Keypoint,
)

SCORE = max(0.9, KEYPOINT_SCORE_THRESHOLD + 0.1)


def _frame(
    idx: int,
    *,
    ombro_esq: tuple[float, float] | None = None,
    cotovelo_esq: tuple[float, float] | None = None,
    pulso_esq: tuple[float, float] | None = None,
    ombro_dir: tuple[float, float] | None = None,
    cotovelo_dir: tuple[float, float] | None = None,
    pulso_dir: tuple[float, float] | None = None,
) -> FrameKeypoints:
    kps: list[Keypoint] = [None] * NUM_KEYPOINTS
    if ombro_esq is not None:
        kps[KP_OMBRO_ESQ] = (ombro_esq[0], ombro_esq[1], SCORE)
    if cotovelo_esq is not None:
        kps[KP_COTOVELO_ESQ] = (cotovelo_esq[0], cotovelo_esq[1], SCORE)
    if pulso_esq is not None:
        kps[KP_PULSO_ESQ] = (pulso_esq[0], pulso_esq[1], SCORE)
    if ombro_dir is not None:
        kps[KP_OMBRO_DIR] = (ombro_dir[0], ombro_dir[1], SCORE)
    if cotovelo_dir is not None:
        kps[KP_COTOVELO_DIR] = (cotovelo_dir[0], cotovelo_dir[1], SCORE)
    if pulso_dir is not None:
        kps[KP_PULSO_DIR] = (pulso_dir[0], pulso_dir[1], SCORE)
    return FrameKeypoints(frame_idx=idx, person_count=1, keypoints=kps)


def test_flexao_90_graus_conhecida() -> None:
    # Ombro (100,100), cotovelo (100,300), pulso (300,300):
    # cotovelo→ombro = (0,-200); cotovelo→pulso = (200,0) → perpendicular (90°).
    frames = [
        _frame(
            0,
            ombro_esq=(100.0, 100.0),
            cotovelo_esq=(100.0, 300.0),
            pulso_esq=(300.0, 300.0),
        ),
    ]

    resultado = calcular_angulo_cotovelo(frames)

    assert resultado.esquerdo is not None
    assert resultado.direito is None
    assert math.isclose(resultado.esquerdo.angulo_medio_graus, 90.0, abs_tol=1e-9)
    assert resultado.esquerdo.frames_validos == 1


def test_flexao_120_graus_conhecida() -> None:
    # Rotação de cotovelo→ombro = (0,-1) por 120° dá (sin 120°, -cos 120°)
    # = (0.866, 0.5). Escalado por 200 e somado ao cotovelo (100,300):
    # pulso ≈ (273.205, 400). O ângulo entre cotovelo→ombro e cotovelo→pulso
    # é, por construção, 120°.
    dx = 200.0 * math.sin(math.radians(120.0))
    dy = -200.0 * math.cos(math.radians(120.0))
    pulso_x = 100.0 + dx
    pulso_y = 300.0 + dy
    frames = [
        _frame(
            0,
            ombro_dir=(100.0, 100.0),
            cotovelo_dir=(100.0, 300.0),
            pulso_dir=(pulso_x, pulso_y),
        ),
    ]

    resultado = calcular_angulo_cotovelo(frames)

    assert resultado.direito is not None
    assert math.isclose(
        resultado.direito.angulo_medio_graus, 120.0, rel_tol=1e-9, abs_tol=1e-9
    )


def test_braco_estendido_retorna_180_graus() -> None:
    # Ombro (100,100), cotovelo (100,300), pulso (100,500): todos colineares.
    # Vetores antiparalelos → 180°.
    frames = [
        _frame(
            0,
            ombro_esq=(100.0, 100.0),
            cotovelo_esq=(100.0, 300.0),
            pulso_esq=(100.0, 500.0),
        ),
    ]

    resultado = calcular_angulo_cotovelo(frames)

    assert resultado.esquerdo is not None
    assert math.isclose(resultado.esquerdo.angulo_medio_graus, 180.0, abs_tol=1e-9)


def test_media_sobre_multiplos_frames() -> None:
    # Frame 0: 180°. Frame 1: 90°. Média esperada = 135°.
    frames = [
        _frame(
            0,
            ombro_esq=(100.0, 100.0),
            cotovelo_esq=(100.0, 300.0),
            pulso_esq=(100.0, 500.0),
        ),
        _frame(
            1,
            ombro_esq=(100.0, 100.0),
            cotovelo_esq=(100.0, 300.0),
            pulso_esq=(300.0, 300.0),
        ),
    ]

    resultado = calcular_angulo_cotovelo(frames)

    assert resultado.esquerdo is not None
    assert resultado.esquerdo.frames_validos == 2
    assert math.isclose(
        resultado.esquerdo.angulo_medio_graus, 135.0, rel_tol=1e-9, abs_tol=1e-9
    )


def test_frames_sem_keypoints_validos_sao_ignorados() -> None:
    # Frame 0 é válido (90°), frame 1 tem pulso ausente → ignorado,
    # frame 2 é válido (180°). Média esperada = 135° sobre 2 frames.
    frames = [
        _frame(
            0,
            ombro_esq=(100.0, 100.0),
            cotovelo_esq=(100.0, 300.0),
            pulso_esq=(300.0, 300.0),
        ),
        _frame(
            1,
            ombro_esq=(100.0, 100.0),
            cotovelo_esq=(100.0, 300.0),
            pulso_esq=None,
        ),
        _frame(
            2,
            ombro_esq=(100.0, 100.0),
            cotovelo_esq=(100.0, 300.0),
            pulso_esq=(100.0, 500.0),
        ),
    ]

    resultado = calcular_angulo_cotovelo(frames)

    assert resultado.esquerdo is not None
    assert resultado.esquerdo.frames_validos == 2
    assert math.isclose(
        resultado.esquerdo.angulo_medio_graus, 135.0, rel_tol=1e-9, abs_tol=1e-9
    )


def test_nenhum_frame_valido_retorna_none() -> None:
    # Apenas um keypoint por frame → nenhum ângulo calculável.
    frames = [
        _frame(0, ombro_esq=(100.0, 100.0)),
        _frame(1, cotovelo_esq=(100.0, 300.0)),
    ]

    resultado = calcular_angulo_cotovelo(frames)

    assert resultado.esquerdo is None
    assert resultado.direito is None


def test_esq_e_dir_calculados_independentemente() -> None:
    # Frame único com esq a 90° e dir a 180°.
    frames = [
        _frame(
            0,
            ombro_esq=(100.0, 100.0),
            cotovelo_esq=(100.0, 300.0),
            pulso_esq=(300.0, 300.0),
            ombro_dir=(500.0, 100.0),
            cotovelo_dir=(500.0, 300.0),
            pulso_dir=(500.0, 500.0),
        ),
    ]

    resultado = calcular_angulo_cotovelo(frames)

    assert resultado.esquerdo is not None
    assert resultado.direito is not None
    assert math.isclose(resultado.esquerdo.angulo_medio_graus, 90.0, abs_tol=1e-9)
    assert math.isclose(resultado.direito.angulo_medio_graus, 180.0, abs_tol=1e-9)


def test_lista_vazia_retorna_ambos_none() -> None:
    resultado = calcular_angulo_cotovelo([])
    assert resultado.esquerdo is None
    assert resultado.direito is None
