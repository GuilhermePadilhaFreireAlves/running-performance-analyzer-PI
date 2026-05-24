"""sessao_analise: add eventos_json column

Revision ID: 0004_sessao_analise_add_eventos
Revises: 0003_sessao_analise_add_dados_brutos
Create Date: 2026-05-24

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_sessao_analise_add_eventos"
down_revision: Union[str, Sequence[str], None] = "0003_sessao_analise_add_dados_brutos"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("sessao_analise") as batch_op:
        batch_op.add_column(
            sa.Column("eventos_json", sa.Text(), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("sessao_analise") as batch_op:
        batch_op.drop_column("eventos_json")
