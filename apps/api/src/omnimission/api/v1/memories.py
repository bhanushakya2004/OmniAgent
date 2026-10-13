"""Transparent Memory API endpoints allowing shoppers to inspect, update, and clear saved preferences."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from omnimission.core.deps import get_current_principal
from omnimission.core.errors import NotFoundError
from omnimission.core.principal import Principal
from omnimission.db.session import get_db_session
from omnimission.schemas.memory import (
    MemoryCreateRequest,
    MemoryListResponse,
    UserMemoryItem,
)
from omnimission.services.memory_service import MemoryService

router = APIRouter(prefix="/memories", tags=["memories"])
memory_service = MemoryService()


@router.get("", response_model=MemoryListResponse)
async def list_user_memories(
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> MemoryListResponse:
    """List all active, transparent memories and compiled preference profile for caller."""
    memories = await memory_service.list_memories(session, principal)
    profile = await memory_service.get_preference_profile(session, principal)

    return MemoryListResponse(
        memories=[
            UserMemoryItem(
                id=m.id,
                key=m.key,
                value=m.value,
                memory_type=m.memory_type,
                source=m.source,
                is_active=m.is_active,
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
            for m in memories
        ],
        compiled_profile=profile,
    )


@router.post("", response_model=UserMemoryItem, status_code=status.HTTP_201_CREATED)
async def set_user_memory(
    req: MemoryCreateRequest,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> UserMemoryItem:
    """Save or update a transparent memory preference."""
    mem = await memory_service.set_memory(
        session=session,
        principal=principal,
        key=req.key,
        value=req.value,
        memory_type=req.memory_type,
        source="user_explicit",
    )
    await session.commit()

    return UserMemoryItem(
        id=mem.id,
        key=mem.key,
        value=mem.value,
        memory_type=mem.memory_type,
        source=mem.source,
        is_active=mem.is_active,
        created_at=mem.created_at,
        updated_at=mem.updated_at,
    )


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_memory(
    memory_id: uuid.UUID,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete a specific memory preference item."""
    success = await memory_service.delete_memory(session, principal, memory_id)
    if not success:
        raise NotFoundError(f"Memory item '{memory_id}' not found.")
    await session.commit()


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def clear_all_memories(
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    """Clear all saved memory preferences for caller."""
    await memory_service.clear_all_memories(session, principal)
    await session.commit()
