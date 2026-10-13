"""Substitution Agent evaluating in-stock alternatives and explaining functional trade-offs."""

from decimal import Decimal

from omnimission.agents.schemas import SubstitutionProposal
from omnimission.core.logging import get_logger
from omnimission.ports.search_backend import SearchResult


class SubstitutionEvaluator:
    """Evaluates closest in-stock candidates when an item is unavailable or exceeds budget."""

    def __init__(self) -> None:
        self.logger = get_logger("substitution_agent")

    def find_best_substitute(
        self,
        needed_label: str,
        category: str,
        dietary_tags: list[str],
        available_candidates: list[SearchResult],
        budget_remaining: Decimal | None = None,
    ) -> SubstitutionProposal | None:
        """Find the most compatible in-stock substitute from available tool results."""
        if not available_candidates:
            return None

        # Filter candidates by dietary constraints
        compatible = []
        for c in available_candidates:
            if c.stock_qty <= 0:
                continue

            # If dietary tag required, ensure candidate satisfies it
            violates_dietary = False
            for req_tag in dietary_tags:
                if req_tag not in c.dietary_tags:
                    violates_dietary = True
                    break

            if not violates_dietary:
                compatible.append(c)

        if not compatible:
            compatible = [c for c in available_candidates if c.stock_qty > 0]

        if not compatible:
            return None

        # Sort by budget compatibility if budget is tight
        if budget_remaining is not None and budget_remaining > 0:
            affordable = [c for c in compatible if c.price <= budget_remaining]
            if affordable:
                compatible = affordable

        best = compatible[0]

        trade_off = (
            f"In-stock substitute for {needed_label}. Satisfies {category} requirement "
            f"at ₹{best.price} located in Aisle {best.aisle}."
        )

        return SubstitutionProposal(
            original_needed=needed_label,
            substitute_product_id=best.product_id,
            substitute_name=best.name,
            unit_price=best.price,
            reason=f"Selected alternative matching {category} and dietary criteria.",
            trade_off=trade_off,
        )
