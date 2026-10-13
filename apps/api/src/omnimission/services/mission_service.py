"""Mission service orchestrating mission creation, SSE event streaming, basket edits, and wayfinding."""

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


class MissionService:
    """Business logic for shopper mission lifecycle."""

    def __init__(self) -> None:
        self.repo = MissionRepository()
        self.workflow = MissionWorkflow()
        self.wayfinding = WayfindingService()

    async def create_mission(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        request: CreateMissionRequest,
    ) -> Mission:
        """Create a pending mission record."""
        mission = await self.repo.create_mission(
            session=session,
            user_id=user_id,
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
        user_id: uuid.UUID,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Stream real-time multi-agent execution events for a mission via SSE."""
        mission = await self.repo.get_by_id(session, mission_id)
        if not mission:
            yield {
                "event": "error",
                "data": json.dumps({"error": f"Mission {mission_id} not found"}),
            }
            return

        if mission.user_id != user_id:
            yield {
                "event": "error",
                "data": json.dumps({"error": "Unauthorized access to mission"}),
            }
            return

        if mission.status == "completed":
            # Replay existing traces if mission was already completed
            for trace in mission.traces:
                yield {
                    "event": "timeline",
                    "data": json.dumps(
                        {
                            "step": trace.step,
                            "status": "completed",
                            "agent": trace.agent,
                            "title": trace.step.replace("_", " ").title(),
                            "description": trace.output_summary,
                            "latency_ms": trace.latency_ms,
                        }
                    ),
                }
            yield {
                "event": "done",
                "data": json.dumps(
                    {
                        "mission_id": str(mission.id),
                        "status": "completed",
                        "total_cost": str(mission.total_cost) if mission.total_cost else "0.00",
                    }
                ),
            }
            return

        try:
            async for event in self.workflow.execute_streaming(
                session=session,
                mission_id=mission.id,
                raw_prompt=mission.raw_text,
                selected_store_ids=mission.selected_store_ids,
                language=mission.language,
            ):
                event_name = "done" if event.step == "complete" else "timeline"
                yield {
                    "event": event_name,
                    "data": json.dumps(event.model_dump(), default=str),
                }
        except Exception as exc:
            yield {
                "event": "error",
                "data": json.dumps({"error": str(exc)}),
            }

    async def get_mission(
        self,
        session: AsyncSession,
        mission_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> MissionResponse:
        """Fetch mission with loaded items, products, and agent execution traces."""
        mission = await self.repo.get_by_id(session, mission_id)
        if not mission:
            raise NotFoundError(detail=f"Mission {mission_id} not found", code="MISSION_NOT_FOUND")

        if mission.user_id != user_id:
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
        user_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> MissionListResponse:
        """Fetch mission history for user."""
        missions = await self.repo.list_for_user(session, user_id, limit=limit, offset=offset)
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
        user_id: uuid.UUID,
        quantity: int,
    ) -> MissionItemResponse:
        """Update an item quantity in a basket and recalculate mission total."""
        mission = await self.repo.get_by_id(session, mission_id)
        if not mission:
            raise NotFoundError(detail=f"Mission {mission_id} not found", code="MISSION_NOT_FOUND")

        if mission.user_id != user_id:
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
        user_id: uuid.UUID,
    ) -> MissionRouteResponse:
        """Compute monotonic in-store walking path for completed mission."""
        mission = await self.repo.get_by_id(session, mission_id)
        if not mission:
            raise NotFoundError(detail=f"Mission {mission_id} not found", code="MISSION_NOT_FOUND")

        if mission.user_id != user_id:
            raise ForbiddenError(
                detail="Unauthorized access to this mission", code="MISSION_FORBIDDEN"
            )

        # Convert mission items into OptimizedBasketItem for WayfindingService
        basket_items: list[OptimizedBasketItem] = []
        store_names: dict[uuid.UUID, str] = {}

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
