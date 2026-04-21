"""Testes do endpoint GET /api/analysis/{id}/raw (US-018)."""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from server.src.database import Base, get_session
from server.src.main import app
from server.src.models import Metrica, SessaoAnalise, Usuario
from server.src.security import create_access_token, hash_password


@pytest.fixture()
def session_factory() -> sessionmaker[Session]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture()
def client(session_factory: sessionmaker[Session]) -> Iterator[TestClient]:
    def _override() -> Iterator[Session]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_session] = _override
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_session, None)


def _seed_user(
    factory: sessionmaker[Session],
    *,
    email: str = "runner@example.com",
    name: str = "Runner",
) -> int:
    with factory() as session:
        user = Usuario(
            name=name,
            email=email,
            senha_hash=hash_password("secret123"),
            altura_cm=175.0,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return int(user.id)


def _seed_sessao(
    factory: sessionmaker[Session],
    usuario_id: int,
    *,
    status: str = "concluido",
    fps: float | None = 60.0,
    dados_brutos_json: str | None = None,
    metricas: list[tuple[str, float, str, bool]] | None = None,
) -> int:
    with factory() as session:
        sessao = SessaoAnalise(
            usuario_id=usuario_id,
            pace_min_km=5.0,
            fps=fps,
            status=status,
            dados_brutos_json=dados_brutos_json,
            nota_geral=8.0 if status == "concluido" else None,
            feedback_ia="ok" if status == "concluido" else None,
        )
        session.add(sessao)
        session.commit()
        session.refresh(sessao)
        sessao_id = int(sessao.id)
        for tipo, valor, unidade, informativa in metricas or []:
            session.add(
                Metrica(
                    sessao_id=sessao_id,
                    tipo=tipo,
                    valor=valor,
                    unidade=unidade,
                    apenas_informativa=informativa,
                )
            )
        session.commit()
        return sessao_id


def _auth_header(user_id: int) -> dict[str, str]:
    token = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


def test_raw_sem_auth_retorna_401(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    user_id = _seed_user(session_factory)
    sessao_id = _seed_sessao(session_factory, user_id)
    response = client.get(f"/api/analysis/{sessao_id}/raw")
    assert response.status_code == 401


def test_raw_token_invalido_retorna_401(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    user_id = _seed_user(session_factory)
    sessao_id = _seed_sessao(session_factory, user_id)
    response = client.get(
        f"/api/analysis/{sessao_id}/raw",
        headers={"Authorization": "Bearer garbage"},
    )
    assert response.status_code == 401


def test_raw_id_inexistente_retorna_404(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    user_id = _seed_user(session_factory)
    response = client.get("/api/analysis/9999/raw", headers=_auth_header(user_id))
    assert response.status_code == 404


def test_raw_sessao_de_outro_usuario_retorna_403(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    owner_id = _seed_user(session_factory, email="owner@example.com")
    other_id = _seed_user(session_factory, email="other@example.com")
    sessao_id = _seed_sessao(session_factory, owner_id)
    response = client.get(
        f"/api/analysis/{sessao_id}/raw", headers=_auth_header(other_id)
    )
    assert response.status_code == 403


def test_raw_feliz_retorna_frames_e_agregadas(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    user_id = _seed_user(session_factory)
    payload = [
        {
            "frame_idx": 0,
            "keypoints": [None] * 17,
            "angulo_joelho_esq": 170.0,
            "angulo_joelho_dir": None,
            "angulo_cotovelo_esq": 95.0,
            "angulo_cotovelo_dir": None,
            "inclinacao_tronco": 7.5,
            "y_com": 200.0,
        },
        {
            "frame_idx": 1,
            "keypoints": [[10.0, 20.0, 0.9]] + [None] * 16,
            "angulo_joelho_esq": None,
            "angulo_joelho_dir": 172.0,
            "angulo_cotovelo_esq": None,
            "angulo_cotovelo_dir": 100.0,
            "inclinacao_tronco": None,
            "y_com": 205.0,
        },
    ]
    sessao_id = _seed_sessao(
        session_factory,
        user_id,
        dados_brutos_json=json.dumps(payload),
        metricas=[
            ("angulo_joelho_esq", 170.0, "graus", False),
            ("simetria_tcs", 5.0, "%", False),
            ("simetria_joelho", 3.0, "%", False),
            ("cadencia", 170.0, "spm", True),
        ],
    )
    response = client.get(
        f"/api/analysis/{sessao_id}/raw", headers=_auth_header(user_id)
    )
    assert response.status_code == 200
    body = response.json()
    assert body["fps"] == 60.0
    assert body["erro"] is None
    assert len(body["frames"]) == 2
    # keypoints ausentes serializados como null
    assert body["frames"][0]["keypoints"][0] is None
    assert body["frames"][1]["keypoints"][0] == [10.0, 20.0, 0.9]
    assert body["frames"][0]["angulo_joelho_esq"] == 170.0
    assert body["frames"][0]["angulo_joelho_dir"] is None
    # simetria populada; métricas agregadas não incluem simetria_*
    assert body["simetria"] == {"tcs": 5.0, "joelho": 3.0, "oscilacao": None}
    tipos = {m["tipo"] for m in body["metricas_agregadas"]}
    assert "angulo_joelho_esq" in tipos
    assert "cadencia" in tipos  # informativa continua aparecendo no raw
    assert "simetria_tcs" not in tipos
    assert "simetria_joelho" not in tipos


def test_raw_sem_dados_brutos_retorna_frames_vazios(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    user_id = _seed_user(session_factory)
    sessao_id = _seed_sessao(session_factory, user_id, dados_brutos_json=None)
    response = client.get(
        f"/api/analysis/{sessao_id}/raw", headers=_auth_header(user_id)
    )
    assert response.status_code == 200
    assert response.json()["frames"] == []


def test_raw_status_erro_qualidade(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    user_id = _seed_user(session_factory)
    sessao_id = _seed_sessao(
        session_factory,
        user_id,
        status="erro_qualidade_keypoints",
        fps=30.0,
    )
    response = client.get(
        f"/api/analysis/{sessao_id}/raw", headers=_auth_header(user_id)
    )
    assert response.status_code == 200
    body = response.json()
    assert body["erro"] == "Erro: qualidade de keypoints insuficiente"
    assert body["frames"] == []
    assert body["metricas_agregadas"] == []


def test_raw_status_erro_multiplas_pessoas(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    user_id = _seed_user(session_factory)
    sessao_id = _seed_sessao(
        session_factory, user_id, status="erro_multiplas_pessoas"
    )
    response = client.get(
        f"/api/analysis/{sessao_id}/raw", headers=_auth_header(user_id)
    )
    assert response.status_code == 200
    body = response.json()
    assert body["erro"] == "Erro: múltiplas pessoas detectadas"


def test_pipeline_persiste_dados_brutos_json(
    session_factory: sessionmaker[Session],
) -> None:
    """O pipeline deve serializar keypoints + per-frame em dados_brutos_json."""
    from unittest.mock import patch

    from server.src.video_pipeline import (
        NUM_KEYPOINTS,
        FrameKeypoints,
        Keypoint,
        PoseExtractionResult,
        run_pipeline,
    )

    SCORE = 0.9

    def _frame(idx: int) -> FrameKeypoints:
        kps: list[Keypoint] = [None] * NUM_KEYPOINTS
        kps[0] = (100.0, 100.0, SCORE)
        kps[5] = (90.0, 150.0, SCORE)
        kps[6] = (110.0, 150.0, SCORE)
        kps[11] = (95.0, 200.0, SCORE)
        kps[12] = (105.0, 200.0, SCORE)
        kps[13] = (95.0, 300.0, SCORE)
        kps[14] = (105.0, 300.0, SCORE)
        kps[15] = (95.0, 450.0 + idx * 10, SCORE)
        kps[16] = (105.0, 450.0 + idx * 10, SCORE)
        return FrameKeypoints(frame_idx=idx, person_count=1, keypoints=kps)

    frames = [_frame(i) for i in range(5)]

    with session_factory() as session:
        user = Usuario(
            name="Tester",
            email="tester@example.com",
            senha_hash="x",
            altura_cm=175.0,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        sessao = SessaoAnalise(
            usuario_id=user.id, pace_min_km=5.0, status="pendente"
        )
        session.add(sessao)
        session.commit()
        session.refresh(sessao)
        sessao_id = int(sessao.id)

    class _FakeExtractor:
        def extract_keypoints(self, video_path: str) -> PoseExtractionResult:
            return PoseExtractionResult(
                fps=60.0,
                total_frames=len(frames),
                frames=frames,
                low_quality_frames=0,
                multi_person_frames=0,
            )

    with patch("server.src.video_pipeline.SessionLocal", session_factory), patch(
        "server.src.video_pipeline._safe_unlink"
    ):
        run_pipeline(
            sessao_id,
            "ignored.mp4",
            extractor=_FakeExtractor(),
            session_factory=session_factory,
            delete_video=False,
        )

    with session_factory() as session:
        sessao_final = session.get(SessaoAnalise, sessao_id)
        assert sessao_final is not None
        assert sessao_final.dados_brutos_json is not None
        parsed = json.loads(sessao_final.dados_brutos_json)
        assert isinstance(parsed, list)
        assert len(parsed) == 5
        assert parsed[0]["frame_idx"] == 0
        assert len(parsed[0]["keypoints"]) == 17
        # ângulo do joelho calculado (perna estendida-ish, perto de 180°)
        assert parsed[0]["angulo_joelho_esq"] is not None
        # y_com = média dos quadris = 200
        assert parsed[0]["y_com"] == 200.0


def test_raw_valores_nao_geram_nan_na_serializacao(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    """Valores ausentes devem virar null — nunca NaN — no JSON."""
    user_id = _seed_user(session_factory)
    payload: list[dict[str, Any]] = [
        {
            "frame_idx": 0,
            "keypoints": [None] * 17,
            "angulo_joelho_esq": None,
            "angulo_joelho_dir": None,
            "angulo_cotovelo_esq": None,
            "angulo_cotovelo_dir": None,
            "inclinacao_tronco": None,
            "y_com": None,
        }
    ]
    sessao_id = _seed_sessao(
        session_factory, user_id, dados_brutos_json=json.dumps(payload)
    )
    response = client.get(
        f"/api/analysis/{sessao_id}/raw", headers=_auth_header(user_id)
    )
    assert response.status_code == 200
    # Parseável como JSON puro (json.loads rejeita NaN por padrão).
    body = json.loads(response.text)
    assert body["frames"][0]["y_com"] is None
