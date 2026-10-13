"""Service for Human-in-the-Loop (HITL) merchant action proposals."""

import datetime
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from omnimission.core.errors import BadRequestError, NotFoundError
from omnimission.models.action_proposal import ActionProposal
from omnimission.models.inventory import StoreInventory
from omnimission.models.restock_task import RestockTask


class ActionProposalService:
    """Orchestrates proposal generation by Store Analyst and review/execution by merchants."""

    async def create_proposal(
        self,
        session: AsyncSession,
        store_id: uuid.UUID,
        action_type: str,
        title: str,
        description: str,
        payload: dict[str, Any],
        created_by: uuid.UUID | None = None,
    ) -> ActionProposal:
        """Create a pending action proposal drafted by the Store Analyst."""
        proposal = ActionProposal(
            id=uuid.uuid4(),
            store_id=store_id,
            created_by=created_by,
            action_type=action_type,
            title=title,
            description=description,
            payload=payload,
            status="pending_approval",
        )
        session.add(proposal)
        await session.flush()
        return proposal

    async def list_proposals(
        self,
        session: AsyncSession,
        store_id: uuid.UUID,
        status: str | None = None,
    ) -> list[ActionProposal]:
        """List proposals for a physical store, optionally filtered by status."""
        stmt = select(ActionProposal).where(ActionProposal.store_id == store_id)
        if status:
            stmt = stmt.where(ActionProposal.status == status)
        stmt = stmt.order_by(ActionProposal.created_at.desc())
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_proposal(
        self,
        session: AsyncSession,
        proposal_id: uuid.UUID,
    ) -> ActionProposal:
        """Retrieve a single action proposal by UUID."""
        stmt = select(ActionProposal).where(ActionProposal.id == proposal_id)
        result = await session.execute(stmt)
        proposal = result.scalar_one_or_none()
        if not proposal:
            raise NotFoundError(f"Action proposal {proposal_id} not found")
        return proposal

    async def approve_proposal(
        self,
        session: AsyncSession,
        proposal_id: uuid.UUID,
        user_id: uuid.UUID,
        decision_note: str | None = None,
    ) -> ActionProposal:
        """Approve and execute a proposal."""
        proposal = await self.get_proposal(session, proposal_id)
        if proposal.status != "pending_approval":
            raise BadRequestError(f"Cannot approve proposal with status '{proposal.status}'")

        # Execute business action based on action_type
        if proposal.action_type in ("restock_inventory", "create_restock_task"):
            product_id_str = proposal.payload.get("product_id")
            recommended_qty = int(proposal.payload.get("recommended_qty", 10))
            reason = proposal.payload.get("reason", proposal.description)

            if product_id_str:
                p_uuid = uuid.UUID(str(product_id_str))
                # Check current inventory position
                inv_stmt = select(StoreInventory).where(
                    StoreInventory.store_id == proposal.store_id,
                    StoreInventory.product_id == p_uuid,
                )
                inv_res = await session.execute(inv_stmt)
                inv = inv_res.scalar_one_or_none()

                current_qty = inv.stock_qty if inv else 0
                aisle = inv.aisle if inv else 1
                bay = inv.bay if inv else 1
                shelf = inv.shelf if inv else 1

                task = RestockTask(
                    id=uuid.uuid4(),
                    store_id=proposal.store_id,
                    product_id=p_uuid,
                    aisle=aisle,
                    bay=bay,
                    shelf=shelf,
                    current_qty=current_qty,
                    recommended_qty=recommended_qty,
                    reason=reason,
                    status="pending",
                )
                session.add(task)

        elif proposal.action_type == "update_stock":
            product_id_str = proposal.payload.get("product_id")
            new_qty = proposal.payload.get("new_stock_level")
            if product_id_str and new_qty is not None:
                p_uuid = uuid.UUID(str(product_id_str))
                inv_stmt = select(StoreInventory).where(
                    StoreInventory.store_id == proposal.store_id,
                    StoreInventory.product_id == p_uuid,
                )
                inv_res = await session.execute(inv_stmt)
                inv = inv_res.scalar_one_or_none()
                if inv:
                    inv.stock_qty = int(new_qty)

        proposal.status = "approved"
        proposal.decision_note = decision_note
        proposal.decided_at = datetime.datetime.now(datetime.UTC)
        proposal.decided_by = user_id

        await session.flush()
        return proposal

    async def reject_proposal(
        self,
        session: AsyncSession,
        proposal_id: uuid.UUID,
        user_id: uuid.UUID,
        decision_note: str | None = None,
    ) -> ActionProposal:
        """Reject a pending proposal."""
        proposal = await self.get_proposal(session, proposal_id)
        if proposal.status != "pending_approval":
            raise BadRequestError(f"Cannot reject proposal with status '{proposal.status}'")

        proposal.status = "rejected"
        proposal.decision_note = decision_note
        proposal.decided_at = datetime.datetime.now(datetime.UTC)
        proposal.decided_by = user_id

        await session.flush()
        return proposal
