"""Unit tests for Governed Tool Registry, Scope Binder, and execution auditing."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from omnimission.agents.tool_registry import (
    SideEffectLevel,
    ToolRegistry,
    ToolScope,
)
from omnimission.core.errors import ForbiddenError
from omnimission.core.principal import Principal


@pytest.fixture
def custom_registry() -> ToolRegistry:
    reg = ToolRegistry()

    def sample_shopper_read(query: str, session: AsyncSession | None = None) -> str:
        _ = session
        return f"result for {query}"

    def sample_shopper_write(
        product_id: str,
        quantity: int,
        cart_id: uuid.UUID | None = None,
        principal: Principal | None = None,
    ) -> dict[str, str]:
        _ = principal
        return {
            "status": "added",
            "product_id": product_id,
            "quantity": str(quantity),
            "cart_id": str(cart_id),
        }

    def sample_merchant_audit(store_id: str, session: AsyncSession | None = None) -> list[str]:
        _ = (store_id, session)
        return ["audit-1", "audit-2"]

    reg.register(
        name="sample_read",
        description="Read-only query tool",
        scope=ToolScope.SHOPPER,
        side_effect_level=SideEffectLevel.READ_ONLY,
        func=sample_shopper_read,
    )
    reg.register(
        name="sample_write",
        description="Cart write tool",
        scope=ToolScope.SHOPPER,
        side_effect_level=SideEffectLevel.IDEMPOTENT_WRITE,
        func=sample_shopper_write,
    )
    reg.register(
        name="sample_merchant_audit",
        description="Merchant audit tool",
        scope=ToolScope.MERCHANT,
        side_effect_level=SideEffectLevel.READ_ONLY,
        func=sample_merchant_audit,
    )
    return reg


@pytest.mark.asyncio
async def test_tool_registration_and_listing(custom_registry: ToolRegistry) -> None:
    all_tools = custom_registry.list_all()
    assert len(all_tools) == 3

    shopper_tools = custom_registry.list_all(scope=ToolScope.SHOPPER)
    assert len(shopper_tools) == 2
    assert {t.name for t in shopper_tools} == {"sample_read", "sample_write"}

    merchant_tools = custom_registry.list_all(scope=ToolScope.MERCHANT)
    assert len(merchant_tools) == 1
    assert merchant_tools[0].name == "sample_merchant_audit"


@pytest.mark.asyncio
async def test_scope_binding_and_permission_enforcement(
    custom_registry: ToolRegistry,
    db_session: AsyncSession,
) -> None:
    # 1. Guest / Shopper Principal
    guest_principal = Principal.create_guest(guest_session_id=uuid.uuid4())
    cart_id = uuid.uuid4()
    bound_guest = custom_registry.bind_scope(
        principal=guest_principal,
        session=db_session,
        cart_id=cart_id,
    )

    available = bound_guest.list_available_tools()
    assert len(available) == 2
    assert "sample_merchant_audit" not in {t.name for t in available}

    # Calling shopper read tool succeeds and records audit
    res1 = await bound_guest.execute_tool("sample_read", query="strawberry")
    assert res1 == "result for strawberry"
    assert len(bound_guest.audits) == 1
    assert bound_guest.audits[0].tool_name == "sample_read"
    assert bound_guest.audits[0].side_effect_level == SideEffectLevel.READ_ONLY
    assert bound_guest.audits[0].success is True

    # Calling shopper write tool injects cart_id and principal
    res2 = await bound_guest.execute_tool("sample_write", product_id="sku-123", quantity=2)
    assert res2["status"] == "added"
    assert res2["cart_id"] == str(cart_id)
    assert len(bound_guest.audits) == 2

    # Attempting to execute merchant tool raises ForbiddenError
    with pytest.raises(ForbiddenError) as exc_info:
        await bound_guest.execute_tool("sample_merchant_audit", store_id="store-1")
    assert "cannot execute merchant-scoped tool" in str(exc_info.value)


@pytest.mark.asyncio
async def test_merchant_principal_access(
    custom_registry: ToolRegistry,
    db_session: AsyncSession,
) -> None:
    merchant_principal = Principal.create_merchant(user_id=uuid.uuid4())
    bound_merchant = custom_registry.bind_scope(
        principal=merchant_principal,
        session=db_session,
    )

    available = bound_merchant.list_available_tools()
    assert len(available) == 3

    res = await bound_merchant.execute_tool("sample_merchant_audit", store_id="store-1")
    assert res == ["audit-1", "audit-2"]
    assert len(bound_merchant.audits) == 1
    assert bound_merchant.audits[0].success is True


@pytest.mark.asyncio
async def test_agno_tool_export_and_signatures(
    custom_registry: ToolRegistry,
    db_session: AsyncSession,
) -> None:
    guest_principal = Principal.create_guest(guest_session_id=uuid.uuid4())
    cart_id = uuid.uuid4()
    bound_guest = custom_registry.bind_scope(
        principal=guest_principal,
        session=db_session,
        cart_id=cart_id,
    )

    agno_tools = bound_guest.get_agno_tools()
    assert len(agno_tools) == 2

    tool_names = {f.__name__ for f in agno_tools}
    assert tool_names == {"sample_read", "sample_write"}

    # Injected dependencies (session, principal, cart_id) must NOT be in the Agno external signature
    import inspect

    write_fn = next(f for f in agno_tools if f.__name__ == "sample_write")
    sig = inspect.signature(write_fn)
    param_names = list(sig.parameters.keys())
    assert param_names == ["product_id", "quantity"]
    assert "cart_id" not in param_names
    assert "session" not in param_names
    assert "principal" not in param_names
