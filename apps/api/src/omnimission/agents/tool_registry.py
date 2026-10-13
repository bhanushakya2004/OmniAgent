"""Governed Tool Registry with permission scoping and side-effect levels.

Provides typed, scoped tool definitions for Agno agents, enforcing:
1. Scope boundaries (shopper vs merchant vs admin) based on caller Principal.
2. Side-effect classification (read_only, idempotent_write, destructive).
3. Secure context binding (session, principal, cart_id, store_ids) to prevent parameter tampering.
4. Telemetry and audit logging for the Agent Inspector.
"""

from __future__ import annotations

import enum
import inspect
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from omnimission.core.errors import ForbiddenError
from omnimission.core.logging import get_logger
from omnimission.core.principal import Principal

logger = get_logger("tool_registry")


class SideEffectLevel(enum.StrEnum):
    """Classification of tool action consequences."""

    READ_ONLY = "read_only"
    IDEMPOTENT_WRITE = "idempotent_write"
    DESTRUCTIVE = "destructive"


class ToolScope(enum.StrEnum):
    """Permission scope required to execute a tool."""

    SHOPPER = "shopper"
    MERCHANT = "merchant"
    ADMIN = "admin"
    SYSTEM = "system"


@dataclass
class ToolExecutionAudit:
    """Telemetry record of a single tool execution."""

    tool_name: str
    side_effect_level: SideEffectLevel
    scope: ToolScope
    duration_ms: int
    success: bool
    error: str | None = None
    input_summary: str = ""
    output_summary: str = ""


@dataclass
class ToolDefinition:
    """Governed specification for an agent-callable tool."""

    name: str
    description: str
    scope: ToolScope
    side_effect_level: SideEffectLevel
    func: Callable[..., Any]
    parameters_schema: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.parameters_schema and callable(self.func):
            sig = inspect.signature(self.func)
            self.parameters_schema = {
                param.name: {
                    "type": str(param.annotation)
                    if param.annotation != inspect.Parameter.empty
                    else "Any",
                    "default": None
                    if param.default == inspect.Parameter.empty
                    else str(param.default),
                    "required": param.default == inspect.Parameter.empty,
                }
                for param in sig.parameters.values()
                if param.name not in ("self", "cls", "session", "principal", "cart_id")
            }


