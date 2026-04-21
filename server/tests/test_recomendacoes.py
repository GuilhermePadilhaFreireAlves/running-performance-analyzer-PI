"""Testes do gerador de recomendações + nota geral (US-016).

Cobertura por faixa da Seção 9 do PRD para cada métrica, mais a conversão
em :class:`AnaliseResultado` (nota, feedback, tupla de recomendações) e o
smoke-test de integração com ``run_pipeline`` (METRICA → RECOMENDACAO +
status=concluido + nota persistida).
"""

from __future__ import annotations

import math
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from server.src.biomechanics.recomendacoes import (
    NOTA_MAXIMA,
    PESO_ATENCAO,
    PESO_CRITICO,
    SEVERIDADE_ATENCAO,
    SEVERIDADE_CRITICO,
    SEVERIDADE_INFORMATIVO,
    AnaliseResultado,
    analisar_metricas,
)
from server.src.database import Base
from server.src.models import Metrica, Recomendacao, SessaoAnalise, Usuario
from server.src.video_pipeline import (
    KEYPOINT_SCORE_THRESHOLD,
    NUM_KEYPOINTS,
    FrameKeypoints,
    Keypoint,
    PoseExtractionResult,
    run_pipeline,
)

SCORE = max(0.9, KEYPOINT_SCORE_THRESHOLD + 0.1)


# ---------------------- classificação por métrica (Seção 9) -------------------


def _severidade_unica(tipo: str, valor: float) -> str:
    resultado = analisar_metricas([(tipo, valor)])
    assert len(resultado.recomendacoes) == 1
    return resultado.recomendacoes[0].severidade


def test_joelho_ideal_flexao_20_retorna_informativo() -> None:
    # interno = 160 ⇒ flexão = 20° (faixa ideal 15°–25°).
    assert _severidade_unica("angulo_joelho_esq", 160.0) == SEVERIDADE_INFORMATIVO


def test_joelho_atencao_flexao_muito_estendido() -> None:
    # interno = 168 ⇒ flexão = 12° (faixa atenção 10°–15°).
    assert _severidade_unica("angulo_joelho_dir", 168.0) == SEVERIDADE_ATENCAO


def test_joelho_atencao_flexao_muito_flexionado() -> None:
    # interno = 150 ⇒ flexão = 30° (faixa atenção 25°–35°).
    assert _severidade_unica("angulo_joelho_esq", 150.0) == SEVERIDADE_ATENCAO


def test_joelho_critico_hiperextensao() -> None:
    # interno = 175 ⇒ flexão = 5° (crítico < 10°).
    assert _severidade_unica("angulo_joelho_esq", 175.0) == SEVERIDADE_CRITICO


def test_joelho_critico_colapso() -> None:
    # interno = 140 ⇒ flexão = 40° (crítico > 35°).
    assert _severidade_unica("angulo_joelho_dir", 140.0) == SEVERIDADE_CRITICO


def test_cotovelo_ideal_90_retorna_informativo() -> None:
    assert _severidade_unica("angulo_cotovelo_esq", 90.0) == SEVERIDADE_INFORMATIVO


def test_cotovelo_atencao_fechado() -> None:
    # 65° ∈ (60, 70) ⇒ atenção.
    assert _severidade_unica("angulo_cotovelo_dir", 65.0) == SEVERIDADE_ATENCAO


def test_cotovelo_atencao_aberto() -> None:
    # 115° ∈ (110, 120) ⇒ atenção.
    assert _severidade_unica("angulo_cotovelo_esq", 115.0) == SEVERIDADE_ATENCAO


def test_cotovelo_critico() -> None:
    assert _severidade_unica("angulo_cotovelo_dir", 55.0) == SEVERIDADE_CRITICO
    assert _severidade_unica("angulo_cotovelo_dir", 125.0) == SEVERIDADE_CRITICO


def test_tronco_ideal_6_retorna_informativo() -> None:
    assert _severidade_unica("inclinacao_tronco", 6.0) == SEVERIDADE_INFORMATIVO


def test_tronco_atencao_ereto_e_inclinado() -> None:
    assert _severidade_unica("inclinacao_tronco", 2.0) == SEVERIDADE_ATENCAO
    assert _severidade_unica("inclinacao_tronco", 12.0) == SEVERIDADE_ATENCAO


