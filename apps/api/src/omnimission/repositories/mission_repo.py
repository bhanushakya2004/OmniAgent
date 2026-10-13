"""Mission repository managing database persistence of missions, items, and traces."""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from omnimission.models.mission import Mission, MissionItem


class MissionRepository:
    """Repository managing mission data access."""

    async def create_mission(
        self,
        session: AsyncSession,
        user_id: uuid.UUID | None,
        raw_text: str,
        selected_store_ids: list[uuid.UUID],
        guest_session_id: uuid.UUID | None = None,
        language: str = "en",
        input_modalities: list[str] | None = None,
        constraints: dict[str, Any] | None = None,
    ) -> Mission:
        """Create initial mission record."""
        mission = Mission(
            user_id=user_id,
            guest_session_id=guest_session_id,
            raw_text=raw_text.strip(),
            selected_store_ids=selected_store_ids,
            language=language,
            input_modalities=input_modalities or ["text"],
            constraints=constraints,
            status="pending",
        )
        session.add(mission)
        await session.flush()
        return mission

    async def get_by_id(self, session: AsyncSession, mission_id: uuid.UUID) -> Mission | None:
        """Fetch mission with loaded items, products, and execution traces."""
        stmt = (
            select(Mission)
            .options(
                selectinload(Mission.items).selectinload(MissionItem.product),
                selectinload(Mission.items).selectinload(MissionItem.store),
                selectinload(Mission.traces),
            )
            .where(Mission.id == mission_id)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        session: AsyncSession,
        user_id: uuid.UUID | None = None,
        guest_session_id: uuid.UUID | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Mission]:
        """List past missions for a user or guest session."""
        stmt = (
            select(Mission)
            .options(selectinload(Mission.items))
            .order_by(Mission.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if user_id:
            stmt = stmt.where(Mission.user_id == user_id)
        elif guest_session_id:
            stmt = stmt.where(Mission.guest_session_id == guest_session_id)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_item_by_id(self, session: AsyncSession, item_id: uuid.UUID) -> MissionItem | None:
        """Fetch specific mission item."""
        stmt = select(MissionItem).where(MissionItem.id == item_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_item_quantity(
        self,
        session: AsyncSession,
        item: MissionItem,
        quantity: int,
    ) -> MissionItem:
        """Update item quantity."""
        item.quantity = quantity
        await session.flush()
        return item
