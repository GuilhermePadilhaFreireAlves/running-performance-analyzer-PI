"""Testes do cálculo de overstriding (cm) esq/dir no contato inicial (US-012)."""

from __future__ import annotations

import math

from server.src.biomechanics.overstriding import (
    KP_QUADRIL_DIR,
    KP_QUADRIL_ESQ,
    KP_TORNOZELO_DIR,
    KP_TORNOZELO_ESQ,
    calcular_overstriding,
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
    quadril_esq: tuple[float, float] | None = None,
    quadril_dir: tuple[float, float] | None = None,
    tornozelo_esq: tuple[float, float] | None = None,
    tornozelo_dir: tuple[float, float] | None = None,
) -> FrameKeypoints:
    kps: list[Keypoint] = [None] * NUM_KEYPOINTS
    if quadril_esq is not None:
        kps[KP_QUADRIL_ESQ] = (quadril_esq[0], quadril_esq[1], SCORE)
    if quadril_dir is not None:
        kps[KP_QUADRIL_DIR] = (quadril_dir[0], quadril_dir[1], SCORE)
    if tornozelo_esq is not None:
        kps[KP_TORNOZELO_ESQ] = (tornozelo_esq[0], tornozelo_esq[1], SCORE)
    if tornozelo_dir is not None:
        kps[KP_TORNOZELO_DIR] = (tornozelo_dir[0], tornozelo_dir[1], SCORE)
    return FrameKeypoints(frame_idx=idx, person_count=1, keypoints=kps)


def test_overstriding_positivo_com_fator_conhecido() -> None:
    # quadril_esq_X=90, quadril_dir_X=110 → CoM_X = 100.
    # tornozelo_esq_X = 150 → overstriding_px = 50; fator_escala = 0.5 cm/px
    # → overstriding_cm = 25.0. Pico de Y do tornozelo esq no frame 1
    # (Y=500 > vizinhos Y=450).
    frames = [
        _frame(
            0,
            quadril_esq=(90.0, 200.0),
            quadril_dir=(110.0, 200.0),
            tornozelo_esq=(150.0, 450.0),
        ),
        _frame(
            1,
            quadril_esq=(90.0, 200.0),
            quadril_dir=(110.0, 200.0),
            tornozelo_esq=(150.0, 500.0),
        ),
        _frame(
            2,
            quadril_esq=(90.0, 200.0),
            quadril_dir=(110.0, 200.0),
            tornozelo_esq=(150.0, 450.0),
        ),
    ]
    resultado = calcular_overstriding(frames, fator_escala=0.5)

    assert resultado.esquerdo is not None
    assert resultado.direito is None
    assert math.isclose(
        resultado.esquerdo.overstriding_medio_cm, 25.0, rel_tol=1e-9
    )
    assert resultado.esquerdo.frames_contato == (1,)


def test_overstriding_negativo_preserva_sinal() -> None:
    # CoM_X = 100; tornozelo_dir_X = 50 → overstriding_px = -50; fator 0.5
    # → -25 cm (pé atrás do CoM).
    frames = [
        _frame(
            0,
            quadril_esq=(90.0, 200.0),
            quadril_dir=(110.0, 200.0),
            tornozelo_dir=(50.0, 450.0),
        ),
        _frame(
            1,
            quadril_esq=(90.0, 200.0),
            quadril_dir=(110.0, 200.0),
            tornozelo_dir=(50.0, 500.0),
        ),
        _frame(
            2,
            quadril_esq=(90.0, 200.0),
            quadril_dir=(110.0, 200.0),
            tornozelo_dir=(50.0, 450.0),
        ),
    ]
    resultado = calcular_overstriding(frames, fator_escala=0.5)

    assert resultado.direito is not None
    assert math.isclose(
        resultado.direito.overstriding_medio_cm, -25.0, rel_tol=1e-9
    )


def test_media_sobre_multiplos_ciclos() -> None:
    # Dois picos no lado esquerdo (frames 1 e 4):
    #   pico 1: tornozelo_esq_X = 150 → overstriding_px = 50
    #   pico 2: tornozelo_esq_X = 200 → overstriding_px = 100
    # fator = 0.4 → overstridings_cm = [20, 40]; média = 30 cm.
    frames = [
        _frame(
            0,
            quadril_esq=(90.0, 200.0),
            quadril_dir=(110.0, 200.0),
            tornozelo_esq=(150.0, 450.0),
        ),
        _frame(
            1,
            quadril_esq=(90.0, 200.0),
            quadril_dir=(110.0, 200.0),
            tornozelo_esq=(150.0, 500.0),
        ),
        _frame(
            2,
            quadril_esq=(90.0, 200.0),
            quadril_dir=(110.0, 200.0),
            tornozelo_esq=(160.0, 350.0),
        ),
        _frame(
            3,
            quadril_esq=(90.0, 200.0),
            quadril_dir=(110.0, 200.0),
            tornozelo_esq=(170.0, 400.0),
        ),
        _frame(
            4,
            quadril_esq=(90.0, 200.0),
            quadril_dir=(110.0, 200.0),
            tornozelo_esq=(200.0, 550.0),
        ),
        _frame(
            5,
            quadril_esq=(90.0, 200.0),
            quadril_dir=(110.0, 200.0),
            tornozelo_esq=(180.0, 400.0),
        ),
    ]
    resultado = calcular_overstriding(frames, fator_escala=0.4)

    assert resultado.esquerdo is not None
    assert resultado.esquerdo.frames_contato == (1, 4)
    assert math.isclose(
        resultado.esquerdo.overstriding_medio_cm, 30.0, rel_tol=1e-9
    )


