"""Port definition for agent database read operations and MCP tools."""

import uuid
from abc import ABC, abstractmethod
from typing import Any


class DataToolPort(ABC):
    """Abstract interface for agent read-only database tools and inventory queries."""

    @abstractmethod
    async def search_store_inventory(
        self, store_id: uuid.UUID, query: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Search in-stock products in a specific physical store."""
        pass

    @abstractmethod
    async def get_product_location(self, store_id: uuid.UUID, sku: str) -> dict[str, Any] | None:
        """Lookup physical aisle, bay, and shelf coordinates for a SKU in a store."""
        pass

    @abstractmethod
    async def check_stock_levels(
        self, store_id: uuid.UUID, product_id: uuid.UUID
    ) -> dict[str, Any] | None:
        """Get live on-shelf stock quantity and unit price for a product."""
        pass

    @abstractmethod
    async def get_dietary_substitutes(
        self, store_id: uuid.UUID, category: str, dietary_tag: str, limit: int = 5
    ) -> list[dict[str, Any]]:
        """Find in-stock substitutes matching a specific dietary requirement."""
        pass

    @abstractmethod
    async def get_store_details(self, store_id: uuid.UUID) -> dict[str, Any] | None:
        """Retrieve store metadata, address, contact, and opening hours."""
        pass

    @abstractmethod
    async def find_nearby_stores(
        self, lat: float, lng: float, radius_km: float = 10.0
    ) -> list[dict[str, Any]]:
        """Find active physical retail stores within a geographic radius."""
        pass

    @abstractmethod
    def get_agno_tools(self) -> list[Any]:
        """Return list of Agno-compatible tools (functions or MCPTools) for agent mounting."""
        pass
