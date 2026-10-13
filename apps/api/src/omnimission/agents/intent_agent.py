"""Intent & Constraint Agent parsing unstructured shopper missions into structured MissionIntent."""

import re

from agno.agent import Agent
from agno.models.google import Gemini

from omnimission.agents.schemas import MissionIntent
from omnimission.core.config import get_settings
from omnimission.core.logging import get_logger

INTENT_SYSTEM_PROMPT = """You are the OmniMission Intent Agent.
Analyze the shopper's natural language input (which may be in English, Hindi, Hinglish, Kannada, Tamil, etc.)
and extract their core mission goal, constraints, dietary preferences, and budget.

Rules:
1. Detect goal_type: 'recipe', 'party', 'travel_kit', 'replacement', or 'general'.
2. Extract servings_or_people (integer count) if mentioned.
3. Extract duration_days if a trip or trip kit is mentioned.
4. Extract budget_inr (numerical amount in Indian Rupees) if specified (e.g. ₹500, 3000, "under 600").
5. Extract dietary_tags: strictly from ['eggless', 'vegetarian', 'vegan', 'gluten_free', 'high_protein', 'sugar_free'].
6. Extract is_travel_size (True if user mentions travel, mini, pocket-size, hotel stay, flight).
7. Extract detected_language ('en', 'hi', 'kn', 'ta', etc.).
8. Extract excluded_items if the user mentioned they already have items in pantry.
"""


def get_gemini_model() -> Gemini | None:
    """Build Gemini model instance according to configuration."""
    settings = get_settings()
    if not settings.google_api_key or settings.google_api_key.startswith("change-me"):
        return None

    if settings.gemini_backend == "vertex":
        return Gemini(
            id=settings.gemini_model_fast,
            vertexai=True,
            project_id=settings.google_cloud_project,
            location=settings.google_cloud_location,
        )
    return Gemini(
        id=settings.gemini_model_fast,
        api_key=settings.google_api_key,
    )


class IntentAgentRunner:
    """Orchestrates intent extraction via Agno Gemini Agent with deterministic fallback."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.logger = get_logger("intent_agent")
        model = get_gemini_model()
        self.agent: Agent | None = None
        if model:
            self.agent = Agent(
                name="Intent & Constraint Agent",
                model=model,
                instructions=INTENT_SYSTEM_PROMPT,
                output_schema=MissionIntent,
            )

    async def parse_intent(self, text: str, user_language: str = "en") -> MissionIntent:
        """Parse natural language into structured MissionIntent."""
        clean_text = text.strip()

        # If live Gemini model is available, execute Agno agent
        if self.agent:
            try:
                response = self.agent.run(clean_text)
                if response and isinstance(response.content, MissionIntent):
                    return response.content
            except Exception as err:
                self.logger.warning("live_gemini_agent_failed_using_rule_fallback", error=str(err))

        # Deterministic multilingual NLP parser fallback
        lower = clean_text.lower()

        # Detect language
        detected_lang = user_language
        if any(w in lower for w in ["chahiye", "saaman", "mujhe", "ke liye", "logon"]):
            detected_lang = "hi"

        # Detect goal type
        goal_type = "general"
        if any(w in lower for w in ["cake", "recipe", "cook", "bake", "pasta", "dish", "curry"]):
            goal_type = "recipe"
        elif any(w in lower for w in ["party", "host", "guests", "celebration", "gathering"]):
            goal_type = "party"
        elif any(w in lower for w in ["travel", "trip", "mumbai", "flight", "hotel", "toiletries"]):
            goal_type = "travel_kit"

        # Detect dietary tags
        dietary_tags: list[str] = []
        if "eggless" in lower or "bina ande" in lower:
            dietary_tags.append("eggless")
        if "protein" in lower:
            dietary_tags.append("high_protein")
        if "vegan" in lower:
            dietary_tags.append("vegan")
        if "gluten" in lower or "gluten-free" in lower:
            dietary_tags.append("gluten_free")
        if "vegetarian" in lower or "veg" in lower:
            dietary_tags.append("vegetarian")

        # Detect travel size
        is_travel = False
        if any(w in lower for w in ["travel", "small", "mini", "pocket", "trip", "50ml", "100ml"]):
            is_travel = True

        # Extract people / servings
        servings: int | None = None
        people_match = re.search(r"(\d+)\s*(people|persons|servings|guests|logon|log)", lower)
        if people_match:
            servings = int(people_match.group(1))

        # Extract duration
        duration: int | None = None
        duration_match = re.search(r"(\d+)\s*(days|day|din)", lower)
        if duration_match:
            duration = int(duration_match.group(1))

        # Extract budget
        budget: float | None = None
        budget_match = re.search(r"(?:budget|under|rs|inr|₹)\s*[:=]?\s*(\d+)", lower)
        if budget_match:
            budget = float(budget_match.group(1))
        else:
            budget_match_2 = re.search(r"(\d+)\s*(?:rupees|rs|budget)", lower)
            if budget_match_2:
                budget = float(budget_match_2.group(1))

        return MissionIntent(
            goal_type=goal_type,
            description=clean_text,
            servings_or_people=servings,
            duration_days=duration,
            budget_inr=budget,
            dietary_tags=dietary_tags,
            is_travel_size=is_travel,
            detected_language=detected_lang,
            excluded_items=[],
        )