def test_esq_e_dir_calculados_independentemente() -> None:
    # Pico no frame 1 para ambos. CoM_X=100; esq tornozelo_X=150 → +50;
    # dir tornozelo_X=50 → -50. fator=1.0 → resultados em "cm"=px.
    frames = [
        _frame(
            0,
            quadril_esq=(90.0, 200.0),
            quadril_dir=(110.0, 200.0),
            tornozelo_esq=(150.0, 450.0),
            tornozelo_dir=(50.0, 450.0),
        ),
        _frame(
            1,
            quadril_esq=(90.0, 200.0),
            quadril_dir=(110.0, 200.0),
            tornozelo_esq=(150.0, 500.0),
            tornozelo_dir=(50.0, 500.0),
        ),
        _frame(
            2,
            quadril_esq=(90.0, 200.0),
            quadril_dir=(110.0, 200.0),
            tornozelo_esq=(150.0, 450.0),
            tornozelo_dir=(50.0, 450.0),
        ),
    ]
    resultado = calcular_overstriding(frames, fator_escala=1.0)

    assert resultado.esquerdo is not None
    assert resultado.direito is not None
    assert math.isclose(
        resultado.esquerdo.overstriding_medio_cm, 50.0, rel_tol=1e-9
    )
    assert math.isclose(
        resultado.direito.overstriding_medio_cm, -50.0, rel_tol=1e-9
    )


def test_frames_sem_keypoints_validos_sao_ignorados() -> None:
    # Pico do frame 1 perde o quadril_dir ⇒ o único candidato é descartado,
    # e o lado esquerdo vem None.
    frames = [
        _frame(
            0,
            quadril_esq=(90.0, 200.0),
            quadril_dir=(110.0, 200.0),
            tornozelo_esq=(150.0, 450.0),
        ),
        _frame(
            1,
            quadril_esq=(90.0, 200.0),
            quadril_dir=None,
            tornozelo_esq=(150.0, 500.0),
        ),
        _frame(
            2,
            quadril_esq=(90.0, 200.0),
            quadril_dir=(110.0, 200.0),
            tornozelo_esq=(150.0, 450.0),
        ),
    ]
    resultado = calcular_overstriding(frames, fator_escala=0.5)

    assert resultado.esquerdo is None
    assert resultado.direito is None


def test_sem_picos_retorna_ambos_none() -> None:
    # Tornozelo com Y monotonicamente crescente ⇒ nenhum pico estrito.
    frames = [
        _frame(
            i,
            quadril_esq=(90.0, 200.0),
            quadril_dir=(110.0, 200.0),
            tornozelo_esq=(150.0, 300.0 + i * 10.0),
            tornozelo_dir=(50.0, 300.0 + i * 10.0),
        )
        for i in range(5)
    ]
    resultado = calcular_overstriding(frames, fator_escala=0.5)

    assert resultado.esquerdo is None
    assert resultado.direito is None


def test_lista_vazia_retorna_ambos_none() -> None:
    resultado = calcular_overstriding([], fator_escala=0.5)
    assert resultado.esquerdo is None
    assert resultado.direito is None


def test_fator_escala_de_altura_real_conhecida() -> None:
    # Replica a escala do teste US-007: altura 175 cm / altura_pixels 500 px
    # = 0.35 cm/px. Tornozelo 40 px à frente do CoM ⇒ overstriding = 14 cm.
    frames = [
        _frame(
            0,
            quadril_esq=(90.0, 200.0),
            quadril_dir=(110.0, 200.0),
            tornozelo_esq=(140.0, 450.0),
        ),
        _frame(
            1,
            quadril_esq=(90.0, 200.0),
            quadril_dir=(110.0, 200.0),
            tornozelo_esq=(140.0, 500.0),
        ),
        _frame(
            2,
            quadril_esq=(90.0, 200.0),
            quadril_dir=(110.0, 200.0),
            tornozelo_esq=(140.0, 450.0),
        ),
    ]
    resultado = calcular_overstriding(frames, fator_escala=0.35)

    assert resultado.esquerdo is not None
    assert math.isclose(
        resultado.esquerdo.overstriding_medio_cm, 14.0, rel_tol=1e-9
    )
