"""Missions, items, and agent traces migration

Revision ID: 0003_missions_and_traces
Revises: 0002_stores_products
Create Date: 2026-10-13 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_missions_and_traces"
down_revision: str | None = "0002_stores_products"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Missions Table
    op.create_table(
        "missions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("raw_text", sa.String(2000), nullable=False),
        sa.Column("language", sa.String(10), nullable=False, server_default="en"),
        sa.Column(
            "input_modalities",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default="{text}",
        ),
        sa.Column("constraints", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "selected_store_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=False
        ),
        sa.Column("total_cost", sa.Numeric(10, 2), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_missions_user_id", "missions", ["user_id"])
    op.create_index("ix_missions_status", "missions", ["status"])

    # 2. Mission Items Table
    op.create_table(
        "mission_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "mission_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("missions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("products.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("requested_label", sa.String(255), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("reason", sa.String(500), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="matched"),
        sa.Column(
            "substitute_for_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mission_items.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "store_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("stores.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("aisle_snapshot", sa.Integer(), nullable=True),
        sa.Column("bay_snapshot", sa.Integer(), nullable=True),
        sa.Column("shelf_snapshot", sa.Integer(), nullable=True),
    )
    op.create_index("ix_mission_items_mission_id", "mission_items", ["mission_id"])
    op.create_index("ix_mission_items_product_id", "mission_items", ["product_id"])
    op.create_index("ix_mission_items_store_id", "mission_items", ["store_id"])

    # 3. Mission Runs / Agent Traces Table
    op.create_table(
        "mission_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "mission_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("missions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("step", sa.String(100), nullable=False),
        sa.Column("agent", sa.String(100), nullable=False),
        sa.Column("input_summary", sa.String(2000), nullable=False),
        sa.Column("output_summary", sa.String(4000), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("token_usage", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error", sa.String(2000), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_mission_runs_mission_id", "mission_runs", ["mission_id"])


def downgrade() -> None:
    op.drop_table("mission_runs")
    op.drop_table("mission_items")
    op.drop_table("missions")
