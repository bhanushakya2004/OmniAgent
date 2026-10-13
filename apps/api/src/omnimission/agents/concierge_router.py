"""Concierge Router Agent classifying shopper and merchant intent across specialised pipelines.

Routes incoming user requests to:
- recipe_planner: Recipe ingredients, cooking goals, dietary substitutions.
- travel_planner: Travel toiletry kits, packing lists, flight-size compliance.
- party_planner: Party hosting, portion calculations, guest scaling.
- catalog_search: Direct SKU searches, price checks, product availability.
- cart_agent: Cart operations (add items, remove item, clear cart, inspect cart).
- order_status: Order tracking and delivery status inquiries.
- store_analyst: Merchant analytics, inventory levels, shrinkage, sales inquiries.
- general_qa: Store policies, return guidelines, operating hours.
"""

from __future__ import annotations

import enum
import re
from typing import Any

from agno.agent import Agent
from pydantic import BaseModel, Field

from omnimission.agents.intent_agent import get_gemini_model
from omnimission.core.logging import get_logger

logger = get_logger("concierge_router")


class RouteType(enum.StrEnum):
    """Categorical mission routes supported by the Concierge Router."""

    RECIPE_MISSION = "recipe_mission"
    TRAVEL_MISSION = "travel_mission"
    PARTY_MISSION = "party_mission"
    CATALOG_SEARCH = "catalog_search"
    CART_ACTION = "cart_action"
    ORDER_STATUS = "order_status"
    MERCHANT_ANALYTICS = "merchant_analytics"
    GENERAL_QA = "general_qa"


class RoutingDecision(BaseModel):
    """Structured routing decision with confidence score and extracted entities."""

    route: RouteType = Field(..., description="Target execution route for the mission.")
    target_agent: str = Field(..., description="Name of the specialized sub-agent.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score.")
    reasoning: str = Field(..., description="Brief rationale for the classification.")
    extracted_entities: dict[str, Any] = Field(
        default_factory=dict,
        description="Extracted entities including servings, duration, dietary tags, items, or action.",
    )


ROUTER_SYSTEM_PROMPT = """You are the OmniMission Concierge Router Agent.
Analyze the user's input and classify it into exactly one target route:

1. recipe_mission: Cooking or baking goals (e.g. "make an eggless strawberry cake", "dinner for 4").
2. travel_mission: Packing or travel toiletries (e.g. "travelling to Mumbai for 3 days", "mini shampoo").
3. party_mission: Hosting parties or gatherings (e.g. "party for 10 people with snacks and drinks").
4. catalog_search: Inquiring about specific products or prices (e.g. "do you have almond milk?", "how much is butter?").
5. cart_action: Explicit cart modifications (e.g. "add them to my cart", "remove item", "clear cart", "view cart").
6. order_status: Checking existing order or delivery status (e.g. "where is order #1234?").
7. merchant_analytics: Store operations questions (e.g. "what is our shrinkage?", "inventory levels in bakery").
8. general_qa: Store policy, return guidelines, operating hours.

Extract key entities:
- servings_or_people: integer
- duration_days: integer
- dietary_tags: list of ['eggless', 'vegetarian', 'vegan', 'gluten_free', 'high_protein', 'keto']
- budget_inr: float or null
- cart_action: 'add', 'remove', 'clear', or 'view'
- product_queries: list of string names
"""


