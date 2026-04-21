"""Testes do cálculo de cadência (US-010)."""

from __future__ import annotations

import math
import re

import pytest

from server.src.biomechanics.cadencia import (
    KP_TORNOZELO_DIR,
    MSG_FPS_INVALIDO,
    calcular_cadencia,
)
from server.src.video_pipeline import (
    KEYPOINT_SCORE_THRESHOLD,
    NUM_KEYPOINTS,
    FrameKeypoints,
    Keypoint,
)

SCORE = max(0.9, KEYPOINT_SCORE_THRESHOLD + 0.1)


def _frame(idx: int, tornozelo_dir_y: float | None) -> FrameKeypoints:
    kps: list[Keypoint] = [None] * NUM_KEYPOINTS
    if tornozelo_dir_y is not None:
        kps[KP_TORNOZELO_DIR] = (100.0, tornozelo_dir_y, SCORE)
    return FrameKeypoints(frame_idx=idx, person_count=1, keypoints=kps)


def _serie_com_picos(n_picos: int, total_frames: int) -> list[FrameKeypoints]:
    """Constrói uma série onde o tornozelo direito tem `n_picos` picos estritos.

    Picos ficam em índices ímpares 1, 3, …, 2*n_picos-1 com Y=500; demais
    frames têm Y=400. Requer `total_frames >= 2*n_picos + 1` para garantir
    que o frame após o último pico seja não-pico (≤ vizinho).
    """
    assert total_frames >= 2 * n_picos + 1, "total_frames insuficiente"
    ys: list[float] = []
    for i in range(total_frames):
        is_peak = (i % 2 == 1) and (i <= 2 * n_picos - 1)
        ys.append(500.0 if is_peak else 400.0)
    return [_frame(i, y) for i, y in enumerate(ys)]


def test_cadencia_basica_com_fps_conhecido() -> None:
    # 3 picos em 60 frames @ 60 fps ⇒ 1 s; cadência = (3 × 2 / 1) × 60 = 360.
    frames = _serie_com_picos(n_picos=3, total_frames=60)
    resultado = calcular_cadencia(frames, fps=60.0)
    assert resultado is not None
    assert resultado.contatos_pe_direito == 3
    assert math.isclose(resultado.duracao_segundos, 1.0, abs_tol=1e-9)
    assert math.isclose(resultado.cadencia_spm, 360.0, abs_tol=1e-9)


def test_cadencia_converte_frames_em_segundos_via_fps() -> None:
    # 2 picos em 120 frames:
    #   @ 60 fps ⇒ 2 s ⇒ cadência = (2 × 2 / 2) × 60 = 120 spm
    #   @ 30 fps ⇒ 4 s ⇒ cadência = (2 × 2 / 4) × 60 = 60 spm
    frames = _serie_com_picos(n_picos=2, total_frames=120)
    r60 = calcular_cadencia(frames, fps=60.0)
    r30 = calcular_cadencia(frames, fps=30.0)
    assert r60 is not None
    assert r30 is not None
    assert math.isclose(r60.cadencia_spm, 120.0, abs_tol=1e-9)
    assert math.isclose(r30.cadencia_spm, 60.0, abs_tol=1e-9)
    assert r60.contatos_pe_direito == 2
    assert r30.contatos_pe_direito == 2


def test_multiplica_por_2_contagem_de_um_pe_apenas() -> None:
    # 1 pico em 60 frames @ 60 fps ⇒ 1 s; cadência = (1 × 2 / 1) × 60 = 120 spm.
    frames = _serie_com_picos(n_picos=1, total_frames=60)
    resultado = calcular_cadencia(frames, fps=60.0)
    assert resultado is not None
    assert resultado.contatos_pe_direito == 1
    assert math.isclose(resultado.cadencia_spm, 120.0, abs_tol=1e-9)


def test_ignora_contatos_do_pe_esquerdo() -> None:
    # Só injeta picos no pé esquerdo — o pé direito não aparece.
    # Resultado: nenhum contato detectado ⇒ None.
    from server.src.biomechanics.cadencia import calcular_cadencia as cc

    kp_tornozelo_esq = 15
    frames: list[FrameKeypoints] = []
    ys = [400.0, 500.0, 400.0, 500.0, 400.0]
    for i, y in enumerate(ys):
        kps: list[Keypoint] = [None] * NUM_KEYPOINTS
        kps[kp_tornozelo_esq] = (100.0, y, SCORE)
        frames.append(FrameKeypoints(frame_idx=i, person_count=1, keypoints=kps))
    assert cc(frames, fps=60.0) is None


def test_sem_picos_retorna_none() -> None:
    # Tornozelo direito com Y monotonamente crescente ⇒ nenhum pico estrito.
    frames = [_frame(i, 400.0 + i) for i in range(10)]
    assert calcular_cadencia(frames, fps=60.0) is None


def test_lista_vazia_retorna_none() -> None:
    assert calcular_cadencia([], fps=60.0) is None


def test_fps_invalido_levanta_value_error() -> None:
    frames = _serie_com_picos(n_picos=2, total_frames=30)
    with pytest.raises(ValueError, match=re.escape(MSG_FPS_INVALIDO)):
        calcular_cadencia(frames, fps=0.0)
    with pytest.raises(ValueError, match=re.escape(MSG_FPS_INVALIDO)):
        calcular_cadencia(frames, fps=-30.0)
