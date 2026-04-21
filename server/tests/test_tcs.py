"""Testes do cálculo de TCS (ms) esq/dir — US-013."""

from __future__ import annotations

import math
import re

import pytest

from server.src.biomechanics.tcs import (
    KP_TORNOZELO_DIR,
    KP_TORNOZELO_ESQ,
    MSG_FPS_INVALIDO,
    _detectar_ciclos_contato,
    calcular_tcs,
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
    tornozelo_esq_y: float | None = None,
    tornozelo_dir_y: float | None = None,
) -> FrameKeypoints:
    kps: list[Keypoint] = [None] * NUM_KEYPOINTS
    if tornozelo_esq_y is not None:
        kps[KP_TORNOZELO_ESQ] = (100.0, tornozelo_esq_y, SCORE)
    if tornozelo_dir_y is not None:
        kps[KP_TORNOZELO_DIR] = (100.0, tornozelo_dir_y, SCORE)
    return FrameKeypoints(frame_idx=idx, person_count=1, keypoints=kps)


def test_detecta_ciclo_simples_com_plateau() -> None:
    # Y cresce até 500 no frame 2, permanece (plateau) até o frame 4, depois
    # cai em 5 ⇒ início em 2, fim em 5, frames_de_contato = 3.
    ys: list[float | None] = [400.0, 450.0, 500.0, 500.0, 500.0, 470.0, 430.0, 400.0]
    ciclos = _detectar_ciclos_contato(ys)
    assert ciclos == [(2, 3)]


def test_detecta_ciclo_sem_plateau_pico_estrito() -> None:
    # Pico estrito: Y cresce em 1, cai em 2 — início=1, fim=2, frames=1.
    ys: list[float | None] = [400.0, 500.0, 400.0]
    ciclos = _detectar_ciclos_contato(ys)
    assert ciclos == [(1, 1)]


def test_detecta_multiplos_ciclos_consecutivos() -> None:
    # Dois plateaus separados — dois ciclos independentes de 3 frames cada.
    ys: list[float | None] = [
        300.0, 500.0, 500.0, 500.0, 400.0,
        300.0, 500.0, 500.0, 500.0, 400.0,
    ]
    ciclos = _detectar_ciclos_contato(ys)
    assert ciclos == [(1, 3), (6, 3)]


def test_tcs_ms_conversao_via_fps() -> None:
    # Contato de 3 frames @ 60 fps ⇒ 50 ms; @ 30 fps ⇒ 100 ms.
    frames = [
        _frame(0, tornozelo_esq_y=400.0),
        _frame(1, tornozelo_esq_y=450.0),
        _frame(2, tornozelo_esq_y=500.0),
        _frame(3, tornozelo_esq_y=500.0),
        _frame(4, tornozelo_esq_y=500.0),
        _frame(5, tornozelo_esq_y=470.0),
        _frame(6, tornozelo_esq_y=430.0),
    ]
    r60 = calcular_tcs(frames, fps=60.0)
    r30 = calcular_tcs(frames, fps=30.0)

    assert r60.esquerdo is not None
    assert r30.esquerdo is not None
    assert r60.direito is None
    assert math.isclose(r60.esquerdo.tcs_medio_ms, 50.0, abs_tol=1e-9)
    assert math.isclose(r30.esquerdo.tcs_medio_ms, 100.0, abs_tol=1e-9)
    assert r60.esquerdo.frames_contato == (2,)


def test_tcs_media_sobre_multiplos_ciclos() -> None:
    # Dois ciclos: 3 frames e 5 frames; @60 fps ⇒ 50 ms e 83.333 ms;
    # média ≈ 66.667 ms. Frames de início: 2 e 9.
    frames = [
        _frame(0, tornozelo_esq_y=400.0),  # 0
        _frame(1, tornozelo_esq_y=450.0),  # 1
        _frame(2, tornozelo_esq_y=500.0),  # 2  ← início ciclo 1
        _frame(3, tornozelo_esq_y=500.0),  # 3
        _frame(4, tornozelo_esq_y=500.0),  # 4
        _frame(5, tornozelo_esq_y=470.0),  # 5  ← fim ciclo 1 (frames=3)
        _frame(6, tornozelo_esq_y=430.0),  # 6
        _frame(7, tornozelo_esq_y=400.0),  # 7
        _frame(8, tornozelo_esq_y=450.0),  # 8
        _frame(9, tornozelo_esq_y=500.0),  # 9  ← início ciclo 2
        _frame(10, tornozelo_esq_y=500.0),  # 10
        _frame(11, tornozelo_esq_y=500.0),  # 11
        _frame(12, tornozelo_esq_y=500.0),  # 12
        _frame(13, tornozelo_esq_y=500.0),  # 13
        _frame(14, tornozelo_esq_y=470.0),  # 14 ← fim ciclo 2 (frames=5)
        _frame(15, tornozelo_esq_y=430.0),  # 15
    ]
    resultado = calcular_tcs(frames, fps=60.0)
    assert resultado.esquerdo is not None
    esperado_ms = ((3 / 60.0) * 1000.0 + (5 / 60.0) * 1000.0) / 2.0
    assert math.isclose(
        resultado.esquerdo.tcs_medio_ms, esperado_ms, abs_tol=1e-9
    )
    assert resultado.esquerdo.frames_contato == (2, 9)