def test_tronco_critico_vertical_e_excessivo() -> None:
    assert _severidade_unica("inclinacao_tronco", 0.5) == SEVERIDADE_CRITICO
    assert _severidade_unica("inclinacao_tronco", 20.0) == SEVERIDADE_CRITICO
    # Inclinação negativa (para trás) ⇒ <1° ⇒ crítico.
    assert _severidade_unica("inclinacao_tronco", -3.0) == SEVERIDADE_CRITICO


def test_overstriding_ideal_pouco_desvio() -> None:
    # |2| < 5 ⇒ informativo.
    assert (
        _severidade_unica("overstriding_esq", 2.0) == SEVERIDADE_INFORMATIVO
    )
    assert (
        _severidade_unica("overstriding_dir", -3.0) == SEVERIDADE_INFORMATIVO
    )


def test_overstriding_atencao_usa_magnitude() -> None:
    # Positivo e negativo ambos classificam pela magnitude.
    assert _severidade_unica("overstriding_esq", 10.0) == SEVERIDADE_ATENCAO
    assert _severidade_unica("overstriding_dir", -12.0) == SEVERIDADE_ATENCAO


def test_overstriding_critico_usa_magnitude() -> None:
    assert _severidade_unica("overstriding_esq", 20.0) == SEVERIDADE_CRITICO
    assert _severidade_unica("overstriding_dir", -18.0) == SEVERIDADE_CRITICO


def test_oscilacao_ideal_em_7_cm() -> None:
    assert (
        _severidade_unica("oscilacao_vertical", 7.0) == SEVERIDADE_INFORMATIVO
    )


def test_oscilacao_atencao_baixa_e_alta() -> None:
    assert _severidade_unica("oscilacao_vertical", 4.0) == SEVERIDADE_ATENCAO
    assert _severidade_unica("oscilacao_vertical", 12.0) == SEVERIDADE_ATENCAO


def test_oscilacao_critica() -> None:
    assert _severidade_unica("oscilacao_vertical", 2.0) == SEVERIDADE_CRITICO
    assert _severidade_unica("oscilacao_vertical", 14.0) == SEVERIDADE_CRITICO


def test_simetria_ideal_atencao_critico_para_todos_os_tipos() -> None:
    for tipo in ("simetria_tcs", "simetria_joelho", "simetria_oscilacao"):
        assert _severidade_unica(tipo, 2.0) == SEVERIDADE_INFORMATIVO
        assert _severidade_unica(tipo, 7.5) == SEVERIDADE_ATENCAO
        assert _severidade_unica(tipo, 15.0) == SEVERIDADE_CRITICO


# ----------------------------- nota + agregação ------------------------------


def test_analisar_metricas_todas_ideais_nota_maxima() -> None:
    metricas = [
        ("angulo_joelho_esq", 160.0),  # flexão 20°
        ("angulo_joelho_dir", 160.0),
        ("angulo_cotovelo_esq", 90.0),
        ("angulo_cotovelo_dir", 95.0),
        ("inclinacao_tronco", 6.0),
        ("overstriding_esq", 2.0),
        ("overstriding_dir", -3.0),
        ("oscilacao_vertical", 7.0),
        ("simetria_tcs", 2.0),
        ("simetria_joelho", 3.0),
        ("simetria_oscilacao", 1.0),
    ]
    resultado = analisar_metricas(metricas)
    assert isinstance(resultado, AnaliseResultado)
    assert resultado.nota_geral == NOTA_MAXIMA
    # Uma recomendação informativa para cada métrica.
    assert len(resultado.recomendacoes) == len(metricas)
    assert all(
        r.severidade == SEVERIDADE_INFORMATIVO for r in resultado.recomendacoes
    )


def test_analisar_metricas_mistura_de_severidades_penaliza() -> None:
    # 1 crítico + 2 atenção + 1 ideal ⇒ nota = 10 - 1.5 - 2*0.5 = 7.5
    metricas = [
        ("angulo_joelho_esq", 175.0),  # flexão 5° ⇒ crítico
        ("angulo_cotovelo_esq", 115.0),  # atenção
        ("inclinacao_tronco", 12.0),  # atenção
        ("oscilacao_vertical", 7.0),  # informativo
    ]
    resultado = analisar_metricas(metricas)
    esperado = NOTA_MAXIMA - PESO_CRITICO - 2 * PESO_ATENCAO
    assert math.isclose(resultado.nota_geral, esperado, rel_tol=1e-9)
    severidades = [r.severidade for r in resultado.recomendacoes]
    assert severidades.count(SEVERIDADE_CRITICO) == 1
    assert severidades.count(SEVERIDADE_ATENCAO) == 2
    assert severidades.count(SEVERIDADE_INFORMATIVO) == 1


