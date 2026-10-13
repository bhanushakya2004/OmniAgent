"""Merchant Operations API endpoints for inventory control, batch CSV import, analytics radar, and visual shelf audits."""

import uuid

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from omnimission.agents.shelf_audit_agent import ShelfAuditResult
from omnimission.core.deps import require_merchant
from omnimission.db.session import get_db_session
from omnimission.models.user import User
from omnimission.ports.analytics_sink import DemandSignal, StoreOverviewKpis
from omnimission.schemas.merchant import (
    CsvImportReport,
    MerchantInventoryItemResponse,
    MerchantStoreResponse,
    RestockTaskResponse,
    ShelfAuditRequest,
    UpdateInventoryRequest,
    UpdateRestockTaskRequest,
)
from omnimission.services.merchant_service import MerchantService

router = APIRouter(prefix="/merchant", tags=["merchant"])


def get_merchant_service() -> MerchantService:
    """Dependency provider for MerchantService."""
    return MerchantService()


@router.get(
    "/stores",
    response_model=list[MerchantStoreResponse],
    summary="List physical stores owned by merchant",
)
async def list_merchant_stores(
    current_user: User = Depends(require_merchant),
    session: AsyncSession = Depends(get_db_session),
    merchant_service: MerchantService = Depends(get_merchant_service),
) -> list[MerchantStoreResponse]:
    """Retrieve all physical retail locations registered to the merchant."""
    return await merchant_service.list_merchant_stores(
        session=session,
        merchant_id=current_user.id,
    )


@router.get(
    "/inventory",
    response_model=list[MerchantInventoryItemResponse],
    summary="List store inventory with shelf coordinates and stock levels",
)
async def list_store_inventory(
    store_id: uuid.UUID = Query(..., description="Store UUID"),
    current_user: User = Depends(require_merchant),
    session: AsyncSession = Depends(get_db_session),
    merchant_service: MerchantService = Depends(get_merchant_service),
) -> list[MerchantInventoryItemResponse]:
    """List inventory SKUs, stock counts, and Aisle/Bay/Shelf positions."""
    return await merchant_service.list_store_inventory(
        session=session,
        store_id=store_id,
        merchant_id=current_user.id,
    )


@router.patch(
    "/inventory/{inventory_id}",
    response_model=MerchantInventoryItemResponse,
    summary="Update SKU stock quantity, price, or shelf location",
)
async def update_inventory_item(
    inventory_id: uuid.UUID,
    request: UpdateInventoryRequest,
    current_user: User = Depends(require_merchant),
    session: AsyncSession = Depends(get_db_session),
    merchant_service: MerchantService = Depends(get_merchant_service),
) -> MerchantInventoryItemResponse:
    """Update stock quantity, active flag, or physical aisle coordinates."""
    return await merchant_service.update_inventory_item(
        session=session,
        inventory_id=inventory_id,
        merchant_id=current_user.id,
        request=request,
    )


@router.post(
    "/inventory/import",
    response_model=CsvImportReport,
    summary="Batch import or update inventory via CSV file",
)
async def import_inventory_csv(
    store_id: uuid.UUID = Query(..., description="Store UUID"),
    file: UploadFile = File(
        ..., description="CSV file with sku_slug, stock_qty, aisle, bay, shelf"
    ),
    current_user: User = Depends(require_merchant),
    session: AsyncSession = Depends(get_db_session),
    merchant_service: MerchantService = Depends(get_merchant_service),
) -> CsvImportReport:
    """Upload CSV inventory batch with atomic validation and error reporting."""
    content_bytes = await file.read()
    csv_text = content_bytes.decode("utf-8-sig", errors="replace")
    return await merchant_service.import_inventory_csv(
        session=session,
        store_id=store_id,
        merchant_id=current_user.id,
        csv_text=csv_text,
    )


@router.get(
    "/analytics/overview",
    response_model=StoreOverviewKpis,
    summary="Store KPI metrics (active missions, grounded GMV, at-risk SKUs)",
)
async def get_overview_kpis(
    store_id: uuid.UUID = Query(..., description="Store UUID"),
    current_user: User = Depends(require_merchant),
    session: AsyncSession = Depends(get_db_session),
    merchant_service: MerchantService = Depends(get_merchant_service),
) -> StoreOverviewKpis:
    """Get operational KPIs for merchant dashboard."""
    return await merchant_service.get_overview_kpis(
        session=session,
        store_id=store_id,
        merchant_id=current_user.id,
    )


@router.get(
    "/analytics/demand",
    response_model=list[DemandSignal],
    summary="Demand radar signals and unmet customer queries",
)
async def get_demand_signals(
    store_id: uuid.UUID = Query(..., description="Store UUID"),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(require_merchant),
    session: AsyncSession = Depends(get_db_session),
    merchant_service: MerchantService = Depends(get_merchant_service),
) -> list[DemandSignal]:
    """Get trending customer intents and out-of-stock substitution frequencies."""
    return await merchant_service.get_demand_signals(
        session=session,
        store_id=store_id,
        merchant_id=current_user.id,
        limit=limit,
    )


@router.post(
    "/shelf-audit",
    response_model=ShelfAuditResult,
    summary="Run AI shelf audit on uploaded photo and auto-draft restock tasks",
)
async def conduct_shelf_audit(
    request: ShelfAuditRequest,
    current_user: User = Depends(require_merchant),
    session: AsyncSession = Depends(get_db_session),
    merchant_service: MerchantService = Depends(get_merchant_service),
) -> ShelfAuditResult:
    """Inspect shelf photo, identify stock gaps against catalog, and draft replenishment tasks."""
    return await merchant_service.conduct_shelf_audit(
        session=session,
        store_id=request.store_id,
        merchant_id=current_user.id,
        file_url=request.file_url,
        aisle=request.aisle,
    )


@router.get(
    "/restock-tasks",
    response_model=list[RestockTaskResponse],
    summary="List replenishment restock tasks",
)
async def list_restock_tasks(
    store_id: uuid.UUID = Query(..., description="Store UUID"),
    current_user: User = Depends(require_merchant),
    session: AsyncSession = Depends(get_db_session),
    merchant_service: MerchantService = Depends(get_merchant_service),
) -> list[RestockTaskResponse]:
    """Retrieve restock replenishment tasks for store operations."""
    return await merchant_service.list_restock_tasks(
        session=session,
        store_id=store_id,
        merchant_id=current_user.id,
    )


@router.patch(
    "/restock-tasks/{task_id}",
    response_model=RestockTaskResponse,
    summary="Update restock task status (approved, completed, dismissed)",
)
async def update_restock_task(
    task_id: uuid.UUID,
    request: UpdateRestockTaskRequest,
    current_user: User = Depends(require_merchant),
    session: AsyncSession = Depends(get_db_session),
    merchant_service: MerchantService = Depends(get_merchant_service),
) -> RestockTaskResponse:
    """Approve or complete a replenishment restock task."""
    return await merchant_service.update_restock_task(
        session=session,
        task_id=task_id,
        merchant_id=current_user.id,
        new_status=request.status,
    )
