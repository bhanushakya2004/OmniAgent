"""Evaluation benchmark script verifying the Physical Grounding Invariant across 20 shopper scenarios."""

import asyncio
import datetime
import uuid
from typing import Any

from sqlalchemy import select

from omnimission.core.principal import Principal
from omnimission.db.session import async_session_factory
from omnimission.models.commerce import GuestSession
from omnimission.models.inventory import StoreInventory
from omnimission.models.product import Product
from omnimission.schemas.mission import CreateMissionRequest
from omnimission.seed.data import STORE_BLR_INDIRANAGAR
from omnimission.services.mission_service import MissionService

SHOPPER_TEST_PROMPTS = [
    "Eggless cake with good protein, suggest all ingredients with quantities",
    "Travelling to Mumbai for 3 days, I need travel-size shampoo, toothpaste, and sanitizer",
    "Hosting a party for 8 people, suggest chips, cold drinks, cookies and paper plates",
    "Vegan high-protein dinner ingredients with tofu, spinach, and brown rice",
    "Gluten-free pancake breakfast ingredients with almond flour and maple syrup",
    "South Indian breakfast essentials: idli rice, urad dal, mustard seeds, curry leaves",
    "Italian pasta night for 4 people with penne, marinara sauce, and parmesan cheese",
    "Organic baby care essentials: hypoallergenic baby wash, baby wipes, and rash cream",
    "Emergency dental and grooming kit: soft toothbrush, floss, mouthwash, and lip balm",
    "Weekend BBQ snacks: pita chips, hummus, roasted almonds, and salsa dip",
    "Sugar-free dessert ingredients with dark chocolate, stevia, and heavy cream",
    "Gym workout recovery snacks: whey protein powder, bananas, peanut butter",
    "Hostel room essentials: instant noodles, green tea bags, and paper towels",
    "Diwali house cleaning supplies: floor disinfectant, microfiber cloths, sponge wipes",
    "Kids birthday party snacks: butter popcorn, fruit juice boxes, and cupcakes",
    "Monsoon hot tea essentials: Assam black tea, fresh ginger, cardamom pods",
    "Mediterranean salad kit: extra virgin olive oil, feta cheese, black olives, cucumber",
    "Quick dorm dinner: basmati rice, ready-to-eat dal tadka, and papad",
    "Office pantry restocking: filter coffee powder, brown sugar sachets, and Marie biscuits",
    "Immunity booster kit: pure raw honey, turmeric powder, amla juice, and chyawanprash",
]


async def run_grounding_benchmark() -> dict[str, Any]:
    """Execute Grounding Invariant benchmark across 20 realistic shopper queries."""
    mission_service = MissionService()
    guest_id = uuid.uuid4()
    session_token = f"guest_eval_{uuid.uuid4().hex[:8]}"
    principal = Principal(
        principal_type="guest",
        guest_session_id=guest_id,
        session_token=session_token,
    )

    total_missions = len(SHOPPER_TEST_PROMPTS)
    total_skus_evaluated = 0
    grounded_skus_count = 0
    price_matched_count = 0
    aisle_valid_count = 0

    # Pre-create guest session in DB
    async with async_session_factory() as setup_session:
        guest_sess = GuestSession(
            id=guest_id,
            session_token=session_token,
            expires_at=datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1),
            properties={"eval": True},
        )
        setup_session.add(guest_sess)
        await setup_session.commit()

    for prompt in SHOPPER_TEST_PROMPTS:
        req = CreateMissionRequest(
            prompt=prompt,
            store_ids=[STORE_BLR_INDIRANAGAR],
            language="en",
        )

        async with async_session_factory() as run_session:
            # Create and execute mission
            mission = await mission_service.create_mission(
                session=run_session,
                principal=principal,
                request=req,
            )

            # Consume stream generator to execute agent workflow
            async for _event in mission_service.stream_mission_execution(
                session=run_session,
                mission_id=mission.id,
                principal=principal,
            ):
                pass

        # Inspect created items in fresh database session
        async with async_session_factory() as inspect_session:
            loaded = await mission_service.get_mission(inspect_session, mission.id, principal)
            for item in loaded.items:
                total_skus_evaluated += 1

                # 1. Product exists in DB
                if item.product_id:
                    p_stmt = select(Product).where(Product.id == item.product_id)
                    p_res = await inspect_session.execute(p_stmt)
                    prod = p_res.scalar_one_or_none()
                    if prod:
                        grounded_skus_count += 1

                    # 2. Inventory exists in selected store with matching price
                    inv_stmt = select(StoreInventory).where(
                        StoreInventory.store_id == STORE_BLR_INDIRANAGAR,
                        StoreInventory.product_id == item.product_id,
                    )
                    inv_res = await inspect_session.execute(inv_stmt)
                    inv = inv_res.scalar_one_or_none()
                    if inv:
                        if abs(float(inv.price) - float(item.unit_price or 0)) < 0.01:
                            price_matched_count += 1
                        if 1 <= inv.aisle <= 12:
                            aisle_valid_count += 1
                else:
                    # Unmatched requested label without SKU
                    pass

    grounding_rate = grounded_skus_count / total_skus_evaluated if total_skus_evaluated > 0 else 1.0
    price_accuracy = price_matched_count / total_skus_evaluated if total_skus_evaluated > 0 else 1.0
    aisle_accuracy = aisle_valid_count / total_skus_evaluated if total_skus_evaluated > 0 else 1.0

    results = {
        "missions_tested": total_missions,
        "total_skus_evaluated": total_skus_evaluated,
        "grounded_skus": grounded_skus_count,
        "grounding_invariant_rate": round(grounding_rate, 4),
        "price_accuracy_rate": round(price_accuracy, 4),
        "aisle_localization_rate": round(aisle_accuracy, 4),
        "hallucinated_products": total_skus_evaluated - grounded_skus_count,
    }
    return results


if __name__ == "__main__":
    res = asyncio.run(run_grounding_benchmark())
    print("=== GROUNDING INVARIANT BENCHMARK ===")
    print(f"Missions Tested:         {res['missions_tested']}")
    print(f"Total SKUs Evaluated:    {res['total_skus_evaluated']}")
    print(f"Grounding Invariant:     {res['grounding_invariant_rate'] * 100}%")
    print(f"Price Accuracy:          {res['price_accuracy_rate'] * 100}%")
    print(f"Aisle Localization:      {res['aisle_localization_rate'] * 100}%")
    print(f"Hallucinated Products:   {res['hallucinated_products']}")
