"""Testes do cálculo de oscilação vertical do CoM (US-014)."""

from __future__ import annotations

import math
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from server.src.biomechanics.oscilacao import (
    KP_QUADRIL_DIR,
    KP_QUADRIL_ESQ,
    KP_TORNOZELO_DIR,
    calcular_oscilacao_vertical,
)
from server.src.database import Base
from server.src.models import Metrica, SessaoAnalise, Usuario
from server.src.video_pipeline import (
    KEYPOINT_SCORE_THRESHOLD,
    NUM_KEYPOINTS,
    FrameKeypoints,
    Keypoint,
    PoseExtractionResult,
    run_pipeline,
)

SCORE = max(0.9, KEYPOINT_SCORE_THRESHOLD + 0.1)


def _frame(
    idx: int,
    *,
    quadril_y: float | None = None,
    tornozelo_dir_y: float | None = None,
    nariz: tuple[float, float] | None = None,
    tornozelo_esq: tuple[float, float] | None = None,
    tornozelo_dir_xy: tuple[float, float] | None = None,
) -> FrameKeypoints:
    """Constrói um FrameKeypoints com keypoints opcionais.

    `quadril_y` preenche ambos os quadris (esq e dir) com X=100 e Y=quadril_y
    para simplificar os testes onde só importa o Y do CoM.
    """
    kps: list[Keypoint] = [None] * NUM_KEYPOINTS
    if quadril_y is not None:
        kps[KP_QUADRIL_ESQ] = (100.0, quadril_y, SCORE)
        kps[KP_QUADRIL_DIR] = (100.0, quadril_y, SCORE)
    if tornozelo_dir_y is not None:
        kps[KP_TORNOZELO_DIR] = (100.0, tornozelo_dir_y, SCORE)
    if nariz is not None:
        kps[0] = (nariz[0], nariz[1], SCORE)
    if tornozelo_esq is not None:
        kps[15] = (tornozelo_esq[0], tornozelo_esq[1], SCORE)
    if tornozelo_dir_xy is not None:
        kps[KP_TORNOZELO_DIR] = (tornozelo_dir_xy[0], tornozelo_dir_xy[1], SCORE)
    return FrameKeypoints(frame_idx=idx, person_count=1, keypoints=kps)


def test_delta_y_e_conversao_em_cm() -> None:
    # Dois contatos do pé direito: pico de Y do tornozelo nos frames 1 e 5.
    # Y_CoM oscila entre 200 (frame 0..1, 5) e 220 (frame 3) → ΔY = 20 px.
    # fator = 0.5 cm/px → oscilação = 10 cm.
    frames = [
        _frame(0, quadril_y=200.0, tornozelo_dir_y=450.0),
        _frame(1, quadril_y=200.0, tornozelo_dir_y=500.0),  # contato 1
        _frame(2, quadril_y=210.0, tornozelo_dir_y=400.0),
        _frame(3, quadril_y=220.0, tornozelo_dir_y=350.0),  # CoM mais baixo (Y maior)
        _frame(4, quadril_y=210.0, tornozelo_dir_y=400.0),
        _frame(5, quadril_y=200.0, tornozelo_dir_y=500.0),  # contato 2
        _frame(6, quadril_y=200.0, tornozelo_dir_y=450.0),
    ]
    resultado = calcular_oscilacao_vertical(frames, fator_escala=0.5)
    assert resultado is not None
    assert math.isclose(resultado.oscilacao_media_cm, 10.0, rel_tol=1e-9)
    assert resultado.ciclos_processados == (1,)


def test_media_sobre_multiplos_ciclos() -> None:
    # Três contatos (frames 1, 5, 9) → dois ciclos:
    #   ciclo 1 (frames 1..5): Y_CoM ∈ {200, 210, 220, 210, 200} → ΔY = 20 px
    #   ciclo 2 (frames 5..9): Y_CoM ∈ {200, 215, 230, 215, 200} → ΔY = 30 px
    # fator = 1.0 cm/px → oscilações [20, 30] cm; média = 25 cm.
    frames = [
        _frame(0, quadril_y=200.0, tornozelo_dir_y=450.0),
        _frame(1, quadril_y=200.0, tornozelo_dir_y=500.0),  # contato 1
        _frame(2, quadril_y=210.0, tornozelo_dir_y=400.0),
        _frame(3, quadril_y=220.0, tornozelo_dir_y=350.0),
        _frame(4, quadril_y=210.0, tornozelo_dir_y=400.0),
        _frame(5, quadril_y=200.0, tornozelo_dir_y=500.0),  # contato 2
        _frame(6, quadril_y=215.0, tornozelo_dir_y=400.0),
        _frame(7, quadril_y=230.0, tornozelo_dir_y=350.0),
        _frame(8, quadril_y=215.0, tornozelo_dir_y=400.0),
        _frame(9, quadril_y=200.0, tornozelo_dir_y=500.0),  # contato 3
        _frame(10, quadril_y=200.0, tornozelo_dir_y=450.0),
    ]
    resultado = calcular_oscilacao_vertical(frames, fator_escala=1.0)
    assert resultado is not None
    assert resultado.ciclos_processados == (1, 5)
    assert math.isclose(resultado.oscilacao_media_cm, 25.0, rel_tol=1e-9)


