"""User and guest transparent memory table

Revision ID: 0008_user_memories
Revises: 0007_guest_cart_order
Create Date: 2026-10-13 18:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008_user_memories"
down_revision: str | None = "0007_guest_cart_order"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_memories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "guest_session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("guest_sessions.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("memory_type", sa.String(50), nullable=False, server_default="preference"),
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column(
            "value",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("source", sa.String(50), nullable=False, server_default="user_explicit"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_user_memories_user_id", "user_memories", ["user_id"])
    op.create_index("ix_user_memories_guest_session_id", "user_memories", ["guest_session_id"])
    op.create_index("ix_user_memories_key", "user_memories", ["key"])
    op.create_index("ix_user_memories_memory_type", "user_memories", ["memory_type"])


def downgrade() -> None:
    op.drop_table("user_memories")
