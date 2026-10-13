"""Comprehensive tests for Merchant Operations: stores, inventory, CSV batch import, analytics radar, shelf audits, and restock tasks."""

import pytest
from httpx import AsyncClient

from omnimission.seed.data import STORE_BLR_INDIRANAGAR


@pytest.fixture
async def merchant_auth_headers(client: AsyncClient) -> dict[str, str]:
    """Authenticate demo merchant and return authorization headers."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "merchant@omnimission.ai", "password": "Merchant123!"},
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def shopper_auth_headers(client: AsyncClient) -> dict[str, str]:
    """Authenticate demo shopper and return authorization headers."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "shopper@omnimission.ai", "password": "Shopper123!"},
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_merchant_stores_and_role_protection(
    client: AsyncClient,
    merchant_auth_headers: dict[str, str],
    shopper_auth_headers: dict[str, str],
) -> None:
    """Ensure GET /merchant/stores returns owned stores and forbids shopper role."""
    # 1. Shopper should be forbidden
    shopper_resp = await client.get("/api/v1/merchant/stores", headers=shopper_auth_headers)
    assert shopper_resp.status_code == 403
    assert shopper_resp.json()["code"] == "ROLE_NOT_AUTHORIZED"

    # 2. Merchant should succeed
    merchant_resp = await client.get("/api/v1/merchant/stores", headers=merchant_auth_headers)
    assert merchant_resp.status_code == 200
    stores = merchant_resp.json()
    assert len(stores) >= 1
    store_ids = [s["id"] for s in stores]
    assert str(STORE_BLR_INDIRANAGAR) in store_ids


@pytest.mark.asyncio
async def test_store_inventory_management(
    client: AsyncClient, merchant_auth_headers: dict[str, str]
) -> None:
    """Test inventory listing and updating stock count and aisle placement."""
    store_id = str(STORE_BLR_INDIRANAGAR)

    # 1. List inventory
    inv_resp = await client.get(
        f"/api/v1/merchant/inventory?store_id={store_id}", headers=merchant_auth_headers
    )
    assert inv_resp.status_code == 200
    items = inv_resp.json()
    assert len(items) >= 20

    first_item = items[0]
    inv_id = first_item["id"]
    old_stock = first_item["stock_qty"]

    # 2. Update inventory
    new_stock = old_stock + 15
    patch_resp = await client.patch(
        f"/api/v1/merchant/inventory/{inv_id}",
        headers=merchant_auth_headers,
        json={"stock_qty": new_stock, "aisle": 3, "bay": 2, "shelf": 1},
    )
    assert patch_resp.status_code == 200
    updated = patch_resp.json()
    assert updated["stock_qty"] == new_stock
    assert updated["aisle"] == 3
    assert updated["bay"] == 2
    assert updated["shelf"] == 1


@pytest.mark.asyncio
async def test_csv_batch_inventory_import(
    client: AsyncClient, merchant_auth_headers: dict[str, str]
) -> None:
    """Test multipart CSV batch upload with validation reporting."""
    store_id = str(STORE_BLR_INDIRANAGAR)

    csv_data = (
        "sku_slug,stock_qty,aisle,bay,shelf\n"
        "almond-flour-500g,45,2,1,2\n"
        "cocoa-powder-100g,60,1,2,1\n"
        "dark-chocolate-chips-200g,30,3,1,1\n"
    )

    files = {"file": ("inventory_batch.csv", csv_data.encode("utf-8"), "text/csv")}
    resp = await client.post(
        f"/api/v1/merchant/inventory/import?store_id={store_id}",
        headers=merchant_auth_headers,
        files=files,
    )
    assert resp.status_code == 200
    report = resp.json()
    assert report["total_rows"] == 3
    assert report["updated_count"] >= 1
    assert len(report["errors"]) == 0

    # Malformed CSV missing headers should fail
    bad_csv = "foo,bar,baz\n1,2,3\n"
    bad_files = {"file": ("bad.csv", bad_csv.encode("utf-8"), "text/csv")}
    bad_resp = await client.post(
        f"/api/v1/merchant/inventory/import?store_id={store_id}",
        headers=merchant_auth_headers,
        files=bad_files,
    )
    assert bad_resp.status_code == 400
    assert bad_resp.json()["code"] == "MISSING_CSV_COLUMNS"


@pytest.mark.asyncio
async def test_merchant_analytics_and_demand_signals(
    client: AsyncClient, merchant_auth_headers: dict[str, str]
) -> None:
    """Test operational overview KPIs and intent demand velocity."""
    store_id = str(STORE_BLR_INDIRANAGAR)

    # 1. Overview KPIs
    kpi_resp = await client.get(
        f"/api/v1/merchant/analytics/overview?store_id={store_id}",
        headers=merchant_auth_headers,
    )
    assert kpi_resp.status_code == 200
    kpis = kpi_resp.json()
    assert "total_missions" in kpis
    assert "total_grounded_gmv" in kpis
    assert "at_risk_skus_count" in kpis
    assert "open_restock_tasks_count" in kpis

    # 2. Demand Signals
    demand_resp = await client.get(
        f"/api/v1/merchant/analytics/demand?store_id={store_id}&limit=5",
        headers=merchant_auth_headers,
    )
    assert demand_resp.status_code == 200
    signals = demand_resp.json()
    assert len(signals) >= 1
    assert "query" in signals[0]
    assert "mention_count" in signals[0]
    assert "trending_score" in signals[0]


@pytest.mark.asyncio
async def test_shelf_audit_and_restock_task_lifecycle(
    client: AsyncClient, merchant_auth_headers: dict[str, str]
) -> None:
    """Test shelf audit photo execution, auto-drafting restock tasks, and task completion."""
    store_id = str(STORE_BLR_INDIRANAGAR)

    # 1. First upload a shelf photo
    valid_jpeg = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 200
    files = {"file": ("shelf_photo.jpg", valid_jpeg, "image/jpeg")}
    upload_resp = await client.post("/api/v1/uploads", headers=merchant_auth_headers, files=files)
    assert upload_resp.status_code == 201
    file_url = upload_resp.json()["file_url"]

    # 2. Run shelf audit
    audit_resp = await client.post(
        "/api/v1/merchant/shelf-audit",
        headers=merchant_auth_headers,
        json={"store_id": store_id, "file_url": file_url, "aisle": 1},
    )
    assert audit_resp.status_code == 200
    audit_data = audit_resp.json()
    assert audit_data["total_gaps_detected"] >= 1
    assert len(audit_data["findings"]) >= 1

    # 3. List drafted restock tasks
    tasks_resp = await client.get(
        f"/api/v1/merchant/restock-tasks?store_id={store_id}",
        headers=merchant_auth_headers,
    )
    assert tasks_resp.status_code == 200
    tasks = tasks_resp.json()
    assert len(tasks) >= 1

    task = tasks[0]
    task_id = task["id"]
    assert task["status"] == "pending"

    # 4. Approve task
    approve_resp = await client.patch(
        f"/api/v1/merchant/restock-tasks/{task_id}",
        headers=merchant_auth_headers,
        json={"status": "approved"},
    )
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "approved"

    # 5. Complete task
    complete_resp = await client.patch(
        f"/api/v1/merchant/restock-tasks/{task_id}",
        headers=merchant_auth_headers,
        json={"status": "completed"},
    )
    assert complete_resp.status_code == 200
    assert complete_resp.json()["status"] == "completed"
