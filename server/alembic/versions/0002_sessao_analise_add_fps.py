"""sessao_analise: add fps column

Revision ID: 0002_sessao_analise_add_fps
Revises: 0001_initial_schema
Create Date: 2026-04-21

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_sessao_analise_add_fps"
down_revision: Union[str, Sequence[str], None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("sessao_analise") as batch_op:
        batch_op.add_column(sa.Column("fps", sa.Float(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("sessao_analise") as batch_op:
        batch_op.drop_column("fps")
