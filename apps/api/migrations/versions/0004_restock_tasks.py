"""Restock tasks migration

Revision ID: 0004_restock_tasks
Revises: 0003_missions_and_traces
Create Date: 2026-10-13 13:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_restock_tasks"
down_revision: str | None = "0003_missions_and_traces"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "restock_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "store_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("stores.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("aisle", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("bay", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("shelf", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("current_qty", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("recommended_qty", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("reason", sa.String(500), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("source", sa.String(50), nullable=False, server_default="shelf_audit"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_restock_tasks_store_id", "restock_tasks", ["store_id"])
    op.create_index("ix_restock_tasks_product_id", "restock_tasks", ["product_id"])
    op.create_index("ix_restock_tasks_status", "restock_tasks", ["status"])


def downgrade() -> None:
    op.drop_index("ix_restock_tasks_status", table_name="restock_tasks")
    op.drop_index("ix_restock_tasks_product_id", table_name="restock_tasks")
    op.drop_index("ix_restock_tasks_store_id", table_name="restock_tasks")
    op.drop_table("restock_tasks")
