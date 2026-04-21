"""Testes do utilitário de fator de escala pixels→cm (US-007)."""

from __future__ import annotations

import math
import re

import pytest

from server.src.biomechanics.escala import (
    KP_NARIZ,
    KP_TORNOZELO_DIR,
    KP_TORNOZELO_ESQ,
    MSG_ALTURA_AUSENTE,
    MSG_SEM_FRAMES_VALIDOS,
    calcular_fator_escala,
)
from server.src.video_pipeline import NUM_KEYPOINTS, FrameKeypoints, Keypoint


def _frame(
    frame_idx: int,
    nariz: Keypoint,
    tornozelo_esq: Keypoint,
    tornozelo_dir: Keypoint,
    person_count: int = 1,
) -> FrameKeypoints:
    """Constrói um FrameKeypoints com apenas os 3 keypoints relevantes preenchidos."""
    keypoints: list[Keypoint] = [None] * NUM_KEYPOINTS
    keypoints[KP_NARIZ] = nariz
    keypoints[KP_TORNOZELO_ESQ] = tornozelo_esq
    keypoints[KP_TORNOZELO_DIR] = tornozelo_dir
    return FrameKeypoints(
        frame_idx=frame_idx,
        person_count=person_count,
        keypoints=keypoints,
    )


def test_calcula_fator_com_altura_conhecida() -> None:
    # Nariz em (100, 100), tornozelos simétricos em (90, 600) e (110, 600)
    # → ponto médio dos tornozelos: (100, 600); altura em pixels = 500.
    # Altura real 175 cm → fator esperado = 175/500 = 0.35 cm/px.
    frames = [
        _frame(0, (100.0, 100.0, 0.9), (90.0, 600.0, 0.9), (110.0, 600.0, 0.9))
    ]
    resultado = calcular_fator_escala(frames, altura_real_cm=175.0)

    assert resultado.frames_usados == 1
    assert math.isclose(resultado.altura_pixels_media, 500.0, rel_tol=1e-9)
    assert math.isclose(resultado.fator_escala, 0.35, rel_tol=1e-9)


def test_media_estabiliza_sobre_multiplos_frames() -> None:
    # Dois frames: alturas em pixels 500 e 400 → média 450; fator 180/450 = 0.4.
    frames = [
        _frame(0, (100.0, 100.0, 0.9), (90.0, 600.0, 0.9), (110.0, 600.0, 0.9)),
        _frame(1, (100.0, 100.0, 0.9), (90.0, 500.0, 0.9), (110.0, 500.0, 0.9)),
    ]
    resultado = calcular_fator_escala(frames, altura_real_cm=180.0)

    assert resultado.frames_usados == 2
    assert math.isclose(resultado.altura_pixels_media, 450.0, rel_tol=1e-9)
    assert math.isclose(resultado.fator_escala, 0.4, rel_tol=1e-9)


def test_ignora_frames_com_keypoints_ausentes() -> None:
    # Apenas o segundo frame tem os três keypoints válidos.
    frames = [
        _frame(0, None, (90.0, 600.0, 0.9), (110.0, 600.0, 0.9)),
        _frame(1, (100.0, 100.0, 0.9), (90.0, 600.0, 0.9), (110.0, 600.0, 0.9)),
        _frame(2, (100.0, 100.0, 0.9), None, (110.0, 600.0, 0.9)),
        _frame(3, (100.0, 100.0, 0.9), (90.0, 600.0, 0.9), None),
    ]
    resultado = calcular_fator_escala(frames, altura_real_cm=175.0)

    assert resultado.frames_usados == 1
    assert math.isclose(resultado.fator_escala, 0.35, rel_tol=1e-9)


def test_altura_none_levanta_erro_descritivo() -> None:
    frames = [
        _frame(0, (100.0, 100.0, 0.9), (90.0, 600.0, 0.9), (110.0, 600.0, 0.9))
    ]
    with pytest.raises(ValueError, match=re.escape(MSG_ALTURA_AUSENTE)):
        calcular_fator_escala(frames, altura_real_cm=None)


def test_altura_nao_positiva_levanta_erro() -> None:
    frames = [
        _frame(0, (100.0, 100.0, 0.9), (90.0, 600.0, 0.9), (110.0, 600.0, 0.9))
    ]
    with pytest.raises(ValueError, match=re.escape(MSG_ALTURA_AUSENTE)):
        calcular_fator_escala(frames, altura_real_cm=0.0)
    with pytest.raises(ValueError, match=re.escape(MSG_ALTURA_AUSENTE)):
        calcular_fator_escala(frames, altura_real_cm=-10.0)


def test_nenhum_frame_valido_levanta_erro() -> None:
    # Nenhum frame contém nariz + ambos tornozelos válidos.
    frames = [
        _frame(0, None, (90.0, 600.0, 0.9), (110.0, 600.0, 0.9)),
        _frame(1, (100.0, 100.0, 0.9), None, (110.0, 600.0, 0.9)),
    ]
    with pytest.raises(ValueError, match=re.escape(MSG_SEM_FRAMES_VALIDOS)):
        calcular_fator_escala(frames, altura_real_cm=175.0)


def test_lista_vazia_levanta_erro() -> None:
    with pytest.raises(ValueError, match=re.escape(MSG_SEM_FRAMES_VALIDOS)):
        calcular_fator_escala([], altura_real_cm=175.0)


def test_distancia_diagonal_correta() -> None:
    # Nariz em (200, 100); tornozelos em (90, 400) e (110, 400) → médio (100, 400).
    # Distância = sqrt(100² + 300²) = sqrt(100000) ≈ 316.2278.
    # Altura real 158.1139 cm → fator ≈ 0.5 cm/px (escolhido para igualdade limpa).
    frames = [
        _frame(0, (200.0, 100.0, 0.9), (90.0, 400.0, 0.9), (110.0, 400.0, 0.9))
    ]
    resultado = calcular_fator_escala(frames, altura_real_cm=158.11388300841898)

    assert math.isclose(resultado.altura_pixels_media, math.sqrt(100000.0), rel_tol=1e-9)
    assert math.isclose(resultado.fator_escala, 0.5, rel_tol=1e-9)
