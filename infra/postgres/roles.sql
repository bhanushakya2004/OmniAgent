-- Role and permissions for Google GenAI / MCP Toolbox for Databases
-- Enforces read-only principle with access granted strictly to curated views.

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

-- 1. Curated View: Store Inventory with joined Product & Store metadata
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

-- 2. Curated View: Product Details
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

-- 3. Curated View: Physical Aisle & Shelf Locations
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

-- 4. Curated View: Store Metadata
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

-- 5. Curated View: Dietary Substitutes
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

-- Grant permissions to toolbox_ro
GRANT CONNECT ON DATABASE omnimission TO toolbox_ro;
GRANT USAGE ON SCHEMA public TO toolbox_ro;
GRANT SELECT ON v_store_inventory TO toolbox_ro;
GRANT SELECT ON v_product_details TO toolbox_ro;
GRANT SELECT ON v_aisle_locations TO toolbox_ro;
GRANT SELECT ON v_store_details TO toolbox_ro;
GRANT SELECT ON v_dietary_substitutes TO toolbox_ro;
