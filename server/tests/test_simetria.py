"""Testes do índice de simetria esq/dir (US-015)."""

from __future__ import annotations

import math

from server.src.biomechanics.simetria import (
    SimetriaResultado,
    calcular_simetria,
    indice_simetria,
)
from server.src.video_pipeline import (
    KEYPOINT_SCORE_THRESHOLD,
    NUM_KEYPOINTS,
    FrameKeypoints,
    Keypoint,
)

KP_NARIZ = 0
KP_QUADRIL_ESQ = 11
KP_QUADRIL_DIR = 12
KP_JOELHO_ESQ = 13
KP_JOELHO_DIR = 14
KP_TORNOZELO_ESQ = 15
KP_TORNOZELO_DIR = 16

SCORE = max(0.9, KEYPOINT_SCORE_THRESHOLD + 0.1)


# ----------------------------- indice_simetria ------------------------------


def test_indice_simetria_lados_iguais_retorna_zero() -> None:
    assert indice_simetria(100.0, 100.0) == 0.0


def test_indice_simetria_formula_padrao() -> None:
    # esq=200, dir=180 ⇒ |20| / 190 × 100 ≈ 10.526...%
    resultado = indice_simetria(200.0, 180.0)
    assert resultado is not None
    assert math.isclose(resultado, abs(20.0) / 190.0 * 100.0, rel_tol=1e-9)


def test_indice_simetria_sinal_nao_importa_ordem() -> None:
    # Troca esq/dir: valor absoluto mantém o resultado.
    r1 = indice_simetria(120.0, 80.0)
    r2 = indice_simetria(80.0, 120.0)
    assert r1 is not None and r2 is not None
    assert math.isclose(r1, r2, rel_tol=1e-12)
    assert math.isclose(r1, 40.0 / 100.0 * 100.0, rel_tol=1e-9)


def test_indice_simetria_lado_ausente_retorna_none() -> None:
    # "Erro controlado": valor ausente em um dos lados ⇒ None.
    assert indice_simetria(None, 120.0) is None
    assert indice_simetria(120.0, None) is None
    assert indice_simetria(None, None) is None


def test_indice_simetria_ambos_zero_retorna_zero() -> None:
    # Caso degenerado (soma=0) ⇒ simetria perfeita, sem divisão por zero.
    assert indice_simetria(0.0, 0.0) == 0.0


# ------------------------ helpers para calcular_simetria --------------------


def _kp(x: float, y: float) -> Keypoint:
    return (x, y, SCORE)


def _frame(
    idx: int,
    *,
    nariz: tuple[float, float] | None = None,
    quadril_esq: tuple[float, float] | None = None,
    quadril_dir: tuple[float, float] | None = None,
    joelho_esq: tuple[float, float] | None = None,
    joelho_dir: tuple[float, float] | None = None,
    tornozelo_esq: tuple[float, float] | None = None,
    tornozelo_dir: tuple[float, float] | None = None,
) -> FrameKeypoints:
    kps: list[Keypoint] = [None] * NUM_KEYPOINTS
    if nariz is not None:
        kps[KP_NARIZ] = _kp(*nariz)
    if quadril_esq is not None:
        kps[KP_QUADRIL_ESQ] = _kp(*quadril_esq)
    if quadril_dir is not None:
        kps[KP_QUADRIL_DIR] = _kp(*quadril_dir)
    if joelho_esq is not None:
        kps[KP_JOELHO_ESQ] = _kp(*joelho_esq)
    if joelho_dir is not None:
        kps[KP_JOELHO_DIR] = _kp(*joelho_dir)
    if tornozelo_esq is not None:
        kps[KP_TORNOZELO_ESQ] = _kp(*tornozelo_esq)
    if tornozelo_dir is not None:
        kps[KP_TORNOZELO_DIR] = _kp(*tornozelo_dir)
    return FrameKeypoints(frame_idx=idx, person_count=1, keypoints=kps)


# ---------------------------- calcular_simetria -----------------------------


