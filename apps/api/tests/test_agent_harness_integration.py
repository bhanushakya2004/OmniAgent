"""End-to-End integration test for Governed Agent Harness with CartAgent and Recipe-RAG."""

import uuid
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from omnimission.adapters.pg_hybrid_search import PgHybridSearch
from omnimission.agents.cart_agent import CartAgent
from omnimission.agents.concierge_router import ConciergeRouter, RouteType
from omnimission.agents.personalisation_agent import PersonalisationAgent
from omnimission.agents.planner_agent import PlannerAgentRunner
from omnimission.agents.schemas import OptimizedBasketItem
from omnimission.agents.validator import GroundingValidator
from omnimission.core.principal import Principal
from omnimission.models.store import Store
from omnimission.seed.data import STORE_BLR_INDIRANAGAR
from omnimission.services.cart_service import CartService
from omnimission.services.memory_service import MemoryService


@pytest.mark.asyncio
async def test_full_guest_recipe_to_cart_pipeline(db_session: AsyncSession) -> None:
    router = ConciergeRouter()
    planner = PlannerAgentRunner()
    search_adapter = PgHybridSearch()
    validator = GroundingValidator()
    cart_agent = CartAgent()
    personalisation = PersonalisationAgent()
    memory_service = MemoryService()

    # 1. Guest user asks for eggless strawberry cake for 8 people
    guest = Principal.create_guest(guest_session_id=uuid.uuid4())
    prompt = "I want everything needed to make an eggless strawberry cake for 8 people"

    # Save a transparent allergen exclusion preference for this guest
    await memory_service.set_memory(db_session, guest, "allergens", ["peanuts"])

    # 2. Concierge Router intent classification
    decision = await router.route(prompt)
    assert decision.route == RouteType.RECIPE_MISSION
    assert decision.target_agent == "recipe_planner"
    assert decision.extracted_entities.get("servings_or_people") == 8

    # 3. Personalisation enrichment
    from omnimission.agents.schemas import MissionIntent

    raw_intent = MissionIntent(
        goal_type="recipe",
        description=prompt,
        servings_or_people=decision.extracted_entities.get("servings_or_people"),
        dietary_tags=decision.extracted_entities.get("dietary_tags", []),
        excluded_items=[],
    )
    enriched_intent, notices = await personalisation.personalize_intent(
        session=db_session,
        principal=guest,
        intent=raw_intent,
    )
    assert "peanuts" in enriched_intent.excluded_items
    assert "eggless" in enriched_intent.dietary_tags

    # 4. Planner Agent expands items
    plan = await planner.plan_items(enriched_intent)
    assert len(plan.items) >= 5
    item_labels = [it.label for it in plan.items]
    assert any("strawberr" in lbl.lower() for lbl in item_labels)
    assert any("flour" in lbl.lower() or "maida" in lbl.lower() for lbl in item_labels)
    assert any("baking powder" in lbl.lower() for lbl in item_labels)

    # 5. Search Catalog across physical store inventory
    store_ids = [STORE_BLR_INDIRANAGAR]
    all_hits = []
    basket_candidates: list[OptimizedBasketItem] = []

    store_res = await db_session.get(Store, STORE_BLR_INDIRANAGAR)
    store_name = store_res.name if store_res else "Indiranagar Store"

    for planned_item in plan.items:
        hits = await search_adapter.search(
            session=db_session,
            query=planned_item.label,
            store_ids=store_ids,
            limit=3,
        )
        all_hits.extend(hits)
        in_stock = [h for h in hits if h.stock_qty > 0]
        if in_stock:
            best = in_stock[0]
            basket_candidates.append(
                OptimizedBasketItem(
                    product_id=best.product_id,
                    requested_label=planned_item.label,
                    name=best.name,
                    brand=best.brand,
                    quantity=planned_item.quantity,
                    unit_price=best.price,
                    subtotal=best.price * Decimal(planned_item.quantity),
                    store_id=best.store_id,
                    store_name=store_name,
                    aisle=best.aisle,
                    bay=best.bay,
                    shelf=best.shelf,
                    status="matched",
                    match_explanation=f"Aisle {best.aisle} Bay {best.bay}",
                )
            )

    # 6. Grounding Validator checks
    validated_basket = validator.validate_and_filter(
        basket_items=basket_candidates,
        tool_results=all_hits,
        selected_store_ids=store_ids,
    )
    assert len(validated_basket) >= 3

    # 7. CartAgent executes basket addition directly to guest cart
    cart_result = await cart_agent.add_basket_to_cart(
        session=db_session,
        principal=guest,
        basket_items=validated_basket,
    )

    assert cart_result.success is True
    assert cart_result.item_count >= 3
    assert cart_result.total_amount > Decimal("0.00")
    assert len(cart_result.added_items) == len(validated_basket)

    # 8. Verify Cart Service reads back the same verified cart
    cart_service = CartService()
    final_cart = await cart_service.get_or_create_cart(db_session, guest)
    assert final_cart.id == cart_result.cart_id
    assert len(final_cart.items) == len(validated_basket)
    assert float(final_cart.subtotal) == float(cart_result.total_amount)