def test_menos_de_dois_contatos_retorna_none() -> None:
    # Apenas um contato detectável (pico no frame 1) ⇒ não há ciclo válido.
    frames = [
        _frame(0, quadril_y=200.0, tornozelo_dir_y=400.0),
        _frame(1, quadril_y=210.0, tornozelo_dir_y=500.0),
        _frame(2, quadril_y=200.0, tornozelo_dir_y=400.0),
    ]
    assert calcular_oscilacao_vertical(frames, fator_escala=0.5) is None


def test_sem_picos_retorna_none() -> None:
    # Y do tornozelo monotonicamente crescente ⇒ nenhum pico estrito.
    frames = [
        _frame(i, quadril_y=200.0 + i, tornozelo_dir_y=300.0 + i * 10.0)
        for i in range(6)
    ]
    assert calcular_oscilacao_vertical(frames, fator_escala=0.5) is None


def test_lista_vazia_retorna_none() -> None:
    assert calcular_oscilacao_vertical([], fator_escala=0.5) is None


def test_ciclo_sem_quadris_validos_e_descartado() -> None:
    # Dois contatos válidos (frames 1 e 5), mas todos os frames intermediários
    # do ciclo perdem ambos os quadris ⇒ ciclo descartado, retorno None.
    frames = [
        _frame(0, quadril_y=200.0, tornozelo_dir_y=450.0),
        _frame(1, tornozelo_dir_y=500.0),                 # contato 1, sem quadris
        _frame(2, tornozelo_dir_y=400.0),
        _frame(3, tornozelo_dir_y=350.0),
        _frame(4, tornozelo_dir_y=400.0),
        _frame(5, tornozelo_dir_y=500.0),                 # contato 2, sem quadris
        _frame(6, quadril_y=200.0, tornozelo_dir_y=450.0),
    ]
    assert calcular_oscilacao_vertical(frames, fator_escala=0.5) is None


def test_fator_escala_amplia_resultado_proporcionalmente() -> None:
    # Mesma série Y; fator menor ⇒ resultado proporcionalmente menor.
    frames = [
        _frame(0, quadril_y=200.0, tornozelo_dir_y=450.0),
        _frame(1, quadril_y=200.0, tornozelo_dir_y=500.0),
        _frame(2, quadril_y=240.0, tornozelo_dir_y=400.0),
        _frame(3, quadril_y=260.0, tornozelo_dir_y=350.0),  # ΔY = 60 px
        _frame(4, quadril_y=240.0, tornozelo_dir_y=400.0),
        _frame(5, quadril_y=200.0, tornozelo_dir_y=500.0),
        _frame(6, quadril_y=200.0, tornozelo_dir_y=450.0),
    ]
    r_full = calcular_oscilacao_vertical(frames, fator_escala=1.0)
    r_half = calcular_oscilacao_vertical(frames, fator_escala=0.5)
    assert r_full is not None and r_half is not None
    assert math.isclose(r_full.oscilacao_media_cm, 60.0, rel_tol=1e-9)
    assert math.isclose(r_half.oscilacao_media_cm, 30.0, rel_tol=1e-9)


def test_fator_escala_realista_de_altura_conhecida() -> None:
    # Replica a escala do teste US-007: altura 175 cm / altura_pixels 500 px
    # = 0.35 cm/px. ΔY = 20 px ⇒ oscilação = 7.0 cm (faixa típica de corredor).
    frames = [
        _frame(0, quadril_y=200.0, tornozelo_dir_y=450.0),
        _frame(1, quadril_y=200.0, tornozelo_dir_y=500.0),
        _frame(2, quadril_y=210.0, tornozelo_dir_y=400.0),
        _frame(3, quadril_y=220.0, tornozelo_dir_y=350.0),
        _frame(4, quadril_y=210.0, tornozelo_dir_y=400.0),
        _frame(5, quadril_y=200.0, tornozelo_dir_y=500.0),
        _frame(6, quadril_y=200.0, tornozelo_dir_y=450.0),
    ]
    resultado = calcular_oscilacao_vertical(frames, fator_escala=0.35)
    assert resultado is not None
    assert math.isclose(resultado.oscilacao_media_cm, 7.0, rel_tol=1e-9)


