"""Personalisation Agent managing memory injection, preference enforcement, and transparent audit."""

from __future__ import annotations

import re

from sqlalchemy.ext.asyncio import AsyncSession

from omnimission.agents.schemas import MissionIntent
from omnimission.core.logging import get_logger
from omnimission.core.principal import Principal
from omnimission.services.memory_service import MemoryService

logger = get_logger("personalisation_agent")


class PersonalisationAgent:
    """Applies stored user preferences to shopping missions and extracts new memory declarations."""

    def __init__(self, memory_service: MemoryService | None = None) -> None:
        self.memory_service = memory_service or MemoryService()

    async def personalize_intent(
        self,
        session: AsyncSession,
        principal: Principal,
        intent: MissionIntent,
    ) -> tuple[MissionIntent, list[str]]:
        """Inject stored user preferences into intent and return transparent notice messages."""
        profile = await self.memory_service.get_preference_profile(session, principal)
        notices: list[str] = []

        # 1. Dietary Tags Injection
        existing_tags = set(intent.dietary_tags)
        stored_diet = set(profile.get("dietary_tags", []))
        new_diet = stored_diet - existing_tags
        if new_diet:
            intent.dietary_tags = list(existing_tags | stored_diet)
            notices.append(f"Applied your saved dietary preferences: {', '.join(new_diet)}.")

        # 2. Household Size / Servings Injection
        if intent.servings_or_people is None and profile.get("household_size"):
            intent.servings_or_people = profile["household_size"]
            notices.append(f"Scaled portions for your household of {intent.servings_or_people}.")

        # 3. Excluded Items / Allergens Injection
        existing_excluded = set(intent.excluded_items)
        stored_excluded = set(profile.get("excluded_items", []))
        new_excluded = stored_excluded - existing_excluded
        if new_excluded:
            intent.excluded_items = list(existing_excluded | stored_excluded)
            notices.append(
                f"Filtered out saved allergen/excluded items: {', '.join(new_excluded)}."
            )

        # 4. Budget Preference Injection
        if intent.budget_inr is None and profile.get("budget_inr"):
            intent.budget_inr = profile["budget_inr"]
            notices.append(f"Set mission budget to your preferred INR {intent.budget_inr:.2f}.")

        return intent, notices

    async def capture_explicit_preferences(
        self,
        session: AsyncSession,
        principal: Principal,
        text: str,
    ) -> list[str]:
        """Detect and store explicit user preference instructions (e.g., 'Remember that I am vegetarian')."""
        lower = text.lower()
        captured_messages: list[str] = []

        # Check for remember / note declarations
        if not any(
            trigger in lower
            for trigger in ["remember", "note that", "save my", "always use", "i am", "i'm"]
        ):
            return captured_messages

        # 1. Dietary detection
        diet_map = {
            "eggless": "eggless",
            "vegan": "vegan",
            "vegetarian": "vegetarian",
            "gluten free": "gluten_free",
            "gluten-free": "gluten_free",
            "keto": "keto",
        }
        for kw, tag in diet_map.items():
            if kw in lower and any(
                p in lower for p in ["remember", "prefer", "am", "i'm", "always"]
            ):
                await self.memory_service.set_memory(
                    session=session,
                    principal=principal,
                    key="diet",
                    value=tag,
                    memory_type="dietary_preference",
                    source="user_explicit",
                )
                captured_messages.append(f"Remembered preference: {tag}")

        # 2. Household size
        hh_match = re.search(r"(?:family of|household of|cooking for)\s+(\d+)", lower)
        if hh_match:
            size = int(hh_match.group(1))
            await self.memory_service.set_memory(
                session=session,
                principal=principal,
                key="household_size",
                value=size,
                memory_type="household_preference",
                source="user_explicit",
            )
            captured_messages.append(f"Remembered household size: {size}")

        # 3. Allergen exclusion
        allergen_match = re.search(
            r"(?:allergic to|avoid|don't eat|no)\s+([a-zA-Z\s]+?)(?:\.|$|,|and)", lower
        )
        if allergen_match and "remember" in lower:
            item = allergen_match.group(1).strip()
            if item and len(item) < 30 and item not in ["meat", "eggs"]:
                await self.memory_service.set_memory(
                    session=session,
                    principal=principal,
                    key="allergens",
                    value=item,
                    memory_type="allergen_exclusion",
                    source="user_explicit",
                )
                captured_messages.append(f"Remembered allergen exclusion: {item}")

        return captured_messages
