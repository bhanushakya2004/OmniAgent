"""Deterministic Wayfinding Service generating in-store walking routes."""

import uuid
from collections import defaultdict

from omnimission.agents.schemas import OptimizedBasketItem, WayfindingStop


class WayfindingService:
    """Calculates ordered physical store walking path (aisle -> bay -> shelf)."""

    def generate_route(
        self,
        basket_items: list[OptimizedBasketItem],
        store_names: dict[uuid.UUID, str] | None = None,
    ) -> list[WayfindingStop]:
        """Generate ordered stops along physical aisles."""
        names = store_names or {}
        # Group items by store and (aisle, bay, shelf) location
        grouped_by_store: dict[uuid.UUID, list[OptimizedBasketItem]] = defaultdict(list)
        for item in basket_items:
            grouped_by_store[item.store_id].append(item)

        stops: list[WayfindingStop] = []
        global_stop_order = 1

        for store_id, items in grouped_by_store.items():
            store_name = names.get(store_id, f"Store {str(store_id)[:8]}")

            # Group items by physical coordinate
            coordinate_groups: dict[tuple[int, int, int], list[str]] = defaultdict(list)
            for it in items:
                coordinate_groups[(it.aisle, it.bay, it.shelf)].append(it.name)

            # Sort coordinates monotonically: aisle ASC, bay ASC, shelf ASC
            sorted_coordinates = sorted(coordinate_groups.keys(), key=lambda c: (c[0], c[1], c[2]))

            for aisle, bay, shelf in sorted_coordinates:
                picked_items = coordinate_groups[(aisle, bay, shelf)]
                items_str = ", ".join(picked_items)
                instruction = (
                    f"Proceed to Aisle {aisle}, Bay {bay}. Pick {items_str} from Shelf {shelf}."
                )

                stops.append(
                    WayfindingStop(
                        stop_order=global_stop_order,
                        store_id=store_id,
                        store_name=store_name,
                        aisle=aisle,
                        bay=bay,
                        shelf=shelf,
                        items=picked_items,
                        instruction=instruction,
                    )
                )
                global_stop_order += 1

        return stops
