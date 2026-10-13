"""User and guest transparent memory service managing saved preferences and exclusions."""

from __future__ import annotations

import datetime
import uuid
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from omnimission.core.logging import get_logger
from omnimission.core.principal import Principal
from omnimission.models.commerce import GuestSession
from omnimission.models.memory import UserMemory

logger = get_logger("memory_service")


class MemoryService:
    """Provides transparent, user-auditable persistent memory for personalization."""

    async def list_memories(
        self,
        session: AsyncSession,
        principal: Principal,
    ) -> list[UserMemory]:
        """List all active memories belonging to the calling principal."""
        if principal.is_authenticated and principal.user_id:
            stmt = (
                select(UserMemory)
                .where(
                    UserMemory.user_id == principal.user_id,
                    UserMemory.is_active == True,  # noqa: E712
                )
                .order_by(UserMemory.created_at.desc())
            )
        else:
            stmt = (
                select(UserMemory)
                .where(
                    UserMemory.guest_session_id == principal.guest_session_id,
                    UserMemory.is_active == True,  # noqa: E712
                )
                .order_by(UserMemory.created_at.desc())
            )

        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def set_memory(
        self,
        session: AsyncSession,
        principal: Principal,
        key: str,
        value: Any,
        memory_type: str = "preference",
        source: str = "user_explicit",
    ) -> UserMemory:
        """Create or update a memory record with transparency."""
        clean_key = key.strip().lower()
        val_dict = value if isinstance(value, dict) else {"val": value}

        # Ensure guest session exists if principal is guest
        if principal.is_guest and principal.guest_session_id:
            guest_rec = await session.get(GuestSession, principal.guest_session_id)
            if not guest_rec:
                token = principal.session_token or f"guest_{principal.guest_session_id.hex}"
                expires = datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=30)
                session.add(
                    GuestSession(
                        id=principal.guest_session_id,
                        session_token=token,
                        expires_at=expires,
                        properties={},
                    )
                )
                await session.flush()

        # Check existing memory with same key
        if principal.is_authenticated and principal.user_id:
            stmt = select(UserMemory).where(
                UserMemory.user_id == principal.user_id,
                UserMemory.key == clean_key,
                UserMemory.is_active == True,  # noqa: E712
            )
        else:
            stmt = select(UserMemory).where(
                UserMemory.guest_session_id == principal.guest_session_id,
                UserMemory.key == clean_key,
                UserMemory.is_active == True,  # noqa: E712
            )

        res = await session.execute(stmt)
        mem = res.scalar_one_or_none()

        if mem:
            mem.value = val_dict
            mem.memory_type = memory_type
            mem.source = source
        else:
            mem = UserMemory(
                user_id=principal.user_id if principal.is_authenticated else None,
                guest_session_id=principal.guest_session_id if principal.is_guest else None,
                memory_type=memory_type,
                key=clean_key,
                value=val_dict,
                source=source,
                is_active=True,
            )
            session.add(mem)

        await session.flush()
        logger.info("memory_saved", key=clean_key, source=source, is_guest=principal.is_guest)
        return mem

    async def delete_memory(
        self,
        session: AsyncSession,
        principal: Principal,
        memory_id: uuid.UUID,
    ) -> bool:
        """Soft-delete or delete a specific memory item."""
        mem = await session.get(UserMemory, memory_id)
        if not mem:
            return False

        if principal.is_authenticated:
            if mem.user_id != principal.user_id:
                return False
        else:
            if mem.guest_session_id != principal.guest_session_id:
                return False

        mem.is_active = False
        await session.flush()
        return True

    async def clear_all_memories(
        self,
        session: AsyncSession,
        principal: Principal,
    ) -> int:
        """Clear all memories for the caller."""
        if principal.is_authenticated and principal.user_id:
            stmt = delete(UserMemory).where(UserMemory.user_id == principal.user_id)
        else:
            stmt = delete(UserMemory).where(
                UserMemory.guest_session_id == principal.guest_session_id
            )
        res = await session.execute(stmt)
        await session.flush()
        return int(getattr(res, "rowcount", 0) or 0)

    async def get_preference_profile(
        self,
        session: AsyncSession,
        principal: Principal,
    ) -> dict[str, Any]:
        """Aggregate all active memories into a unified personalisation profile."""
        memories = await self.list_memories(session, principal)
        profile: dict[str, Any] = {
            "dietary_tags": [],
            "household_size": None,
            "excluded_items": [],
            "preferred_brands": [],
            "budget_inr": None,
        }

        for m in memories:
            k = m.key
            v = m.value.get("val", m.value)

            if k in ("diet", "dietary", "dietary_tags", "diet_tags"):
                if isinstance(v, list):
                    profile["dietary_tags"].extend(v)
                elif isinstance(v, str):
                    profile["dietary_tags"].append(v)
            elif k in ("household", "household_size", "family_size", "people"):
                try:
                    profile["household_size"] = int(v)
                except (ValueError, TypeError):
                    pass
            elif k in ("allergens", "allergies", "exclude", "excluded_items"):
                if isinstance(v, list):
                    profile["excluded_items"].extend(v)
                elif isinstance(v, str):
                    profile["excluded_items"].append(v)
            elif k in ("brands", "preferred_brands"):
                if isinstance(v, list):
                    profile["preferred_brands"].extend(v)
                elif isinstance(v, str):
                    profile["preferred_brands"].append(v)
            elif k in ("budget", "budget_limit"):
                try:
                    profile["budget_inr"] = float(v)
                except (ValueError, TypeError):
                    pass

        # Deduplicate list fields
        profile["dietary_tags"] = list(set(profile["dietary_tags"]))
        profile["excluded_items"] = list(set(profile["excluded_items"]))
        profile["preferred_brands"] = list(set(profile["preferred_brands"]))
        return profile
