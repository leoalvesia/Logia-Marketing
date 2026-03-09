"""add_missing_columns

Revision ID: a1b2c3d4e5f6
Revises: f2a5b8c1d3e4
Create Date: 2026-03-09 00:00:00.000000+00:00

Adiciona colunas ausentes nas migrations anteriores:

  users:
    - onboarding_completed (Boolean, default False)
    - accepted_terms_at   (DateTime, nullable)
    - deleted_at          (DateTime, nullable)

  topics:
    - source_verified  (Boolean, default False)
    - dados_pesquisa   (Text, default '')

Nota: Em PostgreSQL, o Alembic usa batch_alter_table com render_as_batch=True
configurado em env.py. Em SQLite, create_all() já criou as colunas, mas as
migrations garantem consistência entre ambientes.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "f2a5b8c1d3e4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── users ────────────────────────────────────────────────────────────────
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("onboarding_completed", sa.Boolean(), nullable=False, server_default="0")
        )
        batch_op.add_column(sa.Column("accepted_terms_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("deleted_at", sa.DateTime(), nullable=True))

    # ── topics ───────────────────────────────────────────────────────────────
    with op.batch_alter_table("topics", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("source_verified", sa.Boolean(), nullable=False, server_default="0")
        )
        batch_op.add_column(
            sa.Column("dados_pesquisa", sa.Text(), nullable=False, server_default="")
        )


def downgrade() -> None:
    with op.batch_alter_table("topics", schema=None) as batch_op:
        batch_op.drop_column("dados_pesquisa")
        batch_op.drop_column("source_verified")

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("deleted_at")
        batch_op.drop_column("accepted_terms_at")
        batch_op.drop_column("onboarding_completed")
