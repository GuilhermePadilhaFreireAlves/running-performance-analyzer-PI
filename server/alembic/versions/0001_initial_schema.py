"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-04-21

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial_schema"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_SESSAO_STATUS_CHECK = (
    "status IN ("
    "'pendente',"
    "'validando_perspectiva',"
    "'detectando_pose',"
    "'calculando_metricas',"
    "'concluido',"
    "'erro_qualidade_keypoints',"
    "'erro_multiplas_pessoas'"
    ")"
)

_SEVERIDADE_CHECK = "severidade IN ('informativo','atencao','critico')"


def upgrade() -> None:
    op.create_table(
        "usuario",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("senha_hash", sa.String(length=255), nullable=False),
        sa.Column("altura_cm", sa.Float(), nullable=False),
        sa.Column("peso_kg", sa.Float(), nullable=True),
        sa.Column("nivel_experiencia", sa.String(length=50), nullable=True),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("email", name="uq_usuario_email"),
    )
    op.create_index("ix_usuario_email", "usuario", ["email"], unique=True)

    op.create_table(
        "sessao_analise",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column(
            "usuario_id",
            sa.Integer(),
            sa.ForeignKey("usuario.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("pace_min_km", sa.Float(), nullable=True),
        sa.Column("nota_geral", sa.Float(), nullable=True),
        sa.Column("feedback_ia", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="pendente",
        ),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(_SESSAO_STATUS_CHECK, name="ck_sessao_analise_status"),
    )
    op.create_index(
        "ix_sessao_analise_usuario_id",
        "sessao_analise",
        ["usuario_id"],
        unique=False,
    )

    op.create_table(
        "metrica",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column(
            "sessao_id",
            sa.Integer(),
            sa.ForeignKey("sessao_analise.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tipo", sa.String(length=100), nullable=False),
        sa.Column("valor", sa.Float(), nullable=True),
        sa.Column("unidade", sa.String(length=50), nullable=True),
        sa.Column(
            "apenas_informativa",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.create_index("ix_metrica_sessao_id", "metrica", ["sessao_id"], unique=False)

    op.create_table(
        "recomendacao",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column(
            "sessao_id",
            sa.Integer(),
            sa.ForeignKey("sessao_analise.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("categoria", sa.String(length=100), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=False),
        sa.Column("severidade", sa.String(length=20), nullable=False),
        sa.CheckConstraint(_SEVERIDADE_CHECK, name="ck_recomendacao_severidade"),
    )
    op.create_index(
        "ix_recomendacao_sessao_id",
        "recomendacao",
        ["sessao_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_recomendacao_sessao_id", table_name="recomendacao")
    op.drop_table("recomendacao")
    op.drop_index("ix_metrica_sessao_id", table_name="metrica")
    op.drop_table("metrica")
    op.drop_index("ix_sessao_analise_usuario_id", table_name="sessao_analise")
    op.drop_table("sessao_analise")
    op.drop_index("ix_usuario_email", table_name="usuario")
    op.drop_table("usuario")
