"""Merchant service implementing store inventory management, CSV batch import, demand analytics, shelf audits, and restock tasks."""

import csv
import io
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from omnimission.adapters.local_storage import LocalFsStorage
from omnimission.adapters.pg_analytics import PgAnalytics
from omnimission.agents.shelf_audit_agent import ShelfAuditAgentRunner, ShelfAuditResult
from omnimission.core.errors import BadRequestError, ForbiddenError, NotFoundError
from omnimission.models.inventory import StoreInventory
from omnimission.models.product import Product
from omnimission.models.restock_task import RestockTask
from omnimission.models.store import Store
from omnimission.ports.analytics_sink import DemandSignal, StoreOverviewKpis
from omnimission.schemas.merchant import (
    CsvImportReport,
    MerchantInventoryItemResponse,
    MerchantStoreResponse,
    RestockTaskResponse,
    UpdateInventoryRequest,
)


class MerchantService:
    """Business logic for merchant operational workflows."""

    def __init__(self) -> None:
        self.shelf_auditor = ShelfAuditAgentRunner()
        self.storage = LocalFsStorage()

    async def _verify_store_ownership(
        self, session: AsyncSession, store_id: uuid.UUID, merchant_id: uuid.UUID
    ) -> Store:
        """Verify merchant is the registered owner of the store."""
        store = await session.get(Store, store_id)
        if not store:
            raise NotFoundError(detail=f"Store {store_id} not found", code="STORE_NOT_FOUND")
        if store.merchant_id != merchant_id:
            raise ForbiddenError(
                detail="You do not have administrative access to this store", code="STORE_FORBIDDEN"
            )
        return store

    async def list_merchant_stores(
        self, session: AsyncSession, merchant_id: uuid.UUID
    ) -> list[MerchantStoreResponse]:
        """Fetch all physical store branches owned by the authenticated merchant."""
        stmt = (
            select(Store, func.count(StoreInventory.id))
            .outerjoin(StoreInventory, Store.id == StoreInventory.store_id)
            .where(Store.merchant_id == merchant_id)
            .group_by(Store.id)
            .order_by(Store.name)
        )
        rows = (await session.execute(stmt)).all()

        return [
            MerchantStoreResponse(
                id=store.id,
                name=store.name,
                address=store.address,
                city=store.city,
                lat=store.lat,
                lng=store.lng,
                is_active=store.is_active,
                total_skus=sku_count or 0,
            )
            for store, sku_count in rows
        ]

    async def list_store_inventory(
        self, session: AsyncSession, store_id: uuid.UUID, merchant_id: uuid.UUID
    ) -> list[MerchantInventoryItemResponse]:
        """Fetch real-time stock levels, pricing, and shelf placement for a store."""
        await self._verify_store_ownership(session, store_id, merchant_id)

        stmt = (
            select(StoreInventory)
            .options(selectinload(StoreInventory.product))
            .where(StoreInventory.store_id == store_id)
            .order_by(StoreInventory.aisle, StoreInventory.bay, StoreInventory.shelf)
        )
        items = (await session.execute(stmt)).scalars().all()

        results: list[MerchantInventoryItemResponse] = []
        for inv in items:
            if inv.stock_qty == 0:
                stock_status = "out_of_stock"
            elif inv.stock_qty <= inv.low_stock_threshold:
                stock_status = "low_stock"
            else:
                stock_status = "healthy"

            results.append(
                MerchantInventoryItemResponse(
                    id=inv.id,
                    store_id=inv.store_id,
                    product_id=inv.product_id,
                    product_name=inv.product.name if inv.product else inv.sku,
                    product_brand=inv.product.brand if inv.product else "",
                    category=inv.product.category if inv.product else "General",
                    sku=inv.sku,
                    price=inv.price,
                    mrp=inv.mrp,
                    stock_qty=inv.stock_qty,
                    low_stock_threshold=inv.low_stock_threshold,
                    aisle=inv.aisle,
                    bay=inv.bay,
                    shelf=inv.shelf,
                    is_active=inv.stock_qty > 0,
                    stock_status=stock_status,
                )
            )

        return results

    async def update_inventory_item(
        self,
        session: AsyncSession,
        inventory_id: uuid.UUID,
        merchant_id: uuid.UUID,
        request: UpdateInventoryRequest,
    ) -> MerchantInventoryItemResponse:
        """Update stock quantity, pricing, or shelf placement for a SKU."""
        stmt = (
            select(StoreInventory)
            .options(selectinload(StoreInventory.product), selectinload(StoreInventory.store))
            .where(StoreInventory.id == inventory_id)
        )
        inv = (await session.execute(stmt)).scalar_one_or_none()
        if not inv:
            raise NotFoundError(detail="Inventory record not found", code="INVENTORY_NOT_FOUND")

        if inv.store.merchant_id != merchant_id:
            raise ForbiddenError(
                detail="Unauthorized to update inventory for this store", code="FORBIDDEN"
            )

        if request.stock_qty is not None:
            inv.stock_qty = request.stock_qty
        if request.price is not None:
            inv.price = request.price
        if request.aisle is not None:
            inv.aisle = request.aisle
        if request.bay is not None:
            inv.bay = request.bay
        if request.shelf is not None:
            inv.shelf = request.shelf

        await session.commit()
        await session.refresh(inv)

        stock_status = (
            "out_of_stock"
            if inv.stock_qty == 0
            else "low_stock"
            if inv.stock_qty <= inv.low_stock_threshold
            else "healthy"
        )

        return MerchantInventoryItemResponse(
            id=inv.id,
            store_id=inv.store_id,
            product_id=inv.product_id,
            product_name=inv.product.name if inv.product else inv.sku,
            product_brand=inv.product.brand if inv.product else "",
            category=inv.product.category if inv.product else "General",
            sku=inv.sku,
            price=inv.price,
            mrp=inv.mrp,
            stock_qty=inv.stock_qty,
            low_stock_threshold=inv.low_stock_threshold,
            aisle=inv.aisle,
            bay=inv.bay,
            shelf=inv.shelf,
            is_active=inv.stock_qty > 0,
            stock_status=stock_status,
        )

    async def import_inventory_csv(
        self,
        session: AsyncSession,
        store_id: uuid.UUID,
        merchant_id: uuid.UUID,
        csv_text: str,
    ) -> CsvImportReport:
        """Parse and validate batch CSV inventory upload."""
        await self._verify_store_ownership(session, store_id, merchant_id)

        reader = csv.DictReader(io.StringIO(csv_text.strip()))
        if not reader.fieldnames:
            raise BadRequestError(detail="CSV file contains no headers", code="MALFORMED_CSV")

        # Allow either sku_slug or sku
        col_names = set(reader.fieldnames)
        has_id_col = "sku_slug" in col_names or "sku" in col_names or "product_name" in col_names
        has_other_cols = {"stock_qty", "aisle", "bay", "shelf"}.issubset(col_names)

        if not has_id_col or not has_other_cols:
            raise BadRequestError(
                detail="CSV must contain columns: 'sku' (or 'sku_slug'), 'stock_qty', 'aisle', 'bay', 'shelf'",
                code="MISSING_CSV_COLUMNS",
            )

        total_rows = 0
        imported_count = 0
        updated_count = 0
        errors: list[dict[str, Any]] = []

        for row_idx, row in enumerate(reader, start=2):
            total_rows += 1
            identifier = (
                row.get("sku_slug") or row.get("sku") or row.get("product_name") or ""
            ).strip()
            try:
                stock_qty = int(row.get("stock_qty", 0))
                aisle = int(row.get("aisle", 1))
                bay = int(row.get("bay", 1))
                shelf = int(row.get("shelf", 1))
            except ValueError as val_err:
                errors.append(
                    {"line": row_idx, "error": f"Numeric parse error: {val_err}", "row": row}
                )
                continue

            # Look up product by deterministic uuid or name/SKU
            from omnimission.seed.data import deterministic_uuid

            p_id = deterministic_uuid(f"product:{identifier}")
            prod = await session.get(Product, p_id)

            if not prod:
                # Try matching Product by name or StoreInventory by SKU
                prod_stmt = select(Product).where(
                    Product.name.ilike(f"%{identifier.replace('-', ' ')}%")
                )
                prod = (await session.execute(prod_stmt)).scalars().first()

            if not prod:
                # Try matching words from identifier in product name
                words = [w for w in identifier.replace("-", " ").split() if len(w) > 3]
                for word in words:
                    prod_stmt = select(Product).where(Product.name.ilike(f"%{word}%"))
                    prod = (await session.execute(prod_stmt)).scalars().first()
                    if prod:
                        break

            if not prod:
                # Try matching by SKU on store inventory
                inv_by_sku_stmt = (
                    select(StoreInventory)
                    .options(selectinload(StoreInventory.product))
                    .where(
                        StoreInventory.store_id == store_id,
                        StoreInventory.sku.ilike(f"%{identifier}%"),
                    )
                )
                inv_by_sku = (await session.execute(inv_by_sku_stmt)).scalar_one_or_none()
                if inv_by_sku:
                    inv_by_sku.stock_qty = stock_qty
                    inv_by_sku.aisle = aisle
                    inv_by_sku.bay = bay
                    inv_by_sku.shelf = shelf
                    updated_count += 1
                    continue

                errors.append(
                    {
                        "line": row_idx,
                        "error": f"Product '{identifier}' not found in catalog",
                        "row": row,
                    }
                )
                continue

            # Check existing store inventory for this product
            inv_stmt = select(StoreInventory).where(
                StoreInventory.store_id == store_id, StoreInventory.product_id == prod.id
            )
            inv = (await session.execute(inv_stmt)).scalar_one_or_none()

            if inv:
                inv.stock_qty = stock_qty
                inv.aisle = aisle
                inv.bay = bay
                inv.shelf = shelf
                updated_count += 1
            else:
                new_inv = StoreInventory(
                    store_id=store_id,
                    product_id=prod.id,
                    sku=f"SKU-{identifier[:8].upper()}-{store_id.hex[:4].upper()}",
                    price=Decimal("150.00"),
                    mrp=Decimal("180.00"),
                    stock_qty=stock_qty,
                    aisle=aisle,
                    bay=bay,
                    shelf=shelf,
                )
                session.add(new_inv)
                imported_count += 1

        await session.commit()

        return CsvImportReport(
            total_rows=total_rows,
            imported_count=imported_count,
            updated_count=updated_count,
            errors=errors,
        )

    async def get_overview_kpis(
        self, session: AsyncSession, store_id: uuid.UUID, merchant_id: uuid.UUID
    ) -> StoreOverviewKpis:
        """Query store overview KPIs."""
        await self._verify_store_ownership(session, store_id, merchant_id)
        sink = PgAnalytics(session)
        return await sink.get_overview_kpis(store_id)

    async def get_demand_signals(
        self, session: AsyncSession, store_id: uuid.UUID, merchant_id: uuid.UUID, limit: int = 10
    ) -> list[DemandSignal]:
        """Query demand velocity signals."""
        await self._verify_store_ownership(session, store_id, merchant_id)
        sink = PgAnalytics(session)
        return await sink.get_demand_signals(store_id, limit=limit)

    async def conduct_shelf_audit(
        self,
        session: AsyncSession,
        store_id: uuid.UUID,
        merchant_id: uuid.UUID,
        file_url: str,
        aisle: int = 1,
    ) -> ShelfAuditResult:
        """Run vision shelf audit and auto-draft replenishment tasks."""
        await self._verify_store_ownership(session, store_id, merchant_id)

        # Retrieve photo bytes from local storage
        raw_filename = Path(file_url).name
        photo_bytes = await self.storage.get(raw_filename)
        if not photo_bytes:
            raise NotFoundError(
                detail=f"Shelf audit photo '{raw_filename}' not found", code="FILE_NOT_FOUND"
            )

        audit_result = await self.shelf_auditor.audit_shelf(
            session=session,
            store_id=store_id,
            image_bytes=photo_bytes,
            aisle=aisle,
        )

        # Automatically draft RestockTasks for findings
        for finding in audit_result.findings:
            task = RestockTask(
                store_id=store_id,
                product_id=finding.product_id,
                aisle=finding.aisle,
                bay=finding.bay,
                shelf=finding.shelf,
                current_qty=finding.current_qty_estimate,
                recommended_qty=finding.recommended_qty,
                reason=finding.reason,
                status="pending",
                source="shelf_audit",
            )
            session.add(task)

        await session.commit()
        return audit_result

    async def list_restock_tasks(
        self, session: AsyncSession, store_id: uuid.UUID, merchant_id: uuid.UUID
    ) -> list[RestockTaskResponse]:
        """List replenishment restock tasks for a store."""
        await self._verify_store_ownership(session, store_id, merchant_id)

        stmt = (
            select(RestockTask)
            .options(selectinload(RestockTask.product))
            .where(RestockTask.store_id == store_id)
            .order_by(RestockTask.created_at.desc())
        )
        tasks = (await session.execute(stmt)).scalars().all()

        return [
            RestockTaskResponse(
                id=t.id,
                store_id=t.store_id,
                product_id=t.product_id,
                product_name=t.product.name if t.product else "SKU Item",
                aisle=t.aisle,
                bay=t.bay,
                shelf=t.shelf,
                current_qty=t.current_qty,
                recommended_qty=t.recommended_qty,
                reason=t.reason,
                status=t.status,
                source=t.source,
                created_at=t.created_at,
            )
            for t in tasks
        ]

    async def update_restock_task(
        self,
        session: AsyncSession,
        task_id: uuid.UUID,
        merchant_id: uuid.UUID,
        new_status: str,
    ) -> RestockTaskResponse:
        """Update replenishment task status (approved, completed, dismissed)."""
        stmt = (
            select(RestockTask)
            .options(selectinload(RestockTask.product), selectinload(RestockTask.store))
            .where(RestockTask.id == task_id)
        )
        task = (await session.execute(stmt)).scalar_one_or_none()
        if not task:
            raise NotFoundError(detail="Restock task not found", code="TASK_NOT_FOUND")

        if task.store.merchant_id != merchant_id:
            raise ForbiddenError(
                detail="Unauthorized access to this restock task", code="FORBIDDEN"
            )

        task.status = new_status

        # If completed, increment the inventory stock!
        if new_status == "completed":
            inv_stmt = select(StoreInventory).where(
                StoreInventory.store_id == task.store_id,
                StoreInventory.product_id == task.product_id,
            )
            inv = (await session.execute(inv_stmt)).scalar_one_or_none()
            if inv:
                inv.stock_qty += task.recommended_qty

        await session.commit()
        await session.refresh(task)

        return RestockTaskResponse(
            id=task.id,
            store_id=task.store_id,
            product_id=task.product_id,
            product_name=task.product.name if task.product else "SKU Item",
            aisle=task.aisle,
            bay=task.bay,
            shelf=task.shelf,
            current_qty=task.current_qty,
            recommended_qty=task.recommended_qty,
            reason=task.reason,
            status=task.status,
            source=task.source,
            created_at=task.created_at,
        )