def test_analisar_metricas_clamp_em_zero_para_muitas_falhas() -> None:
    # 11 métricas críticas ⇒ penalização 16.5 ⇒ clamp para 0.
    metricas = [
        ("angulo_joelho_esq", 175.0),
        ("angulo_joelho_dir", 140.0),
        ("angulo_cotovelo_esq", 40.0),
        ("angulo_cotovelo_dir", 130.0),
        ("inclinacao_tronco", 20.0),
        ("overstriding_esq", 20.0),
        ("overstriding_dir", -22.0),
        ("oscilacao_vertical", 16.0),
        ("simetria_tcs", 15.0),
        ("simetria_joelho", 18.0),
        ("simetria_oscilacao", 12.0),
    ]
    resultado = analisar_metricas(metricas)
    assert resultado.nota_geral == 0.0
    assert all(
        r.severidade == SEVERIDADE_CRITICO for r in resultado.recomendacoes
    )


def test_analisar_metricas_pesos_critico_maior_que_atencao() -> None:
    # Mesmo número de métricas fora do ideal, mas severidades diferentes
    # ⇒ crítico produz nota menor que atenção.
    nota_critico = analisar_metricas(
        [("angulo_joelho_esq", 175.0)]
    ).nota_geral
    nota_atencao = analisar_metricas(
        [("angulo_joelho_esq", 168.0)]
    ).nota_geral
    assert nota_critico < nota_atencao


def test_analisar_metricas_tipos_desconhecidos_sao_ignorados() -> None:
    resultado = analisar_metricas(
        [
            ("cadencia", 170.0),  # apenas_informativa — não deveria ter chegado aqui
            ("tcs_esq", 240.0),
            ("tipo_inexistente", 42.0),
        ]
    )
    assert resultado.recomendacoes == ()
    assert resultado.nota_geral == NOTA_MAXIMA


def test_analisar_metricas_feedback_contem_nota() -> None:
    resultado = analisar_metricas([("angulo_joelho_esq", 175.0)])
    assert "Nota geral" in resultado.feedback_ia
    assert "crítico" in resultado.feedback_ia.lower()


def test_analisar_metricas_lista_vazia_produz_nota_maxima() -> None:
    resultado = analisar_metricas([])
    assert resultado.nota_geral == NOTA_MAXIMA
    assert resultado.recomendacoes == ()


# -------- Smoke test: integração com run_pipeline + persistência completa ----


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


def _frame_completo(
    idx: int,
    *,
    tornozelo_esq_y: float,
    tornozelo_dir_y: float,
    quadril_y: float = 200.0,
) -> FrameKeypoints:
    """Frame com keypoints suficientes para todas as métricas não-informativas."""
    kps: list[Keypoint] = [None] * NUM_KEYPOINTS
    kps[0] = (100.0, 100.0, SCORE)              # nariz
    kps[5] = (90.0, 150.0, SCORE)               # ombro esq
    kps[6] = (110.0, 150.0, SCORE)              # ombro dir
    kps[7] = (90.0, 200.0, SCORE)               # cotovelo esq
    kps[8] = (110.0, 200.0, SCORE)              # cotovelo dir
    kps[9] = (90.0, 250.0, SCORE)               # pulso esq
    kps[10] = (110.0, 250.0, SCORE)             # pulso dir
    kps[11] = (95.0, quadril_y, SCORE)          # quadril esq
    kps[12] = (105.0, quadril_y, SCORE)         # quadril dir
    kps[13] = (95.0, quadril_y + 100.0, SCORE)  # joelho esq
    kps[14] = (105.0, quadril_y + 100.0, SCORE) # joelho dir
    kps[15] = (95.0, tornozelo_esq_y, SCORE)    # tornozelo esq
    kps[16] = (105.0, tornozelo_dir_y, SCORE)   # tornozelo dir
    return FrameKeypoints(frame_idx=idx, person_count=1, keypoints=kps)


