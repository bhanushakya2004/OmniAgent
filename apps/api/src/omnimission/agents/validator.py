"""Deterministic Grounding Validator enforcing physical catalog accuracy and preventing hallucinations."""

import uuid
from decimal import Decimal

from omnimission.agents.schemas import OptimizedBasketItem
from omnimission.core.logging import get_logger
from omnimission.ports.search_backend import SearchResult


class GroundingViolation(Exception):
    """Raised when an ungrounded SKU or fabricated price is detected."""

    pass


class GroundingValidator:
    """Validator ensuring every basket item originates from verified tool search results."""

    def __init__(self) -> None:
        self.logger = get_logger("grounding_validator")

    def validate_and_filter(
        self,
        basket_items: list[OptimizedBasketItem],
        tool_results: list[SearchResult],
        selected_store_ids: list[uuid.UUID],
    ) -> list[OptimizedBasketItem]:
        """Validate basket items against tool results.

        Corrects any discrepancies with authoritative database ground truth and drops fabricated items.
        """
        # Build lookup table of verified search results by (product_id, store_id)
        verified_lookup: dict[tuple[uuid.UUID, uuid.UUID], SearchResult] = {
            (r.product_id, r.store_id): r for r in tool_results
        }
        product_only_lookup: dict[uuid.UUID, list[SearchResult]] = {}
        for r in tool_results:
            product_only_lookup.setdefault(r.product_id, []).append(r)

        valid_store_set = set(selected_store_ids)
        grounded_basket: list[OptimizedBasketItem] = []

        for item in basket_items:
            # Check 1: Does product exist in search results?
            if item.product_id not in product_only_lookup:
                self.logger.warning(
                    "hallucinated_product_dropped",
                    product_id=str(item.product_id),
                    name=item.name,
                )
                continue

            # Check 2: Is store_id valid and selected?
            if item.store_id not in valid_store_set:
                self.logger.warning(
                    "invalid_store_id_dropped",
                    store_id=str(item.store_id),
                    name=item.name,
                )
                continue

            # Check 3: Check exact (product_id, store_id) match
            hit = verified_lookup.get((item.product_id, item.store_id))
            if not hit:
                # If store mismatch, attach to the first available selected store that has it in stock
                available_hits = product_only_lookup[item.product_id]
                hit = available_hits[0]
                item.store_id = hit.store_id

            # Check 4: Enforce authoritative price and aisle coordinates from DB record
            authoritative_unit_price = Decimal(str(hit.price))
            if item.unit_price != authoritative_unit_price:
                self.logger.info(
                    "price_corrected_from_db",
                    item=item.name,
                    llm_price=str(item.unit_price),
                    db_price=str(authoritative_unit_price),
                )
                item.unit_price = authoritative_unit_price

            item.subtotal = item.unit_price * Decimal(item.quantity)
            item.aisle = hit.aisle
            item.bay = hit.bay
            item.shelf = hit.shelf
            item.name = hit.name
            item.brand = hit.brand

            grounded_basket.append(item)

        return grounded_basket

    def calculate_total(self, items: list[OptimizedBasketItem]) -> Decimal:
        """Deterministic Decimal arithmetic for basket total."""
        return sum((item.subtotal for item in items), Decimal("0.00"))
