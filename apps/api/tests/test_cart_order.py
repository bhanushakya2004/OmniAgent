"""Integration tests for guest session carts, merging upon login, and simulated checkout."""

import uuid

import pytest
from httpx import AsyncClient

from omnimission.adapters.toolbox_gateway import ToolboxGateway
from omnimission.seed.data import STORE_BLR_INDIRANAGAR


@pytest.fixture
def gateway() -> ToolboxGateway:
    """Fixture providing ToolboxGateway."""
    return ToolboxGateway()


@pytest.mark.asyncio
async def test_guest_cart_lifecycle(client: AsyncClient, gateway: ToolboxGateway) -> None:
    """Verify anonymous guest can view empty cart, add items with price/aisle snapshot, and update qty."""
    guest_session_id = f"guest_test_{uuid.uuid4().hex[:8]}"
    headers = {"X-Guest-Session-ID": guest_session_id}

    # 1. Get initial empty cart
    resp = await client.get("/api/v1/cart", headers=headers)
    assert resp.status_code == 200
    cart = resp.json()
    assert cart["status"] == "active"
    assert cart["item_count"] == 0
    assert cart["total_amount"] == 0.0

    # 2. Find a product in Indiranagar store
    items = await gateway.search_store_inventory(STORE_BLR_INDIRANAGAR, "strawberry", 1)
    assert len(items) >= 1
    prod = items[0]

    # 3. Add item to cart
    add_resp = await client.post(
        "/api/v1/cart/items",
        headers=headers,
        json={
            "store_id": str(STORE_BLR_INDIRANAGAR),
            "product_id": str(prod["product_id"]),
            "qty": 2,
            "notes": "Fresh organic box",
        },
    )
    assert add_resp.status_code == 201
    updated_cart = add_resp.json()
    assert updated_cart["item_count"] == 2
    assert len(updated_cart["items"]) == 1
    cart_item = updated_cart["items"][0]
    assert cart_item["product_id"] == str(prod["product_id"])
    assert cart_item["qty"] == 2
    assert cart_item["unit_price"] == prod["price"]
    assert cart_item["aisle"] == prod["aisle"]
    assert cart_item["bay"] == prod["bay"]
    assert cart_item["shelf"] == prod["shelf"]

    # 4. Update quantity to 4
    item_id = cart_item["id"]
    patch_resp = await client.patch(
        f"/api/v1/cart/items/{item_id}",
        headers=headers,
        json={"qty": 4},
    )
    assert patch_resp.status_code == 200
    patched_cart = patch_resp.json()
    assert patched_cart["item_count"] == 4

    # 5. Remove item
    del_resp = await client.delete(
        f"/api/v1/cart/items/{item_id}",
        headers=headers,
    )
    assert del_resp.status_code == 200
    cleared_cart = del_resp.json()
    assert cleared_cart["item_count"] == 0


@pytest.mark.asyncio
async def test_merge_guest_cart_into_user_cart(
    client: AsyncClient, gateway: ToolboxGateway
) -> None:
    """Verify guest cart items are preserved and merged when shopper registers or logs in."""
    guest_session_id = f"guest_merge_{uuid.uuid4().hex[:8]}"
    guest_headers = {"X-Guest-Session-ID": guest_session_id}

    # 1. Add item as guest
    items = await gateway.search_store_inventory(STORE_BLR_INDIRANAGAR, "sugar", 1)
    assert len(items) >= 1
    prod = items[0]

    add_resp = await client.post(
        "/api/v1/cart/items",
        headers=guest_headers,
        json={
            "store_id": str(STORE_BLR_INDIRANAGAR),
            "product_id": str(prod["product_id"]),
            "qty": 3,
        },
    )
    assert add_resp.status_code == 201

    # 2. Get guest cart ID to find guest session UUID
    guest_cart = add_resp.json()
    assert guest_cart["item_count"] == 3

    # Query guest session id from database
    from sqlalchemy import select

    from omnimission.db.session import async_session_factory
    from omnimission.models.commerce import GuestSession

    async with async_session_factory() as session:
        gs_res = await session.execute(
            select(GuestSession).where(GuestSession.session_token == guest_session_id)
        )
        gs = gs_res.scalar_one()
        gs_id = gs.id

    # 3. Register a new user
    email = f"mergetest_{uuid.uuid4().hex[:8]}@example.com"
    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Password123!",
            "full_name": "Merge Shopper",
            "role": "user",
        },
    )
    assert reg_resp.status_code == 201
    auth_data = reg_resp.json()
    token = auth_data["access_token"]
    user_headers = {"Authorization": f"Bearer {token}"}

    # 4. Merge guest cart into user cart
    merge_resp = await client.post(
        "/api/v1/cart/merge",
        headers=user_headers,
        json={"guest_session_id": str(gs_id)},
    )
    assert merge_resp.status_code == 200
    merged = merge_resp.json()
    assert merged["item_count"] == 3
    assert merged["items"][0]["product_id"] == str(prod["product_id"])


@pytest.mark.asyncio
async def test_checkout_and_order_creation(client: AsyncClient, gateway: ToolboxGateway) -> None:
    """Verify authenticated user can checkout cart, creating placed order and simulated payment."""
    # 1. Register and get token
    email = f"order_{uuid.uuid4().hex[:8]}@example.com"
    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Password123!",
            "full_name": "Order Shopper",
            "role": "user",
        },
    )
    assert reg_resp.status_code == 201
    token = reg_resp.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # 2. Add product to cart
    items = await gateway.search_store_inventory(STORE_BLR_INDIRANAGAR, "milk", 1)
    assert len(items) >= 1
    prod = items[0]

    await client.post(
        "/api/v1/cart/items",
        headers=auth_headers,
        json={
            "store_id": str(STORE_BLR_INDIRANAGAR),
            "product_id": str(prod["product_id"]),
            "qty": 2,
        },
    )

    # 3. Checkout cart
    checkout_resp = await client.post(
        "/api/v1/orders/checkout",
        headers=auth_headers,
        json={
            "payment_method": "simulated_upi",
            "pickup_time_slot": "Today between 4 PM - 6 PM",
        },
    )
    assert checkout_resp.status_code == 201
    order = checkout_resp.json()
    assert order["status"] == "placed"
    assert order["payment_status"] == "simulated_paid"
    assert order["total_amount"] > 0.0
    assert "OMNI-" in order["order_number"]
    assert len(order["items"]) == 1
    assert order["items"][0]["qty"] == 2
    order_id = order["id"]

    # 4. Verify cart is now empty / new active cart
    cart_resp = await client.get("/api/v1/cart", headers=auth_headers)
    assert cart_resp.status_code == 200
    assert cart_resp.json()["item_count"] == 0

    # 5. List orders
    list_resp = await client.get("/api/v1/orders", headers=auth_headers)
    assert list_resp.status_code == 200
    orders = list_resp.json()
    assert len(orders) >= 1
    assert orders[0]["id"] == order_id

    # 6. Get order detail
    detail_resp = await client.get(f"/api/v1/orders/{order_id}", headers=auth_headers)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["order_number"] == order["order_number"]
