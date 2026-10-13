"""Search backend port and search hit DTO."""

import uuid
from decimal import Decimal
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict


class SearchResult(BaseModel):
    """Normalized search candidate hit returned from candidate retrieval."""

    model_config = ConfigDict(from_attributes=True)

    product_id: uuid.UUID
    store_id: uuid.UUID
    name: str
    brand: str
    category: str
    size_label: str | None = None
    is_travel_size: bool = False
    dietary_tags: list[str] = []
    price: Decimal
    mrp: Decimal
    stock_qty: int
    aisle: int
    bay: int
    shelf: int
    score: float
    match_method: str = "hybrid_rrf"


@runtime_checkable
class SearchBackend(Protocol):
    """Abstract protocol for candidate product search across selected physical stores."""

    async def search(
        self,
        session: object,  # AsyncSession
        query: str,
        store_ids: list[uuid.UUID],
        dietary_tags: list[str] | None = None,
        is_travel_size: bool | None = None,
        in_stock_only: bool = True,
        limit: int = 10,
    ) -> list[SearchResult]:
        """Retrieve candidate products matching query and store constraints."""
        ...