def test_pipeline_gera_recomendacoes_e_conclui_sessao() -> None:
    SessionTest = _make_test_session()

    # Série simétrica com picos em frames 1 e 5 (pé esq e dir) que produzem
    # várias métricas calculáveis. A geometria é propositalmente genérica —
    # o que importa aqui é verificar que (a) há recomendações gravadas,
    # (b) a sessão foi concluída, (c) a nota foi persistida, (d) o feedback
    # textual está populado.
    frames = [
        _frame_completo(0, tornozelo_esq_y=450.0, tornozelo_dir_y=450.0),
        _frame_completo(1, tornozelo_esq_y=500.0, tornozelo_dir_y=500.0),
        _frame_completo(2, tornozelo_esq_y=420.0, tornozelo_dir_y=420.0, quadril_y=220.0),
        _frame_completo(3, tornozelo_esq_y=380.0, tornozelo_dir_y=380.0, quadril_y=230.0),
        _frame_completo(4, tornozelo_esq_y=420.0, tornozelo_dir_y=420.0, quadril_y=220.0),
        _frame_completo(5, tornozelo_esq_y=500.0, tornozelo_dir_y=500.0),
        _frame_completo(6, tornozelo_esq_y=450.0, tornozelo_dir_y=450.0),
    ]

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
        sessao_final = session.get(SessaoAnalise, sessao_id)
        assert sessao_final is not None
        assert sessao_final.status == "concluido"
        assert sessao_final.nota_geral is not None
        assert 0.0 <= float(sessao_final.nota_geral) <= NOTA_MAXIMA
        assert sessao_final.feedback_ia is not None
        assert "Nota geral" in sessao_final.feedback_ia

        recomendacoes = (
            session.query(Recomendacao)
            .filter(Recomendacao.sessao_id == sessao_id)
            .all()
        )
        assert len(recomendacoes) >= 1
        for rec in recomendacoes:
            assert rec.categoria
            assert rec.descricao
            assert rec.severidade in {
                SEVERIDADE_INFORMATIVO,
                SEVERIDADE_ATENCAO,
                SEVERIDADE_CRITICO,
            }


def test_pipeline_nao_penaliza_metricas_apenas_informativas() -> None:
    """Cadência e TCS absoluto (apenas_informativa=True) não devem afetar a nota.

    Seed direto do DB com duas métricas: uma informativa (cadência absurda
    que, se avaliada, seria crítica) e uma não-informativa (joelho ideal).
    Esperamos nota máxima e uma única recomendação (a do joelho).
    """
    SessionTest = _make_test_session()

    from server.src.video_pipeline import _finalizar_analise

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
            status="calculando_metricas",
        )
        session.add(sessao)
        session.commit()
        session.refresh(sessao)
        sessao_id = sessao.id

        # Joelho ideal (interno = 160 ⇒ flexão 20°)
        session.add(
            Metrica(
                sessao_id=sessao_id,
                tipo="angulo_joelho_esq",
                valor=160.0,
                unidade="graus",
                apenas_informativa=False,
            )
        )
        # Cadência "crítica" se fosse avaliada — mas com flag informativa, é ignorada.
        session.add(
            Metrica(
                sessao_id=sessao_id,
                tipo="cadencia",
                valor=999.0,
                unidade="spm",
                apenas_informativa=True,
            )
        )
        # TCS absoluto (também apenas informativo) — idem, deve ser ignorado.
        session.add(
            Metrica(
                sessao_id=sessao_id,
                tipo="tcs_esq",
                valor=10000.0,
                unidade="ms",
                apenas_informativa=True,
            )
        )
        session.commit()

        _finalizar_analise(session, sessao_id)

    with SessionTest() as session:
        sessao_final = session.get(SessaoAnalise, sessao_id)
        assert sessao_final is not None
        assert sessao_final.status == "concluido"
        assert sessao_final.nota_geral == NOTA_MAXIMA

        recomendacoes = (
            session.query(Recomendacao)
            .filter(Recomendacao.sessao_id == sessao_id)
            .all()
        )
        # Apenas uma — referente à métrica não informativa (joelho).
        assert len(recomendacoes) == 1
        assert recomendacoes[0].severidade == SEVERIDADE_INFORMATIVO
