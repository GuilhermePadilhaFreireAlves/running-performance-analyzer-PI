"""sessao_analise: add dados_brutos_json column

Revision ID: 0003_sessao_analise_add_dados_brutos
Revises: 0002_sessao_analise_add_fps
Create Date: 2026-04-21

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_sessao_analise_add_dados_brutos"
down_revision: Union[str, Sequence[str], None] = "0002_sessao_analise_add_fps"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("sessao_analise") as batch_op:
        batch_op.add_column(
            sa.Column("dados_brutos_json", sa.Text(), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("sessao_analise") as batch_op:
        batch_op.drop_column("dados_brutos_json")
