"""Unit tests for Concierge Router intent classification across shopper and merchant personas."""

import pytest

from omnimission.agents.concierge_router import ConciergeRouter, RouteType


@pytest.fixture
def router() -> ConciergeRouter:
    return ConciergeRouter()


@pytest.mark.asyncio
async def test_route_recipe_mission(router: ConciergeRouter) -> None:
    prompt = "I want everything needed to make an eggless strawberry cake for 8 people"
    decision = await router.route(prompt)

    assert decision.route == RouteType.RECIPE_MISSION
    assert decision.target_agent == "recipe_planner"
    assert decision.confidence >= 0.90
    assert decision.extracted_entities.get("servings_or_people") == 8
    assert "eggless" in decision.extracted_entities.get("dietary_tags", [])


@pytest.mark.asyncio
async def test_route_travel_mission(router: ConciergeRouter) -> None:
    prompt = (
        "I'm travelling to Mumbai for 4 days, I need travel-size shampoo, toothpaste, and sanitizer"
    )
    decision = await router.route(prompt)

    assert decision.route == RouteType.TRAVEL_MISSION
    assert decision.target_agent == "travel_planner"
    assert decision.confidence >= 0.90
    assert decision.extracted_entities.get("duration_days") == 4
    assert decision.extracted_entities.get("is_travel_size") is True


@pytest.mark.asyncio
async def test_route_party_mission(router: ConciergeRouter) -> None:
    prompt = "Hosting a weekend house party for 12 guests with chips, dip, and sodas"
    decision = await router.route(prompt)

    assert decision.route == RouteType.PARTY_MISSION
    assert decision.target_agent == "party_planner"
    assert decision.confidence >= 0.90
    assert decision.extracted_entities.get("servings_or_people") == 12


@pytest.mark.asyncio
async def test_route_cart_actions(router: ConciergeRouter) -> None:
    # Add to cart
    d1 = await router.route("Add all these items to my cart now")
    assert d1.route == RouteType.CART_ACTION
    assert d1.target_agent == "cart_agent"
    assert d1.extracted_entities.get("cart_action") == "add"

    # Clear cart
    d2 = await router.route("Empty my shopping cart")
    assert d2.route == RouteType.CART_ACTION
    assert d2.target_agent == "cart_agent"
    assert d2.extracted_entities.get("cart_action") == "clear"

    # View cart
    d3 = await router.route("Show me what is in my cart")
    assert d3.route == RouteType.CART_ACTION
    assert d3.target_agent == "cart_agent"
    assert d3.extracted_entities.get("cart_action") == "view"


@pytest.mark.asyncio
async def test_route_order_status(router: ConciergeRouter) -> None:
    prompt = "What is the delivery status for my order #10842?"
    decision = await router.route(prompt)

    assert decision.route == RouteType.ORDER_STATUS
    assert decision.target_agent == "order_agent"
    assert "10842" in str(decision.extracted_entities.get("order_id"))


@pytest.mark.asyncio
async def test_route_merchant_analytics(router: ConciergeRouter) -> None:
    # Shopper asking about operational metrics
    d1 = await router.route("Show me inventory shrinkage in bakery this month")
    assert d1.route == RouteType.MERCHANT_ANALYTICS
    assert d1.target_agent == "store_analyst"

    # Merchant dashboard context
    d2 = await router.route("Which products have stockout risk?", is_merchant_context=True)
    assert d2.route == RouteType.MERCHANT_ANALYTICS
    assert d2.target_agent == "store_analyst"


@pytest.mark.asyncio
async def test_route_general_faq(router: ConciergeRouter) -> None:
    prompt = "What is your return policy and what are store opening hours?"
    decision = await router.route(prompt)

    assert decision.route == RouteType.GENERAL_QA
    assert decision.target_agent == "knowledge_qa"


@pytest.mark.asyncio
async def test_route_catalog_search(router: ConciergeRouter) -> None:
    prompt = "Organic almond milk 1L carton"
    decision = await router.route(prompt)

    assert decision.route == RouteType.CATALOG_SEARCH
    assert decision.target_agent == "catalog_search"
    assert decision.confidence >= 0.80
