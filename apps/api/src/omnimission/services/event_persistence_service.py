"""Event persistence service for monotonic sequence recording and SSE replay."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from omnimission.core.logging import get_logger
from omnimission.models.mission import MissionEvent

logger = get_logger("event_persistence")


class EventPersistenceService:
    """Manages ordered persistence of SSE timeline events and replay for reconnection."""

    async def record_event(
        self,
        session: AsyncSession,
        mission_id: uuid.UUID,
        event_type: str,
        payload: dict[str, Any],
    ) -> MissionEvent:
        """Atomically assign the next monotonic sequence_id and persist the mission event."""
        import json

        json_safe_payload = json.loads(json.dumps(payload, default=str))

        # Compute next sequence_id for this mission
        seq_stmt = select(func.coalesce(func.max(MissionEvent.sequence_id), 0)).where(
            MissionEvent.mission_id == mission_id
        )
        current_max = (await session.execute(seq_stmt)).scalar() or 0
        next_seq = current_max + 1

        event = MissionEvent(
            mission_id=mission_id,
            sequence_id=next_seq,
            event_type=event_type,
            payload=json_safe_payload,
        )
        session.add(event)
        await session.flush()
        return event

    async def get_events_after(
        self,
        session: AsyncSession,
        mission_id: uuid.UUID,
        after_seq: int = 0,
    ) -> list[MissionEvent]:
        """Fetch all historical events with sequence_id > after_seq in ascending order."""
        stmt = (
            select(MissionEvent)
            .where(
                MissionEvent.mission_id == mission_id,
                MissionEvent.sequence_id > after_seq,
            )
            .order_by(MissionEvent.sequence_id.asc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def format_sse_frame(
        self,
        event: MissionEvent,
    ) -> str:
        """Format a single event into standard W3C Server-Sent Event frame format."""
        import json

        data_json = json.dumps(event.payload, ensure_ascii=False)
        return f"id: {event.sequence_id}\nevent: {event.event_type}\ndata: {data_json}\n\n"