class ConciergeRouter:
    """Intelligent intent classifier and agent dispatcher."""

    def __init__(self) -> None:
        self.model = get_gemini_model()
        self.agent: Agent | None = None
        if self.model:
            self.agent = Agent(
                name="Concierge Router",
                model=self.model,
                instructions=ROUTER_SYSTEM_PROMPT,
                output_schema=RoutingDecision,
            )

    async def route(self, prompt: str, is_merchant_context: bool = False) -> RoutingDecision:
        """Classify prompt into a RoutingDecision via Gemini with deterministic fallback."""
        clean_prompt = prompt.strip()

        # If LLM agent is available, attempt structured routing
        if self.agent:
            try:
                context_prefix = (
                    "Context: Merchant Operations Dashboard\n"
                    if is_merchant_context
                    else "Context: Retail Shopper\n"
                )
                response = self.agent.run(f"{context_prefix}User Request: {clean_prompt}")
                if response and isinstance(response.content, RoutingDecision):
                    return response.content
            except Exception as err:
                logger.warning(
                    "concierge_agent_llm_failed_falling_back_to_rules",
                    error=str(err),
                    prompt=clean_prompt[:100],
                )

        # Deterministic Rule-Based Classification
        return self._classify_rule_based(clean_prompt, is_merchant_context)

    def _classify_rule_based(self, prompt: str, is_merchant: bool) -> RoutingDecision:
        """Deterministic classifier ensuring 100% test reliability and instant local routing."""
        lower = prompt.lower()

        # 1. Cart Actions
        if any(
            w in lower for w in ["add to cart", "add all", "add them", "put in cart", "add these"]
        ):
            return RoutingDecision(
                route=RouteType.CART_ACTION,
                target_agent="cart_agent",
                confidence=0.98,
                reasoning="Detected explicit cart insertion intent.",
                extracted_entities={"cart_action": "add"},
            )
        if any(w in lower for w in ["clear cart", "empty cart", "delete cart"]) or (
            ("empty" in lower or "clear" in lower) and "cart" in lower
        ):
            return RoutingDecision(
                route=RouteType.CART_ACTION,
                target_agent="cart_agent",
                confidence=0.99,
                reasoning="Detected explicit cart clearing request.",
                extracted_entities={"cart_action": "clear"},
            )
        if any(
            w in lower
            for w in ["view cart", "show cart", "what is in my cart", "my cart", "in my cart"]
        ):
            return RoutingDecision(
                route=RouteType.CART_ACTION,
                target_agent="cart_agent",
                confidence=0.95,
                reasoning="Detected cart inspection inquiry.",
                extracted_entities={"cart_action": "view"},
            )

        # 2. Merchant Analytics
        if is_merchant or any(
            w in lower
            for w in [
                "shrinkage",
                "stockout risk",
                "inventory levels",
                "shelf audit",
                "top selling",
                "restock task",
                "sales today",
                "revenue",
            ]
        ):
            return RoutingDecision(
                route=RouteType.MERCHANT_ANALYTICS,
                target_agent="store_analyst",
                confidence=0.96,
                reasoning="Detected merchant operational metrics or inventory audit inquiry.",
                extracted_entities={},
            )

        # 3. Order Status
        if any(w in lower for w in ["order status", "track order", "where is my order", "order #"]):
            order_match = re.search(r"#([0-9a-fA-F-]+)", lower)
            if not order_match:
                order_match = re.search(r"order\s+([0-9a-fA-F-]+)", lower)
            order_id = order_match.group(1) if order_match else None
            return RoutingDecision(
                route=RouteType.ORDER_STATUS,
                target_agent="order_agent",
                confidence=0.94,
                reasoning="Detected order tracking and delivery status inquiry.",
                extracted_entities={"order_id": order_id},
            )

        # 4. Travel Mission
        if any(
            w in lower for w in ["travel", "mumbai", "trip", "packing", "flight", "mini", "hotel"]
        ):
            days_match = re.search(r"(\d+)\s*(days?|nights?)", lower)
            duration_days = int(days_match.group(1)) if days_match else 3
            return RoutingDecision(
                route=RouteType.TRAVEL_MISSION,
                target_agent="travel_planner",
                confidence=0.95,
                reasoning="Detected travel packing mission requiring TSA-friendly or travel-sized items.",
                extracted_entities={"duration_days": duration_days, "is_travel_size": True},
            )

        # 5. Party Mission
        if any(
            w in lower for w in ["party", "host", "gathering", "friends coming over", "celebration"]
        ):
            people_match = re.search(r"(\d+)\s*(people|guests|friends|persons|pax)", lower)
            servings = int(people_match.group(1)) if people_match else 8
            return RoutingDecision(
                route=RouteType.PARTY_MISSION,
                target_agent="party_planner",
                confidence=0.94,
                reasoning="Detected social hosting mission requiring portion scaling.",
                extracted_entities={"servings_or_people": servings},
            )

        # 6. Recipe Mission
        recipe_keywords = [
            "cake",
            "bake",
            "cook",
            "recipe",
            "ingredient",
            "dinner",
            "lunch",
            "curry",
            "pasta",
            "biryani",
            "eggless",
            "strawberry",
            "paneer",
            "chocolate",
            "soup",
            "salad",
        ]
        if any(w in lower for w in recipe_keywords):
            diet_tags = self._extract_dietary_tags(lower)
            people_match = re.search(r"(\d+)\s*(people|guests|servings|persons|pax)", lower)
            servings = int(people_match.group(1)) if people_match else 4
            return RoutingDecision(
                route=RouteType.RECIPE_MISSION,
                target_agent="recipe_planner",
                confidence=0.95,
                reasoning="Detected culinary recipe mission requiring recipe RAG and ingredient breakdown.",
                extracted_entities={
                    "servings_or_people": servings,
                    "dietary_tags": diet_tags,
                },
            )

        # 7. General Store Policy / FAQ
        if any(
            w in lower
            for w in ["return policy", "opening hours", "timings", "store close", "refund"]
        ):
            return RoutingDecision(
                route=RouteType.GENERAL_QA,
                target_agent="knowledge_qa",
                confidence=0.90,
                reasoning="Detected store policy or FAQ inquiry.",
                extracted_entities={},
            )

        # 8. Catalog Search (Default)
        return RoutingDecision(
            route=RouteType.CATALOG_SEARCH,
            target_agent="catalog_search",
            confidence=0.85,
            reasoning="Defaulted to product catalog search.",
            extracted_entities={"query": prompt},
        )

    def _extract_dietary_tags(self, text: str) -> list[str]:
        tags: list[str] = []
        if "eggless" in text:
            tags.append("eggless")
        if "gluten free" in text or "gluten-free" in text:
            tags.append("gluten_free")
        if "vegan" in text:
            tags.append("vegan")
        if "vegetarian" in text or "veg" in text:
            tags.append("vegetarian")
        if "high protein" in text or "protein" in text:
            tags.append("high_protein")
        if "keto" in text:
            tags.append("keto")
        if "sugar free" in text or "sugar-free" in text:
            tags.append("sugar_free")
        return tags
