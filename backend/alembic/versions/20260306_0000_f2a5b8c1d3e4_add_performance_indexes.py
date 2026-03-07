"""add_performance_indexes

Revision ID: f2a5b8c1d3e4
Revises: ad2c72d53211
Create Date: 2026-03-06 00:00:00.000000+00:00

Adiciona:
  - Tabela request_logs (ausente na migration inicial)
  - Índices compostos de performance em copies, arts, pipeline_sessions,
    monitored_profiles e request_logs
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f2a5b8c1d3e4"
down_revision: Union[str, None] = "ad2c72d53211"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Tabela request_logs ────────────────────────────────────────────────────
    op.create_table(
        "request_logs",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("endpoint", sa.String(500), nullable=False),
        sa.Column("method", sa.String(10), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_request_logs_endpoint_timestamp",
        "request_logs",
        ["endpoint", "timestamp"],
    )

    # ── Índices compostos ──────────────────────────────────────────────────────
    # copies: cobertura para filtros de canal+status e ordenação por data
    op.create_index(
        "ix_copies_pipeline_channel_status",
        "copies",
        ["pipeline_id", "channel", "status"],
    )
    op.create_index(
        "ix_copies_created_at_desc",
        "copies",
        ["created_at"],
    )

    # arts: cobertura para filtro de tipo por pipeline
    op.create_index(
        "ix_arts_pipeline_type",
        "arts",
        ["pipeline_id", "type"],
    )

    # pipeline_sessions: cobertura para filtro de estado por usuário
    op.create_index(
        "ix_pipeline_sessions_user_state",
        "pipeline_sessions",
        ["user_id", "state"],
    )

    # monitored_profiles: cobertura para filtro de plataforma ativa
    op.create_index(
        "ix_monitored_profiles_user_platform_active",
        "monitored_profiles",
        ["user_id", "platform", "active"],
    )


def downgrade() -> None:
    op.drop_index("ix_monitored_profiles_user_platform_active", "monitored_profiles")
    op.drop_index("ix_pipeline_sessions_user_state", "pipeline_sessions")
    op.drop_index("ix_arts_pipeline_type", "arts")
    op.drop_index("ix_copies_created_at_desc", "copies")
    op.drop_index("ix_copies_pipeline_channel_status", "copies")
    op.drop_index("ix_request_logs_endpoint_timestamp", "request_logs")
    op.drop_table("request_logs")
