"""Agno Mission Workflow orchestrating the multi-agent mission pipeline."""

import time
import uuid
from collections.abc import AsyncGenerator
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from omnimission.adapters.pg_hybrid_search import PgHybridSearch
from omnimission.agents.intent_agent import IntentAgentRunner
from omnimission.agents.planner_agent import PlannerAgentRunner
from omnimission.agents.schemas import (
    MissionResult,
    OptimizedBasketItem,
    TimelineEvent,
)
from omnimission.agents.substitution_agent import SubstitutionEvaluator
from omnimission.agents.validator import GroundingValidator
from omnimission.agents.wayfinding import WayfindingService
from omnimission.core.logging import get_logger
from omnimission.models.mission import Mission, MissionItem, MissionRun
from omnimission.models.store import Store
from omnimission.ports.search_backend import SearchResult


class MissionWorkflow:
    """Deterministic Multi-Agent Pipeline with SSE event streaming and strict grounding."""

    def __init__(self) -> None:
        self.intent_runner = IntentAgentRunner()
        self.planner_runner = PlannerAgentRunner()
        self.search_adapter = PgHybridSearch()
        self.substitution_evaluator = SubstitutionEvaluator()
        self.grounding_validator = GroundingValidator()
        self.wayfinding_service = WayfindingService()
        self.logger = get_logger("mission_workflow")

    async def execute_streaming(
        self,
        session: AsyncSession,
        mission_id: uuid.UUID,
        raw_prompt: str,
        selected_store_ids: list[uuid.UUID],
        language: str = "en",
    ) -> AsyncGenerator[TimelineEvent, None]:
        """Execute the multi-agent pipeline and stream real-time timeline events."""
        overall_start = time.perf_counter()

        # Step 1: Parse Intent
        yield TimelineEvent(
            step="parsing_intent",
            status="in_progress",
            agent="Intent & Constraint Agent",
            title="Understanding Mission Intent",
            description="Decomposing natural language request and extracting constraints...",
        )
        t0 = time.perf_counter()
        intent = await self.intent_runner.parse_intent(raw_prompt, language)
        step1_ms = int((time.perf_counter() - t0) * 1000)

        trace1 = MissionRun(
            mission_id=mission_id,
            step="parsing_intent",
            agent="Intent & Constraint Agent",
            input_summary=raw_prompt[:500],
            output_summary=f"Goal={intent.goal_type}, Dietary={intent.dietary_tags}, Budget={intent.budget_inr}",
            latency_ms=step1_ms,
        )
        session.add(trace1)

        yield TimelineEvent(
            step="intent_parsed",
            status="completed",
            agent="Intent & Constraint Agent",
            title="Intent Analyzed",
            description=f"Identified {intent.goal_type} mission with constraints: {', '.join(intent.dietary_tags) or 'standard'}",
            latency_ms=step1_ms,
            data=intent.model_dump(),
        )

        # Step 2: Plan Needed Items
        yield TimelineEvent(
            step="planning_items",
            status="in_progress",
            agent="Mission Planner Agent",
            title="Formulating Shopping Plan",
            description="Expanding intent into required physical items and quantities...",
        )
        t0 = time.perf_counter()
        plan = await self.planner_runner.plan_items(intent)
        step2_ms = int((time.perf_counter() - t0) * 1000)

        trace2 = MissionRun(
            mission_id=mission_id,
            step="planning_items",
            agent="Mission Planner Agent",
            input_summary=f"Goal={intent.goal_type}, Description={intent.description}",
            output_summary=f"Planned {len(plan.items)} items: {', '.join(it.label for it in plan.items[:5])}",
            latency_ms=step2_ms,
        )
        session.add(trace2)

        yield TimelineEvent(
            step="items_planned",
            status="completed",
            agent="Mission Planner Agent",
            title="Plan Formulated",
            description=f"Identified {len(plan.items)} candidate items needed for mission.",
            latency_ms=step2_ms,
            data=plan.model_dump(),
        )

        # Step 3: Search Catalog across physical stores
        yield TimelineEvent(
            step="searching_catalog",
            status="in_progress",
            agent="Catalog Search Agent",
            title="Searching Local Inventory",
            description=f"Querying physical inventory across {len(selected_store_ids)} selected store(s)...",
        )
        t0 = time.perf_counter()

        all_search_hits: list[SearchResult] = []
        item_hits_map: dict[str, list[SearchResult]] = {}

        for item in plan.items:
            hits = await self.search_adapter.search(
                session=session,
                query=item.label,
                store_ids=selected_store_ids,
                is_travel_size=intent.is_travel_size,
                in_stock_only=False,  # Retrieve candidates to evaluate stockout and substitution!
                limit=5,
            )
            item_hits_map[item.label] = hits
            all_search_hits.extend(hits)

        step3_ms = int((time.perf_counter() - t0) * 1000)

        trace3 = MissionRun(
            mission_id=mission_id,
            step="searching_catalog",
            agent="Catalog Search Agent",
            input_summary=f"{len(plan.items)} queries across {len(selected_store_ids)} stores",
            output_summary=f"Retrieved {len(all_search_hits)} grounded inventory candidates",
            latency_ms=step3_ms,
        )
        session.add(trace3)

        yield TimelineEvent(
            step="catalog_searched",
            status="completed",
            agent="Catalog Search Agent",
            title="Inventory Retrieved",
            description="Located matching candidates with verified prices and aisle coordinates.",
            latency_ms=step3_ms,
            data={"total_hits": len(all_search_hits)},
        )

        # Step 4: Substitute and Optimize Basket
        yield TimelineEvent(
            step="optimizing_basket",
            status="in_progress",
            agent="Basket Optimizer Agent",
            title="Optimizing Basket & Substitutions",
            description="Selecting best in-stock SKUs, evaluating substitutions, and checking budget...",
        )
        t0 = time.perf_counter()

        raw_basket: list[OptimizedBasketItem] = []
        substitutions_applied = 0

        # Load store names
        store_names: dict[uuid.UUID, str] = {}
        for s_id in selected_store_ids:
            store_res = await session.get(Store, s_id)
            if store_res:
                store_names[s_id] = store_res.name

        for item in plan.items:
            candidates = item_hits_map.get(item.label, [])
            in_stock_candidates = [c for c in candidates if c.stock_qty > 0]

            if in_stock_candidates:
                # Direct match
                best = in_stock_candidates[0]
                unit_price = best.price
                subtotal = unit_price * Decimal(item.quantity)
                raw_basket.append(
                    OptimizedBasketItem(
                        product_id=best.product_id,
                        requested_label=item.label,
                        name=best.name,
                        brand=best.brand,
                        quantity=item.quantity,
                        unit_price=unit_price,
                        subtotal=subtotal,
                        store_id=best.store_id,
                        store_name=store_names.get(best.store_id, "Local Store"),
                        aisle=best.aisle,
                        bay=best.bay,
                        shelf=best.shelf,
                        status="matched",
                        match_explanation=f"Direct match in Aisle {best.aisle}.",
                    )
                )
            elif candidates:
                # Out of stock in primary candidate -> evaluate substitution
                proposal = self.substitution_evaluator.find_best_substitute(
                    needed_label=item.label,
                    category=item.category,
                    dietary_tags=intent.dietary_tags,
                    available_candidates=all_search_hits,
                )
                if proposal:
                    substitutions_applied += 1
                    # Find hit for proposal
                    prop_hit = next(
                        (
                            h
                            for h in all_search_hits
                            if h.product_id == proposal.substitute_product_id
                        ),
                        candidates[0],
                    )
                    subtotal = prop_hit.price * Decimal(item.quantity)
                    raw_basket.append(
                        OptimizedBasketItem(
                            product_id=prop_hit.product_id,
                            requested_label=item.label,
                            name=prop_hit.name,
                            brand=prop_hit.brand,
                            quantity=item.quantity,
                            unit_price=prop_hit.price,
                            subtotal=subtotal,
                            store_id=prop_hit.store_id,
                            store_name=store_names.get(prop_hit.store_id, "Local Store"),
                            aisle=prop_hit.aisle,
                            bay=prop_hit.bay,
                            shelf=prop_hit.shelf,
                            status="substituted",
                            substitution_reason=proposal.trade_off,
                            match_explanation=proposal.trade_off,
                        )
                    )

        step4_ms = int((time.perf_counter() - t0) * 1000)

        trace4 = MissionRun(
            mission_id=mission_id,
            step="optimizing_basket",
            agent="Basket Optimizer Agent",
            input_summary=f"Basket candidates={len(raw_basket)}, Substitutions={substitutions_applied}",
            output_summary=f"Optimized basket with {len(raw_basket)} items",
            latency_ms=step4_ms,
        )
        session.add(trace4)

        # Step 5: Grounding Validation & Wayfinding Route
        validated_basket = self.grounding_validator.validate_and_filter(
            basket_items=raw_basket,
            tool_results=all_search_hits,
            selected_store_ids=selected_store_ids,
        )
        total_cost = self.grounding_validator.calculate_total(validated_basket)
        route = self.wayfinding_service.generate_route(validated_basket, store_names)

        budget_fit = True
        budget_diff: Decimal | None = None
        if intent.budget_inr is not None:
            budget_limit = Decimal(str(intent.budget_inr))
            budget_diff = budget_limit - total_cost
            budget_fit = total_cost <= budget_limit

        # Distinct stores used
        used_store_ids = {it.store_id for it in validated_basket}
        stores_used = [
            {"id": str(s_id), "name": store_names.get(s_id, "Store")} for s_id in used_store_ids
        ]

        mission_result = MissionResult(
            mission_id=mission_id,
            intent=intent,
            items=validated_basket,
            total_cost=total_cost,
            budget_fit=budget_fit,
            budget_difference=budget_diff,
            stores_used=stores_used,
            route=route,
            summary=(
                f"Assembled {len(validated_basket)} grounded items totaling ₹{total_cost} "
                f"across {len(stores_used)} store(s) with {len(route)} aisle waypoint stops."
            ),
        )

        # Persist Mission Items & Result to database
        db_mission = await session.get(Mission, mission_id)
        if db_mission:
            db_mission.status = "completed"
            db_mission.total_cost = total_cost
            db_mission.constraints = intent.model_dump()

            for it in validated_basket:
                m_item = MissionItem(
                    mission_id=mission_id,
                    product_id=it.product_id,
                    requested_label=it.requested_label,
                    quantity=it.quantity,
                    reason=it.match_explanation,
                    status=it.status,
                    store_id=it.store_id,
                    unit_price=it.unit_price,
                    aisle_snapshot=it.aisle,
                    bay_snapshot=it.bay,
                    shelf_snapshot=it.shelf,
                )
                session.add(m_item)

        await session.commit()

        overall_ms = int((time.perf_counter() - overall_start) * 1000)

        # Final Event
        yield TimelineEvent(
            step="complete",
            status="completed",
            agent="OmniMission Orchestrator",
            title="Mission Complete",
            description=mission_result.summary,
            latency_ms=overall_ms,
            data=mission_result.model_dump(),
        )
