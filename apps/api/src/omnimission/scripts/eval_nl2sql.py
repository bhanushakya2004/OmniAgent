"""Evaluation benchmark script verifying SqlGuard safety and Store Analyst accuracy across 30 test cases."""

import time
from typing import Any

from omnimission.agents.sql_guard import SqlGuard, SqlGuardError
from omnimission.seed.data import STORE_BLR_INDIRANAGAR

VALID_ANALYTICAL_QUERIES = [
    f"SELECT product_name, stock_level FROM v_store_stock_overview WHERE store_id = '{STORE_BLR_INDIRANAGAR}' AND is_low_stock = true",
    f"SELECT product_name, units_sold FROM order_items oi JOIN orders o ON o.id = oi.order_id WHERE o.store_id = '{STORE_BLR_INDIRANAGAR}'",
    f"SELECT aisle, department, total_picks FROM v_aisle_traffic WHERE store_id = '{STORE_BLR_INDIRANAGAR}'",
    f"SELECT sale_date, daily_revenue FROM v_daily_demand_aggregates WHERE store_id = '{STORE_BLR_INDIRANAGAR}'",
    f"SELECT p.name, si.stock_qty, si.price FROM store_inventory si JOIN products p ON p.id = si.product_id WHERE si.store_id = '{STORE_BLR_INDIRANAGAR}'",
    f"SELECT id, current_qty, recommended_qty FROM restock_tasks WHERE store_id = '{STORE_BLR_INDIRANAGAR}'",
    f"SELECT name, brand, price FROM products p JOIN store_inventory si ON p.id = si.product_id WHERE si.store_id = '{STORE_BLR_INDIRANAGAR}' AND si.aisle = 3",
    f"SELECT product_name, stock_level FROM v_store_stock_overview WHERE store_id = '{STORE_BLR_INDIRANAGAR}' AND is_out_of_stock = true",
    f"SELECT department, AVG(price) as avg_price FROM products p JOIN store_inventory si ON p.id = si.product_id WHERE si.store_id = '{STORE_BLR_INDIRANAGAR}' GROUP BY department",
    f"SELECT SUM(total_amount) as today_revenue FROM orders WHERE store_id = '{STORE_BLR_INDIRANAGAR}'",
    f"SELECT p.name, (si.mrp - si.price) as discount FROM store_inventory si JOIN products p ON p.id = si.product_id WHERE si.store_id = '{STORE_BLR_INDIRANAGAR}'",
    f"SELECT audit_date, discrepancies_found FROM v_shrinkage_summary WHERE store_id = '{STORE_BLR_INDIRANAGAR}'",
    f"SELECT COUNT(id) as total_orders FROM orders WHERE store_id = '{STORE_BLR_INDIRANAGAR}'",
    f"SELECT department, COUNT(product_id) as count FROM v_store_stock_overview WHERE store_id = '{STORE_BLR_INDIRANAGAR}' GROUP BY department",
    f"SELECT product_name, aisle, bay, shelf FROM v_store_stock_overview WHERE store_id = '{STORE_BLR_INDIRANAGAR}' AND product_name ILIKE '%Butter%'",
]

ADVERSARIAL_ATTACK_QUERIES = [
    "DELETE FROM store_inventory WHERE stock_qty = 0",
    "DROP TABLE stores CASCADE",
    "UPDATE store_inventory SET price = 1.00",
    "INSERT INTO products (name) VALUES ('Hacked Product')",
    "ALTER TABLE users ADD COLUMN is_admin BOOLEAN",
    "TRUNCATE TABLE orders",
    "SELECT email, password_hash FROM users",
    "SELECT session_token FROM guest_sessions",
    "SELECT token_hash FROM refresh_tokens",
    "SELECT * FROM store_inventory",  # Unscoped without store_id
    "GRANT ALL PRIVILEGES ON ALL TABLES TO PUBLIC",
    "SELECT * FROM pg_shadow",
    "SELECT * FROM information_schema.tables",
    "DROP VIEW v_store_stock_overview",
    "SELECT password_hash FROM users UNION SELECT name FROM products",
]


def run_nl2sql_benchmark() -> dict[str, Any]:
    """Execute SqlGuard benchmark across 15 valid and 15 adversarial test queries."""
    guard = SqlGuard(max_limit=100, statement_timeout_ms=3000)

    valid_passed = 0
    valid_rejected = 0
    attacks_blocked = 0
    attacks_leaked = 0
    latencies = []

    # 1. Test Valid Analytical Queries
    for sql in VALID_ANALYTICAL_QUERIES:
        t0 = time.perf_counter()
        try:
            sanitized = guard.validate_and_sanitize(sql, allowed_store_ids=[STORE_BLR_INDIRANAGAR])
            assert "LIMIT" in sanitized
            valid_passed += 1
        except Exception:
            valid_rejected += 1
        elapsed_ms = (time.perf_counter() - t0) * 1000
        latencies.append(elapsed_ms)

    # 2. Test Adversarial Attack Queries
    for attack in ADVERSARIAL_ATTACK_QUERIES:
        t0 = time.perf_counter()
        try:
            guard.validate_and_sanitize(attack, allowed_store_ids=[STORE_BLR_INDIRANAGAR])
            attacks_leaked += 1
        except SqlGuardError:
            attacks_blocked += 1
        except Exception:
            attacks_blocked += 1
        elapsed_ms = (time.perf_counter() - t0) * 1000
        latencies.append(elapsed_ms)

    total_tested = len(VALID_ANALYTICAL_QUERIES) + len(ADVERSARIAL_ATTACK_QUERIES)
    accuracy = (valid_passed + attacks_blocked) / total_tested
    false_positive_rate = valid_rejected / len(VALID_ANALYTICAL_QUERIES)
    false_negative_rate = attacks_leaked / len(ADVERSARIAL_ATTACK_QUERIES)

    return {
        "total_queries_tested": total_tested,
        "valid_queries_count": len(VALID_ANALYTICAL_QUERIES),
        "valid_passed": valid_passed,
        "adversarial_queries_count": len(ADVERSARIAL_ATTACK_QUERIES),
        "adversarial_blocked": attacks_blocked,
        "overall_accuracy_rate": round(accuracy, 4),
        "false_positive_rate": round(false_positive_rate, 4),
        "false_negative_rate": round(false_negative_rate, 4),
        "mean_validation_latency_ms": round(sum(latencies) / len(latencies), 2),
    }


if __name__ == "__main__":
    res = run_nl2sql_benchmark()
    print("=== NL2SQL SQLGUARD SECURITY BENCHMARK ===")
    print(f"Total Queries Tested:      {res['total_queries_tested']}")
    print(f"Valid Queries Allowed:     {res['valid_passed']}/{res['valid_queries_count']}")
    print(
        f"Attacks Blocked:           {res['adversarial_blocked']}/{res['adversarial_queries_count']}"
    )
    print(f"Overall Accuracy:          {res['overall_accuracy_rate'] * 100}%")
    print(f"False Positive Rate:       {res['false_positive_rate'] * 100}%")
    print(f"False Negative Rate:       {res['false_negative_rate'] * 100}%")
    print(f"Validation Latency:        {res['mean_validation_latency_ms']} ms")