# ---- Smoke test: integração com run_pipeline + persistência em METRICA ----

class _FakeExtractor:
    def __init__(self, frames: list[FrameKeypoints], fps: float) -> None:
        self._frames = frames
        self._fps = fps

    def extract_keypoints(self, video_path: str) -> PoseExtractionResult:
        return PoseExtractionResult(
            fps=self._fps,
            total_frames=len(self._frames),
            frames=self._frames,
            low_quality_frames=0,
            multi_person_frames=0,
        )


def _make_test_session() -> sessionmaker[Session]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def test_pipeline_persiste_oscilacao_vertical_em_metrica() -> None:
    SessionTest = _make_test_session()

    # Frames sintéticos com nariz e ambos tornozelos (fator de escala
    # calculável) + dois contatos do pé direito + Y_CoM oscilando.
    # Para manter `altura_pixels` constante, ambos os tornozelos sobem e descem
    # juntos: midpoint Y dos tornozelos é constante = 700 → altura_pixels = 500
    # (entre nariz Y=200 e midpoint Y=700) → fator = 175 / 500 = 0.35 cm/px.
    # ΔY do CoM por ciclo = 20 px → oscilação = 0.35 × 20 = 7.0 cm.
    NARIZ_Y = 200.0
    frames: list[FrameKeypoints] = []
    quadris_y_serie = [200.0, 200.0, 210.0, 220.0, 210.0, 200.0, 200.0]
    tornozelo_dir_y_serie = [650.0, 700.0, 600.0, 550.0, 600.0, 700.0, 650.0]
    # tornozelo esquerdo é o "espelho" do direito em torno de 700 para que o
    # midpoint Y dos tornozelos permaneça 700 em todos os frames.
    tornozelo_esq_y_serie = [1400.0 - y for y in tornozelo_dir_y_serie]
    for i, (qy, ty_dir, ty_esq) in enumerate(
        zip(quadris_y_serie, tornozelo_dir_y_serie, tornozelo_esq_y_serie)
    ):
        kps: list[Keypoint] = [None] * NUM_KEYPOINTS
        kps[0] = (100.0, NARIZ_Y, SCORE)
        kps[KP_QUADRIL_ESQ] = (100.0, qy, SCORE)
        kps[KP_QUADRIL_DIR] = (100.0, qy, SCORE)
        kps[15] = (100.0, ty_esq, SCORE)
        kps[KP_TORNOZELO_DIR] = (100.0, ty_dir, SCORE)
        frames.append(
            FrameKeypoints(frame_idx=i, person_count=1, keypoints=kps)
        )

    with SessionTest() as session:
        usuario = Usuario(
            name="Tester",
            email="tester@example.com",
            senha_hash="x",
            altura_cm=175.0,
        )
        session.add(usuario)
        session.commit()
        session.refresh(usuario)

        sessao = SessaoAnalise(
            usuario_id=usuario.id,
            pace_min_km=5.0,
            status="pendente",
        )
        session.add(sessao)
        session.commit()
        session.refresh(sessao)
        sessao_id = sessao.id

    fake = _FakeExtractor(frames, fps=60.0)
    with patch("server.src.video_pipeline.SessionLocal", SessionTest), patch(
        "server.src.video_pipeline._safe_unlink"
    ):
        run_pipeline(
            sessao_id,
            video_path="ignored.mp4",
            extractor=fake,
            session_factory=SessionTest,
            delete_video=False,
        )

    with SessionTest() as session:
        metricas = (
            session.query(Metrica)
            .filter(Metrica.sessao_id == sessao_id)
            .all()
        )
        oscilacao = next(
            (m for m in metricas if m.tipo == "oscilacao_vertical"), None
        )
        assert oscilacao is not None
        assert oscilacao.unidade == "cm"
        assert oscilacao.apenas_informativa is False
        assert oscilacao.valor is not None
        assert math.isclose(float(oscilacao.valor), 7.0, abs_tol=1e-6)
