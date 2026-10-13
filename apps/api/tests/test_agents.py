"""Comprehensive tests for GroundingValidator, WayfindingService, MissionWorkflow, and Mission API."""

import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient

from omnimission.agents.schemas import (
    OptimizedBasketItem,
)
from omnimission.agents.validator import GroundingValidator
from omnimission.agents.wayfinding import WayfindingService
from omnimission.agents.workflow import MissionWorkflow
from omnimission.db.session import async_session_factory
from omnimission.ports.search_backend import SearchResult
from omnimission.seed.data import STORE_BLR_INDIRANAGAR


def test_grounding_validator_enforces_tool_truth() -> None:
    """Ensure GroundingValidator forces price/aisle from DB tool hits and filters phantom items."""
    validator = GroundingValidator()
    store1 = uuid.uuid4()
    store2 = uuid.uuid4()
    prod1 = uuid.uuid4()
    prod2 = uuid.uuid4()
    prod_phantom = uuid.uuid4()

    tool_results = [
        SearchResult(
            product_id=prod1,
            name="Almond Milk Unsweetened 1L",
            brand="Raw Pressery",
            category="Dairy & Alternatives",
            price=Decimal("180.00"),
            mrp=Decimal("200.00"),
            stock_qty=15,
            aisle=2,
            bay=1,
            shelf=2,
            store_id=store1,
            score=0.95,
        ),
        SearchResult(
            product_id=prod2,
            name="Organic Rolled Oats 500g",
            brand="True Elements",
            category="Breakfast & Cereals",
            price=Decimal("175.00"),
            mrp=Decimal("199.00"),
            stock_qty=10,
            aisle=1,
            bay=2,
            shelf=1,
            store_id=store1,
            score=0.90,
        ),
    ]

    basket_candidates = [
        # Candidate with hallucinated price (₹500 instead of ₹180) and wrong aisle (9 instead of 2)
        OptimizedBasketItem(
            product_id=prod1,
            requested_label="almond milk",
            name="Hallucinated Milk Name",
            brand="Wrong Brand",
            quantity=2,
            unit_price=Decimal("500.00"),
            subtotal=Decimal("1000.00"),
            store_id=store1,
            store_name="Store 1",
            aisle=9,
            bay=9,
            shelf=9,
            status="matched",
        ),
        # Phantom candidate not present in tool hits
        OptimizedBasketItem(
            product_id=prod_phantom,
            requested_label="magic powder",
            name="Magic Powder",
            brand="Ghost Brand",
            quantity=1,
            unit_price=Decimal("999.00"),
            subtotal=Decimal("999.00"),
            store_id=store1,
            store_name="Store 1",
            aisle=1,
            bay=1,
            shelf=1,
            status="matched",
        ),
        # Candidate belonging to an unselected store
        OptimizedBasketItem(
            product_id=prod2,
            requested_label="rolled oats",
            name="Oats",
            brand="Brand",
            quantity=1,
            unit_price=Decimal("175.00"),
            subtotal=Decimal("175.00"),
            store_id=store2,  # Not in selected_store_ids!
            store_name="Store 2",
            aisle=1,
            bay=2,
            shelf=1,
            status="matched",
        ),
    ]

    validated = validator.validate_and_filter(
        basket_items=basket_candidates,
        tool_results=tool_results,
        selected_store_ids=[store1],
    )

    # Only prod1 in store1 should survive
    assert len(validated) == 1
    item = validated[0]
    assert item.product_id == prod1
    # Truth from SearchResult must be enforced
    assert item.unit_price == Decimal("180.00")
    assert item.aisle == 2
    assert item.bay == 1
    assert item.shelf == 2
    assert item.subtotal == Decimal("360.00")  # 2 * 180.00
    assert validator.calculate_total(validated) == Decimal("360.00")


def test_wayfinding_service_monotonic_ordering() -> None:
    """Ensure WayfindingService generates strictly monotonic aisle -> bay -> shelf paths."""
    service = WayfindingService()
    store_id = uuid.uuid4()

    items = [
        OptimizedBasketItem(
            product_id=uuid.uuid4(),
            requested_label="item3",
            name="Dark Chocolate",
            brand="Amul",
            quantity=1,
            unit_price=Decimal("150.00"),
            subtotal=Decimal("150.00"),
            store_id=store_id,
            store_name="Indiranagar",
            aisle=3,
            bay=1,
            shelf=2,
            status="matched",
        ),
        OptimizedBasketItem(
            product_id=uuid.uuid4(),
            requested_label="item1",
            name="Whole Wheat Bread",
            brand="The Baker's Dozen",
            quantity=1,
            unit_price=Decimal("65.00"),
            subtotal=Decimal("65.00"),
            store_id=store_id,
            store_name="Indiranagar",
            aisle=1,
            bay=1,
            shelf=1,
            status="matched",
        ),
        OptimizedBasketItem(
            product_id=uuid.uuid4(),
            requested_label="item2",
            name="Sourdough Loaf",
            brand="The Baker's Dozen",
            quantity=1,
            unit_price=Decimal("140.00"),
            subtotal=Decimal("140.00"),
            store_id=store_id,
            store_name="Indiranagar",
            aisle=1,
            bay=1,
            shelf=1,  # Same coordinate as Whole Wheat Bread
            status="matched",
        ),
    ]

    stops = service.generate_route(items, {store_id: "Indiranagar"})

    # Should consolidate items at (1, 1, 1) into 1 stop, total 2 stops
    assert len(stops) == 2
    stop1 = stops[0]
    assert stop1.stop_order == 1
    assert stop1.aisle == 1
    assert stop1.bay == 1
    assert stop1.shelf == 1
    assert "Whole Wheat Bread" in stop1.items
    assert "Sourdough Loaf" in stop1.items

    stop2 = stops[1]
    assert stop2.stop_order == 2
    assert stop2.aisle == 3
    assert stop2.bay == 1
    assert stop2.shelf == 2
    assert "Dark Chocolate" in stop2.items


