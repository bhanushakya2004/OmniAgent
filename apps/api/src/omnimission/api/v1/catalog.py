"""Catalog search API router."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from omnimission.adapters.pg_hybrid_search import PgHybridSearch
from omnimission.db.session import get_db_session
from omnimission.ports.search_backend import SearchBackend, SearchResult

router = APIRouter(prefix="/catalog", tags=["Catalog"])


def get_search_backend() -> SearchBackend:
    """Dependency provider for SearchBackend port."""
    return PgHybridSearch()


@router.get(
    "/search",
    response_model=list[SearchResult],
    summary="Search catalog across selected stores",
)
async def search_catalog(
    q: Annotated[str, Query(min_length=1, description="Search query string")],
    store_ids: Annotated[
        list[uuid.UUID], Query(description="Selected store UUIDs to search within")
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    search_backend: Annotated[SearchBackend, Depends(get_search_backend)],
    dietary_tags: Annotated[list[str] | None, Query(description="Dietary filter tags")] = None,
    is_travel_size: Annotated[bool | None, Query(description="Filter travel-size SKUs")] = None,
    in_stock_only: Annotated[bool, Query(description="Filter in-stock SKUs only")] = True,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
) -> list[SearchResult]:
    """Execute hybrid search using pgvector, full-text search, and trigram RRF."""
    return await search_backend.search(
        session=session,
        query=q,
        store_ids=store_ids,
        dietary_tags=dietary_tags,
        is_travel_size=is_travel_size,
        in_stock_only=in_stock_only,
        limit=limit,
    )
