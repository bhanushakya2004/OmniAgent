"""Abstract analytics sink port for merchant demand telemetry and KPIs."""

import uuid
from decimal import Decimal
from typing import Protocol

from pydantic import BaseModel


class DemandSignal(BaseModel):
    """Aggregated shopper intent demand velocity."""

    query: str
    mention_count: int
    unmet_count: int
    trending_score: float


class StoreOverviewKpis(BaseModel):
    """Store level operational KPIs."""

    store_id: uuid.UUID
    store_name: str
    total_missions: int
    total_grounded_gmv: Decimal
    at_risk_skus_count: int
    open_restock_tasks_count: int


class AnalyticsSink(Protocol):
    """Port interface for querying demand signals, stockout velocity, and KPI metrics."""

    async def get_overview_kpis(self, store_id: uuid.UUID) -> StoreOverviewKpis:
        """Calculate store KPI aggregates."""
        ...

    async def get_demand_signals(self, store_id: uuid.UUID, limit: int = 10) -> list[DemandSignal]:
        """Aggregate top requested queries and unmet demand counts."""
        ...