def test_calcular_simetria_lados_iguais_retorna_zero_em_tudo() -> None:
    # Série curta e simétrica: picos de Y do tornozelo esq e dir no frame 1,
    # ambos com a mesma configuração de joelho (ângulo interno 180°).
    # Sem ciclos suficientes para TCS/oscilação — mas joelho simétrico ⇒ 0%.
    frames = [
        _frame(
            0,
            quadril_esq=(100.0, 100.0),
            joelho_esq=(100.0, 300.0),
            tornozelo_esq=(100.0, 450.0),
            quadril_dir=(200.0, 100.0),
            joelho_dir=(200.0, 300.0),
            tornozelo_dir=(200.0, 450.0),
        ),
        _frame(
            1,
            quadril_esq=(100.0, 100.0),
            joelho_esq=(100.0, 300.0),
            tornozelo_esq=(100.0, 500.0),  # pico esq
            quadril_dir=(200.0, 100.0),
            joelho_dir=(200.0, 300.0),
            tornozelo_dir=(200.0, 500.0),  # pico dir
        ),
        _frame(
            2,
            quadril_esq=(100.0, 100.0),
            joelho_esq=(100.0, 300.0),
            tornozelo_esq=(100.0, 450.0),
            quadril_dir=(200.0, 100.0),
            joelho_dir=(200.0, 300.0),
            tornozelo_dir=(200.0, 450.0),
        ),
    ]
    resultado = calcular_simetria(frames, fps=60.0, fator_escala=0.5)
    assert isinstance(resultado, SimetriaResultado)
    # Joelho e TCS: série curta mas idêntica entre lados ⇒ 0% de assimetria.
    assert resultado.simetria_joelho == 0.0
    assert resultado.simetria_tcs == 0.0
    # Apenas um pico por lado ⇒ < 2 contatos para delimitar ciclos de
    # oscilação vertical ⇒ simetria_oscilacao indefinida (None).
    assert resultado.simetria_oscilacao is None


def test_calcular_simetria_joelho_valor_assimetrico() -> None:
    # Esq: joelho colinear ⇒ 180°. Dir: joelho em 90° (joelho→quadril e
    # joelho→tornozelo perpendiculares). IS = |180-90|/135 × 100 ≈ 66.66%.
    frames = [
        _frame(
            0,
            quadril_esq=(100.0, 100.0),
            joelho_esq=(100.0, 300.0),
            tornozelo_esq=(100.0, 450.0),
            quadril_dir=(200.0, 100.0),
            joelho_dir=(200.0, 300.0),
            tornozelo_dir=(400.0, 250.0),
        ),
        _frame(
            1,
            quadril_esq=(100.0, 100.0),
            joelho_esq=(100.0, 300.0),
            tornozelo_esq=(100.0, 500.0),  # pico esq
            quadril_dir=(200.0, 100.0),
            joelho_dir=(200.0, 300.0),
            tornozelo_dir=(400.0, 300.0),  # pico dir (perpendicular)
        ),
        _frame(
            2,
            quadril_esq=(100.0, 100.0),
            joelho_esq=(100.0, 300.0),
            tornozelo_esq=(100.0, 450.0),
            quadril_dir=(200.0, 100.0),
            joelho_dir=(200.0, 300.0),
            tornozelo_dir=(400.0, 250.0),
        ),
    ]
    resultado = calcular_simetria(frames, fps=60.0, fator_escala=0.5)
    assert resultado.simetria_joelho is not None
    esperado = abs(180.0 - 90.0) / ((180.0 + 90.0) / 2.0) * 100.0
    assert math.isclose(resultado.simetria_joelho, esperado, rel_tol=1e-9)


def test_calcular_simetria_joelho_lado_ausente_retorna_none() -> None:
    # Apenas o lado esquerdo tem pico de contato; o direito não tem picos
    # com keypoints válidos ⇒ simetria_joelho = None.
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
    resultado = calcular_simetria(frames, fps=60.0, fator_escala=0.5)
    assert resultado.simetria_joelho is None


def test_calcular_simetria_tcs_dois_lados() -> None:
    # Plateau de 3 frames em cada pé, mesmos frames ⇒ TCS idêntico ⇒ 0%.
    frames = [
        _frame(0, tornozelo_esq=(100.0, 400.0), tornozelo_dir=(200.0, 400.0)),
        _frame(1, tornozelo_esq=(100.0, 450.0), tornozelo_dir=(200.0, 450.0)),
        _frame(2, tornozelo_esq=(100.0, 500.0), tornozelo_dir=(200.0, 500.0)),
        _frame(3, tornozelo_esq=(100.0, 500.0), tornozelo_dir=(200.0, 500.0)),
        _frame(4, tornozelo_esq=(100.0, 500.0), tornozelo_dir=(200.0, 500.0)),
        _frame(5, tornozelo_esq=(100.0, 470.0), tornozelo_dir=(200.0, 470.0)),
        _frame(6, tornozelo_esq=(100.0, 430.0), tornozelo_dir=(200.0, 430.0)),
    ]
    resultado = calcular_simetria(frames, fps=60.0, fator_escala=0.5)
    assert resultado.simetria_tcs == 0.0