def test_esq_e_dir_calculados_independentemente() -> None:
    # Pé esquerdo: plateau em [2..4] ⇒ 3 frames; pé direito: plateau em
    # [3..5] ⇒ 3 frames — mesma duração, frames de início diferentes.
    frames = [
        _frame(0, tornozelo_esq_y=400.0, tornozelo_dir_y=400.0),
        _frame(1, tornozelo_esq_y=450.0, tornozelo_dir_y=420.0),
        _frame(2, tornozelo_esq_y=500.0, tornozelo_dir_y=450.0),
        _frame(3, tornozelo_esq_y=500.0, tornozelo_dir_y=500.0),
        _frame(4, tornozelo_esq_y=500.0, tornozelo_dir_y=500.0),
        _frame(5, tornozelo_esq_y=470.0, tornozelo_dir_y=500.0),
        _frame(6, tornozelo_esq_y=430.0, tornozelo_dir_y=470.0),
        _frame(7, tornozelo_esq_y=400.0, tornozelo_dir_y=430.0),
    ]
    resultado = calcular_tcs(frames, fps=60.0)
    assert resultado.esquerdo is not None
    assert resultado.direito is not None
    assert resultado.esquerdo.frames_contato == (2,)
    assert resultado.direito.frames_contato == (3,)
    assert math.isclose(resultado.esquerdo.tcs_medio_ms, 50.0, abs_tol=1e-9)
    assert math.isclose(resultado.direito.tcs_medio_ms, 50.0, abs_tol=1e-9)


def test_sem_contatos_retorna_none_no_lado() -> None:
    # Y monotonicamente crescente ⇒ nenhum ciclo (nunca há queda estrita).
    frames = [_frame(i, tornozelo_esq_y=400.0 + i * 10.0) for i in range(8)]
    resultado = calcular_tcs(frames, fps=60.0)
    assert resultado.esquerdo is None
    assert resultado.direito is None


def test_lista_vazia_retorna_ambos_none() -> None:
    resultado = calcular_tcs([], fps=60.0)
    assert resultado.esquerdo is None
    assert resultado.direito is None


def test_frames_sem_tornozelo_sao_ignorados() -> None:
    # Y do tornozelo esq indisponível em todos os frames ⇒ lado esq = None.
    frames = [
        _frame(0),
        _frame(1),
        _frame(2),
        _frame(3),
    ]
    resultado = calcular_tcs(frames, fps=60.0)
    assert resultado.esquerdo is None
    assert resultado.direito is None


def test_none_interno_quebra_ciclo_em_andamento() -> None:
    # Um frame sem tornozelo durante o plateau interrompe o ciclo —
    # descartado silenciosamente. O ciclo seguinte ainda é detectado.
    frames = [
        _frame(0, tornozelo_esq_y=400.0),
        _frame(1, tornozelo_esq_y=450.0),
        _frame(2, tornozelo_esq_y=500.0),  # início (não confirmado)
        _frame(3),                          # None quebra ciclo
        _frame(4, tornozelo_esq_y=470.0),
        _frame(5, tornozelo_esq_y=430.0),
        _frame(6, tornozelo_esq_y=400.0),
        _frame(7, tornozelo_esq_y=450.0),
        _frame(8, tornozelo_esq_y=500.0),   # início ciclo válido
        _frame(9, tornozelo_esq_y=500.0),
        _frame(10, tornozelo_esq_y=470.0),  # fim (frames=2)
        _frame(11, tornozelo_esq_y=430.0),
    ]
    resultado = calcular_tcs(frames, fps=60.0)
    assert resultado.esquerdo is not None
    assert resultado.esquerdo.frames_contato == (8,)
    esperado_ms = (2 / 60.0) * 1000.0
    assert math.isclose(
        resultado.esquerdo.tcs_medio_ms, esperado_ms, abs_tol=1e-9
    )


def test_fps_invalido_levanta_value_error() -> None:
    frames = [_frame(i, tornozelo_esq_y=400.0 + i * 10.0) for i in range(4)]
    with pytest.raises(ValueError, match=re.escape(MSG_FPS_INVALIDO)):
        calcular_tcs(frames, fps=0.0)
    with pytest.raises(ValueError, match=re.escape(MSG_FPS_INVALIDO)):
        calcular_tcs(frames, fps=-60.0)