@pytest.mark.asyncio
async def test_workflow_execution_and_persistence() -> None:
    """Test full multi-agent workflow streaming execution and database trace persistence."""
    workflow = MissionWorkflow()
    store_id = STORE_BLR_INDIRANAGAR

    async with async_session_factory() as session:
        # Create a test mission record
        from sqlalchemy import select

        from omnimission.models.mission import Mission
        from omnimission.models.user import User

        user_stmt = select(User).where(User.email == "shopper@omnimission.ai")
        user = (await session.execute(user_stmt)).scalar_one()

        test_mission = Mission(
            user_id=user.id,
            raw_text="party snacks for 6 people with chips, cola and cookies",
            selected_store_ids=[store_id],
            language="en",
            input_modalities=["text"],
            status="pending",
        )
        session.add(test_mission)
        await session.commit()
        await session.refresh(test_mission)

        events = []
        async for evt in workflow.execute_streaming(
            session=session,
            mission_id=test_mission.id,
            raw_prompt=test_mission.raw_text,
            selected_store_ids=[store_id],
            language="en",
        ):
            events.append(evt)

        assert len(events) >= 5
        steps = [e.step for e in events]
        assert "parsing_intent" in steps
        assert "complete" in steps

        # Check DB updates via repository with eager selectinload
        from omnimission.repositories.mission_repo import MissionRepository

        repo = MissionRepository()
        saved_mission = await repo.get_by_id(session, test_mission.id)
        assert saved_mission is not None
        assert saved_mission.status == "completed"
        assert saved_mission.total_cost is not None
        assert saved_mission.total_cost > Decimal("0.00")
        assert len(saved_mission.items) > 0
        assert len(saved_mission.traces) >= 4


@pytest.mark.asyncio
async def test_missions_api_lifecycle(client: AsyncClient) -> None:
    """Test mission API: create, get, list, edit quantity, and route."""
    # 1. Register a test shopper
    email = f"mission_shopper_{uuid.uuid4().hex[:6]}@example.com"
    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Password123!",
            "full_name": "Mission Tester",
            "role": "user",
        },
    )
    assert reg_resp.status_code == 201
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. POST /missions
    store_id = str(STORE_BLR_INDIRANAGAR)
    create_resp = await client.post(
        "/api/v1/missions",
        headers=headers,
        json={
            "prompt": "Eggless cake with good protein",
            "store_ids": [store_id],
            "language": "en",
        },
    )
    assert create_resp.status_code == 201
    mission_data = create_resp.json()
    mission_id = mission_data["id"]
    assert "stream_url" in mission_data

    # 3. GET /missions (list before execution)
    list_resp = await client.get("/api/v1/missions", headers=headers)
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] >= 1

    # 4. Trigger workflow directly to simulate streaming completion
    async with async_session_factory() as session:
        workflow = MissionWorkflow()
        m_uuid = uuid.UUID(mission_id)
        async for _ in workflow.execute_streaming(
            session=session,
            mission_id=m_uuid,
            raw_prompt="Eggless cake with good protein",
            selected_store_ids=[STORE_BLR_INDIRANAGAR],
        ):
            pass

    # 5. GET /missions/{id}
    detail_resp = await client.get(f"/api/v1/missions/{mission_id}", headers=headers)
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["status"] == "completed"
    assert len(detail["items"]) > 0
    assert len(detail["traces"]) >= 4

    first_item = detail["items"][0]
    first_item_id = first_item["id"]
    old_qty = first_item["quantity"]

    # 6. PATCH /missions/{id}/items/{item_id}
    new_qty = old_qty + 2
    patch_resp = await client.patch(
        f"/api/v1/missions/{mission_id}/items/{first_item_id}",
        headers=headers,
        json={"quantity": new_qty},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["quantity"] == new_qty

    # 7. GET /missions/{id}/route
    route_resp = await client.get(f"/api/v1/missions/{mission_id}/route", headers=headers)
    assert route_resp.status_code == 200
    route_data = route_resp.json()
    assert route_data["total_stops"] >= 1
    assert len(route_data["waypoints"]) >= 1
    assert route_data["waypoints"][0]["step_number"] == 1
