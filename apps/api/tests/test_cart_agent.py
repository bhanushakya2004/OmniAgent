"""Unit and integration tests for CartAgent grounded basket additions and cart mutations."""

import uuid
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from omnimission.adapters.toolbox_gateway import ToolboxGateway
from omnimission.agents.cart_agent import CartAgent
from omnimission.agents.schemas import OptimizedBasketItem
from omnimission.core.principal import Principal
from omnimission.seed.data import STORE_BLR_INDIRANAGAR


@pytest.fixture
def cart_agent() -> CartAgent:
    return CartAgent()


@pytest.fixture
def gateway() -> ToolboxGateway:
    return ToolboxGateway()


@pytest.mark.asyncio
async def test_add_basket_to_cart(
    db_session: AsyncSession,
    cart_agent: CartAgent,
    gateway: ToolboxGateway,
) -> None:
    # 1. Retrieve real seeded products from Indiranagar store
    flour_items = await gateway.search_store_inventory(STORE_BLR_INDIRANAGAR, "flour", 1)
    straw_items = await gateway.search_store_inventory(STORE_BLR_INDIRANAGAR, "strawberry", 1)
    assert len(flour_items) >= 1
    assert len(straw_items) >= 1

    p1 = flour_items[0]
    p2 = straw_items[0]

    # 2. Prepare Basket Items
    basket = [
        OptimizedBasketItem(
            product_id=p1["product_id"],
            requested_label="Flour",
            name=p1["product_name"],
            brand=p1["brand"],
            quantity=2,
            unit_price=Decimal(str(p1["price"])),
            subtotal=Decimal(str(p1["price"])) * 2,
            store_id=STORE_BLR_INDIRANAGAR,
            store_name="Nature's Basket Indiranagar",
            aisle=p1["aisle"],
            bay=p1["bay"],
            shelf=p1["shelf"],
            status="matched",
            match_explanation="Direct in-stock match",
        ),
        OptimizedBasketItem(
            product_id=p2["product_id"],
            requested_label="Strawberries",
            name=p2["product_name"],
            brand=p2["brand"],
            quantity=1,
            unit_price=Decimal(str(p2["price"])),
            subtotal=Decimal(str(p2["price"])),
            store_id=STORE_BLR_INDIRANAGAR,
            store_name="Nature's Basket Indiranagar",
            aisle=p2["aisle"],
            bay=p2["bay"],
            shelf=p2["shelf"],
            status="matched",
            match_explanation="Fresh produce section",
        ),
    ]

    guest = Principal.create_guest(guest_session_id=uuid.uuid4())

    # 3. Execute CartAgent basket addition
    result = await cart_agent.add_basket_to_cart(
        session=db_session,
        principal=guest,
        basket_items=basket,
    )

    expected_total = (Decimal(str(p1["price"])) * 2) + Decimal(str(p2["price"]))

    assert result.success is True
    assert result.item_count == 3
    assert result.total_amount == expected_total
    assert len(result.added_items) == 2
    assert len(result.skipped_items) == 0
    assert result.cart_id is not None


@pytest.mark.asyncio
async def test_cart_agent_atomic_actions(
    db_session: AsyncSession,
    cart_agent: CartAgent,
    gateway: ToolboxGateway,
) -> None:
    milk_items = await gateway.search_store_inventory(STORE_BLR_INDIRANAGAR, "milk", 1)
    assert len(milk_items) >= 1
    prod = milk_items[0]

    guest = Principal.create_guest(guest_session_id=uuid.uuid4())

    # 1. Action: ADD
    add_res = await cart_agent.execute_cart_action(
        session=db_session,
        principal=guest,
        action="add",
        product_id=str(prod["product_id"]),
        store_id=str(STORE_BLR_INDIRANAGAR),
        quantity=2,
    )
    assert add_res.success is True
    assert add_res.item_count == 2
    assert add_res.total_amount == Decimal(str(prod["price"])) * 2

    # 2. Action: VIEW
    view_res = await cart_agent.execute_cart_action(
        session=db_session,
        principal=guest,
        action="view",
    )
    assert view_res.item_count == 2
    assert len(view_res.added_items) == 1
    assert view_res.added_items[0].product_name == prod["product_name"]

    # 3. Action: CLEAR
    clear_res = await cart_agent.execute_cart_action(
        session=db_session,
        principal=guest,
        action="clear",
    )
    assert clear_res.success is True
    assert clear_res.item_count == 0
    assert clear_res.total_amount == Decimal("0.00")
