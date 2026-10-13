"""Mission service orchestrating mission creation, resumable SSE streaming, basket edits, and wayfinding."""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncGenerator
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from omnimission.agents.schemas import OptimizedBasketItem
from omnimission.agents.wayfinding import WayfindingService
from omnimission.agents.workflow import MissionWorkflow
from omnimission.core.errors import ForbiddenError, NotFoundError
from omnimission.core.principal import Principal
from omnimission.models.mission import Mission
from omnimission.repositories.mission_repo import MissionRepository
from omnimission.schemas.mission import (
    CreateMissionRequest,
    MissionItemResponse,
    MissionListItemResponse,
    MissionListResponse,
    MissionResponse,
    MissionRouteResponse,
    MissionTraceResponse,
    RouteWaypointResponse,
)
from omnimission.services.event_persistence_service import EventPersistenceService


class MissionService:
    """Business logic for shopper mission lifecycle with resumable SSE streaming."""

    def __init__(self) -> None:
        self.repo = MissionRepository()
        self.workflow = MissionWorkflow()
        self.wayfinding = WayfindingService()
        self.event_persistence = EventPersistenceService()

    async def create_mission(
        self,
        session: AsyncSession,
        principal: Principal,
        request: CreateMissionRequest,
    ) -> Mission:
        """Create a pending mission record for user or anonymous guest."""
        mission = await self.repo.create_mission(
            session=session,
            user_id=principal.user_id if principal.is_authenticated else None,
            guest_session_id=principal.guest_session_id if principal.is_guest else None,
            raw_text=request.prompt,
            selected_store_ids=request.store_ids,
            language=request.language,
            input_modalities=request.input_modalities,
            constraints=request.constraints,
        )
        await session.commit()
        return mission

    async def stream_mission_execution(
        self,
        session: AsyncSession,
        mission_id: uuid.UUID,
        principal: Principal,
        last_event_id: int | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Stream real-time multi-agent execution events with sequence IDs and Last-Event-ID replay."""
        mission = await self.repo.get_by_id(session, mission_id)
        if not mission:
            yield {
                "id": "1",
                "event": "error",
                "data": json.dumps({"error": f"Mission {mission_id} not found"}),
            }
            return

        # Ownership authorization check
        if mission.user_id and principal.is_authenticated:
            if mission.user_id != principal.user_id:
                yield {
                    "id": "1",
                    "event": "error",
                    "data": json.dumps({"error": "Unauthorized access to mission"}),
                }
                return
        elif mission.guest_session_id and principal.is_guest:
            if mission.guest_session_id != principal.guest_session_id:
                yield {
                    "id": "1",
                    "event": "error",
                    "data": json.dumps({"error": "Unauthorized access to mission"}),
                }
                return

        # 1. REPLAY PHASE: Deliver historical events with sequence_id > last_event_id
        start_seq = last_event_id or 0
        historical_events = await self.event_persistence.get_events_after(
            session=session,
            mission_id=mission_id,
            after_seq=start_seq,
        )
        for h_event in historical_events:
            yield {
                "id": str(h_event.sequence_id),
                "event": h_event.event_type,
                "data": json.dumps(h_event.payload, default=str),
            }

        # If mission was already completed, stop stream after historical replay
        if mission.status == "completed":
            return

        # 2. LIVE EXECUTION PHASE
        def map_event_type(step: str) -> str:
            if step in ("parsing_intent", "intent_parsed", "planning_items", "items_planned"):
                return "agent_thought"
            if step == "searching_catalog":
                return "tool_call"
            if step == "catalog_searched":
                return "tool_result"
            if step == "optimizing_basket":
                return "basket_update"
            if step == "grounding_validated":
                return "grounding_check"
            if step == "wayfinding_routed":
                return "wayfinding_route"
            if step == "complete":
                return "mission_complete"
            return "agent_thought"

        try:
            async for event in self.workflow.execute_streaming(
                session=session,
                mission_id=mission.id,
                raw_prompt=mission.raw_text,
                selected_store_ids=mission.selected_store_ids,
                language=mission.language,
            ):
                event_type = map_event_type(event.step)
                payload = event.model_dump(mode="json")

                # Persist event with monotonic sequence_id
                recorded = await self.event_persistence.record_event(
                    session=session,
                    mission_id=mission.id,
                    event_type=event_type,
                    payload=payload,
                )
                await session.commit()

                yield {
                    "id": str(recorded.sequence_id),
                    "event": event_type,
                    "data": json.dumps(payload, default=str),
                }
        except Exception as exc:
            err_payload = {"error": str(exc)}
            recorded_err = await self.event_persistence.record_event(
                session=session,
                mission_id=mission.id,
                event_type="error",
                payload=err_payload,
            )
            await session.commit()
            yield {
                "id": str(recorded_err.sequence_id),
                "event": "error",
                "data": json.dumps(err_payload),
            }

    async def get_mission(
        self,
        session: AsyncSession,
        mission_id: uuid.UUID,
        principal: Principal,
    ) -> MissionResponse:
        """Fetch mission with loaded items, products, and agent execution traces."""
        mission = await self.repo.get_by_id(session, mission_id)
        if not mission:
            raise NotFoundError(detail=f"Mission {mission_id} not found", code="MISSION_NOT_FOUND")

        if mission.user_id and principal.is_authenticated:
            if mission.user_id != principal.user_id:
                raise ForbiddenError(
                    detail="Unauthorized access to this mission", code="MISSION_FORBIDDEN"
                )
        elif mission.guest_session_id and principal.is_guest:
            if mission.guest_session_id != principal.guest_session_id:
                raise ForbiddenError(
                    detail="Unauthorized access to this mission", code="MISSION_FORBIDDEN"
                )

        items_resp: list[MissionItemResponse] = []
        for it in mission.items:
            unit_price = it.unit_price or Decimal("0.00")
            subtotal = unit_price * Decimal(it.quantity)
            items_resp.append(
                MissionItemResponse(
                    id=it.id,
                    mission_id=it.mission_id,
                    product_id=it.product_id,
                    product_name=it.product.name if it.product else it.requested_label,
                    product_brand=it.product.brand if it.product else "",
                    requested_label=it.requested_label,
                    quantity=it.quantity,
                    unit_price=unit_price,
                    subtotal=subtotal,
                    store_id=it.store_id,
                    store_name=it.store.name if it.store else "Store",
                    status=it.status,
                    reason=it.reason,
                    aisle=it.aisle_snapshot,
                    bay=it.bay_snapshot,
                    shelf=it.shelf_snapshot,
                )
            )

        traces_resp: list[MissionTraceResponse] = [
            MissionTraceResponse(
                id=tr.id,
                step=tr.step,
                agent=tr.agent,
                input_summary=tr.input_summary,
                output_summary=tr.output_summary,
                latency_ms=tr.latency_ms,
                created_at=tr.created_at,
            )
            for tr in mission.traces
        ]

        return MissionResponse(
            id=mission.id,
            user_id=mission.user_id,
            guest_session_id=mission.guest_session_id,
            raw_text=mission.raw_text,
            status=mission.status,
            language=mission.language,
            input_modalities=mission.input_modalities,
            constraints=mission.constraints,
            selected_store_ids=mission.selected_store_ids,
            total_cost=mission.total_cost,
            created_at=mission.created_at,
            items=items_resp,
            traces=traces_resp,
        )

    async def list_missions(
        self,
        session: AsyncSession,
        principal: Principal,
        limit: int = 20,
        offset: int = 0,
    ) -> MissionListResponse:
        """Fetch mission history for user or guest."""
        missions = await self.repo.list_for_user(
            session=session,
            user_id=principal.user_id if principal.is_authenticated else None,
            guest_session_id=principal.guest_session_id if principal.is_guest else None,
            limit=limit,
            offset=offset,
        )
        summary_items = [
            MissionListItemResponse(
                id=m.id,
                raw_text=m.raw_text,
                status=m.status,
                total_cost=m.total_cost,
                item_count=len(m.items),
                created_at=m.created_at,
            )
            for m in missions
        ]
        return MissionListResponse(missions=summary_items, total=len(summary_items))

    async def update_mission_item(
        self,
        session: AsyncSession,
        mission_id: uuid.UUID,
        item_id: uuid.UUID,
        principal: Principal,
        quantity: int,
    ) -> MissionItemResponse:
        """Update an item quantity in a basket and recalculate mission total."""
        mission = await self.repo.get_by_id(session, mission_id)
        if not mission:
            raise NotFoundError(detail=f"Mission {mission_id} not found", code="MISSION_NOT_FOUND")

        if mission.user_id and principal.is_authenticated:
            if mission.user_id != principal.user_id:
                raise ForbiddenError(
                    detail="Unauthorized access to this mission", code="MISSION_FORBIDDEN"
                )
        elif mission.guest_session_id and principal.is_guest:
            if mission.guest_session_id != principal.guest_session_id:
                raise ForbiddenError(
                    detail="Unauthorized access to this mission", code="MISSION_FORBIDDEN"
                )

        item = await self.repo.get_item_by_id(session, item_id)
        if not item or item.mission_id != mission_id:
            raise NotFoundError(detail="Item not found in mission", code="ITEM_NOT_FOUND")

        if quantity <= 0:
            await session.delete(item)
            await session.flush()
        else:
            await self.repo.update_item_quantity(session, item, quantity)

        # Recalculate total cost
        refreshed_mission = await self.repo.get_by_id(session, mission_id)
        if refreshed_mission:
            new_total = sum(
                (
                    (it.unit_price or Decimal("0.00")) * Decimal(it.quantity)
                    for it in refreshed_mission.items
                ),
                start=Decimal("0.00"),
            )
            refreshed_mission.total_cost = new_total
            await session.commit()

        unit_price = item.unit_price or Decimal("0.00")
        subtotal = unit_price * Decimal(quantity)

        return MissionItemResponse(
            id=item.id,
            mission_id=item.mission_id,
            product_id=item.product_id,
            product_name=item.product.name if item.product else item.requested_label,
            product_brand=item.product.brand if item.product else "",
            requested_label=item.requested_label,
            quantity=quantity,
            unit_price=unit_price,
            subtotal=subtotal,
            store_id=item.store_id,
            store_name=item.store.name if item.store else "Store",
            status=item.status,
            reason=item.reason,
            aisle=item.aisle_snapshot,
            bay=item.bay_snapshot,
            shelf=item.shelf_snapshot,
        )

    async def get_mission_route(
        self,
        session: AsyncSession,
        mission_id: uuid.UUID,
        principal: Principal,
    ) -> MissionRouteResponse:
        """Generate wayfinding path for mission items."""
        mission = await self.repo.get_by_id(session, mission_id)
        if not mission:
            raise NotFoundError(detail=f"Mission {mission_id} not found", code="MISSION_NOT_FOUND")

        if mission.user_id and principal.is_authenticated:
            if mission.user_id != principal.user_id:
                raise ForbiddenError(
                    detail="Unauthorized access to this mission", code="MISSION_FORBIDDEN"
                )
        elif mission.guest_session_id and principal.is_guest:
            if mission.guest_session_id != principal.guest_session_id:
                raise ForbiddenError(
                    detail="Unauthorized access to this mission", code="MISSION_FORBIDDEN"
                )

        store_names: dict[uuid.UUID, str] = {}
        basket_items: list[OptimizedBasketItem] = []

        for it in mission.items:
            s_name = it.store.name if it.store else "Store"
            if it.store_id:
                store_names[it.store_id] = s_name

            basket_items.append(
                OptimizedBasketItem(
                    product_id=it.product_id or uuid.uuid4(),
                    requested_label=it.requested_label,
                    name=it.product.name if it.product else it.requested_label,
                    brand=it.product.brand if it.product else "",
                    quantity=it.quantity,
                    unit_price=it.unit_price or Decimal("0.00"),
                    subtotal=(it.unit_price or Decimal("0.00")) * Decimal(it.quantity),
                    store_id=it.store_id or uuid.uuid4(),
                    store_name=s_name,
                    aisle=it.aisle_snapshot or 1,
                    bay=it.bay_snapshot or 1,
                    shelf=it.shelf_snapshot or 1,
                    status=it.status,
                )
            )

        stops = self.wayfinding.generate_route(basket_items, store_names)
        waypoints = [
            RouteWaypointResponse(
                step_number=s.stop_order,
                store_id=s.store_id,
                store_name=s.store_name,
                aisle=s.aisle,
                bay=s.bay,
                shelf=s.shelf,
                product_name=", ".join(s.items),
                quantity=1,
                action=s.instruction,
            )
            for s in stops
        ]

        return MissionRouteResponse(
            mission_id=mission.id,
            total_stops=len(waypoints),
            waypoints=waypoints,
        )

    async def get_mission_inspector_telemetry(
        self,
        session: AsyncSession,
        mission_id: uuid.UUID,
        principal: Principal,
    ) -> dict[str, Any]:
        """Compile comprehensive glass-box inspector telemetry for a mission."""
        mission = await self.repo.get_by_id(session, mission_id)
        if not mission:
            raise NotFoundError(detail=f"Mission {mission_id} not found", code="MISSION_NOT_FOUND")

        if mission.user_id and principal.is_authenticated:
            if mission.user_id != principal.user_id:
                raise ForbiddenError(
                    detail="Unauthorized access to this mission", code="MISSION_FORBIDDEN"
                )
        elif mission.guest_session_id and principal.is_guest:
            if mission.guest_session_id != principal.guest_session_id:
                raise ForbiddenError(
                    detail="Unauthorized access to this mission", code="MISSION_FORBIDDEN"
                )

        events = await self.event_persistence.get_events_after(session, mission_id, after_seq=0)

        thoughts = [e.payload for e in events if e.event_type == "agent_thought"]
        tool_calls = [e.payload for e in events if e.event_type == "tool_call"]
        tool_results = [e.payload for e in events if e.event_type == "tool_result"]
        grounding_checks = [e.payload for e in events if e.event_type == "grounding_check"]
        basket_updates = [e.payload for e in events if e.event_type == "basket_update"]

        return {
            "mission_id": str(mission.id),
            "status": mission.status,
            "raw_text": mission.raw_text,
            "selected_store_ids": [str(s) for s in mission.selected_store_ids],
            "total_cost": float(mission.total_cost or 0),
            "item_count": len(mission.items),
            "telemetry": {
                "model": "gemini-2.5-flash",
                "event_count": len(events),
                "tool_call_count": len(tool_calls),
                "grounding_check_count": len(grounding_checks),
            },
            "thoughts": thoughts,
            "tool_calls": tool_calls,
            "tool_results": tool_results,
            "grounding_checks": grounding_checks,
            "basket_updates": basket_updates,
            "events": [
                {
                    "sequence_id": e.sequence_id,
                    "event_type": e.event_type,
                    "payload": e.payload,
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                }
                for e in events
            ],
        }
