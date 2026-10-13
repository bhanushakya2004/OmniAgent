"""Mission Planner Agent expanding MissionIntent into a NeededItemList."""

from agno.agent import Agent

from omnimission.agents.intent_agent import get_gemini_model
from omnimission.agents.schemas import MissionIntent, NeededItem, NeededItemList
from omnimission.core.logging import get_logger

PLANNER_SYSTEM_PROMPT = """You are the OmniMission Mission Planner Agent.
Given a structured MissionIntent, expand the goal into the specific individual ingredients, supplies, or items needed.

Rules:
1. Ensure all dietary constraints in the intent are strictly reflected.
   - If 'eggless', do NOT include eggs; include moisture/binding replacers like yogurt, curd, or condensed milk.
   - If 'high_protein', include protein-dense ingredients (e.g. Greek yogurt, almond flour, or protein powder).
   - If 'is_travel_size', specify travel/mini toiletries (shampoo, toothpaste, sanitizer under 100ml).
2. Adjust quantities based on servings_or_people or duration_days.
3. Exclude any items listed in excluded_items.
"""


class PlannerAgentRunner:
    """Orchestrates mission item expansion using Agno Gemini Agent with deterministic fallback."""

    def __init__(self) -> None:
        self.logger = get_logger("planner_agent")
        model = get_gemini_model()
        self.agent: Agent | None = None
        if model:
            self.agent = Agent(
                name="Mission Planner Agent",
                model=model,
                instructions=PLANNER_SYSTEM_PROMPT,
                output_schema=NeededItemList,
            )

    async def plan_items(self, intent: MissionIntent) -> NeededItemList:
        """Expand intent into needed item list."""
        if self.agent:
            try:
                prompt = (
                    f"Goal: {intent.goal_type}\n"
                    f"Description: {intent.description}\n"
                    f"People: {intent.servings_or_people}\n"
                    f"Dietary: {intent.dietary_tags}\n"
                    f"Travel Size: {intent.is_travel_size}\n"
                    f"Budget: {intent.budget_inr}\n"
                    f"Excluded: {intent.excluded_items}"
                )
                response = self.agent.run(prompt)
                if response and isinstance(response.content, NeededItemList):
                    return response.content
            except Exception as err:
                self.logger.warning("live_planner_agent_failed_using_deterministic_fallback", error=str(err))

        # Deterministic domain expansion
        items: list[NeededItem] = []
        desc = intent.description.lower()

        if intent.goal_type == "travel_kit" or intent.is_travel_size:
            items = [
                NeededItem(label="Travel Shampoo 50ml", category="Personal Care", quantity=1, unit="ml", importance="essential"),
                NeededItem(label="Mini Toothpaste 30g", category="Personal Care", quantity=1, unit="g", importance="essential"),
                NeededItem(label="Compact Travel Toothbrush", category="Personal Care", quantity=1, unit="piece", importance="essential"),
                NeededItem(label="Pocket Hand Sanitizer 50ml", category="Personal Care", quantity=1, unit="ml", importance="essential"),
                NeededItem(label="Pocket Deodorant Roll-on", category="Personal Care", quantity=1, unit="ml", importance="essential"),
                NeededItem(label="Travel Sunscreen 50ml", category="Personal Care", quantity=1, unit="ml", importance="optional"),
            ]
            rationale = "Generated flight-compliant, airline baggage travel kit under 100ml."

        elif intent.goal_type == "party":
            count = intent.servings_or_people or 8
            cup_packs = max(1, count // 10)
            items = [
                NeededItem(label="Paper Beverage Cups", category="Party & Household", quantity=cup_packs, unit="pack", importance="essential"),
                NeededItem(label="Compostable Dinner Plates", category="Party & Household", quantity=cup_packs, unit="pack", importance="essential"),
                NeededItem(label="Party Table Napkins", category="Party & Household", quantity=1, unit="pack", importance="essential"),
                NeededItem(label="Aloo Bhujia Spicy Snack", category="Snacks & Munchies", quantity=2, unit="pack", importance="essential"),
                NeededItem(label="Classic Salted Potato Chips", category="Snacks & Munchies", quantity=2, unit="pack", importance="essential"),
                NeededItem(label="Spiced Ginger Ale Sparkling Cans", category="Beverages", quantity=1, unit="pack", importance="essential"),
            ]
            rationale = f"Balanced party supplies and snacks tailored for {count} guests."

        elif "cake" in desc or intent.goal_type == "recipe":
            items = [
                NeededItem(label="Maida All-Purpose Flour", category="Baking & Cooking", quantity=1, unit="kg", importance="essential"),
                NeededItem(label="Cocoa Powder", category="Baking & Cooking", quantity=1, unit="g", importance="essential"),
                NeededItem(label="Double Action Baking Powder", category="Baking & Cooking", quantity=1, unit="g", importance="essential"),
                NeededItem(label="Pure Baking Soda", category="Baking & Cooking", quantity=1, unit="g", importance="essential"),
                NeededItem(label="High Protein Greek Yogurt Curd", category="Dairy", quantity=1, unit="g", importance="essential"),
                NeededItem(label="Protein Powder Supplement", category="Health & Nutrition", quantity=1, unit="pack", importance="essential"),
                NeededItem(label="Bourbon Vanilla Extract", category="Baking & Cooking", quantity=1, unit="ml", importance="optional"),
            ]
            rationale = "Formulated complete eggless cake recipe with Greek yogurt binder and protein supplement."

        else:
            items = [
                NeededItem(label=intent.description, category="General", quantity=1, importance="essential")
            ]
            rationale = f"Planned items directly matching intent query: {intent.description}"

        return NeededItemList(items=items, rationale=rationale)
