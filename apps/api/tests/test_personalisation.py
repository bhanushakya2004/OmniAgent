"""Tests for transparent MemoryService, PersonalisationAgent, and memory REST endpoints."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from omnimission.agents.personalisation_agent import PersonalisationAgent
from omnimission.agents.schemas import MissionIntent
from omnimission.core.principal import Principal
from omnimission.services.memory_service import MemoryService


@pytest.fixture
def memory_service() -> MemoryService:
    return MemoryService()


@pytest.fixture
def personalisation_agent(memory_service: MemoryService) -> PersonalisationAgent:
    return PersonalisationAgent(memory_service=memory_service)


@pytest.mark.asyncio
async def test_memory_service_lifecycle(
    db_session: AsyncSession,
    memory_service: MemoryService,
) -> None:
    guest = Principal.create_guest(guest_session_id=uuid.uuid4())

    # 1. Set memories
    m1 = await memory_service.set_memory(
        session=db_session,
        principal=guest,
        key="diet",
        value="eggless",
        memory_type="dietary_preference",
    )
    assert m1.key == "diet"
    assert m1.value == {"val": "eggless"}

    await memory_service.set_memory(
        session=db_session,
        principal=guest,
        key="household_size",
        value=4,
        memory_type="household_preference",
    )
    await memory_service.set_memory(
        session=db_session,
        principal=guest,
        key="allergens",
        value=["peanuts", "tree_nuts"],
        memory_type="allergen_exclusion",
    )

    # 2. List memories
    all_memories = await memory_service.list_memories(db_session, guest)
    assert len(all_memories) == 3
    assert {m.key for m in all_memories} == {"diet", "household_size", "allergens"}

    # 3. Preference profile
    profile = await memory_service.get_preference_profile(db_session, guest)
    assert "eggless" in profile["dietary_tags"]
    assert profile["household_size"] == 4
    assert "peanuts" in profile["excluded_items"]

    # 4. Update memory in place
    m_updated = await memory_service.set_memory(
        session=db_session,
        principal=guest,
        key="household_size",
        value=6,
    )
    assert m_updated.id == all_memories[1].id or m_updated.key == "household_size"
    profile_updated = await memory_service.get_preference_profile(db_session, guest)
    assert profile_updated["household_size"] == 6

    # 5. Delete one memory
    del_res = await memory_service.delete_memory(db_session, guest, m1.id)
    assert del_res is True
    remaining = await memory_service.list_memories(db_session, guest)
    assert len(remaining) == 2

    # 6. Clear all memories
    cleared_count = await memory_service.clear_all_memories(db_session, guest)
    assert cleared_count >= 2
    after_clear = await memory_service.list_memories(db_session, guest)
    assert len(after_clear) == 0


@pytest.mark.asyncio
async def test_personalisation_agent_intent_enrichment(
    db_session: AsyncSession,
    memory_service: MemoryService,
    personalisation_agent: PersonalisationAgent,
) -> None:
    guest = Principal.create_guest(guest_session_id=uuid.uuid4())

    # Pre-seed transparent preferences
    await memory_service.set_memory(db_session, guest, "diet", "vegan")
    await memory_service.set_memory(db_session, guest, "household_size", 5)
    await memory_service.set_memory(db_session, guest, "allergens", ["mushrooms"])

    raw_intent = MissionIntent(
        goal_type="recipe",
        description="Dinner meal planning",
        servings_or_people=None,
        dietary_tags=[],
        excluded_items=[],
    )

    enriched_intent, notices = await personalisation_agent.personalize_intent(
        session=db_session,
        principal=guest,
        intent=raw_intent,
    )

    assert "vegan" in enriched_intent.dietary_tags
    assert enriched_intent.servings_or_people == 5
    assert "mushrooms" in enriched_intent.excluded_items
    assert len(notices) == 3


@pytest.mark.asyncio
async def test_personalisation_capture_explicit_statement(
    db_session: AsyncSession,
    personalisation_agent: PersonalisationAgent,
    memory_service: MemoryService,
) -> None:
    guest = Principal.create_guest(guest_session_id=uuid.uuid4())

    prompt = "Please remember that I am vegetarian for my household of 4 and allergic to peanuts."
    captured = await personalisation_agent.capture_explicit_preferences(
        session=db_session,
        principal=guest,
        text=prompt,
    )
    assert len(captured) >= 2

    profile = await memory_service.get_preference_profile(db_session, guest)
    assert "vegetarian" in profile["dietary_tags"]
    assert profile["household_size"] == 4


@pytest.mark.asyncio
async def test_memories_rest_api(client: AsyncClient) -> None:
    guest_session_id = f"guest_mem_{uuid.uuid4().hex[:8]}"
    headers = {"X-Guest-Session-ID": guest_session_id}

    # 1. Initial empty memories
    resp = await client.get("/api/v1/memories", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["memories"]) == 0

    # 2. Add preference
    post_resp = await client.post(
        "/api/v1/memories",
        headers=headers,
        json={"key": "diet", "value": "gluten_free", "memory_type": "dietary_preference"},
    )
    assert post_resp.status_code == 201
    mem_item = post_resp.json()
    assert mem_item["key"] == "diet"
    mem_id = mem_item["id"]

    # 3. Retrieve list showing new memory and compiled profile
    list_resp = await client.get("/api/v1/memories", headers=headers)
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert len(list_data["memories"]) == 1
    assert "gluten_free" in list_data["compiled_profile"]["dietary_tags"]

    # 4. Delete item
    del_resp = await client.delete(f"/api/v1/memories/{mem_id}", headers=headers)
    assert del_resp.status_code == 204

    # 5. Verify deletion
    verify_resp = await client.get("/api/v1/memories", headers=headers)
    assert len(verify_resp.json()["memories"]) == 0
