"""Testes do endpoint GET /api/historico-analise (US-019)."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from server.src.database import Base, get_session
from server.src.main import app
from server.src.models import SessaoAnalise, Usuario
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


def _seed_sessoes(
    factory: sessionmaker[Session],
    usuario_id: int,
    *,
    count: int,
    base_time: datetime | None = None,
    status_value: str = "concluido",
) -> list[int]:
    """Cria `count` sessões com `criado_em` escalonado minuto a minuto (ordem decrescente)."""
    if base_time is None:
        base_time = datetime(2026, 4, 1, 12, 0, 0, tzinfo=timezone.utc)
    ids: list[int] = []
    with factory() as session:
        for i in range(count):
            sessao = SessaoAnalise(
                usuario_id=usuario_id,
                pace_min_km=5.0 + (i * 0.1),
                status=status_value,
                nota_geral=8.0 if status_value == "concluido" else None,
                criado_em=base_time + timedelta(minutes=i),
            )
            session.add(sessao)
        session.commit()
        rows = (
            session.query(SessaoAnalise)
            .filter(SessaoAnalise.usuario_id == usuario_id)
            .order_by(SessaoAnalise.criado_em.asc())
            .all()
        )
        ids = [int(r.id) for r in rows]
    return ids


def _auth_header(user_id: int) -> dict[str, str]:
    token = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


def test_historico_sem_auth_retorna_401(client: TestClient) -> None:
    response = client.get("/api/historico-analise")
    assert response.status_code == 401


def test_historico_token_invalido_retorna_401(client: TestClient) -> None:
    response = client.get(
        "/api/historico-analise",
        headers={"Authorization": "Bearer garbage"},
    )
    assert response.status_code == 401


def test_historico_usuario_sem_sessoes_retorna_vazio(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    user_id = _seed_user(session_factory)
    response = client.get(
        "/api/historico-analise", headers=_auth_header(user_id)
    )
    assert response.status_code == 200
    body = response.json()
    assert body == {"items": [], "total": 0, "page": 1, "limit": 10}


def test_historico_retorna_apenas_sessoes_do_usuario(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    owner_id = _seed_user(session_factory, email="owner@example.com")
    other_id = _seed_user(session_factory, email="other@example.com")
    _seed_sessoes(session_factory, owner_id, count=3)
    _seed_sessoes(session_factory, other_id, count=5)

    response = client.get(
        "/api/historico-analise", headers=_auth_header(owner_id)
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert len(body["items"]) == 3


def test_historico_ordenacao_decrescente_por_criado_em(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    user_id = _seed_user(session_factory)
    # _seed_sessoes cria em ordem asc; ids crescem junto com criado_em
    ids = _seed_sessoes(session_factory, user_id, count=4)

    response = client.get(
        "/api/historico-analise", headers=_auth_header(user_id)
    )
    assert response.status_code == 200
    body = response.json()
    received_ids = [item["id"] for item in body["items"]]
    assert received_ids == list(reversed(ids))


def test_historico_shape_do_item(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    user_id = _seed_user(session_factory)
    _seed_sessoes(session_factory, user_id, count=1)
    response = client.get(
        "/api/historico-analise", headers=_auth_header(user_id)
    )
    assert response.status_code == 200
    body = response.json()
    item = body["items"][0]
    assert set(item.keys()) == {
        "id",
        "criado_em",
        "pace_min_km",
        "status",
        "nota_geral",
    }
    assert item["status"] == "concluido"
    assert item["nota_geral"] == 8.0


def test_historico_paginacao(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    user_id = _seed_user(session_factory)
    ids = _seed_sessoes(session_factory, user_id, count=5)
    desc_ids = list(reversed(ids))

    # page=1&limit=2 → primeiros 2 mais recentes
    r1 = client.get(
        "/api/historico-analise?page=1&limit=2",
        headers=_auth_header(user_id),
    )
    assert r1.status_code == 200
    body1 = r1.json()
    assert body1["total"] == 5
    assert body1["page"] == 1
    assert body1["limit"] == 2
    assert [item["id"] for item in body1["items"]] == desc_ids[0:2]

    # page=2&limit=2 → próximos 2
    r2 = client.get(
        "/api/historico-analise?page=2&limit=2",
        headers=_auth_header(user_id),
    )
    body2 = r2.json()
    assert body2["page"] == 2
    assert [item["id"] for item in body2["items"]] == desc_ids[2:4]

    # page=3&limit=2 → última (incompleta)
    r3 = client.get(
        "/api/historico-analise?page=3&limit=2",
        headers=_auth_header(user_id),
    )
    body3 = r3.json()
    assert [item["id"] for item in body3["items"]] == desc_ids[4:5]


def test_historico_limit_clamped_para_50(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    user_id = _seed_user(session_factory)
    _seed_sessoes(session_factory, user_id, count=60)

    response = client.get(
        "/api/historico-analise?limit=100",
        headers=_auth_header(user_id),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 60
    assert body["limit"] == 50
    assert len(body["items"]) == 50


def test_historico_page_zero_retorna_422(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    user_id = _seed_user(session_factory)
    response = client.get(
        "/api/historico-analise?page=0",
        headers=_auth_header(user_id),
    )
    assert response.status_code == 422


def test_historico_page_negativa_retorna_422(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    user_id = _seed_user(session_factory)
    response = client.get(
        "/api/historico-analise?page=-1",
        headers=_auth_header(user_id),
    )
    assert response.status_code == 422


def test_historico_limit_zero_retorna_422(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    user_id = _seed_user(session_factory)
    response = client.get(
        "/api/historico-analise?limit=0",
        headers=_auth_header(user_id),
    )
    assert response.status_code == 422


def test_historico_limit_nao_numerico_retorna_422(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    user_id = _seed_user(session_factory)
    response = client.get(
        "/api/historico-analise?limit=abc",
        headers=_auth_header(user_id),
    )
    assert response.status_code == 422


def test_historico_defaults_page_1_limit_10(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    user_id = _seed_user(session_factory)
    _seed_sessoes(session_factory, user_id, count=3)
    response = client.get(
        "/api/historico-analise", headers=_auth_header(user_id)
    )
    assert response.status_code == 200
    body = response.json()
    assert body["page"] == 1
    assert body["limit"] == 10


def test_historico_inclui_sessoes_com_erro(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    user_id = _seed_user(session_factory)
    _seed_sessoes(
        session_factory, user_id, count=2, status_value="erro_qualidade_keypoints"
    )
    response = client.get(
        "/api/historico-analise", headers=_auth_header(user_id)
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert all(item["status"] == "erro_qualidade_keypoints" for item in body["items"])
    assert all(item["nota_geral"] is None for item in body["items"])
