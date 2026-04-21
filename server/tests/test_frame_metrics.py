"""Testes dos helpers per-frame usados pelo endpoint ``/raw`` (US-018)."""

from __future__ import annotations

import math

import pytest

from server.src.biomechanics.frame_metrics import (
    angulo_cotovelo_frame,
    angulo_joelho_frame,
    inclinacao_tronco_frame,
    y_com_frame,
)
from server.src.video_pipeline import NUM_KEYPOINTS, FrameKeypoints, Keypoint

SCORE = 0.9


def _frame_vazio(idx: int = 0) -> FrameKeypoints:
    kps: list[Keypoint] = [None] * NUM_KEYPOINTS
    return FrameKeypoints(frame_idx=idx, person_count=1, keypoints=kps)


# ----------------------------- ângulo do joelho ------------------------------


def test_angulo_joelho_esq_perna_estendida_180() -> None:
    frame = _frame_vazio()
    frame.keypoints[11] = (100.0, 100.0, SCORE)
    frame.keypoints[13] = (100.0, 200.0, SCORE)
    frame.keypoints[15] = (100.0, 300.0, SCORE)
    angulo = angulo_joelho_frame(frame, "esq")
    assert angulo is not None
    assert math.isclose(angulo, 180.0, rel_tol=1e-6)


def test_angulo_joelho_dir_90_graus() -> None:
    frame = _frame_vazio()
    frame.keypoints[12] = (100.0, 100.0, SCORE)
    frame.keypoints[14] = (100.0, 200.0, SCORE)
    frame.keypoints[16] = (200.0, 200.0, SCORE)
    angulo = angulo_joelho_frame(frame, "dir")
    assert angulo is not None
    assert math.isclose(angulo, 90.0, rel_tol=1e-6)


def test_angulo_joelho_none_quando_keypoint_ausente() -> None:
    frame = _frame_vazio()
    frame.keypoints[11] = (100.0, 100.0, SCORE)
    frame.keypoints[13] = (100.0, 200.0, SCORE)
    # tornozelo esq ausente → None
    assert angulo_joelho_frame(frame, "esq") is None


def test_angulo_joelho_lado_invalido_levanta() -> None:
    with pytest.raises(ValueError):
        angulo_joelho_frame(_frame_vazio(), "centro")


# ----------------------------- ângulo do cotovelo ----------------------------


def test_angulo_cotovelo_dir_90_graus() -> None:
    frame = _frame_vazio()
    frame.keypoints[6] = (100.0, 100.0, SCORE)
    frame.keypoints[8] = (100.0, 200.0, SCORE)
    frame.keypoints[10] = (200.0, 200.0, SCORE)
    angulo = angulo_cotovelo_frame(frame, "dir")
    assert angulo is not None
    assert math.isclose(angulo, 90.0, rel_tol=1e-6)


def test_angulo_cotovelo_esq_180_braco_estendido() -> None:
    frame = _frame_vazio()
    frame.keypoints[5] = (100.0, 100.0, SCORE)
    frame.keypoints[7] = (100.0, 200.0, SCORE)
    frame.keypoints[9] = (100.0, 300.0, SCORE)
    angulo = angulo_cotovelo_frame(frame, "esq")
    assert angulo is not None
    assert math.isclose(angulo, 180.0, rel_tol=1e-6)


def test_angulo_cotovelo_none_quando_ombro_ausente() -> None:
    frame = _frame_vazio()
    frame.keypoints[7] = (100.0, 200.0, SCORE)
    frame.keypoints[9] = (100.0, 300.0, SCORE)
    assert angulo_cotovelo_frame(frame, "esq") is None


def test_angulo_cotovelo_lado_invalido_levanta() -> None:
    with pytest.raises(ValueError):
        angulo_cotovelo_frame(_frame_vazio(), "xxx")


# --------------------------- inclinação do tronco ----------------------------


def test_inclinacao_tronco_ereto_zero() -> None:
    frame = _frame_vazio()
    frame.keypoints[5] = (95.0, 100.0, SCORE)
    frame.keypoints[6] = (105.0, 100.0, SCORE)
    frame.keypoints[11] = (95.0, 200.0, SCORE)
    frame.keypoints[12] = (105.0, 200.0, SCORE)
    inc = inclinacao_tronco_frame(frame)
    assert inc is not None
    assert math.isclose(inc, 0.0, abs_tol=1e-6)


def test_inclinacao_tronco_10_graus_para_frente() -> None:
    # Tronco inclinado 10°: ΔX = tan(10°) * 100, ΔY (imagem) = -100.
    dx = math.tan(math.radians(10.0)) * 100.0
    frame = _frame_vazio()
    frame.keypoints[5] = (100.0 + dx - 5.0, 100.0, SCORE)
    frame.keypoints[6] = (100.0 + dx + 5.0, 100.0, SCORE)
    frame.keypoints[11] = (95.0, 200.0, SCORE)
    frame.keypoints[12] = (105.0, 200.0, SCORE)
    inc = inclinacao_tronco_frame(frame)
    assert inc is not None
    assert math.isclose(inc, 10.0, rel_tol=1e-6)


def test_inclinacao_tronco_sem_apoio_medio_ainda_retorna_valor() -> None:
    """Per-frame não filtra por fase de apoio — vale qualquer frame com dados."""
    frame = _frame_vazio()
    frame.keypoints[5] = (95.0, 100.0, SCORE)
    frame.keypoints[6] = (105.0, 100.0, SCORE)
    frame.keypoints[11] = (95.0, 200.0, SCORE)
    frame.keypoints[12] = (105.0, 200.0, SCORE)
    # Sem joelhos/tornozelos: agregada retornaria None; per-frame retorna 0.0.
    assert inclinacao_tronco_frame(frame) == 0.0


def test_inclinacao_tronco_none_quando_quadril_ausente() -> None:
    frame = _frame_vazio()
    frame.keypoints[5] = (95.0, 100.0, SCORE)
    frame.keypoints[6] = (105.0, 100.0, SCORE)
    # quadris ausentes
    assert inclinacao_tronco_frame(frame) is None


def test_inclinacao_tronco_none_quando_tronco_invertido() -> None:
    # Ombro abaixo dos quadris → -ΔY ≤ 0 → None.
    frame = _frame_vazio()
    frame.keypoints[5] = (95.0, 300.0, SCORE)
    frame.keypoints[6] = (105.0, 300.0, SCORE)
    frame.keypoints[11] = (95.0, 200.0, SCORE)
    frame.keypoints[12] = (105.0, 200.0, SCORE)
    assert inclinacao_tronco_frame(frame) is None


# ------------------------------------- y_com ---------------------------------


def test_y_com_media_dos_quadris() -> None:
    frame = _frame_vazio()
    frame.keypoints[11] = (95.0, 200.0, SCORE)
    frame.keypoints[12] = (105.0, 240.0, SCORE)
    assert y_com_frame(frame) == 220.0


def test_y_com_none_quando_quadril_ausente() -> None:
    frame = _frame_vazio()
    frame.keypoints[11] = (95.0, 200.0, SCORE)
    assert y_com_frame(frame) is None
