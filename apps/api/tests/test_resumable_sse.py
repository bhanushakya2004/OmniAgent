"""Tests for resumable Server-Sent Events (SSE) streaming and Last-Event-ID replay."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from omnimission.models.mission import Mission
from omnimission.seed.data import STORE_BLR_INDIRANAGAR
from omnimission.services.event_persistence_service import EventPersistenceService
from omnimission.services.mission_service import MissionService


@pytest.fixture
def event_persistence() -> EventPersistenceService:
    return EventPersistenceService()


@pytest.fixture
def mission_service() -> MissionService:
    return MissionService()


@pytest.mark.asyncio
async def test_event_persistence_monotonic_sequences(
    db_session: AsyncSession,
    event_persistence: EventPersistenceService,
) -> None:
    # 1. Create a guest session and mission
    import datetime

    from omnimission.models.commerce import GuestSession

    mission_id = uuid.uuid4()
    guest_session_id = uuid.uuid4()
    g_sess = GuestSession(
        id=guest_session_id,
        session_token=f"test_session_{guest_session_id.hex[:8]}",
        expires_at=datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1),
        properties={},
    )
    db_session.add(g_sess)

    mission = Mission(
        id=mission_id,
        guest_session_id=guest_session_id,
        raw_text="quick test mission",
        selected_store_ids=[STORE_BLR_INDIRANAGAR],
        status="in_progress",
    )
    db_session.add(mission)
    await db_session.commit()

    # 2. Record sequence of events
    e1 = await event_persistence.record_event(
        db_session, mission_id, "agent_thought", {"thought": "Analyzing request"}
    )
    e2 = await event_persistence.record_event(
        db_session, mission_id, "tool_call", {"tool": "search_catalog", "query": "cake"}
    )
    e3 = await event_persistence.record_event(
        db_session, mission_id, "tool_result", {"tool": "search_catalog", "hits": 5}
    )
    e4 = await event_persistence.record_event(
        db_session, mission_id, "mission_complete", {"total_cost": "250.00"}
    )
    await db_session.commit()

    assert e1.sequence_id == 1
    assert e2.sequence_id == 2
    assert e3.sequence_id == 3
    assert e4.sequence_id == 4

    # 3. Test replay filtering
    all_events = await event_persistence.get_events_after(db_session, mission_id, after_seq=0)
    assert len(all_events) == 4

    replayed_from_2 = await event_persistence.get_events_after(db_session, mission_id, after_seq=2)
    assert len(replayed_from_2) == 2
    assert replayed_from_2[0].sequence_id == 3
    assert replayed_from_2[0].event_type == "tool_result"
    assert replayed_from_2[1].sequence_id == 4
    assert replayed_from_2[1].event_type == "mission_complete"


@pytest.mark.asyncio
async def test_resumable_sse_stream_replay(
    client: AsyncClient,
    db_session: AsyncSession,
    event_persistence: EventPersistenceService,
) -> None:
    # 1. Create completed mission with 4 persisted events
    guest_session_id = f"guest_sse_{uuid.uuid4().hex[:8]}"
    headers = {"X-Guest-Session-ID": guest_session_id}

    mission_id = uuid.uuid4()
    g_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, guest_session_id)

    # Ensure guest session exists
    import datetime

    from omnimission.models.commerce import GuestSession

    g_sess = GuestSession(
        id=g_uuid,
        session_token=guest_session_id,
        expires_at=datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1),
        properties={},
    )
    db_session.add(g_sess)

    mission = Mission(
        id=mission_id,
        guest_session_id=g_uuid,
        raw_text="party snacks",
        selected_store_ids=[STORE_BLR_INDIRANAGAR],
        status="completed",
        total_cost=200,
    )
    db_session.add(mission)
    await db_session.commit()

    # Pre-populate 4 events
    for i in range(1, 5):
        await event_persistence.record_event(
            session=db_session,
            mission_id=mission_id,
            event_type="agent_thought" if i < 4 else "mission_complete",
            payload={"step": f"step_{i}", "detail": f"info {i}"},
        )
    await db_session.commit()

    # 2. First connection from start (Last-Event-ID not set)
    stream_url = f"/api/v1/missions/{mission_id}/stream"
    resp1 = await client.get(stream_url, headers=headers)
    assert resp1.status_code == 200
    body1 = resp1.text
    assert "id: 1" in body1
    assert "id: 2" in body1
    assert "id: 3" in body1
    assert "id: 4" in body1

    # 3. Reconnect with Last-Event-ID: 2 (Simulating drop after event 2)
    headers_resumed = {
        "X-Guest-Session-ID": guest_session_id,
        "Last-Event-ID": "2",
    }
    resp2 = await client.get(stream_url, headers=headers_resumed)
    assert resp2.status_code == 200
    body2 = resp2.text

    # Events 1 and 2 must NOT be re-sent
    assert "id: 1" not in body2
    assert "id: 2" not in body2

    # Events 3 and 4 MUST be present
    assert "id: 3" in body2
    assert "id: 4" in body2
    assert "mission_complete" in body2
