"""Toolbox views and read-only role migration

Revision ID: 0005_toolbox_views_and_roles
Revises: 0004_restock_tasks
Create Date: 2026-10-13 14:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0005_toolbox_views_and_roles"
down_revision: str | None = "0004_restock_tasks"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create curated views for agent read-only tools
    op.execute(
        """
        CREATE OR REPLACE VIEW v_store_inventory AS
        SELECT
            si.id AS inventory_id,
            si.store_id,
            s.name AS store_name,
            p.id AS product_id,
            si.sku,
            p.name AS product_name,
            p.brand,
            p.category,
            p.subcategory,
            p.size_label,
            p.unit,
            p.dietary_tags,
            p.is_travel_size,
            si.stock_qty,
            si.price,
            si.mrp,
            si.currency,
            si.aisle,
            si.bay,
            si.shelf
        FROM store_inventory si
        JOIN products p ON si.product_id = p.id
        JOIN stores s ON si.store_id = s.id;
        """
    )

    op.execute(
        """
        CREATE OR REPLACE VIEW v_product_details AS
        SELECT
            p.id AS product_id,
            p.name AS product_name,
            p.brand,
            p.description,
            p.category,
            p.subcategory,
            p.size_label,
            p.unit,
            p.is_travel_size,
            p.dietary_tags,
            p.image_url
        FROM products p;
        """
    )

    op.execute(
        """
        CREATE OR REPLACE VIEW v_aisle_locations AS
        SELECT
            si.store_id,
            s.name AS store_name,
            p.id AS product_id,
            si.sku,
            p.name AS product_name,
            p.brand,
            si.aisle,
            si.bay,
            si.shelf,
            si.stock_qty,
            si.price
        FROM store_inventory si
        JOIN products p ON si.product_id = p.id
        JOIN stores s ON si.store_id = s.id;
        """
    )

    op.execute(
        """
        CREATE OR REPLACE VIEW v_store_details AS
        SELECT
            id AS store_id,
            merchant_id,
            name AS store_name,
            address,
            city,
            lat,
            lng,
            phone,
            opening_hours,
            is_active
        FROM stores;
        """
    )

    op.execute(
        """
        CREATE OR REPLACE VIEW v_dietary_substitutes AS
        SELECT
            si.store_id,
            p.id AS product_id,
            si.sku,
            p.name AS product_name,
            p.brand,
            p.category,
            p.subcategory,
            p.dietary_tags,
            si.stock_qty,
            si.price,
            si.aisle,
            si.bay,
            si.shelf
        FROM store_inventory si
        JOIN products p ON si.product_id = p.id
        WHERE si.stock_qty > 0;
        """
    )

    # 2. Setup toolbox_ro role safely if permission permits
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'toolbox_ro') THEN
                BEGIN
                    CREATE ROLE toolbox_ro WITH LOGIN PASSWORD 'toolbox_ro_secret';
                EXCEPTION WHEN duplicate_object THEN
                    NULL;
                END;
            END IF;
        END
        $$;
        """
    )

    # Grant select on views
    op.execute(
        """
        DO $$
        BEGIN
            BEGIN
                GRANT USAGE ON SCHEMA public TO toolbox_ro;
                GRANT SELECT ON v_store_inventory TO toolbox_ro;
                GRANT SELECT ON v_product_details TO toolbox_ro;
                GRANT SELECT ON v_aisle_locations TO toolbox_ro;
                GRANT SELECT ON v_store_details TO toolbox_ro;
                GRANT SELECT ON v_dietary_substitutes TO toolbox_ro;
            EXCEPTION WHEN undefined_object THEN
                NULL;
            END;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS v_dietary_substitutes;")
    op.execute("DROP VIEW IF EXISTS v_store_details;")
    op.execute("DROP VIEW IF EXISTS v_aisle_locations;")
    op.execute("DROP VIEW IF EXISTS v_product_details;")
    op.execute("DROP VIEW IF EXISTS v_store_inventory;")
