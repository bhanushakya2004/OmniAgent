"""Deterministic and idempotent seed data loader for OmniMission AI."""

import asyncio
import sys
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from omnimission.core.logging import get_logger, setup_logging
from omnimission.core.security import hash_password
from omnimission.db.session import async_session_factory
from omnimission.models.inventory import StoreInventory
from omnimission.models.product import Product
from omnimission.models.store import Store
from omnimission.models.user import User
from omnimission.seed.data import (
    CATALOG_ITEMS,
    DEMO_STORES,
    DEMO_USERS,
    STORE_BLR_INDIRANAGAR,
    STORE_BLR_KORAMANGALA,
    deterministic_uuid,
)


async def seed_database(session: AsyncSession) -> None:
    """Populate database with deterministic Indian retail accounts, stores, products, and inventory."""
    logger = get_logger("seed")
    logger.info("seed_database_started")

    # 1. Seed Users
    user_count = 0
    for u in DEMO_USERS:
        user_stmt = select(User).where(User.email == u["email"])
        existing_user = (await session.execute(user_stmt)).scalar_one_or_none()
        if existing_user is None:
            user = User(
                id=u["id"],
                email=u["email"],
                password_hash=hash_password(u["password"]),
                full_name=u["full_name"],
                role=u["role"],
                preferred_language=u["preferred_language"],
                is_active=True,
            )
            session.add(user)
            user_count += 1
    await session.flush()
    logger.info("users_seeded", count=user_count)

    # 2. Seed Stores
    store_count = 0
    for s in DEMO_STORES:
        store_stmt = select(Store).where(Store.id == s["id"])
        existing_store = (await session.execute(store_stmt)).scalar_one_or_none()
        if existing_store is None:
            store = Store(
                id=s["id"],
                merchant_id=s["merchant_id"],
                name=s["name"],
                address=s["address"],
                city=s["city"],
                lat=s["lat"],
                lng=s["lng"],
                phone=s["phone"],
                opening_hours=s["opening_hours"],
                is_active=s["is_active"],
            )
            session.add(store)
            store_count += 1
    await session.flush()
    logger.info("stores_seeded", count=store_count)

    # 3. Seed Products
    product_count = 0
    product_map: dict[str, Product] = {}
    for item in CATALOG_ITEMS:
        slug = item["slug"]
        p_id = deterministic_uuid(f"product:{slug}")
        prod_stmt = select(Product).where(Product.id == p_id)
        product = (await session.execute(prod_stmt)).scalar_one_or_none()

        if product is None:
            product = Product(
                id=p_id,
                name=item["name"],
                brand=item["brand"],
                description=item["description"],
                category=item["category"],
                subcategory=item["subcategory"],
                size_label=item["size_label"],
                is_travel_size=item["is_travel_size"],
                unit=item["unit"],
                dietary_tags=item["dietary_tags"],
                image_url=f"/images/products/{slug}.svg",
                tsv=func.to_tsvector(
                    "english",
                    f"{item['name']} {item['brand']} {item['description']} {item['category']}",
                ),
            )
            session.add(product)
            product_count += 1
        product_map[slug] = product

    await session.flush()
    logger.info("products_seeded", count=product_count)

    # 4. Seed Store Inventory with realistic stockout variations
    inv_count = 0
    for store_dict in DEMO_STORES:
        store_uuid = store_dict["id"]

        for item in CATALOG_ITEMS:
            slug = item["slug"]
            prod = product_map[slug]
            inv_stmt = select(StoreInventory).where(
                StoreInventory.store_id == store_uuid,
                StoreInventory.product_id == prod.id,
            )
            existing_inv = (await session.execute(inv_stmt)).scalar_one_or_none()
            if existing_inv is not None:
                continue

            # Deterministic inventory variations for demo scenarios
            stock_qty = 20
            price = Decimal(str(item["price"]))
            mrp = Decimal(str(item["mrp"]))

            # Indiranagar variations (Store 1)
            if store_uuid == STORE_BLR_INDIRANAGAR:
                if slug == "plant-protein-chocolate-500g":
                    stock_qty = 0  # Out of stock to force substitution or multi-store split!
                elif slug == "whey-protein-raw-1kg":
                    stock_qty = 14
                elif slug == "cocoa-powder-100g":
                    stock_qty = 9

            # Koramangala variations (Store 2)
            elif store_uuid == STORE_BLR_KORAMANGALA:
                if slug == "whey-protein-raw-1kg":
                    stock_qty = 0  # Out of stock in Koramangala!
                elif slug == "plant-protein-chocolate-500g":
                    stock_qty = 18  # In stock!
                elif slug == "cocoa-powder-100g":
                    stock_qty = 3  # Low stock threshold trigger

            inv = StoreInventory(
                id=deterministic_uuid(f"inventory:{store_uuid}:{prod.id}"),
                store_id=store_uuid,
                product_id=prod.id,
                sku=f"SKU-{slug[:8].upper()}-{store_uuid.hex[:4].upper()}",
                price=price,
                mrp=mrp,
                currency="INR",
                stock_qty=stock_qty,
                low_stock_threshold=5,
                aisle=item["aisle"],
                bay=item["bay"],
                shelf=item["shelf"],
            )
            session.add(inv)
            inv_count += 1

    await session.commit()
    logger.info("inventory_seeded", count=inv_count)
    logger.info("seed_database_completed")


async def main() -> None:
    """CLI entrypoint."""
    setup_logging()
    async with async_session_factory() as session:
        await seed_database(session)


if __name__ == "__main__":
    asyncio.run(main())
