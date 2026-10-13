"""Add action_proposals table for merchant agent human-in-the-loop proposals.

Revision ID: 0010_action_proposals
Revises: 0009_mission_events
Create Date: 2026-10-13 19:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0010_action_proposals"
down_revision: str | None = "0009_mission_events"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "action_proposals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "store_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("stores.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "status", sa.String(length=30), nullable=False, server_default="pending_approval"
        ),
        sa.Column("decision_note", sa.String(length=500), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "decided_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_action_proposals_store_id", "action_proposals", ["store_id"])
    op.create_index("ix_action_proposals_action_type", "action_proposals", ["action_type"])
    op.create_index("ix_action_proposals_status", "action_proposals", ["status"])


def downgrade() -> None:
    op.drop_index("ix_action_proposals_status", table_name="action_proposals")
    op.drop_index("ix_action_proposals_action_type", table_name="action_proposals")
    op.drop_index("ix_action_proposals_store_id", table_name="action_proposals")
    op.drop_table("action_proposals")
