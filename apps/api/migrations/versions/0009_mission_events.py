"""Persisted mission events and guest session support for resumable SSE streaming

Revision ID: 0009_mission_events
Revises: 0008_user_memories
Create Date: 2026-10-13 19:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009_mission_events"
down_revision: str | None = "0008_user_memories"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Update missions table for guest support
    op.alter_column("missions", "user_id", nullable=True)
    op.add_column(
        "missions",
        sa.Column(
            "guest_session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("guest_sessions.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    op.create_index("ix_missions_guest_session_id", "missions", ["guest_session_id"])

    # 2. Create mission_events table
    op.create_table(
        "mission_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "mission_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("missions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sequence_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("mission_id", "sequence_id", name="uq_mission_sequence"),
    )
    op.create_index("ix_mission_events_mission_id", "mission_events", ["mission_id"])
    op.create_index("ix_mission_events_sequence_id", "mission_events", ["sequence_id"])
    op.create_index("ix_mission_events_event_type", "mission_events", ["event_type"])


def downgrade() -> None:
    op.drop_table("mission_events")
    op.drop_index("ix_missions_guest_session_id", table_name="missions")
    op.drop_column("missions", "guest_session_id")
    op.alter_column("missions", "user_id", nullable=False)