class BoundToolRegistry:
    """Context-bound tool registry tied to a specific session and caller principal.

    Automatically injects infrastructure dependencies (session, principal, cart_id)
    and enforces role-based permission gates before dispatching tool calls.
    """

    def __init__(
        self,
        definitions: list[ToolDefinition],
        principal: Principal,
        session: AsyncSession,
        cart_id: uuid.UUID | None = None,
        store_ids: list[uuid.UUID] | None = None,
    ) -> None:
        self.definitions = {t.name: t for t in definitions}
        self.principal = principal
        self.session = session
        self.cart_id = cart_id
        self.store_ids = store_ids or []
        self.audits: list[ToolExecutionAudit] = []

    def can_access(self, tool: ToolDefinition) -> bool:
        """Check if caller principal satisfies the tool's scope boundary."""
        if tool.scope == ToolScope.SHOPPER:
            # All callers (guests, users, merchants) can access shopper tools
            return True
        if tool.scope == ToolScope.MERCHANT:
            return self.principal.is_merchant or self.principal.role == "merchant"
        if tool.scope in (ToolScope.ADMIN, ToolScope.SYSTEM):
            return self.principal.role == "admin"
        return False

    def list_available_tools(self) -> list[ToolDefinition]:
        """List all tools accessible to current bound principal."""
        return [t for t in self.definitions.values() if self.can_access(t)]

    async def execute_tool(self, tool_name: str, **kwargs: Any) -> Any:
        """Execute tool by name with permission gating, dependency injection, and auditing."""
        tool = self.definitions.get(tool_name)
        if not tool:
            raise KeyError(f"Tool '{tool_name}' not registered in registry.")

        if not self.can_access(tool):
            err_msg = (
                f"Permission denied: Principal role '{self.principal.role}' "
                f"cannot execute {tool.scope.value}-scoped tool '{tool_name}'."
            )
            logger.warning("tool_execution_forbidden", tool=tool_name, principal=self.principal)
            raise ForbiddenError(err_msg)

        # Inspect tool signature to inject bound dependencies
        sig = inspect.signature(tool.func)
        call_kwargs = dict(kwargs)

        if "session" in sig.parameters:
            call_kwargs["session"] = self.session
        if "principal" in sig.parameters:
            call_kwargs["principal"] = self.principal
        if "cart_id" in sig.parameters:
            call_kwargs["cart_id"] = self.cart_id
        if "store_ids" in sig.parameters and "store_ids" not in call_kwargs:
            call_kwargs["store_ids"] = self.store_ids

        start_time = time.perf_counter()
        success = True
        error_msg: str | None = None
        result: Any = None

        try:
            if inspect.iscoroutinefunction(tool.func):
                result = await tool.func(**call_kwargs)
            else:
                result = tool.func(**call_kwargs)
            return result
        except Exception as exc:
            success = False
            error_msg = str(exc)
            logger.error("tool_execution_failed", tool=tool_name, error=error_msg, exc_info=True)
            raise
        finally:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            audit = ToolExecutionAudit(
                tool_name=tool_name,
                side_effect_level=tool.side_effect_level,
                scope=tool.scope,
                duration_ms=duration_ms,
                success=success,
                error=error_msg,
                input_summary=str(kwargs)[:300],
                output_summary=str(result)[:300] if result is not None else "",
            )
            self.audits.append(audit)

    def get_agno_tools(self) -> list[Callable[..., Any]]:
        """Export bound tools as Agno-compatible async callables with docstrings and type annotations."""
        agno_callables: list[Callable[..., Any]] = []

        for tool in self.list_available_tools():
            # Create a wrapper that captures the tool
            wrapper = self._create_agno_wrapper(tool)
            agno_callables.append(wrapper)

        return agno_callables

    def _create_agno_wrapper(self, tool: ToolDefinition) -> Callable[..., Any]:
        """Wrap a governed tool into a clean callable preserving signature for LLM tools."""
        original_sig = inspect.signature(tool.func)
        # Filter out injected params from LLM-facing signature
        external_params = [
            p
            for p in original_sig.parameters.values()
            if p.name not in ("session", "principal", "cart_id")
        ]
        new_sig = original_sig.replace(parameters=external_params)

        async def wrapped(**kwargs: Any) -> Any:
            return await self.execute_tool(tool.name, **kwargs)

        wrapped.__name__ = tool.name
        wrapped.__doc__ = f"{tool.description}\n\nSide effect: {tool.side_effect_level.value}"
        wrapped.__signature__ = new_sig  # type: ignore[attr-defined]
        return wrapped


class ToolRegistry:
    """Master registry storing tool definitions and vending bound scoped registries."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(
        self,
        name: str,
        description: str,
        scope: ToolScope,
        side_effect_level: SideEffectLevel,
        func: Callable[..., Any],
    ) -> ToolDefinition:
        """Register a new governed tool in the registry."""
        tool = ToolDefinition(
            name=name,
            description=description.strip(),
            scope=scope,
            side_effect_level=side_effect_level,
            func=func,
        )
        self._tools[name] = tool
        return tool

    def get(self, name: str) -> ToolDefinition | None:
        """Retrieve tool definition by name."""
        return self._tools.get(name)

    def list_all(self, scope: ToolScope | None = None) -> list[ToolDefinition]:
        """List all registered tools, optionally filtered by scope."""
        if scope:
            return [t for t in self._tools.values() if t.scope == scope]
        return list(self._tools.values())

    def bind_scope(
        self,
        principal: Principal,
        session: AsyncSession,
        cart_id: uuid.UUID | None = None,
        store_ids: list[uuid.UUID] | None = None,
    ) -> BoundToolRegistry:
        """Bind registry to an active execution scope and security context."""
        return BoundToolRegistry(
            definitions=list(self._tools.values()),
            principal=principal,
            session=session,
            cart_id=cart_id,
            store_ids=store_ids,
        )


# Global singleton registry
default_tool_registry = ToolRegistry()
