"""Missions API endpoints for creating, streaming, editing, and routing missions."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from omnimission.core.deps import get_current_user, require_user
from omnimission.db.session import get_db_session
from omnimission.models.user import User
from omnimission.schemas.mission import (
    CreateMissionRequest,
    MissionItemResponse,
    MissionListResponse,
    MissionResponse,
    MissionRouteResponse,
    UpdateMissionItemRequest,
)
from omnimission.services.mission_service import MissionService

router = APIRouter(prefix="/missions", tags=["missions"])


def get_mission_service() -> MissionService:
    """Dependency provider for MissionService."""
    return MissionService()


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new mission",
    response_model=dict[str, Any],
)
async def create_mission(
    request: CreateMissionRequest,
    current_user: User = Depends(require_user),
    session: AsyncSession = Depends(get_db_session),
    mission_service: MissionService = Depends(get_mission_service),
) -> dict[str, Any]:
    """Initiate a shopping mission across specified physical stores."""
    mission = await mission_service.create_mission(
        session=session,
        user_id=current_user.id,
        request=request,
    )
    return {
        "id": str(mission.id),
        "status": mission.status,
        "stream_url": f"/api/v1/missions/{mission.id}/stream",
    }


@router.get(
    "/{mission_id}/stream",
    summary="Stream real-time agent workflow events via SSE",
)
async def stream_mission(
    mission_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    mission_service: MissionService = Depends(get_mission_service),
) -> EventSourceResponse:
    """Server-Sent Events (SSE) stream emitting real-time agent thought steps and final grounded basket."""
    event_generator = mission_service.stream_mission_execution(
        session=session,
        mission_id=mission_id,
        user_id=current_user.id,
    )
    return EventSourceResponse(event_generator)


@router.get(
    "/{mission_id}",
    response_model=MissionResponse,
    summary="Get mission details, grounded basket, and traces",
)
async def get_mission(
    mission_id: uuid.UUID,
    current_user: User = Depends(require_user),
    session: AsyncSession = Depends(get_db_session),
    mission_service: MissionService = Depends(get_mission_service),
) -> MissionResponse:
    """Retrieve full mission entity with verified items, physical aisle coordinates, and execution trace."""
    return await mission_service.get_mission(
        session=session,
        mission_id=mission_id,
        user_id=current_user.id,
    )


@router.get(
    "",
    response_model=MissionListResponse,
    summary="List past missions for authenticated user",
)
async def list_missions(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_user),
    session: AsyncSession = Depends(get_db_session),
    mission_service: MissionService = Depends(get_mission_service),
) -> MissionListResponse:
    """List historical shopping missions."""
    return await mission_service.list_missions(
        session=session,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )


@router.patch(
    "/{mission_id}/items/{item_id}",
    response_model=MissionItemResponse,
    summary="Update quantity or remove an item from basket",
)
async def update_mission_item(
    mission_id: uuid.UUID,
    item_id: uuid.UUID,
    request: UpdateMissionItemRequest,
    current_user: User = Depends(require_user),
    session: AsyncSession = Depends(get_db_session),
    mission_service: MissionService = Depends(get_mission_service),
) -> MissionItemResponse:
    """Update item quantity (0 removes item from basket) and recalculates total."""
    return await mission_service.update_mission_item(
        session=session,
        mission_id=mission_id,
        item_id=item_id,
        user_id=current_user.id,
        quantity=request.quantity,
    )


@router.get(
    "/{mission_id}/route",
    response_model=MissionRouteResponse,
    summary="Get monotonic in-store wayfinding walking path",
)
async def get_mission_route(
    mission_id: uuid.UUID,
    current_user: User = Depends(require_user),
    session: AsyncSession = Depends(get_db_session),
    mission_service: MissionService = Depends(get_mission_service),
) -> MissionRouteResponse:
    """Calculate and return ordered walking path through physical aisles and shelves."""
    return await mission_service.get_mission_route(
        session=session,
        mission_id=mission_id,
        user_id=current_user.id,
    )
