"""Tests for Merchant Store Analyst, Guarded NL2SQL (SqlGuard), and HITL Action Proposals."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from omnimission.agents.sql_guard import SqlGuard, SqlGuardError
from omnimission.agents.store_analyst import StoreAnalystAgent
from omnimission.models.user import User
from omnimission.seed.data import STORE_BLR_INDIRANAGAR
from omnimission.services.action_proposal_service import ActionProposalService
from omnimission.services.briefing_service import DailyBriefingService


@pytest.fixture
def sql_guard() -> SqlGuard:
    return SqlGuard(max_limit=100, statement_timeout_ms=3000)


@pytest.fixture
def proposal_service() -> ActionProposalService:
    return ActionProposalService()


@pytest.fixture
def analyst_agent() -> StoreAnalystAgent:
    return StoreAnalystAgent()


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
async def merchant_user(db_session: AsyncSession) -> User:
    """Fetch existing seeded merchant user."""
    from sqlalchemy import select

    res = await db_session.execute(select(User).where(User.email == "merchant@omnimission.ai"))
    user = res.scalar_one_or_none()
    assert user is not None
    return user


def test_sql_guard_valid_select(sql_guard: SqlGuard) -> None:
    """Verify standard read-only select passes and limit is injected."""
    raw = f"SELECT product_name, stock_level FROM v_store_stock_overview WHERE store_id = '{STORE_BLR_INDIRANAGAR}'"
    sanitized = sql_guard.validate_and_sanitize(raw, allowed_store_ids=[STORE_BLR_INDIRANAGAR])
    assert "LIMIT 100" in sanitized
    assert "SELECT" in sanitized


def test_sql_guard_rewrites_excessive_limit(sql_guard: SqlGuard) -> None:
    """Verify limit > 100 is constrained to max_limit."""
    raw = f"SELECT product_name FROM v_store_stock_overview WHERE store_id = '{STORE_BLR_INDIRANAGAR}' LIMIT 500"
    sanitized = sql_guard.validate_and_sanitize(raw, allowed_store_ids=[STORE_BLR_INDIRANAGAR])
    assert "LIMIT 100" in sanitized


@pytest.mark.parametrize(
    "forbidden_sql",
    [
        "DELETE FROM store_inventory WHERE stock_level = 0",
        "INSERT INTO products (name) VALUES ('Hacked Product')",
        "UPDATE store_inventory SET stock_level = 999",
        "DROP TABLE stores CASCADE",
        "ALTER TABLE users DROP COLUMN email",
        "TRUNCATE TABLE orders",
    ],
)
def test_sql_guard_blocks_mutations(sql_guard: SqlGuard, forbidden_sql: str) -> None:
    """Verify mutation queries are blocked with SqlGuardError."""
    with pytest.raises(SqlGuardError):
        sql_guard.validate_and_sanitize(forbidden_sql)


@pytest.mark.parametrize(
    "sensitive_sql",
    [
        "SELECT email, password_hash FROM users",
        "SELECT session_token FROM guest_sessions",
        "SELECT token_hash FROM refresh_tokens",
    ],
)
def test_sql_guard_blocks_sensitive_tables(sql_guard: SqlGuard, sensitive_sql: str) -> None:
    """Verify PII and credential tables cannot be queried."""
    with pytest.raises(SqlGuardError, match="strictly forbidden"):
        sql_guard.validate_and_sanitize(sensitive_sql)


def test_sql_guard_enforces_store_scoping(sql_guard: SqlGuard) -> None:
    """Verify queries touching store-scoped tables must have store_id in where clause."""
    unscoped_sql = "SELECT * FROM store_inventory WHERE stock_level < 5"
    with pytest.raises(SqlGuardError, match="lacks a 'store_id' filter"):
        sql_guard.validate_and_sanitize(unscoped_sql, allowed_store_ids=[STORE_BLR_INDIRANAGAR])


@pytest.mark.asyncio
async def test_action_proposal_lifecycle(
    db_session: AsyncSession,
    proposal_service: ActionProposalService,
    merchant_user: User,
) -> None:
    """Test full HITL lifecycle: propose -> list -> approve / reject."""
    # 1. Propose restock
    p1 = await proposal_service.create_proposal(
        session=db_session,
        store_id=STORE_BLR_INDIRANAGAR,
        action_type="restock_inventory",
        title="Restock Amul Butter",
        description="Current stock is 2 units. Replenish 24 units.",
        payload={"recommended_qty": 24, "reason": "Low stock"},
        created_by=merchant_user.id,
    )
    assert p1.status == "pending_approval"

    # 2. List proposals
    proposals = await proposal_service.list_proposals(
        session=db_session,
        store_id=STORE_BLR_INDIRANAGAR,
        status="pending_approval",
    )
    assert len(proposals) >= 1
    assert any(p.id == p1.id for p in proposals)

    # 3. Approve proposal
    approved = await proposal_service.approve_proposal(
        session=db_session,
        proposal_id=p1.id,
        user_id=merchant_user.id,
        decision_note="Approved for morning delivery",
    )
    assert approved.status == "approved"
    assert approved.decided_by == merchant_user.id
    assert approved.decision_note == "Approved for morning delivery"

    # 4. Propose and reject another
    p2 = await proposal_service.create_proposal(
        session=db_session,
        store_id=STORE_BLR_INDIRANAGAR,
        action_type="update_stock",
        title="Manual Stock Override",
        description="Discrepancy audit",
        payload={"new_stock_level": 50},
        created_by=merchant_user.id,
    )
    rejected = await proposal_service.reject_proposal(
        session=db_session,
        proposal_id=p2.id,
        user_id=merchant_user.id,
        decision_note="Physical audit pending",
    )
    assert rejected.status == "rejected"
    assert rejected.decided_by == merchant_user.id


@pytest.mark.asyncio
async def test_store_analyst_low_stock_query(
    db_session: AsyncSession,
    analyst_agent: StoreAnalystAgent,
    merchant_user: User,
) -> None:
    """Test Store Analyst answering low stock query with chart data."""
    res = await analyst_agent.analyze(
        session=db_session,
        query="Which items have low stock?",
        store_id=STORE_BLR_INDIRANAGAR,
        merchant_id=merchant_user.id,
    )
    assert res.chart_config is not None
    assert res.chart_config.chart_type == "bar"
    assert res.chart_config.x_axis == "product_name"
    assert res.chart_config.y_axis == "stock_level"
    assert res.sql_query is not None
    assert "v_store_stock_overview" in res.sql_query
    assert isinstance(res.data, list)


@pytest.mark.asyncio
async def test_daily_briefing_generation(
    db_session: AsyncSession,
) -> None:
    """Test DailyBriefingService generating operational morning report."""
    service = DailyBriefingService()
    briefing = await service.generate_briefing(session=db_session, store_id=STORE_BLR_INDIRANAGAR)
    assert briefing.store_id == str(STORE_BLR_INDIRANAGAR)
    assert "Store Health" in briefing.headline
    assert "kpis" in briefing.model_dump()
    assert briefing.kpis["low_stock_skus"] >= 0


@pytest.mark.asyncio
async def test_merchant_analyst_api(
    client: AsyncClient,
    merchant_auth_headers: dict[str, str],
) -> None:
    """Test REST API endpoints for Store Analyst, Briefing, and Proposals."""
    # 1. Query Analyst
    res = await client.post(
        "/api/v1/merchant/analyst/query",
        json={
            "query": "Show me top selling items this week",
            "store_id": str(STORE_BLR_INDIRANAGAR),
        },
        headers=merchant_auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert "answer" in data
    assert "chart_config" in data
    assert data["chart_config"]["chart_type"] in ("bar", "table", "line", "pie")

    # 2. Get Daily Briefing
    b_res = await client.get(
        f"/api/v1/merchant/analyst/briefing?store_id={STORE_BLR_INDIRANAGAR}",
        headers=merchant_auth_headers,
    )
    assert b_res.status_code == 200
    b_data = b_res.json()
    assert "headline" in b_data
    assert "kpis" in b_data

    # 3. List and act on proposals
    p_res = await client.get(
        f"/api/v1/merchant/proposals?store_id={STORE_BLR_INDIRANAGAR}",
        headers=merchant_auth_headers,
    )
    assert p_res.status_code == 200
    proposals = p_res.json()
    assert isinstance(proposals, list)