def test_calcular_simetria_tcs_fps_invalido_retorna_none() -> None:
    # FPS inválido não interrompe o pipeline — apenas a simetria de TCS
    # degrada para None. Joelho segue (não depende de fps).
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
    resultado = calcular_simetria(frames, fps=0.0, fator_escala=0.5)
    assert resultado.simetria_tcs is None


def test_calcular_simetria_oscilacao_dois_lados() -> None:
    # Mesma série Y_CoM, contatos em ambos os pés no mesmo ritmo ⇒ oscilação
    # por lado idêntica ⇒ simetria_oscilacao = 0%.
    # Picos esq+dir nos frames 1 e 5. ΔY_CoM por ciclo = 20 px.
    frames = [
        _frame(
            0,
            quadril_esq=(100.0, 200.0),
            quadril_dir=(100.0, 200.0),
            tornozelo_esq=(90.0, 450.0),
            tornozelo_dir=(110.0, 450.0),
        ),
        _frame(
            1,
            quadril_esq=(100.0, 200.0),
            quadril_dir=(100.0, 200.0),
            tornozelo_esq=(90.0, 500.0),
            tornozelo_dir=(110.0, 500.0),
        ),
        _frame(
            2,
            quadril_esq=(100.0, 210.0),
            quadril_dir=(100.0, 210.0),
            tornozelo_esq=(90.0, 400.0),
            tornozelo_dir=(110.0, 400.0),
        ),
        _frame(
            3,
            quadril_esq=(100.0, 220.0),
            quadril_dir=(100.0, 220.0),
            tornozelo_esq=(90.0, 350.0),
            tornozelo_dir=(110.0, 350.0),
        ),
        _frame(
            4,
            quadril_esq=(100.0, 210.0),
            quadril_dir=(100.0, 210.0),
            tornozelo_esq=(90.0, 400.0),
            tornozelo_dir=(110.0, 400.0),
        ),
        _frame(
            5,
            quadril_esq=(100.0, 200.0),
            quadril_dir=(100.0, 200.0),
            tornozelo_esq=(90.0, 500.0),
            tornozelo_dir=(110.0, 500.0),
        ),
        _frame(
            6,
            quadril_esq=(100.0, 200.0),
            quadril_dir=(100.0, 200.0),
            tornozelo_esq=(90.0, 450.0),
            tornozelo_dir=(110.0, 450.0),
        ),
    ]
    resultado = calcular_simetria(frames, fps=60.0, fator_escala=0.5)
    assert resultado.simetria_oscilacao == 0.0


def test_calcular_simetria_oscilacao_fator_none_retorna_none() -> None:
    # Sem fator de escala (altura do usuário ausente em produção) ⇒ simetria
    # de oscilação não pode ser calculada em cm ⇒ None.
    frames = [
        _frame(
            0,
            quadril_esq=(100.0, 200.0),
            quadril_dir=(100.0, 200.0),
            tornozelo_dir=(110.0, 450.0),
        ),
        _frame(
            1,
            quadril_esq=(100.0, 200.0),
            quadril_dir=(100.0, 200.0),
            tornozelo_dir=(110.0, 500.0),
        ),
        _frame(
            2,
            quadril_esq=(100.0, 220.0),
            quadril_dir=(100.0, 220.0),
            tornozelo_dir=(110.0, 400.0),
        ),
    ]
    resultado = calcular_simetria(frames, fps=60.0, fator_escala=None)
    assert resultado.simetria_oscilacao is None


def test_calcular_simetria_lista_vazia_retorna_todos_none() -> None:
    resultado = calcular_simetria([], fps=60.0, fator_escala=0.5)
    assert resultado.simetria_tcs is None
    assert resultado.simetria_joelho is None
    assert resultado.simetria_oscilacao is None
